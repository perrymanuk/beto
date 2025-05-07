# Home Assistant Integration

## Overview

The RadBot framework provides integration with Home Assistant, allowing the agent to control smart home devices, retrieve sensor data, check device status, and trigger automations. This document explains the implementation approaches, design considerations, and configuration details.

## Integration Methods

RadBot supports two main methods of Home Assistant integration:

1. **REST API Approach**: Direct HTTP integration with Home Assistant's REST API
2. **MCP Server Approach**: Integration via Home Assistant's Model Context Protocol (MCP) Server

Both methods have their strengths and are supported for different use cases.

## REST API Implementation

### Architecture

The REST API implementation consists of three main components:

1. **HomeAssistantClient**: A Python class that handles REST API communication
2. **Function Tools**: ADK-compatible tool functions for agent integration
3. **Connection Configuration**: Environment-based configuration for the client

### HomeAssistantClient Class

This class encapsulates all communication with the Home Assistant REST API:

```python
class HomeAssistantClient:
    """A client for interacting with the Home Assistant REST API."""
    def __init__(self, base_url: str, token: str):
        """
        Initializes the Home Assistant client.

        Args:
            base_url: The base URL of the Home Assistant instance (e.g., http://homeassistant.local:8123).
            token: The Long-Lived Access Token.
        """
        self.base_url = base_url
        self.api_url = f"{self.base_url}api/"
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self._session = requests.Session()
        self._session.headers.update(self._headers)
        
    def get_api_status(self) -> bool:
        """Checks if the Home Assistant API is running."""
        response_data = self._request("GET", "")
        return response_data is not None and response_data.get("message") == "API running."
    
    def list_entities(self) -> Optional[List[Dict[str, Any]]]:
        """Lists all entities and their states."""
        return self._request("GET", "states")
    
    def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Gets the state of a specific entity."""
        return self._request("GET", f"states/{entity_id}")
    
    def call_service(self, domain: str, service: str, entity_id: Union[str, List[str]]) -> Optional[List[Dict[str, Any]]]:
        """Calls a service in Home Assistant."""
        payload = {"entity_id": entity_id}
        endpoint = f"services/{domain}/{service}"
        return self._request("POST", endpoint, json=payload)
```

### ADK Function Tools

Tools built on the HomeAssistantClient for integration with the ADK:

```python
def list_ha_entities() -> Dict[str, Any]:
    """
    Lists all available entities in Home Assistant, returning their ID, state,
    and friendly name if available.
    """
    entities = ha_client.list_entities()
    formatted_entities = []
    for entity in entities:
        entity_id = entity.get('entity_id')
        state = entity.get('state')
        friendly_name = entity.get('attributes', {}).get('friendly_name')
        formatted_entities.append({
            "entity_id": entity_id,
            "state": state,
            "friendly_name": friendly_name if friendly_name else entity_id
        })
    return {"status": "success", "data": formatted_entities}

def get_ha_entity_state(entity_id: str) -> Dict[str, Any]:
    """
    Gets the current state and attributes of a specific entity in Home Assistant.
    """
    state = ha_client.get_state(entity_id)
    return {"status": "success", "data": {
        "entity_id": state.get("entity_id"),
        "state": state.get("state"),
        "attributes": state.get("attributes", {}),
        "last_changed": state.get("last_changed")
    }}

def turn_on_ha_entity(entity_id: str) -> Dict[str, Any]:
    """Turns on a Home Assistant entity."""
    domain = entity_id.split('.')[0]
    result = ha_client.call_service(domain, "turn_on", entity_id)
    return {"status": "success", "message": f"Turn on command sent to '{entity_id}'."}

def turn_off_ha_entity(entity_id: str) -> Dict[str, Any]:
    """Turns off a Home Assistant entity."""
    domain = entity_id.split('.')[0]
    result = ha_client.call_service(domain, "turn_off", entity_id)
    return {"status": "success", "message": f"Turn off command sent to '{entity_id}'."}
    
def toggle_ha_entity(entity_id: str) -> Dict[str, Any]:
    """Toggles a Home Assistant entity."""
    domain = entity_id.split('.')[0]
    result = ha_client.call_service(domain, "toggle", entity_id)
    return {"status": "success", "message": f"Toggle command sent to '{entity_id}'."}

def search_ha_entities(search_term: str, domain_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Searches for Home Assistant entities matching a search term,
    optionally filtering by domain.
    """
    entities = ha_client.list_entities()
    matching_entities = []
    
    search_term = search_term.lower()
    for entity in entities:
        entity_id = entity.get('entity_id', '').lower()
        friendly_name = entity.get('attributes', {}).get('friendly_name', '').lower()
        
        # Apply domain filter if provided
        if domain_filter and not entity_id.startswith(f"{domain_filter.lower()}."):
            continue
            
        # Check if entity matches the search term
        if (search_term in entity_id or 
            search_term in friendly_name):
            matching_entities.append({
                "entity_id": entity.get('entity_id'),
                "state": entity.get('state'),
                "friendly_name": entity.get('attributes', {}).get('friendly_name')
            })
            
    return {
        "status": "success",
        "count": len(matching_entities),
        "entities": matching_entities
    }
```

