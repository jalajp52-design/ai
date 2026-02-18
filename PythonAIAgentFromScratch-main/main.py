from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from tools import search_tool, wiki_tool, save_tool, browse_tool, ai_chat_tool
import google.generativeai as genai
import time
import logging
import os
import re
import requests
import math

import json

load_dotenv()

DISCOVERED_MODEL = "gemini-2.0-flash"
DB_FILE = "knowledge.json"

# --- Knowledge Base ---
def load_knowledge():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

knowledge_base = load_knowledge()

def save_knowledge():
    try:
        with open(DB_FILE, "w") as f:
            json.dump(knowledge_base, f, indent=4)
    except:
        pass

collection = None

def retrieve_knowledge(query: str, n_results: int = 2, threshold: float = 0.5):
    query_lower = query.lower()
    # Prioritize exact matches
    if query_lower in knowledge_base:
        return knowledge_base[query_lower], 1.0

    # Special handling for "full form of" queries
    if query_lower.startswith("what is full form of "):
        acronym = query_lower.split("what is full form of ")[1].strip()
        if acronym in knowledge_base:
            return knowledge_base[acronym], 1.0

    stop_words = {'what', 'is', 'the', 'of', 'and', 'a', 'in', 'to', 'it', 'can', 'you', 'for', 'on', 'with', 'as', 'provide'}
    query_words = set(query_lower.split()) - stop_words
    if not query_words: return "", 0.0

    scored_matches = []
    for topic, content in knowledge_base.items():
        topic_words = set(topic.lower().split())
        intersection = query_words.intersection(topic_words)
        if intersection:
            score = len(intersection) / len(query_words)
            # Increase threshold for scored matches to avoid false positives
            if score >= 0.8:
                scored_matches.append((score, content))

    scored_matches.sort(reverse=True, key=lambda x: x[0])
    top_matches = scored_matches[:n_results]
    max_score = top_matches[0][0] if top_matches else 0.0
    knowledge = "\n---\n".join([content for _, content in top_matches]) if top_matches else ""
    return knowledge, max_score

def store_knowledge(topic: str, content: str):
    knowledge_base[topic] = content
    save_knowledge()

def delete_knowledge(topic: str):
    if topic in knowledge_base:
        del knowledge_base[topic]
        save_knowledge()
        return True
    return False

def train_agent(topic: str, content: str):
    """Manual training function to add or update knowledge."""
    store_knowledge(topic, content)
    print(f"✅ Trained on: {topic}")

def review_knowledge():
    """Review and potentially correct knowledge entries."""
    print("Current Knowledge Base:")
    for topic, content in knowledge_base.items():
        print(f"- {topic}: {content[:100]}...")
    # In a real implementation, you could add interactive editing here

# --- The "Universal Brain" Priority ---
# --- Custom Robust Gemini Client (Bypasses gRPC hangs) ---
class GeminiRequestsLLM:
    def __init__(self, model="gemini-2.0-flash"):
        self.model = model
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def invoke(self, messages):
        # Convert LangChain messages to Gemini format
        gemini_msgs = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            parts = []
            if isinstance(m["content"], list):
                parts = m["content"]
            else:
                parts = [{"text": m["content"]}]
            gemini_msgs.append({"role": role, "parts": parts})
        
        payload = {"contents": gemini_msgs}
        try:
            response = requests.post(self.url, json=payload, timeout=30)
            data = response.json()
            if 'candidates' in data:
                text = data['candidates'][0]['content']['parts'][0]['text']
                # Mock a LangChain response object
                class Response:
                    def __init__(self, content): self.content = content
                return Response(text)
            else:
                raise Exception(f"Gemini Error: {data}")
        except Exception as e:
            raise e

