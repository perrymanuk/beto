"""
Example of using an agent with Home Assistant MCP integration.

This example demonstrates how to create and use an agent that can
interact with Home Assistant through the Model Context Protocol.
"""

import os
import uuid
import logging
from dotenv import load_dotenv

from radbot.tools.basic_tools import get_current_time, get_weather
from radbot.tools.mcp_tools import create_home_assistant_toolset, create_ha_mcp_enabled_agent
from radbot.tools.mcp_utils import test_home_assistant_connection, list_home_assistant_domains
from radbot.agent.agent import AgentFactory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Run the Home Assistant MCP agent example."""
    print("=" * 60)
    print("Home Assistant MCP Agent Example".center(60))
    print("=" * 60)
    
    # Test Home Assistant connection
    print("\nTesting Home Assistant MCP connection...")
    ha_result = test_home_assistant_connection()
    
    if ha_result["success"]:
        print(f"✅ Connected to Home Assistant MCP server")
        print(f"Found {ha_result.get('tools_count', 0)} tools")
        
        # List domains
        domains_result = list_home_assistant_domains()
        if domains_result["success"]:
            print(f"Available domains: {', '.join(domains_result.get('domains', []))}")
    else:
        print(f"❌ Failed to connect to Home Assistant MCP server")
        print(f"Error: {ha_result.get('error', 'Unknown error')}")
        print("\nPlease check your Home Assistant MCP configuration in .env file:")
        print("- HA_MCP_SSE_URL should point to your Home Assistant MCP Server SSE endpoint")
        print("- HA_AUTH_TOKEN should contain a valid long-lived access token")
        print("\nContinuing with basic agent (without Home Assistant capabilities)...")
    
    print("\nCreating agent with Home Assistant integration...")
    
    # Method 1: Using create_ha_mcp_enabled_agent helper
    agent = create_ha_mcp_enabled_agent(
        agent_factory=AgentFactory.create_root_agent,
        base_tools=[get_current_time, get_weather]
    )
    
    # Method 2: Manual setup
    """
    # Create tools list
    tools = [get_current_time, get_weather]
    
    # Try to add Home Assistant MCP tools
    ha_toolset = create_home_assistant_toolset()
    if ha_toolset:
        print("Home Assistant MCP tools added to agent")
        tools.append(ha_toolset)
    
    # Create the agent
    agent = AgentFactory.create_root_agent(tools=tools)
    """
    
    if not agent:
        print("Failed to create agent. Exiting.")
        return
    
    print("\nAgent created successfully.")
    print("Type 'exit' to quit.")
    print("=" * 60)
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    # Start interactive loop
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == "exit":
            print("Exiting...")
            break
        
        # Process the message
        try:
            print("\nProcessing...")
            response = agent.process_message(user_id=session_id, message=user_input)
            print(f"\nAgent: {response}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            print(f"\nError: {str(e)}")
            print("Continuing with new message...")
    
if __name__ == "__main__":
    main()