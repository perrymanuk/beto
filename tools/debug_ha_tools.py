#!/usr/bin/env python3
"""
Debug script for Home Assistant MCP tools registration.

This script tests loading Home Assistant tools and verifying they're properly registered.
"""

import os
import sys
import logging
from pprint import pprint

# Add the parent directory to the path so we can import radbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from radbot.tools.mcp_tools import create_home_assistant_toolset
from radbot.tools.mcp_utils import test_home_assistant_connection
from radbot.agent.agent import create_agent
from radbot.tools.basic_tools import get_current_time, get_weather

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Run the Home Assistant tools debug routine."""
    print("=" * 60)
    print(" Home Assistant MCP Tools Debug ".center(60, "="))
    print("=" * 60)
    
    print("\nStep 1: Testing direct connection to Home Assistant MCP...")
    ha_status = test_home_assistant_connection()
    
    if not ha_status.get("success"):
        print(f"\n❌ Connection failed: {ha_status.get('error', 'Unknown error')}")
        print("Check your environment variables and Home Assistant configuration.")
        return 1
        
    print(f"\n✅ Connection successful! Found {ha_status.get('tools_count', 0)} tools")
    
    if ha_status.get("tools"):
        print("\nSample tools:")
        for tool in ha_status.get("tools", [])[:10]:
            print(f"  - {tool}")
    
    print("\nStep 2: Loading Home Assistant tools...")
    ha_tools = create_home_assistant_toolset()
    
    if not ha_tools or len(ha_tools) == 0:
        print("\n❌ Failed to load Home Assistant tools")
        print("The connection was successful but no tools were loaded.")
        return 1
        
    print(f"\n✅ Successfully loaded {len(ha_tools)} Home Assistant tools")
    
    # Examine first few tools
    print("\nFirst few tools:")
    for i, tool in enumerate(ha_tools[:5]):
        print(f"  {i+1}. {tool.name if hasattr(tool, 'name') else str(tool)}")
        
        if hasattr(tool, 'description'):
            print(f"     Description: {tool.description}")
            
        if hasattr(tool, 'parameters'):
            print(f"     Parameters: {tool.parameters}")
            
    print("\nStep 3: Creating test agent with Home Assistant tools...")
    
    # Create a basic tools list
    basic_tools = [get_current_time, get_weather]
    
    # All tools
    all_tools = list(basic_tools)
    all_tools.extend(ha_tools)
    
    print(f"Creating agent with {len(all_tools)} total tools")
    
    # Create a test agent
    agent = create_agent(tools=all_tools)
    
    if not agent:
        print("\n❌ Failed to create test agent")
        return 1
        
    config = agent.get_configuration()
    print(f"\n✅ Successfully created test agent with {config.get('tools_count', 0)} tools")
    
    # Check if Home Assistant tools are properly registered
    if hasattr(agent, 'root_agent') and hasattr(agent.root_agent, 'tools'):
        registered_tools = agent.root_agent.tools
        ha_tool_count = sum(1 for t in registered_tools if hasattr(t, 'name') and (
            t.name.startswith('Hass') or 
            'home_assistant' in str(t).lower()
        ))
        
        print(f"\nRegistered tools: {len(registered_tools)}, Home Assistant tools: {ha_tool_count}")
        
        if ha_tool_count == 0:
            print("\n❌ No Home Assistant tools were registered with the agent!")
            print("This indicates the tools are being loaded but not properly registered.")
            
            print("\nRegistered tool names:")
            for t in registered_tools:
                print(f"  - {getattr(t, 'name', None) or getattr(t, '__name__', str(t))}")
        else:
            print(f"\n✅ {ha_tool_count} Home Assistant tools were properly registered")
            
    print("\nTest complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())