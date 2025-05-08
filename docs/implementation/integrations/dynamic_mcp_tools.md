# Dynamic MCP Tools Loading

This document describes the dynamic MCP tools loading system that automatically registers tools from all enabled MCP servers defined in the configuration.

## Overview

The dynamic MCP tools loader eliminates the need to manually add code to register tools from each new MCP server. Instead, it:

1. Reads all enabled MCP servers from the configuration
2. Connects to each server
3. Retrieves all available tools
4. Adds them to the agent's tool set

This approach greatly simplifies adding new MCP servers to the system.

## Architecture

The dynamic tools loading system consists of:

1. A tools loader module that handles automatic discovery and registration
2. Integration with the agent initialization process
3. Configuration-driven tool loading

Key components:

- `dynamic_tools_loader.py`: Contains functions for tool discovery and loading
- `agent_tools_setup.py`: Uses the loader to add tools to the agent
- `config.yaml`: Defines the MCP servers to load tools from

## Implementation

### The Dynamic Tools Loader

The loader provides two main functions:

```python
def load_dynamic_mcp_tools() -> List[Any]:
    """Load tools from all enabled MCP servers in config."""
    # Implementation details...
    
def load_specific_mcp_tools(server_id: str) -> List[Any]:
    """Load tools from a specific MCP server."""
    # Implementation details...
```

These functions:

1. Get clients for MCP servers using the `MCPClientFactory`
2. Retrieve tools from each client
3. Return a combined list of all discovered tools

### Integration with Agent Initialization

The dynamic loader is integrated into the agent initialization process:

```python
# Add dynamic MCP tools from all enabled servers
try:
    mcp_tools = load_dynamic_mcp_tools()
    if mcp_tools:
        tools.extend(mcp_tools)
        logger.info(f"Added {len(mcp_tools)} tools from enabled MCP servers")
except Exception as e:
    logger.warning(f"Failed to load dynamic MCP tools: {e}")
```

This code is added to `agent_tools_setup.py` to dynamically load tools from all enabled MCP servers.

### Configuration-Driven Tool Loading

The system uses the configuration in `config.yaml` to determine which MCP servers to load tools from:

```yaml
integrations:
  mcp:
    servers:
      - id: server1
        enabled: true
        # Other configuration...
      - id: server2
        enabled: true
        # Other configuration...
```

Only enabled servers are processed by the loader.

## Adding New MCP Servers

With this system, adding a new MCP server is as simple as:

1. Add the server configuration to `config.yaml`
2. Restart the application

No code changes are required. The dynamic loader will automatically:

1. Find the new server in the configuration
2. Get a client for it using the `MCPClientFactory`
3. Retrieve its tools
4. Add them to the agent's tool set

## Benefits

This approach provides several advantages:

1. **Simplified Integration**: No need to modify code when adding new MCP servers
2. **Reduced Coupling**: The agent doesn't need to know about specific MCP servers
3. **Configuration-Driven**: All server configuration is in a single place
4. **Maintainability**: Less code to maintain when adding or removing servers
5. **Consistent Error Handling**: Centralized error handling for all MCP servers

## Limitations and Considerations

A few points to be aware of:

1. **Initialization Time**: Dynamic loading may slightly increase startup time
2. **Error Handling**: Individual server failures won't prevent others from loading
3. **Tool Conflicts**: Tools with the same name from different servers may conflict
4. **Debug Information**: Individual server loading issues will be logged

## Usage Example

To use the dynamic tools loader:

```python
from radbot.tools.mcp.dynamic_tools_loader import load_dynamic_mcp_tools

# Load all tools from enabled MCP servers
all_tools = load_dynamic_mcp_tools()

# Or load tools from a specific server
context7_tools = load_specific_mcp_tools("context7")
```

## References

- `radbot/tools/mcp/dynamic_tools_loader.py`: Dynamic tools loader implementation
- `radbot/agent/agent_tools_setup.py`: Agent tools setup with dynamic loading
- `config.yaml`: MCP server configuration