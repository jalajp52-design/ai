from main import run_agent

# Test the math computation
query = "what is log(2)"
response, knowledge, source = run_agent(query)
print(f"Query: {query}")
print(f"Response: {response}")
print(f"Source: {source}")
