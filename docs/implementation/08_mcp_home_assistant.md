# MCP Integration for Home Assistant

This document details the implementation of Model Context Protocol (MCP) integration with Home Assistant for the Raderbot agent framework.

## MCP Integration Architecture

The integration consists of several key components:

1. **MCP Client Configuration**: Setup for connecting to Home Assistant's MCP server
2. **MCPToolset Integration**: Integration with ADK's built-in MCP tooling
3. **Home Assistant Agent**: A specialized agent for smart home control
4. **Error Handling & Security**: Robust error handling and security considerations

## MCP Client Implementation

### Home Assistant MCP Client (`tools/mcp_tools.py`)

```python
# raderbot/tools/mcp_tools.py

"""
MCP integration tools for connecting to Home Assistant.

This module provides utilities for connecting to Home Assistant via the Model Context Protocol (MCP).
"""

import os
import logging
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
from google.adk.tools.mcp_tool import MCPToolset, SseServerParams

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

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

## Integration with Agent Configuration

To add the Home Assistant tools to an agent:

```python
from raderbot.tools.mcp_tools import create_home_assistant_toolset
from raderbot.agent.agent import AgentFactory

# Create Home Assistant toolset
ha_toolset = create_home_assistant_toolset()

# Create basic tools list
tools = [get_current_time, get_weather]

# Add Home Assistant tools if available
if ha_toolset:
    tools.append(ha_toolset)

# Create the agent with tools
root_agent = AgentFactory.create_root_agent(tools=tools)
```

## MCP Testing and Utility Functions

### Home Assistant MCP Testing (`tools/mcp_utils.py`)

```python
# raderbot/tools/mcp_utils.py

"""
Utility functions for working with the Model Context Protocol (MCP).

This module provides helper functions for testing and debugging MCP connections.
"""

import os
import logging
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
from google.adk.tools.mcp_tool import MCPToolset, SseServerParams

from raderbot.tools.mcp_tools import create_home_assistant_toolset

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def test_home_assistant_connection() -> Dict[str, Any]:
    """
    Test the connection to the Home Assistant MCP server.
    
    This function attempts to connect to the Home Assistant MCP server and
    retrieve basic information about available entities.
    
    Returns:
        Dictionary with the test results and information
    """
    # Initialize the Home Assistant MCP
    ha_toolset = create_home_assistant_toolset()
    
    if not ha_toolset:
        return {
            "success": False,
            "status": "initialization_failed",
            "error": "Failed to create Home Assistant MCP toolset",
            "details": None
        }
    
    # Try to list available tools
    try:
        # Note: This assumes MCPToolset has a method to list tools.
        # Actual implementation may vary based on ADK version.
        # This is a placeholder for the concept.
        tools = ha_toolset.list_tools()
        
        return {
            "success": True,
            "status": "connected",
            "tools_count": len(tools),
            "tools": tools
        }
    except Exception as e:
        return {
            "success": False,
            "status": "connection_error",
            "error": str(e),
            "details": None
        }
```

## Integration with CLI Interface

Update the CLI interface to include Home Assistant MCP status:

```python
# raderbot/cli/main.py (updated)

import logging
import os
import sys
import uuid
from typing import Optional

from dotenv import load_dotenv

from raderbot.agent.agent import AgentFactory, create_runner
from raderbot.tools.basic_tools import get_current_time, get_weather
from raderbot.tools.mcp_tools import create_home_assistant_toolset
from raderbot.tools.mcp_utils import test_home_assistant_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def setup_agent():
    """Set up and configure the agent with tools and memory."""
    try:
        # Create tools list
        tools = [get_current_time, get_weather]
        
        # Try to add Home Assistant MCP tools
        ha_toolset = create_home_assistant_toolset()
        if ha_toolset:
            logger.info("Home Assistant MCP tools added to agent")
            tools.append(ha_toolset)
        
        # Create the agent
        root_agent = AgentFactory.create_root_agent(tools=tools)
        
        # Create the runner
        runner = create_runner(root_agent)
        
        return runner
    except Exception as e:
        logger.error(f"Error setting up agent: {str(e)}")
        return None


