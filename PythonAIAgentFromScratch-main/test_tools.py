from tools import search_web, wiki_tool

query = "what is full form of fssai"
print("Testing search_web...")
try:
    res = search_web(query)
    print(f"Search Res: {res[:200]}")
except Exception as e:
    print(f"Search Error: {e}")

print("\nTesting wiki_tool...")
try:
    # Check if it has run method (standard LangChain tool)
    if hasattr(wiki_tool, 'run'):
        res = wiki_tool.run(query)
    else:
        res = wiki_tool(query)
    print(f"Wiki Res: {res[:200]}")
except Exception as e:
    print(f"Wiki Error: {e}")
