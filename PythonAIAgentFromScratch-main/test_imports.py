print("Starting imports...")
import os
print("os done")
from dotenv import load_dotenv
print("dotenv done")
from langchain_anthropic import ChatAnthropic
print("anthropic done")
from langchain_openai import ChatOpenAI
print("openai done")
from langchain_google_genai import ChatGoogleGenerativeAI
print("google-genai done")
from langchain_groq import ChatGroq
print("groq done")
from langchain_community.llms import Ollama
print("ollama done")
from langchain_core.prompts import ChatPromptTemplate
print("prompts done")
from langgraph.prebuilt import create_react_agent
print("langgraph done")
import google.generativeai as genai
print("genai done")
print("All imports finished!")
