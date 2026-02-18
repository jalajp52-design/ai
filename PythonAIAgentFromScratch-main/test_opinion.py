from main import run_agent

# Test the opinion functionality
query = "do you like donald trump"
response, knowledge, source = run_agent(query)
print(f"Query: {query}")
print(f"Response: {response}")
print(f"Source: {source}")
