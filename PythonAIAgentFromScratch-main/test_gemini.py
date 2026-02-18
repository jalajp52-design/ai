import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
print("Starting Gemini test...")
try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv('GOOGLE_API_KEY'))
    res = llm.invoke("Say 'Hello World'")
    print(f"Response: {res.content}")
except Exception as e:
    print(f"Error: {e}")
