#!/usr/bin/env python
"""
Test the crawl4ai tool call directly.
"""

import os
import sys
import logging
import time

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

def test_crawl4ai_tool_call():
    """Test a direct call to the Crawl4AI tool."""
    from radbot.tools.mcp.client import MCPSSEClient
    
    # Create client
    url = "https://crawl4ai.demonsafe.com/mcp/sse"
    client = MCPSSEClient(url=url, timeout=60)
    
    # Initialize client - this will create dummy tools
    success = client.initialize()
    if not success:
        logger.error("Failed to initialize client")
        return
    
    # Log available tools
    logger.info(f"Available tools: {[getattr(t, 'name', str(t)) for t in client.tools]}")
    
    # Call the crawl tool directly
    logger.info("Calling crawl4ai_crawl tool directly...")
    url_to_crawl = "https://github.com/google/adk-samples"
    
    # Access the _call_tool method directly
    start_time = time.time()
    result = client._call_tool("crawl4ai_crawl", {"url": url_to_crawl})
    logger.info(f"Tool call completed in {time.time() - start_time:.2f} seconds")
    
    # Print the result
    logger.info(f"Result: {result}")
    
    # Try enabling verbose logging
    client.headers["X-Debug"] = "true"
    
    # Test different endpoints
    test_endpoints = [
        "/v1/invoke",
        "",
        "/invoke",
        "/api/invoke"
    ]
    
    for endpoint in test_endpoints:
        try:
            logger.info(f"Testing endpoint: {url}{endpoint}")
            invoke_url = f"{url}{endpoint}"
            
            # Prepare JSON-RPC request
            import uuid
            request_data = {
                "jsonrpc": "2.0",
                "method": "invoke",
                "params": {
                    "name": "crawl4ai_crawl",
                    "arguments": {"url": url_to_crawl}
                },
                "id": str(uuid.uuid4())
            }
            
            # Make direct request
            import requests
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Debug": "true"
            }
            
            response = requests.post(
                invoke_url,
                headers=headers,
                json=request_data,
                timeout=30
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            if response.status_code == 200:
                try:
                    logger.info(f"Response content: {response.json()}")
                except:
                    logger.info(f"Response content (raw): {response.text[:500]}...")
            else:
                logger.info(f"Response content: {response.text[:500]}...")
        except Exception as e:
            logger.error(f"Error testing endpoint {endpoint}: {e}")
    
    return result

if __name__ == "__main__":
    test_crawl4ai_tool_call()