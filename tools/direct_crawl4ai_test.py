#!/usr/bin/env python3
"""
Direct Crawl4AI test script.

This script directly tests the connection to the Crawl4AI server without
going through the full Radbot framework.
"""

import argparse
import logging
import requests
import json
import uuid
import time

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("direct_crawl4ai")

def test_crawl4ai(url: str, target_url: str):
    """Test Crawl4AI connection directly."""
    logger.info(f"Testing Crawl4AI connection to {url}")
    
    # Step 1: Establish SSE connection to get session ID
    logger.info("Step 1: Establishing SSE connection")
    
    headers = {
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache"
    }
    
    try:
        sse_response = requests.get(url, headers=headers, stream=True, timeout=10)
        
        if sse_response.status_code != 200:
            logger.error(f"SSE connection failed with status {sse_response.status_code}")
            return False
        
        logger.info("SSE connection established, parsing events...")
        
        session_id = None
        message_endpoint = None
        
        # Read the first few lines from the SSE stream
        for i, line in enumerate(sse_response.iter_lines(decode_unicode=True)):
            if i > 20:  # Limit to first 20 lines
                break
                
            if line:
                logger.info(f"SSE event: {line}")
                
            if line and line.startswith("event: endpoint"):
                # Get the next line for data
                try:
                    data_line = next(sse_response.iter_lines(decode_unicode=True), "")
                    logger.info(f"Data line: {data_line}")
                    
                    if data_line.startswith("data: "):
                        endpoint_path = data_line[6:].strip()
                        
                        # Get base URL
                        base_url = url.split("/mcp/")[0] if "/mcp/" in url else url.rsplit("/", 1)[0]
                        
                        # Construct message endpoint
                        message_endpoint = f"{base_url}{endpoint_path}"
                        
                        # Extract session ID if present
                        if "session_id=" in message_endpoint:
                            session_id = message_endpoint.split("session_id=")[1].split("&")[0]
                            
                        logger.info(f"Found message endpoint: {message_endpoint}")
                        logger.info(f"Extracted session ID: {session_id}")
                        break
                except Exception as e:
                    logger.error(f"Error parsing data line: {e}")
        
        # Close the SSE connection
        try:
            sse_response.close()
        except:
            pass
            
        # If we didn't find a message endpoint, create one
        if not message_endpoint:
            logger.info("No message endpoint found in SSE response, creating one")
            
            # Get base URL
            base_url = url.split("/mcp/")[0] if "/mcp/" in url else url.rsplit("/", 1)[0]
            
            # Create session ID
            session_id = str(uuid.uuid4())
            
            # Create message endpoint
            if url.endswith("/sse"):
                message_endpoint = f"{url[:-4]}/messages/?session_id={session_id}"
            else:
                message_endpoint = f"{url.replace('/sse', '/messages/')}?session_id={session_id}"
                
            logger.info(f"Created message endpoint: {message_endpoint}")
            logger.info(f"Created session ID: {session_id}")
        
        # Step 2: Get schema to find available tools
        logger.info("Step 2: Getting schema")
        
        schema_url = f"{url.split('/sse')[0]}/schema"
        logger.info(f"Schema URL: {schema_url}")
        
        try:
            schema_response = requests.get(schema_url, timeout=5)
            
            if schema_response.status_code == 200:
                schema = schema_response.json()
                
                tools = []
                if "tools" in schema and isinstance(schema["tools"], list):
                    tools = [t.get("name") for t in schema["tools"] if "name" in t]
                    
                logger.info(f"Available tools: {tools}")
                
                # Use "crawl" tool if available
                tool_name = "crawl" if "crawl" in tools else tools[0] if tools else "crawl"
            else:
                logger.warning(f"Schema request failed with status {schema_response.status_code}")
                tool_name = "crawl"  # Default
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            tool_name = "crawl"  # Default
        
        # Step 3: Call the tool
        logger.info(f"Step 3: Calling tool {tool_name}")
        
        request_data = {
            "jsonrpc": "2.0",
            "method": "invoke",
            "params": {
                "name": tool_name,
                "arguments": {
                    "url": target_url
                }
            },
            "id": str(uuid.uuid4())
        }
        
        logger.info(f"Sending request to: {message_endpoint}")
        logger.info(f"Request data: {json.dumps(request_data, indent=2)}")
        
        try:
            invoke_response = requests.post(
                message_endpoint,
                headers={"Content-Type": "application/json"},
                json=request_data,
                timeout=60
            )
            
            logger.info(f"Tool invocation status: {invoke_response.status_code}")
            
            if invoke_response.status_code == 200:
                try:
                    result = invoke_response.json()
                    logger.info("Tool invocation succeeded!")
                    logger.info(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    return True
                except json.JSONDecodeError:
                    logger.error(f"Response is not valid JSON: {invoke_response.text[:200]}...")
                    return False
            else:
                logger.error(f"Tool invocation failed: {invoke_response.text}")
                return False
        except Exception as e:
            logger.error(f"Error invoking tool: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error establishing SSE connection: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test Crawl4AI connection directly")
    parser.add_argument("--url", default="https://crawl4ai.demonsafe.com/mcp/sse",
                        help="URL of the Crawl4AI MCP SSE endpoint")
    parser.add_argument("--target", default="https://python.org",
                        help="URL to crawl")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = test_crawl4ai(args.url, args.target)
    
    if success:
        logger.info("Test completed successfully!")
        return 0
    else:
        logger.error("Test failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())