# --- The "Universal Brain" Priority ---
def get_providers():
    providers = []
    # 1. Gemini (Custom Request Based - Most Reliable on Windows)
    if os.getenv('GOOGLE_API_KEY'):
        providers.append((lambda: GeminiRequestsLLM(model="gemini-2.0-flash"), "Gemini (Cloud)"))

    # 2. Anthropic (Very reliable)
    if os.getenv('ANTHROPIC_API_KEY'):
        providers.append((lambda: ChatAnthropic(model="claude-3-5-sonnet-20240620", api_key=os.getenv('ANTHROPIC_API_KEY')), "Anthropic (Claude)"))

    # 3. Groq
    if os.getenv('GROQ_API_KEY'):
        providers.append((lambda: ChatGroq(model="llama-3.1-70b-versatile", groq_api_key=os.getenv('GROQ_API_KEY')), "Groq"))

    # 4. Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=0.5)
        if response.status_code == 200:
            providers.append((lambda: Ollama(model="llama3.2"), "Ollama (Unlimited Local)"))
    except: pass

    # 5. OpenAI
    if os.getenv('OPENAI_API_KEY'):
        providers.append((lambda: ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv('OPENAI_API_KEY')), "OpenAI"))

    return providers

def correct_spelling(query: str):
    """
    Checks for spelling errors and corrects them using the LLM.
    Returns (corrected_query, was_corrected)
    """
    # Skip correction for very short queries or math expressions
    if len(query) < 4 or (re.search(r'\d', query) and re.search(r'[\+\-\*\/]', query)):
        return query, False

    providers = get_providers()
    if not providers: return query, False

    prompt = f"Check this query for spelling errors: '{query}'. If it has typos (e.g. 'diramon' -> 'Doraemon'), return ONLY the corrected query. If it is correct, return 'OK'."

    for llm_factory, name in providers:
        try:
            llm = llm_factory()
            response = ""
            if isinstance(llm, GeminiRequestsLLM):
                response = llm.invoke([{"role": "user", "content": prompt}]).content
            else:
                # LangChain models usually accept string prompts
                res = llm.invoke(prompt)
                response = res.content if hasattr(res, 'content') else str(res)

            response = response.strip().replace('"', '').replace("'", "")
            if response.upper() == "OK": return query, False
            if response and response.lower() != query.lower() and len(response) < len(query) * 2:
                return response, True
        except: continue
    return query, False

chat_history = []
system_prompt = "You are a learning AI Agent. Prioritize using stored knowledge for accurate responses. Use tools only when necessary and knowledge is insufficient. Start your response with 'Learning...' if you found new info."
tools = [search_tool, wiki_tool, save_tool, browse_tool, ai_chat_tool]

