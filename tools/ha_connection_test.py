#!/usr/bin/env python3
"""
Test script for Home Assistant MCP connection.

This script tests the connection to Home Assistant via MCP and displays available tools.
"""

import os
import logging
import sys
from pprint import pprint

# Add the parent directory to the path so we can import radbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from radbot.tools.mcp_tools import create_home_assistant_toolset
from radbot.tools.mcp_utils import test_home_assistant_connection, list_home_assistant_domains

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the Home Assistant MCP connection test."""
    print("=" * 60)
    print(" Home Assistant MCP Connection Test ".center(60, "="))
    print("=" * 60)
    
    # Test the Home Assistant MCP connection
    print("\nTesting connection to Home Assistant MCP server...")
    result = test_home_assistant_connection()
    
    if result["success"]:
        print(f"\n✅ Connection successful!")
        print(f"Found {result.get('tools_count', 0)} tools")
        
        # List available domains
        domains = list_home_assistant_domains()
        if domains["success"] and domains["domains"]:
            print(f"\nAvailable domains: {', '.join(domains['domains'])}")
            
            # Display all tools
            if result.get("tools"):
                print("\nAvailable tools:")
                for tool in sorted(result["tools"]):
                    print(f"  - {tool}")
        else:
            print("\nNo domains found. Home Assistant may not have exposed any tools.")
    else:
        print(f"\n❌ Connection failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print("\nCheck your environment variables:")
        print(f"  HA_MCP_SSE_URL: {'SET' if os.getenv('HA_MCP_SSE_URL') else 'NOT SET'}")
        print(f"  HA_AUTH_TOKEN: {'SET' if os.getenv('HA_AUTH_TOKEN') else 'NOT SET'}")

if __name__ == "__main__":
    main()