def main():
    """Main CLI entry point."""
    print("Raderbot CLI")
    
    # Check Home Assistant MCP status
    ha_status = "Not configured"
    try:
        ha_result = test_home_assistant_connection()
        if ha_result["success"]:
            ha_status = f"Connected ({ha_result.get('tools_count', 0)} tools available)"
        else:
            ha_status = f"Error: {ha_result.get('error', 'Unknown error')}"
    except Exception as e:
        ha_status = f"Error: {str(e)}"
    
    print(f"Home Assistant MCP: {ha_status}")
    print("Type 'exit' to quit")
    
    # Set up agent (stub for now)
    runner = setup_agent()
    
    if not runner:
        print("Failed to set up agent. Exiting.")
        return
    
    # Interactive loop
    session_id = str(uuid.uuid4())  # Generate a unique session ID
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        print("\nAgent: Processing your request...")
        
        # In the actual implementation, we'd run the agent with the runner:
        """
        for event in runner.run(message=user_input, session_id=session_id):
            if event.message and event.message.content:
                print(f"\nAgent: {event.message.content}")
        """
        
        # For now, just show a stub response
        print("\nAgent: This is a stub response. The actual agent would process your query here.")
```

## Home Assistant MCP Server Configuration

### Home Assistant MCP Server Setup

Detailed instructions for setting up the Home Assistant MCP Server:

1. **Enable the MCP Server Integration**:
   - Open Home Assistant
   - Navigate to Settings > Devices & Services
   - Click "Add Integration"
   - Search for "Model Context Protocol Server" and add it
   - Follow the setup wizard

2. **Generate Long-Lived Access Token**:
   - Navigate to your profile page (click your username in the bottom left)
   - Scroll down to "Long-Lived Access Tokens"
   - Create a new token with a descriptive name (e.g., "Raderbot Agent")
   - Copy the token immediately (it's only shown once)

3. **Configure Environment Variables**:
   Set these variables in your `.env` file:
   ```
   # Home Assistant MCP Configuration
   HA_MCP_SSE_URL=http://your-ha-ip:8123/api/mcp_server/sse
   HA_AUTH_TOKEN=your_long_lived_access_token
   ```

4. **Security Considerations**:
   - Store the auth token securely
   - Consider restricting the Home Assistant user account privileges
   - Use HTTPS if Home Assistant is exposed to the internet

## Available Home Assistant Tools

The Home Assistant MCP server exposes various tools based on the devices and services configured in your Home Assistant instance. Common tool categories include:

### Device Control

- `light.turn_on`: Turn on a light
- `light.turn_off`: Turn off a light
- `switch.turn_on`: Turn on a switch
- `switch.turn_off`: Turn off a switch

### State Information

- `sensor.get_state`: Get the current state of a sensor
- `climate.get_state`: Get the current state of a climate device

### Scene and Automation

- `scene.turn_on`: Activate a scene
- `automation.trigger`: Trigger an automation

## Agent Instructions for Home Assistant Tools

The agent needs to be instructed on how to use the Home Assistant tools. Add the following to the agent's instruction:

```
You can control smart home devices through Home Assistant. Here are some examples:

- To turn on lights: Use the home_assistant_mcp.light.turn_on tool with the entity_id parameter
- To check sensor values: Use the home_assistant_mcp.sensor.get_state tool with the entity_id parameter
- To activate scenes: Use the home_assistant_mcp.scene.turn_on tool with the entity_id parameter

Always tell the user what action you're taking, and report back the results. If a Home Assistant tool fails, inform the user politely about the issue.
```

## Security Considerations

1. Store the HA_AUTH_TOKEN securely and never include it directly in code
2. Set appropriate permissions for the Long-Lived Access Token in Home Assistant
3. Consider network security between your agent application and Home Assistant

## Next Steps

1. Implement entity discovery for auto-completion and suggestions
2. Add better error handling and retries for Home Assistant interactions
3. Create tests for Home Assistant MCP tool integration