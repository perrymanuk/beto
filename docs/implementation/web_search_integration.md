# Web Search Integration

This document provides details about the web search capabilities added to radbot using the Tavily API.

## Overview

radbot can now search the web using the Tavily API, allowing it to find information from across the internet to answer user queries. This is implemented as a standalone tool that can be added to any agent.

## Technical Implementation

### Components

1. **Tavily Search Tool**:
   - Defined in `radbot/tools/web_search_tools.py`
   - Uses the LangChain integration with Tavily API
   - Wrapped for Google ADK compatibility using `LangchainTool`

2. **Agent Factory**:
   - Implemented in `radbot/agent/web_search_agent_factory.py`
   - Provides factory functions for creating agents with web search capabilities
   - Supports customization of search parameters

### Search Parameters

The Tavily search tool can be configured with the following parameters:

- `max_results`: Maximum number of search results to return (default: 5)
- `search_depth`: Search depth, either "basic" or "advanced" (default: "advanced")
- `include_answer`: Whether to include an AI-generated answer (default: True)
- `include_raw_content`: Whether to include the raw content of search results (default: True)
- `include_images`: Whether to include images in search results (default: False)

## Usage

### Prerequisites

1. Obtain a Tavily API key from [https://tavily.com/](https://tavily.com/)
2. Add your Tavily API key to your `.env` file:
   ```
   TAVILY_API_KEY=your_tavily_api_key
   ```
3. Install the required dependencies:
   ```bash
   pip install -e ".[web]"
   ```

### Creating an Agent with Web Search

```python
from radbot.agent import create_websearch_agent

# Create a radbot agent with web search capabilities
agent = create_websearch_agent(
    max_results=5,
    search_depth="advanced"
)

# Process a message that might require web searching
response = agent.process_message(user_id="user123", message="What's happening in the news today?")
print(response)
```

### Creating a Root Agent with Web Search

```python
from radbot.agent import create_websearch_enabled_root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Create a root agent with web search capabilities
root_agent = create_websearch_enabled_root_agent(
    name="web_search_agent",
    max_results=3,
    search_depth="basic"
)

# Create a session service and runner
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="radbot",
    session_service=session_service
)

# Run the agent
events = list(runner.run(user_id="user123", message="What's the latest on AI advancements?"))
for event in events:
    if hasattr(event, 'message') and event.message:
        print(event.message.content)
```

## Limitations

- Requires a valid Tavily API key
- Search results depend on Tavily API's coverage and may not include very recent information
- The quality and relevance of results depend on the search queries

## Future Improvements

- Add support for other web search providers
- Implement caching to reduce API calls for similar queries
- Add support for specialized search types (news, academic, etc.)
- Implement better error handling and fallback mechanisms