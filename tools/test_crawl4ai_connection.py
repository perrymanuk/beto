#!/usr/bin/env python3
"""
Diagnostic script for testing Crawl4AI MCP server connection.

This script directly tests the connectivity to a Crawl4AI MCP server
and analyzes potential issues without going through the full Radbot client
implementation. It can be used to verify that the server is working
correctly and to diagnose any connection issues.

Usage:
    python test_crawl4ai_connection.py --url https://crawl4ai.demonsafe.com/mcp/sse
    python test_crawl4ai_connection.py --url https://crawl4ai.demonsafe.com/mcp/sse --tool crawl
    python test_crawl4ai_connection.py --url https://crawl4ai.demonsafe.com/mcp/sse --tool search --target "python requests"
"""

import requests
import json
import logging
import time
import argparse
from typing import Dict, Any, Optional, List
import sys

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("crawl4ai_test")

class Crawl4AITester:
    """
    Tester class for validating Crawl4AI MCP server connections.
    
    This class implements step-by-step tests for:
    1. Server health check
    2. Schema discovery
    3. SSE connection and endpoint extraction
    4. Tool invocation with various tool names
    """
    
    def __init__(self, sse_url: str, debug: bool = False):
        """Initialize the tester with the SSE URL."""
        self.sse_url = sse_url
        # Extract base URL from the SSE URL
        if "/mcp/sse" in sse_url:
            self.base_url = sse_url.split("/mcp/sse")[0]
        elif "/sse" in sse_url:
            self.base_url = sse_url.split("/sse")[0]
        else:
            self.base_url = sse_url.rsplit("/", 1)[0]  # Remove the last part
            
        self.session_id = None
        self.message_endpoint = None
        self.headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json"
        }
        
        # Set debug logging if requested
        if debug:
            logger.setLevel(logging.DEBUG)
            logging.getLogger().setLevel(logging.DEBUG)
            
        logger.info(f"Initialized tester for URL: {sse_url}")
        logger.info(f"Extracted base URL: {self.base_url}")
    
    def test_health(self) -> bool:
        """Test the server health endpoint."""
        health_url = f"{self.base_url}/health"
        logger.info(f"Testing health endpoint: {health_url}")
        
        try:
            health_response = requests.get(health_url, timeout=5)
            logger.info(f"Health check status: {health_response.status_code}")
            logger.info(f"Health response: {health_response.text}")
            
            if health_response.status_code == 200:
                logger.info("✓ Health check succeeded")
                return True
            else:
                logger.warning("✗ Health check failed with non-200 status code")
                return False
        except Exception as e:
            logger.error(f"✗ Health check failed with exception: {e}")
            # Try alternative health endpoints
            alt_urls = [
                f"{self.base_url}/",
                f"{self.base_url}/status",
                f"{self.base_url}/api/health"
            ]
            
            for alt_url in alt_urls:
                try:
                    logger.info(f"Trying alternative health endpoint: {alt_url}")
                    alt_response = requests.get(alt_url, timeout=3)
                    if alt_response.status_code == 200:
                        logger.info(f"✓ Alternative health check succeeded: {alt_url}")
                        logger.info(f"Response: {alt_response.text[:100]}")
                        return True
                except Exception:
                    pass
                    
            logger.error("All health checks failed")
            return False
    
    def test_schema(self) -> Optional[List[str]]:
        """Test the schema endpoint and return available tool names."""
        schema_endpoints = [
            f"{self.base_url}/mcp/schema",
            f"{self.base_url}/schema",
            f"{self.base_url}/tools",
            f"{self.base_url}/api/tools"
        ]
        
        tool_names = []
        
        for schema_url in schema_endpoints:
            logger.info(f"Testing schema endpoint: {schema_url}")
            
            try:
                schema_response = requests.get(
                    schema_url, 
                    headers={"Accept": "application/json"},
                    timeout=5
                )
                logger.info(f"Schema check status for {schema_url}: {schema_response.status_code}")
                
                if schema_response.status_code == 200:
                    try:
                        schema = schema_response.json()
                        
                        # Handle different schema formats
                        if "tools" in schema and isinstance(schema["tools"], list):
                            tools = schema["tools"]
                            for tool in tools:
                                if "name" in tool:
                                    tool_names.append(tool["name"])
                        elif "functions" in schema and isinstance(schema["functions"], list):
                            functions = schema["functions"]
                            for func in functions:
                                if "name" in func:
                                    tool_names.append(func["name"])
                        elif isinstance(schema, list):
                            # Handle root array response
                            for item in schema:
                                if isinstance(item, dict) and "name" in item:
                                    tool_names.append(item["name"])
                        
                        if tool_names:
                            logger.info(f"✓ Schema check succeeded: found {len(tool_names)} tools")
                            logger.info(f"Available tools: {', '.join(tool_names)}")
                            return tool_names
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in schema response from {schema_url}")
            except Exception as e:
                logger.warning(f"Schema check failed for {schema_url}: {e}")
                
        if not tool_names:
            logger.warning("✗ No tools found in any schema endpoint")
            # Try to guess common tool names for Crawl4AI
            logger.info("Using guessed tool names for Crawl4AI")
            return ["crawl", "search", "extract", "scrape", 
                    "crawl_website", "web_search", "extract_content", "scrape_webpage",
                    "crawl4ai_crawl", "crawl4ai_search", "crawl4ai_extract", "crawl4ai_scrape"]
            
        return None
    
    def establish_sse_connection(self) -> bool:
        """Establish an SSE connection and extract the message endpoint."""
        logger.info(f"Establishing SSE connection to: {self.sse_url}")
        
        try:
            session = requests.Session()
            sse_response = session.get(
                self.sse_url,
                headers=self.headers,
                stream=True,
                timeout=10
            )
            
            if sse_response.status_code != 200:
                logger.error(f"✗ SSE connection failed with status: {sse_response.status_code}")
                return False
                
            logger.info("SSE connection established, parsing events...")
            
            # Flag to track if we found an endpoint
            found_endpoint = False
            
            # Read events from the SSE stream
            try:
                for i, line in enumerate(sse_response.iter_lines(decode_unicode=True)):
                    if i > 50:  # Limit the number of lines we read
                        break
                        
                    if line:
                        logger.debug(f"SSE event: {line}")
                        
                    if line and line.startswith("event: endpoint"):
                        # Next line should be the data
                        data_line = next(sse_response.iter_lines(decode_unicode=True), "")
                        if isinstance(data_line, bytes):
                            data_line = data_line.decode('utf-8')
                            
                        logger.debug(f"Endpoint data line: {data_line}")
                        
                        if data_line.startswith("data: "):
                            endpoint_path = data_line[6:].strip()  # Remove "data: " prefix
                            
                            # Construct the full message endpoint URL
                            self.message_endpoint = f"{self.base_url}{endpoint_path}"
                            
                            # Extract session ID if present in the endpoint URL
                            if "session_id=" in self.message_endpoint:
                                self.session_id = self.message_endpoint.split("session_id=")[1].split("&")[0]
                                logger.info(f"Extracted session ID: {self.session_id}")
                            
                            logger.info(f"✓ Extracted message endpoint: {self.message_endpoint}")
                            found_endpoint = True
                            break
                
                if not found_endpoint:
                    logger.warning("No endpoint event found in SSE stream")
                    # Try to generate a message endpoint
                    if "/sse" in self.sse_url:
                        import uuid
                        self.session_id = str(uuid.uuid4())
                        # Try to generate a message endpoint based on common patterns
                        if "/mcp/sse" in self.sse_url:
                            self.message_endpoint = f"{self.sse_url.replace('/mcp/sse', '/mcp/messages')}?session_id={self.session_id}"
                        else:
                            self.message_endpoint = f"{self.sse_url.replace('/sse', '/messages')}?session_id={self.session_id}"
                        logger.info(f"Generated message endpoint: {self.message_endpoint}")
                        logger.info(f"Generated session ID: {self.session_id}")
                        found_endpoint = True
            except Exception as e:
                logger.error(f"Error parsing SSE events: {e}")
                
            try:
                sse_response.close()
                session.close()
            except Exception:
                pass
            
            return found_endpoint
        except Exception as e:
            logger.error(f"✗ SSE connection failed: {e}")
            return False
    
    def test_tool_invocation(self, tool_name: str, target_url: str = "https://python.org") -> bool:
        """Test invoking a tool with the extracted message endpoint."""
        if not self.message_endpoint:
            logger.error("Cannot invoke tool without message endpoint")
            return False
            
        logger.info(f"Testing tool invocation: {tool_name}")
        
        # Prepare arguments based on tool name
        arguments = {}
        if tool_name in ["crawl", "crawl_website", "crawl4ai_crawl", "scrape", "scrape_webpage", "crawl4ai_scrape"]:
            arguments = {"url": target_url}
        elif tool_name in ["search", "web_search", "crawl4ai_search"]:
            arguments = {"query": target_url}  # Using target_url as query
        elif tool_name in ["extract", "extract_content", "crawl4ai_extract"]:
            arguments = {"url": target_url, "prompt": "Summarize this page"}
            
        # Create the JSON-RPC request
        request_data = {
            "jsonrpc": "2.0",
            "method": "invoke",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": "test-123"
        }
        
        try:
            logger.info(f"Sending request to: {self.message_endpoint}")
            logger.info(f"Request data: {json.dumps(request_data, indent=2)}")
            
            invoke_response = requests.post(
                self.message_endpoint,
                headers={"Content-Type": "application/json"},
                json=request_data,
                timeout=60
            )
            
            logger.info(f"Tool invocation status: {invoke_response.status_code}")
            
            if invoke_response.status_code == 200:
                try:
                    result = invoke_response.json()
                    logger.info(f"Response data: {json.dumps(result, indent=2)}")
                    
                    if "result" in result:
                        logger.info("✓ Tool invocation succeeded with standard JSON-RPC format")
                        return True
                    elif "output" in result:
                        logger.info("✓ Tool invocation succeeded with output format")
                        return True
                    elif "error" in result:
                        error_msg = result.get("error", {}).get("message", "Unknown error")
                        logger.error(f"✗ Tool invocation returned error: {error_msg}")
                        return False
                    else:
                        logger.info("✓ Tool invocation succeeded with custom format")
                        return True
                except json.JSONDecodeError:
                    logger.error(f"✗ Response is not valid JSON: {invoke_response.text[:200]}...")
                    return False
            else:
                logger.error(f"✗ Tool invocation failed with status code: {invoke_response.status_code}")
                try:
                    error_response = invoke_response.json()
                    logger.error(f"Error details: {json.dumps(error_response, indent=2)}")
                except:
                    logger.error(f"Error response text: {invoke_response.text[:200]}...")
                return False
        except Exception as e:
            logger.error(f"✗ Tool invocation failed with exception: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Test Crawl4AI MCP server")
    parser.add_argument("--url", default="https://crawl4ai.demonsafe.com/mcp", 
                        help="MCP base URL")
    parser.add_argument("--transport", default="http", choices=["http", "sse"],
                        help="Transport to use (http or sse)")
    parser.add_argument("--tool", default="crawl", 
                        help="Tool name to test")
    parser.add_argument("--target", default="https://python.org", 
                        help="URL to crawl or query to search")
    parser.add_argument("--debug", action="store_true", 
                        help="Enable debug logging")
    args = parser.parse_args()
    
    logger.info("=== Crawl4AI MCP Connection Test ===")
    logger.info(f"Testing URL: {args.url}")
    logger.info(f"Transport: {args.transport}")
    logger.info(f"Testing tool: {args.tool}")
    logger.info(f"Target: {args.target}")
    
    # Build the actual URL based on transport
    full_url = args.url
    if args.transport == "sse":
        if not full_url.endswith("/sse"):
            full_url = f"{args.url}/sse"
    elif args.transport == "http":
        # Remove /sse suffix if it exists
        if full_url.endswith("/sse"):
            full_url = full_url[:-4]
    
    logger.info(f"Full URL to test: {full_url}")
    tester = Crawl4AITester(full_url, debug=args.debug)
    
    # Step 1: Health check
    logger.info("\n=== Step 1: Health Check ===")
    if not tester.test_health():
        logger.error("Health check failed, but continuing with other tests")
    
    # Step 2: Schema check
    logger.info("\n=== Step 2: Schema Check ===")
    tool_names = tester.test_schema()
    if tool_names:
        logger.info("Schema check succeeded")
        
        # Check if the specified tool exists
        if args.tool not in tool_names:
            logger.warning(f"Specified tool '{args.tool}' not found in schema")
            logger.info(f"Available tools: {', '.join(tool_names)}")
            logger.info(f"Will try the specified tool anyway")
    
    # Step 3: Establish connection based on transport
    if args.transport == "sse":
        logger.info("\n=== Step 3: SSE Connection ===")
        if not tester.establish_sse_connection():
            logger.error("Failed to establish SSE connection, aborting")
            return 1
    else:
        logger.info("\n=== Step 3: HTTP Connection ===")
        # For HTTP transport, we need to set the message endpoint with trailing slash
        tester.message_endpoint = f"{args.url}/messages/"
        logger.info(f"Using HTTP transport with endpoint: {tester.message_endpoint}")
        
        # Generate a session ID for testing
        import uuid
        tester.session_id = str(uuid.uuid4())
        logger.info(f"Generated test session ID: {tester.session_id}")
        
        # Update message endpoint with session ID
        tester.message_endpoint = f"{tester.message_endpoint}?session_id={tester.session_id}"
        logger.info(f"Complete message endpoint with session ID: {tester.message_endpoint}")
    
    # Step 4: Tool invocation
    logger.info("\n=== Step 4: Tool Invocation ===")
    if not tester.test_tool_invocation(args.tool, args.target):
        logger.warning(f"Tool '{args.tool}' invocation failed, trying alternative tool names")
        
        # Try alternative tool names if the primary one fails
        if args.tool.startswith("crawl4ai_"):
            # Try without prefix
            alt_tool = args.tool[len("crawl4ai_"):]
            logger.info(f"Trying alternative tool name: {alt_tool}")
            if tester.test_tool_invocation(alt_tool, args.target):
                logger.info(f"✓ Alternative tool '{alt_tool}' invocation succeeded")
                logger.info(f"The correct tool name to use is: {alt_tool}")
                return 0
        else:
            # Try with prefix
            alt_tool = f"crawl4ai_{args.tool}"
            logger.info(f"Trying alternative tool name: {alt_tool}")
            if tester.test_tool_invocation(alt_tool, args.target):
                logger.info(f"✓ Alternative tool '{alt_tool}' invocation succeeded")
                logger.info(f"The correct tool name to use is: {alt_tool}")
                return 0
        
        logger.error("Tool invocation failed with all attempted names")
        
        # Print summary report
        logger.info("\n=== Connection Test Results ===")
        logger.info(f"✗ Tool invocation test FAILED")
        logger.info(f"SSE URL: {args.url}")
        logger.info(f"Message endpoint: {tester.message_endpoint}")
        logger.info(f"Session ID: {tester.session_id}")
        logger.info(f"Attempted tool name: {args.tool}")
        
        logger.info("\n=== Suggestions ===")
        logger.info("1. Verify the Crawl4AI MCP server URL is correct")
        logger.info("2. Ensure the tool name is correct (try both with and without 'crawl4ai_' prefix)")
        logger.info("3. Verify network connectivity to the server")
        logger.info("4. Check if the server requires authentication")
        logger.info("5. Try running the test with --debug flag for more detailed logs")
        
        return 1
    
    # All tests passed
    logger.info("\n=== Connection Test Results ===")
    logger.info("✓ All tests PASSED successfully!")
    logger.info(f"SSE URL: {args.url}")
    logger.info(f"Message endpoint: {tester.message_endpoint}")
    logger.info(f"Session ID: {tester.session_id}")
    logger.info(f"Working tool name: {args.tool}")
    
    # Configuration advice
    logger.info("\n=== Configuration Advice ===")
    logger.info("Add the following to your config.yaml file:")
    print(f"""
mcp_servers:
  - id: crawl4ai
    url: {args.url}
    message_endpoint: {tester.message_endpoint}
    tools:
      - crawl
      - search
      - extract
      - scrape
    transport: sse
    description: "Crawl4AI web research tools"
    """)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())