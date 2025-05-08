# Memory System Configuration Fix

## Overview

This document describes the issue with the memory system after migrating from `.env` to `config.yaml` for configuration and the implemented fixes.

## Problem

The memory system using Qdrant database was broken in the web application after switching from `.env` file to `config.yaml` for configuration. The main issues were:

1. The memory service (QdrantMemoryService) was still using environment variables instead of reading from the config.yaml file
2. The memory service wasn't properly passed to the web application's Runner
3. There was no mechanism to pass the memory service to the memory tools in the tool context

## Solution

The solution involved several changes across different parts of the application:

### 1. Update `agent_core.py` to Initialize Memory Service from Config

In `radbot/agent/agent_core.py`, added code to initialize QdrantMemoryService with configuration from config.yaml:

```python
# Initialize memory service from vector_db configuration
memory_service = None
try:
    # Get Qdrant settings from config_loader
    vector_db_config = config_loader.get_config().get("vector_db", {})
    url = vector_db_config.get("url")
    api_key = vector_db_config.get("api_key")
    host = vector_db_config.get("host", "localhost")
    port = vector_db_config.get("port", 6333)
    collection = vector_db_config.get("collection", "radbot_memories")
    
    # Fallback to environment variables for backward compatibility
    if not url:
        url = os.getenv("QDRANT_URL")
    if not api_key:
        api_key = os.getenv("QDRANT_API_KEY")
    if not host or host == "localhost":
        host = os.getenv("QDRANT_HOST", host)
    if port == 6333:
        port = os.getenv("QDRANT_PORT", port)
    if collection == "radbot_memories":
        collection = os.getenv("QDRANT_COLLECTION", collection)
    
    # Log memory service configuration
    logger.info(f"Initializing QdrantMemoryService with host={host}, port={port}, collection={collection}")
    if url:
        logger.info(f"Using Qdrant URL: {url}")
    
    # Create memory service
    memory_service = QdrantMemoryService(
        collection_name=collection,
        host=host,
        port=int(port) if isinstance(port, str) else port,
        url=url,
        api_key=api_key
    )
    logger.info(f"Successfully initialized QdrantMemoryService with collection '{collection}'")
    
    # Add memory tools to the tools list if they're not already included
    memory_tools = [search_past_conversations, store_important_information]
    tool_names = [tool.__name__ if hasattr(tool, '__name__') else tool.name if hasattr(tool, 'name') else None for tool in tools]
    
    for memory_tool in memory_tools:
        tool_name = memory_tool.__name__ if hasattr(memory_tool, '__name__') else None
        if tool_name and tool_name not in tool_names:
            tools.append(memory_tool)
            logger.info(f"Added memory tool: {tool_name}")
    
except Exception as e:
    logger.error(f"Failed to initialize QdrantMemoryService: {str(e)}")
    logger.warning("Memory service will not be available for this session")
    import traceback
    logger.debug(f"Memory service initialization traceback: {traceback.format_exc()}")
```

And then attached the memory service to the root agent:

```python
# Store memory_service as an attribute of the agent after creation
# This attribute will be used by the Runner in web/api/session.py
if memory_service:
    root_agent._memory_service = memory_service
    logger.info("Added memory_service to root_agent as _memory_service attribute")
```

### 2. Update `web/api/session.py` to Pass Memory Service to Runner

In `radbot/web/api/session.py`, modified the SessionRunner class to:

1. Get the memory service from the root agent
2. Store it in the global ToolContext for tools to access
3. Pass it to the Runner

```python
# Get memory service from root_agent if available
memory_service = None
if hasattr(root_agent, '_memory_service'):
    memory_service = root_agent._memory_service
    logger.info("Using memory service from root agent")
elif hasattr(root_agent, 'memory_service'):
    memory_service = root_agent.memory_service
    logger.info("Using memory service from root agent")

# Store memory_service in the global ToolContext class so memory tools can find it
if memory_service:
    from google.adk.tools.tool_context import ToolContext
    # Set memory_service in the ToolContext class for tools to access
    setattr(ToolContext, "memory_service", memory_service)
    logger.info("Set memory_service in global ToolContext class")
    
# Create the Runner with artifact service and memory service
self.runner = Runner(
    agent=root_agent,
    app_name=app_name,
    session_service=self.session_service,
    artifact_service=self.artifact_service,
    memory_service=memory_service
)
```

Also added code to set the user_id in the global ToolContext:

```python
# Set user_id in ToolContext for memory tools
if hasattr(self.runner, 'memory_service') and self.runner.memory_service:
    from google.adk.tools.tool_context import ToolContext
    setattr(ToolContext, "user_id", self.user_id)
    logger.info(f"Set user_id '{self.user_id}' in global ToolContext")
```

### 3. Update Memory Tools to Use Global ToolContext

In `radbot/tools/memory/memory_tools.py`, updated both `search_past_conversations` and `store_important_information` functions to check for user_id in the global ToolContext:

```python
# Get user ID - first look in tool_context
user_id = getattr(tool_context, "user_id", None)

# If not found in tool_context, try getting from session
if not user_id and hasattr(tool_context, "session"):
    session = getattr(tool_context, "session", None)
    if session and hasattr(session, "user_id"):
        user_id = session.user_id

# If we still don't have a user_id, check if it's in global ToolContext
if not user_id:
    global_user_id = getattr(ToolContext, "user_id", None)
    if global_user_id:
        user_id = global_user_id
        logger.info(f"Using user_id '{user_id}' from global ToolContext")
    else:
        # In web UI context, use a default user ID for testing
        logger.warning("No user ID found in any context, using default 'web_user'")
        user_id = "web_user"
```

## Testing

Several test scripts were created to verify the fixes:

1. `tools/test_web_memory.py` - Tests the memory initialization in the web interface context
2. `tools/test_memory_tool.py` - Tests the memory tools directly using global ToolContext

These tests demonstrated that:
- The memory service is properly initialized from config.yaml
- The memory service is correctly passed to the web interface's Runner
- The memory tools can access the memory service and user_id from the global ToolContext

## Future Improvements

Consider the following potential improvements:

1. Make memory service initialization a separate module that can be reused by all agent factories
2. Add more robust error handling for memory tools when the memory service is not available
3. Add cache settings to the memory service to improve performance
4. Consider using a dedicated class for memory operations instead of the current function-based approach