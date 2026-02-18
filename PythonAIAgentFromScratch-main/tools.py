from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from duckduckgo_search import DDGS
import time

@tool
def save_text_to_file(data: str, filename: str = "research_output.txt") -> str:
    """Saves structured research data to a text file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"--- Research Output ---\nTimestamp: {timestamp}\n\n{data}\n\n"

    with open(filename, "a", encoding="utf-8") as f:
        f.write(formatted_text)

    return f"Data successfully saved to {filename}"

save_tool = save_text_to_file

# DuckDuckGo search
@tool
def search_web(query: str) -> str:
    """Search the web for information using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=5)
            if not results:
                return "No results found."
            return "\n\n".join([f"Title: {r['title']}\nSnippet: {r['body']}\nSource: {r['href']}" for r in results])
    except Exception as e:
        return f"Error searching DuckDuckGo: {str(e)}"

search_tool = search_web

# Wikipedia search
api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=500)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper)

@tool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information about a topic."""
    return wiki.run(query)

wiki_tool = search_wikipedia

@tool
def browse_web(url: str) -> str:
    """
    Browse a specific URL and extract the main content.
    Use this tool when you need to read the content from a specific webpage.
    """
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # Wait for dynamic content

        # Extract text from main content areas
        body = driver.find_element(By.TAG_NAME, "body")
        text = body.text

        # Limit to first 2000 characters to avoid too much data
        return text[:2000] + "..." if len(text) > 2000 else text
    except Exception as e:
        return f"Error browsing {url}: {str(e)}"
    finally:
        driver.quit()

browse_tool = browse_web

@tool
def ai_chat_tool(query: str, site: str = "chatgpt") -> str:
    """
    Interact with AI chat websites (e.g., ChatGPT or Gemini) by automating browser actions.
    Navigates to the specified site, inputs the query, waits for the response, and extracts it.
    Assumes the browser is pre-logged in to the site. Use 'chatgpt' for chat.openai.com or 'gemini' for gemini.google.com.
    """
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    try:
        if site == "chatgpt":
            url = "https://chat.openai.com/"
        elif site == "gemini":
            url = "https://gemini.google.com/"
        else:
            return f"Unsupported site: {site}. Supported: chatgpt, gemini."

        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Wait for chat input (adjust selectors based on site; these are placeholders)
        if site == "chatgpt":
            input_selector = "textarea[data-testid='prompt-textarea']"  # Example selector for ChatGPT
            submit_selector = "button[data-testid='send-button']"
            response_selector = ".markdown"  # Example for response
        elif site == "gemini":
            input_selector = "textarea[aria-label='Ask Gemini']"  # Example selector for Gemini
            submit_selector = "button[aria-label='Send message']"
            response_selector = ".response-content"  # Example for response

        # Wait for input field
        input_field = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, input_selector)))
        input_field.send_keys(query)

        # Submit the query
        submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, submit_selector)))
        submit_button.click()

        # Wait for response (adjust time as needed)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, response_selector)))
        time.sleep(5)  # Additional wait for dynamic content

        # Extract the latest response
        responses = driver.find_elements(By.CSS_SELECTOR, response_selector)
        if responses:
            return responses[-1].text[:2000]  # Limit to 2000 chars
        else:
            return "No response found on the page."

    except Exception as e:
        return f"Error interacting with {site}: {str(e)}"
    finally:
        driver.quit()