### Configuration for REST API

The REST API integration uses these environment variables:

```
HA_URL=http://your-home-assistant:8123
HA_TOKEN=your_long_lived_access_token
```

## MCP Server Implementation

### Architecture

The MCP Server implementation consists of three main components:

1. **MCPToolset Integration**: Using ADK's built-in MCP tooling
2. **MCP Client Configuration**: Setup for connecting to Home Assistant's MCP server
3. **Home Assistant Agent Factory**: A factory for creating agents with HA capabilities

### MCP Client Implementation

```python
def create_home_assistant_toolset() -> Optional[MCPToolset]:
    """
    Create an MCPToolset for connecting to Home Assistant's MCP Server.
    
    Uses environment variables for configuration (HA_MCP_SSE_URL, HA_AUTH_TOKEN).
    
    Returns:
        MCPToolset: The configured Home Assistant MCP toolset, or None if configuration fails
    """
    try:
        # Get connection parameters from environment variables
        ha_mcp_url = os.getenv("HA_MCP_SSE_URL")
        ha_auth_token = os.getenv("HA_AUTH_TOKEN")
        
        if not ha_mcp_url or not ha_auth_token:
            logger.error("Home Assistant MCP configuration missing. "
                      "Please set HA_MCP_SSE_URL and HA_AUTH_TOKEN environment variables.")
            return None
        
        # Configure the SSE parameters for Home Assistant MCP server
        ha_mcp_params = SseServerParams(
            url=ha_mcp_url,
            headers={
                "Authorization": f"Bearer {ha_auth_token}"
            }
        )
        
        # Create the MCPToolset
        ha_toolset = MCPToolset(
            server_params={"home_assistant_mcp": ha_mcp_params}
        )
        
        logger.info("Successfully created Home Assistant MCP toolset")
        return ha_toolset
        
    except Exception as e:
        logger.error(f"Failed to create Home Assistant MCP toolset: {str(e)}")
        return None
```

### Home Assistant Agent Factory

```python
def create_home_assistant_agent_factory(
    agent_factory: Callable,
    base_tools: Optional[List[Any]] = None
) -> RadBotAgent:
    """
    Creates an agent with Home Assistant capabilities using the MCP protocol.
    
    Args:
        agent_factory: The agent factory function to use (e.g., AgentFactory.create_root_agent)
        base_tools: List of additional tools to add to the agent
        
    Returns:
        A RadBotAgent instance with Home Assistant capabilities
    """
    tools = base_tools or []
    
    # Create Home Assistant MCP toolset
    ha_toolset = create_home_assistant_toolset()
    if ha_toolset:
        tools.append(ha_toolset)
        logger.info("Added Home Assistant MCP toolset to agent tools")
    
    # Create the agent using the provided factory function
    agent = agent_factory(tools=tools)
    
    return agent
```

### Configuration for MCP Server

The MCP Server integration uses these environment variables:

```
HA_MCP_SSE_URL=http://your-home-assistant:8123/api/mcp_server/sse
HA_AUTH_TOKEN=your_long_lived_access_token
```

## Home Assistant Entity Search

One of the key challenges in Home Assistant integration is mapping user requests (e.g., "turn on the living room lamp") to specific Home Assistant entity_ids (e.g., light.living_room_lamp).

The implementation includes a specialized search function that can:

1. Search by friendly name or entity ID
2. Filter by domain (lights, switches, sensors, etc.)
3. Handle partial matches and case insensitivity

### Entity Search Function

```python
def search_ha_entities(search_term: str, domain_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Searches for Home Assistant entities matching a search term,
    optionally filtering by domain.
    
    Args:
        search_term: The search term to match against entity IDs and friendly names
        domain_filter: Optional domain to filter by (e.g., 'light', 'switch')
        
    Returns:
        Dictionary with matching entities
    """
    entities = ha_client.list_entities()
    matching_entities = []
    
    search_term = search_term.lower()
    for entity in entities:
        entity_id = entity.get('entity_id', '').lower()
        friendly_name = entity.get('attributes', {}).get('friendly_name', '').lower()
        
        # Apply domain filter if provided
        if domain_filter and not entity_id.startswith(f"{domain_filter.lower()}."):
            continue
            
        # Check if entity matches the search term
        if (search_term in entity_id or 
            search_term in friendly_name):
            matching_entities.append({
                "entity_id": entity.get('entity_id'),
                "state": entity.get('state'),
                "friendly_name": entity.get('attributes', {}).get('friendly_name')
            })
            
    return {
        "status": "success",
        "count": len(matching_entities),
        "entities": matching_entities
    }
```

## Usage Examples

### Creating an Agent with Home Assistant REST API

