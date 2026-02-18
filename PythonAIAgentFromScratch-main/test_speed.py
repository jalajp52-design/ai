import time
import sys
sys.path.append('.')
import main

# Test query that should trigger research engine
query = "what is the capital of France"

start_time = time.time()
response, _, source = main.run_agent(query)
end_time = time.time()

elapsed = end_time - start_time
print(f"Query: {query}")
print(f"Response: {response[:200]}...")
print(f"Source: {source}")
print(f"Time taken: {elapsed:.2f} seconds")
