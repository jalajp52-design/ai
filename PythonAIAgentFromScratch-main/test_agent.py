from main import run_agent

history = []
query = "What is the capital of France?"
try:
    response, knowledge, model = run_agent(query, history)
    print(f"Response: {response}")
    print(f"Model: {model}")
except Exception as e:
    import traceback
    traceback.print_exc()
