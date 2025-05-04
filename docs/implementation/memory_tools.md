# Memory Tools

This document explains the memory tools implementation in RadBot.

## Overview

RadBot's memory system allows the agent to store and retrieve information from past conversations. The memory tools provide functions for agents to interact with the memory system.

## Module Structure

The memory tools are organized in a structured module hierarchy:

```
radbot/
  └── tools/
      └── memory/
          ├── __init__.py
          └── memory_tools.py
```

The `__init__.py` file exports the tools for easy import, while `memory_tools.py` contains the actual implementation.

## Available Tools

### 1. `search_past_conversations`

Searches the memory database for relevant information from past conversations.

**Parameters:**
- `query`: The search query (what to look for in past conversations)
- `max_results`: Maximum number of results to return (default: 5)
- `time_window_days`: Optional time window to restrict search (e.g., 7 for last week)
- `tool_context`: Tool context for accessing memory service
- `memory_type`: Type of memory to filter by (e.g., 'conversation_turn', 'user_query')
- `limit`: Alternative way to specify maximum results (overrides max_results if provided)
- `return_stats_only`: If True, returns statistics about memory content instead of search results

**Returns:**
A dictionary with search results or memory statistics.

### 2. `store_important_information`

Stores important information in the memory database for future reference.

**Parameters:**
- `information`: The text information to store
- `memory_type`: Type of memory (e.g., 'important_fact', 'user_preference')
- `metadata`: Additional metadata to store with the information
- `tool_context`: Tool context for accessing memory service

**Returns:**
A dictionary with the status of the operation.

## Usage in Agent

The memory tools can be included in a RadBot agent using the `create_agent` function with `include_memory_tools=True` (default):

```python
from radbot.agent.agent import create_agent

# Create an agent with memory tools
agent = create_agent(include_memory_tools=True)
```

Or they can be imported directly:

```python
from radbot.tools.memory.memory_tools import search_past_conversations, store_important_information
```

## Memory Service Integration

The memory tools work with the `QdrantMemoryService` to store and retrieve vector embeddings of conversation data. The tools can access the memory service in two ways:

1. Through the `tool_context` parameter provided by the ADK Runner
2. Through a fallback global memory service stored in the `ToolContext` class

## Error Handling

Both memory tools have robust error handling to ensure they gracefully handle scenarios where:

- The memory service is not available
- The user ID cannot be determined
- The memory database cannot be accessed
- Query or storage operations fail

In all cases, they return meaningful error messages rather than raising exceptions.

## Troubleshooting

**Import Error: "No module named 'radbot.tools.memory_tools'"**

This occurs when trying to import directly from `radbot.tools.memory_tools` instead of the correct path `radbot.tools.memory.memory_tools`. 

The correct import statement is:
```python
from radbot.tools.memory.memory_tools import search_past_conversations, store_important_information
```

Or alternatively:
```python
from radbot.tools.memory import search_past_conversations, store_important_information
```
