#!/usr/bin/env python3
"""
Test script for the dynamic MCP tools loader.

This script tests the ability to dynamically load tools from MCP servers
defined in the configuration.
"""

import logging
import sys
import os
from typing import List, Dict, Any, Optional

# Add parent directory to path to allow importing radbot modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from radbot.tools.mcp.dynamic_tools_loader import load_dynamic_mcp_tools, load_specific_mcp_tools
from radbot.config.config_loader import config_loader

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dynamic_tool_loading():
    """Test loading tools from all enabled MCP servers."""
    print("\n🔍 Testing dynamic MCP tools loading...")
    
    # Get all tools
    tools = load_dynamic_mcp_tools()
    
    if not tools:
        print("❌ No tools were loaded dynamically")
        return False
        
    print(f"✅ Successfully loaded {len(tools)} tools dynamically")
    
    # Print some info about the tools
    tool_count_by_type = {}
    
    for tool in tools:
        tool_type = type(tool).__name__
        tool_count_by_type[tool_type] = tool_count_by_type.get(tool_type, 0) + 1
        
    print("\nTool types:")
    for tool_type, count in tool_count_by_type.items():
        print(f"  - {tool_type}: {count}")
        
    return True

def test_specific_servers():
    """Test loading tools from specific MCP servers."""
    print("\n🔍 Testing specific MCP servers...")
    
    # Get all enabled MCP servers
    servers = config_loader.get_enabled_mcp_servers()
    if not servers:
        print("❌ No enabled MCP servers found in configuration")
        return False
        
    print(f"Found {len(servers)} enabled MCP servers")
    
    # Track results for each server
    results = {}
    
    for server in servers:
        server_id = server.get("id")
        if not server_id:
            continue
            
        print(f"\nTesting server: {server_id}")
        
        # Load tools for this server
        tools = load_specific_mcp_tools(server_id)
        
        if not tools:
            print(f"❌ No tools loaded from {server_id}")
            results[server_id] = False
        else:
            print(f"✅ Loaded {len(tools)} tools from {server_id}")
            
            # Print tool names
            print("Tools:")
            for tool in tools:
                if hasattr(tool, "name"):
                    print(f"  - {tool.name}")
                elif hasattr(tool, "__name__"):
                    print(f"  - {tool.__name__}")
                else:
                    print(f"  - {str(tool)}")
                    
            results[server_id] = True
            
    # Summary
    success_count = sum(1 for result in results.values() if result)
    print(f"\n📊 Summary: Successfully loaded tools from {success_count}/{len(results)} servers")
    
    return success_count > 0

def main():
    """Main test function."""
    print("\n🔄 Dynamic MCP Tools Loader Test\n")
    
    # Test dynamic loading
    dynamic_success = test_dynamic_tool_loading()
    
    # Test specific servers
    specific_success = test_specific_servers()
    
    # Overall result
    if dynamic_success and specific_success:
        print("\n✅ All tests passed - Dynamic MCP tools loading is working properly")
        return 0
    else:
        print("\n⚠️ Some tests failed - Check the logs for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())