```python
from radbot.agent.agent import create_agent
from radbot.tools.homeassistant import (
    list_ha_entities,
    get_ha_entity_state,
    turn_on_ha_entity,
    turn_off_ha_entity,
    toggle_ha_entity,
    search_ha_entities
)

# Create the agent with Home Assistant tools
agent = create_agent(
    tools=[
        list_ha_entities,
        get_ha_entity_state,
        turn_on_ha_entity,
        turn_off_ha_entity,
        toggle_ha_entity,
        search_ha_entities
    ],
    name="home_assistant_agent"
)
```

### Creating an Agent with Home Assistant MCP Server

```python
from radbot.agent.agent import AgentFactory
from radbot.agent.home_assistant_agent_factory import create_home_assistant_agent_factory

# Create agent with Home Assistant MCP integration
agent = create_home_assistant_agent_factory(
    agent_factory=AgentFactory.create_root_agent,
    base_tools=[other_tools]
)
```

## Authentication and Security

### Long-Lived Access Tokens

Both integration methods use Home Assistant Long-Lived Access Tokens (LLATs) for authentication:

1. **Generation**:
   - In Home Assistant, navigate to your profile (click on your username in the sidebar)
   - Scroll to the bottom of the page to the "Long-Lived Access Tokens" section
   - Click "Create Token"
   - Give it a name (e.g., "RadBot")
   - Copy the token (it will only be shown once)

2. **Security Considerations**:
   - Tokens provide persistent access (typically valid for 10 years)
   - Store the token securely, never hardcode it in source code
   - Use environment variables or a secure secrets management system
   - Consider creating a Home Assistant user with limited permissions for the token

## Error Handling

The implementation includes robust error handling:

1. **Connection Errors**: Handling server unreachable, authentication failures
2. **Entity Validation**: Checking if entities exist before acting on them
3. **Service Validation**: Checking if services exist before executing them
4. **Timeouts**: Setting appropriate timeouts for API calls
5. **Logging**: Detailed logging of errors and warnings

## Home Assistant MCP Server Setup

To use the MCP Server integration method, you need to set up the Home Assistant MCP Server:

1. **Enable the MCP Server Integration**:
   - Open Home Assistant
   - Navigate to Settings > Devices & Services
   - Click "Add Integration"
   - Search for "Model Context Protocol Server" and add it
   - Follow the setup wizard

2. **Generate Long-Lived Access Token** as described above

3. **Configure Environment Variables** as described above

## Comparison of Integration Methods

| Feature | REST API | MCP Server |
|---------|----------|------------|
| Setup Complexity | Simpler | Requires MCP Server setup |
| Functionality | Limited to REST API | More comprehensive |
| Performance | Slightly slower | Potentially faster |
| Error Handling | More control | Handled by ADK |
| Flexibility | More customizable | Limited to MCP capabilities |
| Dependencies | Only requests library | ADK MCP tools |

## Available Tools

### REST API Tools

- `list_ha_entities()`: Lists all entities
- `get_ha_entity_state(entity_id)`: Gets state of specific entity
- `turn_on_ha_entity(entity_id)`: Turns on an entity
- `turn_off_ha_entity(entity_id)`: Turns off an entity
- `toggle_ha_entity(entity_id)`: Toggles an entity
- `search_ha_entities(search_term, domain_filter)`: Searches for entities

### MCP Server Tools

The MCP Server exposes various tools based on the devices and services configured in your Home Assistant instance:

- `home_assistant_mcp.light.turn_on`: Turn on a light
- `home_assistant_mcp.light.turn_off`: Turn off a light
- `home_assistant_mcp.switch.turn_on`: Turn on a switch
- `home_assistant_mcp.sensor.get_state`: Get sensor state
- `home_assistant_mcp.climate.set_temperature`: Set climate temperature
- And many more, depending on your Home Assistant configuration

## Agent Instructions

The following instructions are added to the agent's prompt to help it use the Home Assistant tools:

```
You have access to Home Assistant smart home control tools through the REST API integration.

First, search for entities:
- Use search_ha_entities("search_term") to find entities matching your search
- For domain-specific search, use search_ha_entities("search_term", "domain_filter") 
  Example domains: light, switch, sensor, climate, media_player, etc.

You can also list all entities:
- Use list_ha_entities() to get all Home Assistant entities

Get information about specific entities:
- Use get_ha_entity_state("entity_id") to get the state of a specific entity
  Example: get_ha_entity_state("light.living_room")

Once you have the entity IDs, you can control them using:
- turn_on_ha_entity("entity_id") - to turn on devices
- turn_off_ha_entity("entity_id") - to turn off devices
- toggle_ha_entity("entity_id") - to toggle devices (on if off, off if on)

Always check the entity state before controlling it to understand its current status.
```

## Future Improvements

Potential future enhancements:

1. **Caching Mechanism**: Add caching for entity states to reduce API calls
2. **Improved Entity Matching**: Enhanced fuzzy matching for entity names
3. **Template Support**: Add template support for complex queries
4. **Memory Integration**: Integrate with the memory system to remember user preferences
5. **Scene and Script Management**: Add specialized tools for scenes and scripts
6. **UI Integration**: Add a web UI for managing Home Assistant connections
7. **WebSocket Integration**: Add WebSocket support for real-time updates