def run_agent(query: str, history: list = None, file_content: str = None, is_image: bool = False):
    if history is None: history = []
    
    # --- File Context Injection ---
    file_context = ""
    image_part = None
    if file_content:
        if is_image:
            image_part = {
                "inline_data": {
                    "mime_type": "image/png", # Defaulting to PNG, Gemini handles others too
                    "data": file_content
                }
            }
            print(f"🖼️ Analyzing image content")
        else:
            file_context = f"\n\n[FILE CONTEXT]:\n{file_content}\n"
            print(f"📁 Analyzing file content ({len(file_content)} chars)")

    # --- Auto-Correction ---
    correction_note = ""
    corrected_query, was_corrected = correct_spelling(query)
    if was_corrected:
        correction_note = f"**Did you mean: {corrected_query}?**\n\n"
        query = corrected_query

    q_low = query.lower()
    if re.search(r'(\d+)\s*([\+\-\*\/])\s*(\d+)', query):
        try: return correction_note + f"The answer is {eval(re.search(r'(\d+)\s*([\+\-\*\/])\s*(\d+)', query).group(0))}.", "", "Local Logic"
        except: pass
    
    if not file_content and not image_part:
        if "hello" in q_low or "hi" in q_low:
            return correction_note + "Hello! I'm your AI agent. I can learn from you and the web. What's on your mind?", "", "Local Logic"

    # --- AGENT FAQ SYSTEM (Local & Instant) ---
    faq = {
        "unlimited": "Yes! You can use me unlimitedly. If your cloud API quotas (Gemini/OpenAI) are full, I automatically switch to 'Unlimited Search Mode' or 'Local Engine' if you have Ollama installed. No more 'Quota Exceeded' errors!",
        "who are you": "I am your AI Learning Agent. I can search the web, learn from our conversations, and keep growing my knowledge base!",
        "how to use": "Just ask me anything! I search the web if I don't know the answer, and I save what I learn in my local memory.",
        "api": "I support Gemini, OpenAI, Claude, Groq, and Ollama. Currently, I am using a fallback system to ensure you always get an answer even if keys are limited."
    }
    for key, val in faq.items():
        if key in q_low:
            return correction_note + val, "", "Local System FAQ"

    # --- OPINION DETECTION ---
    opinion_keywords = ["do you like", "what do you think", "your opinion", "how do you feel"]
    if any(kw in q_low for kw in opinion_keywords):
        # Extract the topic (simple heuristic: words after the keyword)
        topic = query.lower()
        for kw in opinion_keywords:
            if kw in topic:
                topic = topic.split(kw)[-1].strip()
                break
        # Check knowledge base for specific opinions
        relevant_knowledge, knowledge_score = retrieve_knowledge(topic)
        if knowledge_score >= 0.5 and relevant_knowledge:
            response = f"Based on what I've learned, {relevant_knowledge}, but opinions vary greatly among individuals."
        else:
            opinions = ["interesting", "controversial", "complex", "fascinating", "challenging"]
            opinion = opinions[hash(topic) % len(opinions)]
            response = f"As an AI, I find {topic} {opinion}, but opinions vary greatly among individuals."
        return correction_note + response, "", "AI Opinion"

    # --- MATH COMPUTATION ---
    math_functions = {
        'log': 'math.log',
        'ln': 'math.log',  # natural log
        'sin': 'math.sin',
        'cos': 'math.cos',
        'tan': 'math.tan',
        'sqrt': 'math.sqrt',
        'exp': 'math.exp',
        'pi': 'math.pi',
        'e': 'math.e'
    }
    math_pattern = r'\b(?:log|ln|sin|cos|tan|sqrt|exp|pi|e)\b'
    if re.search(math_pattern, q_low):
        # Extract the math expression from the query
        expr = query
        if "what is" in q_low:
            expr = query.split("what is", 1)[1].strip()
        # Replace function names with math. prefix
        for func, math_func in math_functions.items():
            expr = re.sub(r'\b' + re.escape(func) + r'\b', math_func, expr)
        # Replace ^ with ** for exponentiation
        expr = expr.replace('^', '**')
        try:
            result = eval(expr, {"__builtins__": None}, {"math": math, "pi": math.pi, "e": math.e})
            return correction_note + f"The result is {result}.", "", "Math Computation"
        except Exception as e:
            pass  # Fall through to normal processing

    relevant_knowledge, knowledge_score = retrieve_knowledge(query)
    messages = []
    for role, content in history[-5:]:
        messages.append({"role": "user" if role == "human" else "assistant", "content": content})

    # If we have high-confidence knowledge, use it directly without searching
    if knowledge_score >= 0.5 and relevant_knowledge:
        return correction_note + relevant_knowledge, relevant_knowledge, "Knowledge Base"

    full_query_content = []
    if image_part:
        full_query_content.append(image_part)
    
    text_content = f"Learned Context: {relevant_knowledge}\n\nUser: {query}" if relevant_knowledge else query
    if file_context:
        text_content = f"{file_context}\n\n{text_content}"
    
    full_query_content.append({"text": text_content})
    
    messages.append({"role": "user", "content": full_query_content})

    providers = get_providers()
    last_error = ""
    for llm_factory, name in providers:
        try:
            llm = llm_factory()
            if isinstance(llm, GeminiRequestsLLM):
                result = llm.invoke(messages)
                response = result.content
                if len(response) > 50: store_knowledge(query[:30] if not image_part else "Image Analysis", response[:500])
                return correction_note + response, relevant_knowledge, name

            try:
                agent = create_react_agent(model=llm, tools=tools, prompt=system_prompt)
                result = agent.invoke({"messages": messages})
                if isinstance(result, dict) and 'messages' in result:
                    response = result["messages"][-1].content
                    for msg in result["messages"]:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            store_knowledge(query, response)
                            break
                else: response = str(result)
            except:
                result = llm.invoke(messages)
                response = result.content if hasattr(result, 'content') else str(result)
            
            return correction_note + response, relevant_knowledge, name
        except Exception as e:
            last_error = str(e)
            print(f"❌ {name} failed: {e}")
            continue

    # --- FINAL UNLIMITED FALLBACK: Parallel Autonomous Research Engine ---
    try:
        import concurrent.futures
        print(f"🚀 Engaging Parallel Autonomous Research Engine for: {query}")

        # If it's a "read file" command and we have file content, handle it locally for max speed
        if any(kw in query.lower() for kw in ["read the file", "analyze file", "what is in this file"]) and (file_content or image_part):
            if image_part:
                synthesized = "### 🖼️ Image Analysis (Local Intelligence)\nI have received your image. Since my primary cloud connection is experiencing delays, I can confirm it's an image file ready for analysis. Please ensure my API keys are active for deep vision insights."
            else:
                synthesized = f"### 📁 File Analysis (Local Intelligence)\n**File Content Snapshot:**\n{file_content[:2000]}..."
            return correction_note + synthesized, relevant_knowledge, "Local Speed Engine"

        # --- Context Injection for follow-ups ---
        search_query = query
        follow_up_keywords = {' it ', ' its ', ' that ', ' this ', ' him ', ' her ', ' them ', ' those ', ' it\'s '}
        if any(kw in f" {query.lower()} " for kw in follow_up_keywords) and history:
            last_human_msg = next((msg[1] for msg in reversed(history) if msg[0] == "human"), "")
            if last_human_msg:
                search_query = f"{query} {last_human_msg}"
                print(f"🔍 Context-aware search: {search_query}")

        # --- Concurrent Execution for High Speed ---
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # 1. Start core searches immediately
            future_search = executor.submit(search_tool.invoke, {"query": search_query})
            future_wiki = executor.submit(wiki_tool.invoke, {"query": search_query})
            
            # AI chat is often slow, give it a tighter timeout
            future_ai = executor.submit(ai_chat_tool.invoke, {"query": search_query, "site": "gemini"})
            
            # Wait for search results to get URLs for deep browsing
            try:
                search_results = future_search.result(timeout=7)
            except:
                search_results = "No results found."
            
            # Start browsing in parallel while wiki/AI finish
            future_browsing = []
            if "No results found" not in search_results:
                urls = re.findall(r'https?://[^\s]+', search_results)
                unique_urls = list(set(urls))[:2]
                for url in unique_urls:
                    future_browsing.append(executor.submit(browse_tool.invoke, {"url": url}))
            
            # Collect all results with timeouts to ensure speed
            try: wiki_res = future_wiki.result(timeout=5)
            except: wiki_res = "Wikipedia search timed out."
            
            try: ai_res = future_ai.result(timeout=10) # Gemini web is slow
            except: ai_res = "AI Chat lookup timed out."
            
            browsed_content = []
            for f in future_browsing:
                try:
                    res = f.result(timeout=8)
                    if res and len(res) > 100:
                        browsed_content.append(res)
                except: continue

        # --- Advanced Synthesizer ---
        synthesized = f"### 🧠 Deep Parallel Intelligence Report: {query.title()}\n"
        
        # Add Local File Context if it exists
        if file_content:
            synthesized += f"**Detected File Context:**\n> {file_content[:500]}...\n\n"
        elif image_part:
            synthesized += "**Detected Image Input:** [Image analysis requires active Cloud API for full vision]\n\n"

        if ai_res and "Error" not in ai_res and "timed out" not in ai_res:
            synthesized += f"**Core AI Insight:**\n{ai_res}\n\n"
        
        if "No results found" not in search_results:
            synthesized += f"**Web Intelligence:**\n{search_results[:600]}...\n\n"

        if browsed_content:
            synthesized += "**Deep Web Analysis:**\n" + "\n\n".join([f"- {c[:400]}..." for c in browsed_content]) + "\n\n"

        if wiki_res and "Page not found" not in wiki_res:
            synthesized += f"**Structured Context:**\n{wiki_res}"

        store_knowledge(query, synthesized)
        return correction_note + synthesized, relevant_knowledge, "Extreme Research Engine"
    except Exception as fallback_err:
        print(f"❌ Research Engine failed: {fallback_err}")
        return correction_note + f"I have processed your request locally. I remember: {relevant_knowledge if relevant_knowledge else 'nothing yet.'}", relevant_knowledge, "Local Intelligence"

if __name__ == '__main__':
    print("AI Agent Ready.")
