#!/usr/bin/env python3
"""
Simple test script for Crawl4AI.

This is a minimal test that directly instantiates the MCPSSEClient
and tries to use it to access Crawl4AI, without going through the
full agent framework.
"""

import logging
import argparse
from radbot.tools.mcp.client import MCPSSEClient

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_crawl4ai_simple")

def main():
    parser = argparse.ArgumentParser(description="Test Crawl4AI with MCPSSEClient")
    parser.add_argument("--url", default="https://python.org",
                        help="URL to crawl")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Testing Crawl4AI with target URL: {args.url}")
    
    # Create a client
    client = MCPSSEClient(
        url="https://crawl4ai.demonsafe.com/mcp/sse",
        timeout=60,
        message_endpoint="https://crawl4ai.demonsafe.com/mcp/messages/"
    )
    
    # Initialize
    logger.info("Initializing client...")
    if not client.initialize():
        logger.error("Failed to initialize client")
        return 1
    
    logger.info(f"Client initialized successfully")
    logger.info(f"Message endpoint: {client.message_endpoint}")
    logger.info(f"Session ID: {client.session_id}")
    logger.info(f"Created {len(client.tools)} tools")
    
    # Look for the crawl tool
    # Print the tool information for debugging
    for i, tool in enumerate(client.tools):
        logger.info(f"Tool {i}: {str(tool)}")
        
    # Simplify the approach - just use the client directly
    crawl_tool = "crawl"  # Just use the tool name, don't use the tool object
    
    # The test can continue even without finding a specific tool since we'll call _call_tool directly
    
    # Try to use the crawl tool
    logger.info(f"Using crawl tool to access {args.url}")
    try:
        # Call the tool directly using the client's _call_tool method
        result = client._call_tool("crawl", {"url": args.url})
        
        logger.info("Crawl successful!")
        if isinstance(result, dict):
            logger.info(f"Result keys: {list(result.keys())}")
            
            # If there's a markdown field, show a preview
            if "markdown" in result and result["markdown"]:
                logger.info(f"Markdown preview: {result['markdown'][:200]}...")
        else:
            logger.info(f"Result type: {type(result)}")
        
        return 0
    except Exception as e:
        logger.error(f"Crawl failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())