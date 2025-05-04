# Tavily Web Search Integration Fix Guide

This document describes the issues with the Tavily web search integration in radbot and how they were fixed.

## Issues

Two main issues were identified with the Tavily web search integration:

1. **Tool Creation and Usage**: The Tavily search tool wasn't being properly created or invoked in certain cases.
   
2. **ADK Version Compatibility**: The RadBotAgent's `process_message` method had compatibility issues with ADK 0.3.0, which uses different parameters for Runner.run() than expected.

## Fixes Implemented

### 1. Web Search Tool Improvements

The `web_search_tools.py` file was fixed to:

- Properly check for both `tavily-python` and `langchain-community` dependencies
- Add support for direct Tavily API if LangChain integration is unavailable
- Explicitly set the `name` and `description` attributes on the FunctionTool
- Improve documentation for better LLM discovery
- Add better error handling and logging

### 2. RadBotAgent Compatibility Fix

The `agent.py` file's `process_message` method was updated to handle ADK 0.3.0's API changes:

```python
def process_message(self, user_id: str, message: str) -> str:
    # ...logging code...
    
    # For ADK 0.3.0, try different approaches to run the agent
    try:
        # Try different approaches based on ADK version
        try:
            # Try to create a session directly
            session = self.session_service.create_session(
                user_id=user_id, 
                app_name="radbot"  # ADK 0.3.0 requires app_name
            )
            
            # Try to run the agent directly
            response = self.root_agent.process(message)
            return response
        except (TypeError, AttributeError):
            # If that doesn't work, try using the runner with different parameters
            try:
                # Method 1: Use "query" parameter instead of "message"
                events = list(self.runner.run(user_id=user_id, query=message))
            except TypeError:
                try:
                    # Method 2: Try to import and use Message object
                    try:
                        from google.adk.chat.message import Message, MessageType
                        query = Message(content=message, type=MessageType.HUMAN)
                        events = list(self.runner.run(user_id=user_id, query=query))
                    except ImportError:
                        # Method 3: Old style dict format
                        events = list(self.runner.run(user_id=user_id, text=message))
                except TypeError:
                    # Final fallback - try direct process method
                    return self.root_agent.process(message)
        
        # Extract response from events...
```

This implementation tries multiple approaches to handle different ADK versions, with fallbacks to ensure something works.

### 3. Diagnostic and Testing Tools

Several diagnostic and testing tools were created:

1. **Basic Diagnostics**: `tests/debug/test_tavily_tool.py` - Tests the Tavily tool in isolation

2. **Direct API Test**: `tests/debug/test_tavily_direct.py` - Accesses the tool function directly

3. **Example Script**: `examples/web_search_example.py` - Demonstrates using the agent with web search

4. **Standalone Utility**: `tools/tavily_search_util.py` - Command-line tool for direct searches 

5. **Fix & Test Script**: `fix_tavily_and_test.py` - Applies fixes and tests functionality

## How to Apply the Fixes

1. Run the automated fix and test script:
   ```bash
   python fix_tavily_and_test.py
   ```

2. Ensure you have the required dependencies:
   ```bash
   pip install -e ".[web]"
   ```
   Or directly:
   ```bash
   pip install "tavily-python>=0.3.8" "langchain-community>=0.2.16"
   ```

3. Make sure your `.env` file has the TAVILY_API_KEY set:
   ```
   TAVILY_API_KEY=your_api_key_here
   ```

## Using the Tavily Web Search

After applying the fixes, you can use the Tavily web search in several ways:

### 1. Direct Tool Usage

```python
from radbot.tools.web_search_tools import create_tavily_search_tool

# Create the tool
tool = create_tavily_search_tool(max_results=3, search_depth="advanced")

# Access the function directly and use it
if hasattr(tool, 'func') and callable(tool.func):
    result = tool.func("Your search query here")
    print(result)
```

### 2. Agent with Web Search

```python
from radbot.agent import create_websearch_agent

# Create an agent with web search capabilities
agent = create_websearch_agent(max_results=3, search_depth="advanced")

# Process a message that requires web search
response = agent.process_message(
    user_id="user123",
    message="What's happening in the news today?"
)
print(response)
```

### 3. Command-line Tool

```bash
python tools/tavily_search_util.py "Your search query here"
```

## Troubleshooting

If you encounter any issues:

1. **Check Dependencies**: Ensure you have installed both `tavily-python` and `langchain-community`

2. **Verify API Key**: Make sure your TAVILY_API_KEY is set in the environment or .env file

3. **Run Diagnostics**: Use the diagnostic scripts to test the tool in isolation:
   ```bash
   python tests/debug/test_tavily_direct.py
   ```

4. **Check Logs**: Increase logging level to DEBUG for more detailed information:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

5. **Tool Inspection**: If the agent isn't using the tool, check if it's properly attached:
   ```python
   # Print tools attached to agent
   for tool in agent.root_agent.tools:
       print(getattr(tool, 'name', None) or getattr(tool, '__name__', str(tool)))
   ```

## Notes for Future Updates

1. Consider adding more robust caching for the Tavily API responses to reduce API calls

2. Add support for more web search providers as alternatives to Tavily

3. Implement better error handling and fallback mechanisms if the search API is unavailable

4. Consider enhancing the web search results with additional context or formatting