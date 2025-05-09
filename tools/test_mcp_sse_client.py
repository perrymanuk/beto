#!/usr/bin/env python
"""
Test script for the improved MCPSSEClient implementation.

This script tests the connection to an MCP server using the improved MCPSSEClient.
"""

import os
import sys
import argparse
import logging
import time
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_mcp_client(url: str, auth_token: Optional[str] = None, timeout: int = 30):
    """
    Test the MCPSSEClient with the given URL.
    
    Args:
        url: The URL of the MCP server
        auth_token: Optional authentication token
        timeout: Request timeout in seconds
    """
    try:
        from radbot.tools.mcp.client import MCPSSEClient
        
        # Create the client
        logger.info(f"Creating MCPSSEClient for {url}")
        start_time = time.time()
        client = MCPSSEClient(url=url, auth_token=auth_token, timeout=timeout)
        logger.info(f"Client created in {time.time() - start_time:.2f} seconds")
        
        # Initialize the client
        logger.info(f"Initializing client...")
        start_time = time.time()
        success = client.initialize()
        elapsed = time.time() - start_time
        
        if success:
            logger.info(f"Client initialization successful in {elapsed:.2f} seconds")
            logger.info(f"Retrieved {len(client.tools)} tools from the server")
            
            # Print the tool names
            if client.tools:
                logger.info("Tools:")
                for i, tool in enumerate(client.tools):
                    tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
                    logger.info(f"  {i+1}. {tool_name}")
            else:
                logger.warning("No tools were retrieved")
        else:
            logger.error(f"Client initialization failed after {elapsed:.2f} seconds")
        
        return success
    except Exception as e:
        logger.error(f"Error testing MCP client: {e}")
        return False

def test_crawl4ai_server(auth_token: Optional[str] = None, timeout: int = 30):
    """
    Test connection to a Crawl4AI MCP server.
    
    Args:
        auth_token: Optional authentication token
        timeout: Request timeout in seconds
    """
    # First check if we have a Crawl4AI server configured
    from radbot.config.config_loader import config_loader
    
    servers = config_loader.get_enabled_mcp_servers()
    crawl4ai_server = None
    
    for server in servers:
        server_id = server.get("id", "unknown")
        if "crawl4ai" in server_id.lower():
            crawl4ai_server = server
            break
    
    if not crawl4ai_server:
        logger.warning("No Crawl4AI MCP server found in configuration")
        return False
    
    url = crawl4ai_server.get("url")
    if not url:
        logger.warning("Crawl4AI MCP server has no URL in configuration")
        return False
    
    # Use the configured auth token if not provided
    if not auth_token and crawl4ai_server.get("auth_token"):
        auth_token = crawl4ai_server.get("auth_token")
    
    logger.info(f"Testing connection to Crawl4AI MCP server at {url}")
    return test_mcp_client(url, auth_token, timeout)

def main():
    """Main function to run the test script."""
    parser = argparse.ArgumentParser(description="Test the MCPSSEClient implementation")
    parser.add_argument("--url", help="URL of the MCP server")
    parser.add_argument("--token", help="Authentication token for the MCP server")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--crawl4ai", action="store_true", help="Test connection to Crawl4AI MCP server from config")
    
    args = parser.parse_args()
    
    if args.crawl4ai:
        # Test connection to Crawl4AI MCP server from config
        success = test_crawl4ai_server(args.token, args.timeout)
    elif args.url:
        # Test connection to specified URL
        success = test_mcp_client(args.url, args.token, args.timeout)
    else:
        parser.print_help()
        sys.exit(1)
    
    if success:
        logger.info("MCP client test PASSED")
        sys.exit(0)
    else:
        logger.error("MCP client test FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()