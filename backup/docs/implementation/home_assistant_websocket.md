# Home Assistant WebSocket Integration

## Overview

This document describes the implementation of the Home Assistant WebSocket integration for the radbot project. This integration replaces the previous Model Context Protocol (MCP) based implementation with a more direct, robust WebSocket connection that provides real-time state updates and better control capabilities.

## Architecture

The Home Assistant WebSocket integration consists of the following components:

1. **WebSocket Client**: Manages a persistent connection to the Home Assistant WebSocket API, handles authentication, event subscription, and service calls.
2. **State Cache**: Maintains an up-to-date cache of Home Assistant entity states from real-time events.
3. **Tool Schemas**: Defines the function schemas for the Google GenAI function calling interface.
4. **Tool Implementations**: Implements the functions that interact with Home Assistant via the WebSocket client.
5. **Agent Factory**: Creates agents with Home Assistant capabilities, supporting both WebSocket and legacy MCP approaches.

## Components

### HomeAssistantWebsocketClient

The `HomeAssistantWebsocketClient` class is responsible for managing the WebSocket connection to Home Assistant. It:

- Establishes a persistent connection to the Home Assistant WebSocket API
- Handles authentication with a long-lived access token
- Subscribes to state_changed events to receive real-time updates
- Provides methods for calling Home Assistant services
- Implements robust reconnection logic to handle network issues or Home Assistant restarts

The client uses an asynchronous design with asyncio and the websockets library to maintain a non-blocking connection that can run concurrently with other agent tasks.

### HomeAssistantStateCache

The `HomeAssistantStateCache` class provides an in-memory cache of Home Assistant entity states. It:

- Maintains a dictionary of entity states indexed by entity_id
- Tracks domains and their associated entities
- Provides methods for querying the state cache by entity_id, domain, or search term
- Uses asyncio locks to ensure thread safety when updating the cache from event callbacks

This cache enables fast access to entity states without requiring additional WebSocket calls each time the agent needs state information.

### Tool Schemas for Google GenAI

The integration defines the following tools for the Google GenAI function calling interface:

1. `get_home_assistant_entity_state`: Gets the current state of a specific entity
2. `call_home_assistant_service`: Calls a Home Assistant service to control entities
3. `search_home_assistant_entities`: Searches for entities by name or ID
4. `get_home_assistant_entities_by_domain`: Gets all entities of a specific domain
5. `get_home_assistant_domains`: Gets all available domains in Home Assistant

These function declarations enable the GenAI model to understand when and how to interact with Home Assistant.

### Tool Implementations

The tool implementations connect the function declarations to the WebSocket client and state cache. They:

- Validate inputs and handle errors gracefully
- Access the state cache for read operations
- Use the WebSocket client for control operations
- Format responses in a way that's useful to the GenAI model

The implementations are designed to be asynchronous and work within the Google GenAI function calling framework.

### Agent Factory

The `create_home_assistant_agent_factory` function creates a factory function that adds Home Assistant capabilities to agents. It:

- Supports both WebSocket and MCP approaches based on configuration
- Adds the appropriate tools to the agent
- Sets up the necessary mappings between function declarations and implementations
- Ensures backward compatibility with existing code

## Configuration

The integration can be configured via environment variables:

```
# Choose between WebSocket (preferred) or MCP integration
HA_USE_WEBSOCKET=TRUE  # Set to FALSE for legacy MCP approach

# WebSocket Configuration (preferred)
HA_WEBSOCKET_URL=ws://your-home-assistant:8123/api/websocket
HA_WEBSOCKET_TOKEN=your_long_lived_access_token

# MCP Configuration (legacy)
HA_MCP_SSE_URL=http://your-home-assistant:8123/api/mcp_server/sse
HA_AUTH_TOKEN=your_long_lived_access_token
```

The `ConfigManager` class has been updated to support both approaches and will automatically derive WebSocket configuration from MCP configuration when possible.

## How It Works

1. **Startup**: The `setup_websocket_home_assistant` function initializes the WebSocket client and connects it to Home Assistant.

2. **Event Handling**: The WebSocket client subscribes to `state_changed` events and forwards them to the state cache via a callback function.

3. **Agent Creation**: When a Home Assistant enabled agent is created, it includes tools that use the Google GenAI function calling interface.

4. **Tool Usage**: When the agent determines it needs to interact with Home Assistant, it calls one of the defined functions:
   - To get the state of an entity, it calls `get_home_assistant_entity_state`
   - To control an entity, it calls `call_home_assistant_service`
   - To search for entities, it calls `search_home_assistant_entities`

5. **Function Execution**: The function is executed by the Google GenAI function calling mechanism, which calls the corresponding Python function. This function accesses the state cache or sends commands via the WebSocket client.

6. **Response Handling**: The function returns a response containing the requested information or the status of the command. The agent uses this response to generate its reply to the user.

7. **Cleanup**: When the application shuts down, the `cleanup_websocket_home_assistant` function closes the WebSocket connection and cleans up resources.

## Advantages over MCP Approach

The WebSocket approach offers several advantages over the previous MCP implementation:

1. **Direct Connection**: Connects directly to Home Assistant instead of going through an intermediate MCP server.

2. **Real-time Updates**: Receives state changes in real-time via WebSocket events, ensuring the agent always has the latest information.

3. **Better Control**: Provides more precise control over service calls with full parameter support.

4. **Reduced Latency**: Eliminates an extra layer of communication, reducing response times.

5. **Robust Reconnection**: Implements sophisticated reconnection logic to handle network issues or Home Assistant restarts.

6. **State Caching**: Maintains an in-memory cache of entity states for fast access without requiring additional API calls.

7. **Enhanced Search**: Provides better entity search capabilities that work across all entity domains.

## Usage Example

```python
from radbot.config.settings import ConfigManager
from radbot.agent.home_assistant_agent_factory import (
    setup_websocket_home_assistant,
    cleanup_websocket_home_assistant,
    create_home_assistant_agent_factory,
)

# Set up Home Assistant WebSocket connection
await setup_websocket_home_assistant()

# Create an agent factory with Home Assistant capabilities
agent_factory = create_home_assistant_agent_factory(base_agent_factory)

# Create an agent
agent = agent_factory()

# Use the agent...

# Clean up
await cleanup_websocket_home_assistant()
```

For a complete example, see `examples/home_assistant_websocket_example.py`.

## Migration from MCP Approach

The integration supports both WebSocket and MCP approaches, allowing for a gradual migration:

1. **Configuration**: Update your environment variables to use WebSocket instead of MCP.
2. **Agent Creation**: Use the `create_home_assistant_agent_factory` function instead of directly using `create_ha_mcp_enabled_agent`.
3. **Startup/Cleanup**: Add calls to `setup_websocket_home_assistant` and `cleanup_websocket_home_assistant` to your application lifecycle.

The configuration system will automatically determine which approach to use based on the `HA_USE_WEBSOCKET` environment variable.

## Future Work

- Complete integration tests for the WebSocket-based tools
- Phase out the MCP-based implementation when WebSocket approach is stable
- Implement proactive notifications based on Home Assistant events
- Add support for additional Home Assistant capabilities like script execution and automation triggering