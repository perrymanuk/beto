#!/usr/bin/env python3
"""
Test script for MCP configuration and tools.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from radbot.config.config_loader import config_loader
from radbot.tools.mcp.mcp_client_factory import MCPClientFactory
from radbot.tools.mcp.mcp_tools import get_available_mcp_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_config_loader():
    """Test the ConfigLoader."""
    print("\n=== Testing ConfigLoader ===")
    
    # Get the full configuration
    config = config_loader.get_config()
    print(f"Configuration file path: {config_loader.config_path}")
    print(f"Configuration sections: {', '.join(config.keys())}")
    
    # Get MCP configuration
    mcp_config = config_loader.get_mcp_config()
    servers = config_loader.get_mcp_servers()
    enabled_servers = config_loader.get_enabled_mcp_servers()
    
    print(f"MCP servers configured: {len(servers)}")
    print(f"MCP servers enabled: {len(enabled_servers)}")
    
    # Print details of each server
    for i, server in enumerate(servers):
        enabled = server.get("enabled", True)
        server_id = server.get("id")
        server_name = server.get("name", server_id)
        transport = server.get("transport", "sse")
        url = server.get("url")
        
        print(f"\n  Server {i+1}: {server_name} ({server_id})")
        print(f"  Enabled: {enabled}")
        print(f"  Transport: {transport}")
        print(f"  URL: {url}")
        
        # Check if specific server exists
        is_enabled = config_loader.is_mcp_server_enabled(server_id)
        print(f"  is_mcp_server_enabled: {is_enabled}")
        
        server_config = config_loader.get_mcp_server(server_id)
        if server_config:
            print(f"  get_mcp_server: Found")
        else:
            print(f"  get_mcp_server: Not found")

def test_mcp_client_factory():
    """Test the MCPClientFactory."""
    print("\n=== Testing MCPClientFactory ===")
    
    # Get all enabled servers
    servers = config_loader.get_enabled_mcp_servers()
    
    for server in servers:
        server_id = server.get("id")
        server_name = server.get("name", server_id)
        
        print(f"\nTesting client for server: {server_name} ({server_id})")
        
        try:
            # Try to get a client
            client = MCPClientFactory.get_client(server_id)
            print(f"  Client created successfully: {type(client).__name__}")
            
            # Test client properties and methods
            if hasattr(client, "url"):
                print(f"  URL: {client.url}")
            
            # Check if client has tools
            if hasattr(client, "tools") and isinstance(client.tools, list):
                print(f"  Tools: {len(client.tools)} found")
                
                # Print the first 3 tool names
                tool_names = []
                for tool in client.tools[:3]:
                    if hasattr(tool, "name"):
                        tool_names.append(tool.name)
                    elif hasattr(tool, "__name__"):
                        tool_names.append(tool.__name__)
                    else:
                        tool_names.append(str(type(tool)))
                
                if tool_names:
                    print(f"  Sample tools: {', '.join(tool_names)}")
            
            # Check for get_tools method
            if hasattr(client, "get_tools") and callable(client.get_tools):
                print("  get_tools method: Available")
            else:
                print("  get_tools method: Not available")
            
            # Check for create_tools method
            if hasattr(client, "create_tools") and callable(client.create_tools):
                print("  create_tools method: Available")
            else:
                print("  create_tools method: Not available")
                
        except Exception as e:
            print(f"  Error creating client: {e}")

def test_get_available_mcp_tools():
    """Test getting all available MCP tools."""
    print("\n=== Testing get_available_mcp_tools ===")
    
    try:
        tools = get_available_mcp_tools()
        print(f"Found {len(tools)} MCP tools")
        
        # Group tools by type/name
        tool_types = {}
        for tool in tools:
            if hasattr(tool, "name"):
                name = tool.name
            elif hasattr(tool, "__name__"):
                name = tool.__name__
            else:
                name = str(type(tool))
                
            # Extract tool type (prefix before first underscore or digit)
            import re
            match = re.match(r'^([a-zA-Z]+)', name)
            if match:
                tool_type = match.group(1)
            else:
                tool_type = "Unknown"
                
            if tool_type not in tool_types:
                tool_types[tool_type] = []
            tool_types[tool_type].append(name)
        
        # Print summary by type
        print("\nTools by type:")
        for tool_type, names in tool_types.items():
            print(f"  {tool_type}: {len(names)} tools")
            # Print up to 3 sample tool names
            samples = names[:3]
            if samples:
                print(f"    Samples: {', '.join(samples)}")
                
    except Exception as e:
        print(f"Error getting MCP tools: {e}")

def main():
    print("Testing MCP Configuration and Tools")
    print("==================================")
    
    try:
        test_config_loader()
        test_mcp_client_factory()
        test_get_available_mcp_tools()
        
        print("\nAll tests completed successfully!")
        return 0
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())