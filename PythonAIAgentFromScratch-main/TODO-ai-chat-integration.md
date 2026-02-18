# TODO: Integrate AI Chat Tool for Multi-Model Interaction and Learning

## Tasks
- [x] Add `ai_chat_tool` in tools.py: Implement Selenium-based automation to interact with AI websites (e.g., chat.openai.com, gemini.google.com). The tool should navigate to the site, input the query, wait for response, and extract it. Assume browser is pre-logged in; handle errors gracefully.
- [x] Update tools import in main.py: Import the new `ai_chat_tool`.
- [x] Modify `run_agent` in main.py: Integrate `ai_chat_tool` as a fallback to query multiple AIs (e.g., if API fails or for accuracy). Gather answers from different sources and synthesize for better responses.
- [ ] Enhance knowledge base learning: Store and learn from responses obtained via `ai_chat_tool` to improve future accuracy.
- [ ] Test the new tool: Run sample queries to verify interaction with websites and response extraction.
- [ ] Update requirements.txt if needed: Check if Selenium or other deps are missing (though browse_tool already uses it).
- [ ] Run the agent: Verify overall functionality, multi-model querying, and learning improvements.
