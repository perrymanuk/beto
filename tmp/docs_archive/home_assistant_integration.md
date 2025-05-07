# Home Assistant Integration

## Overview

The Home Assistant integration provides a way for radbot to interact with Home Assistant through the Model Context Protocol (MCP). This integration allows the agent to query and control Home Assistant entities, retrieve states, and execute services.

## Components

### MCP Tools Module (`mcp_tools.py`)

The primary module for creating and managing Home Assistant MCP connections.

#### Key Functions:

- `create_home_assistant_toolset()`: Creates an MCPToolset for connecting to Home Assistant's MCP Server.
- `create_ha_mcp_enabled_agent()`: Helper function to create an agent with Home Assistant MCP capabilities.

#### Authentication:

Authentication is handled through environment variables:
- `HA_MCP_SSE_URL`: The URL for Home Assistant's MCP Server SSE endpoint
- `HA_AUTH_TOKEN`: A long-lived access token for authentication

### MCP Utils Module (`mcp_utils.py`)

Utility functions for testing and debugging Home Assistant MCP connections.

#### Key Functions:

- `test_home_assistant_connection()`: Tests the connection to Home Assistant MCP server
- `check_entity_exists()`: Verifies if a specific entity exists in Home Assistant
- `list_home_assistant_domains()`: Lists all available domains in the Home Assistant instance
- `list_domain_entities()`: Lists entities belonging to a specific domain

## Usage

### Basic Setup

```python
from radbot.tools.mcp_tools import create_home_assistant_toolset

# Create the Home Assistant toolset
ha_toolset = create_home_assistant_toolset()

# Add to your agent's tools
tools = [other_tools, ha_toolset]

# Create agent with these tools
agent = create_agent(tools=tools)
```

### Using the Helper Function

```python
from radbot.tools.mcp_tools import create_ha_mcp_enabled_agent
from radbot.agent.agent import AgentFactory

# Create agent with Home Assistant integration
agent = create_ha_mcp_enabled_agent(
    agent_factory=AgentFactory.create_root_agent,
    base_tools=[other_tools]
)
```

## Configuration

### Environment Variables

Required environment variables:

```
HA_MCP_SSE_URL=http://your-home-assistant:8123/api/mcp/stream
HA_AUTH_TOKEN=your_long_lived_access_token
```

These can be set in a `.env` file, your system environment, or provided programmatically.

### Creating a Long-Lived Access Token

1. In Home Assistant, navigate to your profile (click on your username in the sidebar)
2. Scroll to the bottom of the page to the "Long-Lived Access Tokens" section
3. Click "Create Token"
4. Give it a name like "radbot"
5. Copy the token (it will only be shown once)
6. Add it to your environment variables

## Capabilities

With this integration, the agent can:

1. Query entity states (e.g., "Is the living room light on?")
2. Control entities (e.g., "Turn off the kitchen light")
3. Get sensor readings (e.g., "What's the temperature in the bedroom?")
4. Execute services (e.g., "Lock the front door")
5. Get entity lists (e.g., "What lights do I have?")

## Error Handling

The integration includes robust error handling:

- Connection errors (server unreachable, authentication failures)
- Entity validation (checking if entities exist before acting on them)
- Service validation (checking if services exist before executing them)

All errors are properly logged and appropriate error messages are returned to help with debugging.

## Examples

See `examples/home_assistant_agent_example.py` for a complete working example of an agent with Home Assistant integration.

## Future Improvements

Potential future enhancements:

1. Caching mechanism for entity states
2. More sophisticated entity filtering
3. Template support for complex queries
4. Integration with the memory system to remember user preferences
5. More specialized Home Assistant-specific tools

## Related Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Home Assistant MCP Integration Documentation](https://www.home-assistant.io/integrations/mcp/)
- [Home Assistant MCP Server Integration Documentation](https://www.home-assistant.io/integrations/mcp_server/)