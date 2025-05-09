#!/usr/bin/env python
"""
Test the fixed implementation of the Crawl4AI MCP client connection.

This script validates that the improved MCP client can connect to the
Crawl4AI MCP server and execute tool calls successfully.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Run the test for the fixed Crawl4AI MCP connection."""
    # Import required modules
    from radbot.config.config_loader import config_loader
    from radbot.tools.mcp.client import MCPSSEClient
    
    # Get the server configuration from config.yaml
    server_config = config_loader.get_mcp_server("crawl4ai")
    
    if not server_config:
        logger.error("Crawl4AI server not configured in config.yaml")
        return False
    
    url = server_config.get("url")
    message_endpoint = server_config.get("message_endpoint")
    auth_token = server_config.get("auth_token")
    
    logger.info(f"Testing connection to Crawl4AI MCP server: {url}")
    logger.info(f"Message endpoint: {message_endpoint}")
    logger.info(f"Auth token available: {auth_token is not None}")
    
    # Create the MCP client
    client = MCPSSEClient(
        url=url,
        auth_token=auth_token,
        message_endpoint=message_endpoint,
        timeout=30  # Use a reasonable timeout
    )
    
    # Initialize the client to get tools
    logger.info("Initializing MCP client...")
    success = client.initialize()
    
    if not success:
        logger.error("Failed to initialize MCP client")
        return False
    
    logger.info(f"Successfully initialized client, found {len(client.tools)} tools")
    
    # Print the tools that were found
    logger.info(f"Tools found: {len(client.tools)}")
    
    # Try directly using the client's _call_tool method for crawl4ai_search
    logger.info("Testing crawl4ai_search tool directly...")
    try:
        # Call the search tool directly using the client's _call_tool method
        search_args = {"query": "Google Agent Development Kit"}
        result = client._call_tool("crawl4ai_search", search_args)
        
        if result:
            logger.info(f"Search result successful: {str(result)[:500]}...")
            return True
        else:
            logger.warning("Search returned empty result")
            return False
            
    except Exception as e:
        logger.error(f"Error during direct tool invocation: {e}")
        return False

if __name__ == "__main__":
    result = main()
    if result:
        logger.info("Test successful!")
        sys.exit(0)
    else:
        logger.error("Test failed!")
        sys.exit(1)