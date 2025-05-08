"""
Custom MCP client implementation for Radbot.

This module provides an improved MCP client implementation for
connecting to MCP servers from Radbot, based on best practices from
the official MCP Python SDK and other examples, with modifications
for robustness and error resilience.
"""

import logging
import requests
import json
import re
import time
import asyncio
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple, Callable, Union

logger = logging.getLogger(__name__)

class MCPSSEClient:
    """
    An improved MCP client for Radbot.
    
    This implementation provides better resilience for MCP servers
    over Server-Sent Events (SSE) or HTTP transport with support for timeouts
    and fallback mechanisms, following patterns from the official
    MCP Python SDK with simplifications for synchronous usage.
    
    This client supports both SSE and standard HTTP transports, automatically
    adapting to the server's capabilities.
    """
    
    # Protocol and version constants
    PROTOCOL_VERSION = "2025-03-26"
    SUPPORTED_VERSIONS = ["2025-03-26", "2024-04-18", "2024-02-15"]
    
    def __init__(self, url: str, auth_token: Optional[str] = None,
                 timeout: int = 30, headers: Optional[Dict[str, str]] = None,
                 message_endpoint: Optional[str] = None):
        """
        Initialize the MCP SSE client.
        
        Args:
            url: The URL of the MCP server
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
            headers: Optional additional headers
            message_endpoint: Optional URL for sending tool invocation messages
                              (used with SSE transport)
        """
        # Normalize and validate the URL
        self.url = self._normalize_url(url)
        self.auth_token = auth_token
        self.timeout = timeout
        self.headers = headers or {}
        self.message_endpoint = message_endpoint
        
        # Add authorization header if token is provided
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
        
        # Add required headers for SSE
        self.headers.update({
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json"
        })
        
        # Initialize tools list and server info
        self.tools = []
        self.server_info = {}
        self.server_version = None
        self.session_id = None
        logger.info(f"Initialized MCPSSEClient for {url}")
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize the URL by ensuring it has the correct scheme and path.
        
        Args:
            url: The URL to normalize
            
        Returns:
            Normalized URL
        """
        # Remove trailing slashes
        url = url.rstrip("/")
        
        # Ensure URL has a scheme
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            logger.info(f"Added HTTPS scheme to URL: {url}")
        
        # Try to parse the URL to validate it
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.netloc:
                raise ValueError(f"Invalid URL: {url}")
        except Exception as e:
            logger.warning(f"URL validation warning: {e}")
        
        return url
    
    def initialize(self) -> bool:
        """
        Initialize the connection to the MCP server and retrieve tools.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # First, use a quick check to see if the server is responding
            logger.info(f"Testing connection to MCP server: {self.url}")
            
            # Use a very short timeout for initial connection check
            test_timeout = min(5, self.timeout)
            
            # Try a HEAD request to check if server is alive
            try:
                head_response = requests.head(
                    self.url,
                    headers={**self.headers, "Accept": "application/json"},  # Override Accept for this call
                    timeout=test_timeout
                )
                
                if head_response.status_code >= 400:
                    logger.warning(f"MCP server returned status code: {head_response.status_code}")
                    # Don't return here, continue to try the list_tools endpoint
            except requests.exceptions.RequestException as e:
                logger.warning(f"Head request to MCP server failed: {e}")
                # Continue with the main approach
            
            # Now try to actually get the list of tools from the server
            try:
                # Try different endpoints for tools based on common MCP server implementations
                tool_endpoints = [
                    "/tools",        # Standard endpoint
                    "",              # Base URL (some servers provide tools directly)
                    "/v1/tools",     # Version-specific endpoint
                    "/api/tools"     # Alternative API path
                ]
                
                tools_found = False
                
                for endpoint in tool_endpoints:
                    tools_url = f"{self.url}{endpoint}"
                    logger.info(f"Requesting tools from: {tools_url}")
                    
                    try:
                        tools_response = requests.get(
                            tools_url,
                            headers={**self.headers, "Accept": "application/json"},  # Override Accept for this call
                            timeout=test_timeout
                        )
                        
                        if tools_response.status_code == 200:
                            try:
                                # Try to parse the response as JSON
                                tools_data = tools_response.json()
                                
                                # Check if this looks like a tools response
                                if isinstance(tools_data, list) and len(tools_data) > 0:
                                    logger.info(f"Successfully got tools from {tools_url}: {len(tools_data)} tools found")
                                    self._process_tools(tools_data)
                                    tools_found = True
                                    break
                                elif isinstance(tools_data, dict) and ("tools" in tools_data or "functions" in tools_data):
                                    # Some servers return a wrapper object
                                    tools_key = "tools" if "tools" in tools_data else "functions"
                                    tools_list = tools_data.get(tools_key, [])
                                    if isinstance(tools_list, list) and len(tools_list) > 0:
                                        logger.info(f"Successfully got tools from {tools_url}: {len(tools_list)} tools found")
                                        self._process_tools(tools_list)
                                        tools_found = True
                                        break
                                else:
                                    logger.warning(f"Response from {tools_url} doesn't match expected tools format")
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.warning(f"Error parsing tools response from {tools_url}: {e}")
                        else:
                            logger.warning(f"Endpoint {tools_url} returned status code: {tools_response.status_code}")
                    except requests.exceptions.RequestException as e:
                        logger.warning(f"Error requesting from {tools_url}: {e}")
                
                if tools_found and len(self.tools) > 0:
                    return True
            except Exception as e:
                logger.warning(f"Error during tools discovery: {e}")
            
            # If we couldn't get the tools through the direct endpoints,
            # try using SSE to get server info
            try:
                # Try different SSE endpoints based on common MCP server implementations
                sse_endpoints = [
                    "/v1",          # Standard SSE endpoint
                    "",             # Direct base URL
                    "/sse",         # Explicit SSE path
                    "/api/sse",     # Alternative API path
                    "/stream"       # Alternative stream endpoint
                ]
                
                for endpoint in sse_endpoints:
                    sse_url = f"{self.url}{endpoint}"
                    logger.info(f"Attempting SSE connection to: {sse_url}")
                    
                    try:
                        session = requests.Session()
                        
                        # Use the session to make a GET request with stream=True for SSE
                        sse_response = session.get(
                            sse_url,
                            headers=self.headers,
                            stream=True,
                            timeout=test_timeout
                        )
                        
                        if sse_response.status_code == 200:
                            # Read the first few events to get server info
                            server_info = None
                            for i, line in enumerate(sse_response.iter_lines(decode_unicode=True)):
                                if i > 50:  # Limit the number of lines we read
                                    break
                                    
                                if line.startswith("data:"):
                                    try:
                                        data = json.loads(line[5:].strip())
                                        if "type" in data and data["type"] == "serverInfo":
                                            server_info = data
                                            break
                                    except json.JSONDecodeError:
                                        pass
                            
                            # Close the connection
                            sse_response.close()
                            session.close()
                            
                            # Process server info if we got it
                            if server_info:
                                logger.info("Successfully got server info from SSE connection")
                                self._process_server_info(server_info)
                                if len(self.tools) > 0:
                                    return True
                                break
                        else:
                            logger.warning(f"SSE connection to {sse_url} returned status code: {sse_response.status_code}")
                            sse_response.close()
                            session.close()
                    except requests.exceptions.RequestException as e:
                        logger.warning(f"Error establishing SSE connection to {sse_url}: {e}")
            except Exception as e:
                logger.warning(f"Error during SSE connection attempts: {e}")
            
            # If we still don't have any tools, use our fallback method
            logger.info("Using fallback method to create tools based on server URL")
            self._create_dummy_tools_for_server()
            return len(self.tools) > 0
            
        except Exception as e:
            logger.error(f"Error initializing MCP client: {e}")
            # Try to create dummy tools as a last resort
            try:
                self._create_dummy_tools_for_server()
                return len(self.tools) > 0
            except:
                return False
    
    def _process_server_info(self, server_info: Dict[str, Any]) -> None:
        """
        Process server information and capabilities.
        
        Args:
            server_info: The server information from the MCP server
        """
        if "tools" in server_info:
            self._process_tools(server_info["tools"])
        elif "functions" in server_info:
            self._process_tools(server_info["functions"])
    
    def _process_tools(self, tools_info: List[Dict[str, Any]]) -> None:
        """
        Process tool information from the MCP server.
        
        Args:
            tools_info: The list of tools from the MCP server
        """
        from google.adk.tools import FunctionTool
        
        for tool_info in tools_info:
            try:
                # Create a FunctionTool from the tool information
                tool_name = tool_info.get("name", "unknown_tool")
                
                # Create the function that will call the MCP server
                def create_tool_function(name):
                    def tool_function(**kwargs):
                        # Special handling for crawl4ai tools
                        if "crawl4ai" in self.url.lower() and name.startswith("crawl4ai_"):
                            logger.info(f"Special handling for crawl4ai tool: {name}")
                            
                            # Set message_endpoint if not already set
                            if not self.message_endpoint and "/sse" in self.url:
                                # Crawl4AI requires trailing slash for messages endpoint
                                self.message_endpoint = self.url.replace("/sse", "/messages/")
                                logger.info(f"Auto-set message_endpoint for crawl4ai: {self.message_endpoint}")
                            
                        return self._call_tool(name, kwargs)
                    tool_function.__name__ = name
                    return tool_function
                
                # Create the tool function
                function = create_tool_function(tool_name)
                
                # Use different approaches to create FunctionTool based on ADK version
                try:
                    # Try the new schema parameter approach (ADK 0.4.0+)
                    tool = FunctionTool(
                        function=function,
                        function_schema=tool_info
                    )
                except TypeError:
                    # Fall back to the older approach
                    try:
                        # Try with schema param
                        tool = FunctionTool(function, schema=tool_info)
                    except TypeError:
                        # Very old ADK version, use without schema
                        tool = FunctionTool(function)
                
                # Add the tool to our list
                self.tools.append(tool)
                logger.info(f"Added MCP tool: {tool_name}")
            except Exception as e:
                logger.error(f"Error creating tool from MCP server: {e}")
    
    def _create_dummy_tools_for_server(self) -> None:
        """
        Create dummy tools based on the server URL and available information.
        This is a fallback when we can't properly fetch the tools from the server.
        """
        from google.adk.tools import FunctionTool
        
        # Parse the server type from the URL with improved detection
        server_type = "unknown"
        
        # Check for Crawl4AI in any part of the URL
        if "crawl4ai" in self.url.lower():
            server_type = "crawl4ai"
        # Check for specific MCP path patterns that indicate Crawl4AI
        elif "/mcp/sse" in self.url.lower() and any(x in self.url.lower() for x in ["firecrawl", "crawl", "search"]):
            server_type = "crawl4ai"
        # Check for Home Assistant
        elif any(x in self.url.lower() for x in ["homeassistant", "home-assistant", "home_assistant"]):
            server_type = "home_assistant"
            
        logger.info(f"Detected server type: {server_type} from URL: {self.url}")
        
        # Create tools based on server type
        if server_type == "crawl4ai":
            logger.info(f"Creating Crawl4AI MCP tools for {self.url}")
            
            # Create functions for common Crawl4AI operations
            def crawl4ai_scrape(url: str, **kwargs):
                return self._call_tool("crawl4ai_scrape", {"url": url, **kwargs})
                
            def crawl4ai_search(query: str, **kwargs):
                return self._call_tool("crawl4ai_search", {"query": query, **kwargs})
                
            def crawl4ai_extract(url: str, prompt: str, **kwargs):
                return self._call_tool("crawl4ai_extract", {"url": url, "prompt": prompt, **kwargs})
                
            def crawl4ai_crawl(url: str, **kwargs):
                return self._call_tool("crawl4ai_crawl", {"url": url, **kwargs})
            
            # Create function tools with schemas
            crawl4ai_scrape_schema = {
                "name": "crawl4ai_scrape",
                "description": "Scrape a web page using Crawl4AI",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to scrape"
                        }
                    },
                    "required": ["url"]
                }
            }
            
            crawl4ai_search_schema = {
                "name": "crawl4ai_search",
                "description": "Search the web using Crawl4AI",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
            
            crawl4ai_extract_schema = {
                "name": "crawl4ai_extract",
                "description": "Extract information from a web page using Crawl4AI",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string", 
                            "description": "URL to extract information from"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Prompt to guide extraction"
                        }
                    },
                    "required": ["url", "prompt"]
                }
            }
            
            crawl4ai_crawl_schema = {
                "name": "crawl4ai_crawl",
                "description": "Crawl a website using Crawl4AI",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Starting URL to crawl"
                        }
                    },
                    "required": ["url"]
                }
            }
            
            # Create tools
            try:
                # Try first with new FunctionTool API
                scrape_tool = FunctionTool(crawl4ai_scrape, schema=crawl4ai_scrape_schema)
                search_tool = FunctionTool(crawl4ai_search, schema=crawl4ai_search_schema)
                extract_tool = FunctionTool(crawl4ai_extract, schema=crawl4ai_extract_schema)
                crawl_tool = FunctionTool(crawl4ai_crawl, schema=crawl4ai_crawl_schema)
                
                # Add tools to list
                self.tools = [scrape_tool, search_tool, extract_tool, crawl_tool]
                logger.info(f"Created {len(self.tools)} Crawl4AI MCP tools")
            except TypeError:
                # Fallback for older ADK versions
                logger.info("Falling back to FunctionTool without schema parameter")
                try:
                    scrape_tool = FunctionTool(crawl4ai_scrape)
                    search_tool = FunctionTool(crawl4ai_search)
                    extract_tool = FunctionTool(crawl4ai_extract)
                    crawl_tool = FunctionTool(crawl4ai_crawl)
                    
                    # Add tools to list
                    self.tools = [scrape_tool, search_tool, extract_tool, crawl_tool]
                    logger.info(f"Created {len(self.tools)} Crawl4AI MCP tools with auto-schema")
                except Exception as e:
                    logger.error(f"Failed to create Crawl4AI tools with auto-schema: {e}")
        
        # Add more server types as needed
        
        # If no specific tools were created, add a generic dummy tool
        if not self.tools:
            logger.warning(f"No specific tools created for server type: {server_type}")
            
            def generic_mcp_tool(query: str):
                return {
                    "message": f"This is a dummy tool for MCP server {self.url}. The server type '{server_type}' is not specifically supported.",
                    "query": query
                }
                
            try:
                dummy_tool = FunctionTool(generic_mcp_tool)
                self.tools = [dummy_tool]
                logger.info("Created generic dummy MCP tool")
            except Exception as e:
                logger.error(f"Failed to create dummy tool: {e}")
    
    def _call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: The name of the tool to call
            args: The arguments to pass to the tool
            
        Returns:
            The result of the tool call
        """
        try:
            # Prepare the invoke request following the MCP specification
            request_data = {
                "jsonrpc": "2.0",
                "method": "invoke",
                "params": {
                    "name": tool_name,
                    "arguments": args
                },
                "id": self._generate_request_id()
            }
            
            logger.info(f"Calling MCP tool {tool_name} with arguments: {args}")
            
            # For MCP servers using SSE, we need to send messages to the messages endpoint
            from radbot.config.config_loader import config_loader
            
            # Try to get server_id from the URL to find the configuration
            server_id = None
            for server in config_loader.get_enabled_mcp_servers():
                if server.get("url") == self.url:
                    server_id = server.get("id")
                    break
                    
            # If we found the server configuration, check for message_endpoint
            message_endpoint = None
            if server_id:
                server_config = config_loader.get_mcp_server(server_id)
                if server_config:
                    message_endpoint = server_config.get("message_endpoint")
            
            # Priority order for endpoints:
            # 1. Instance message_endpoint property
            # 2. Configured message_endpoint
            # 3. Parse from SSE URL (replace /sse with /messages)
            # 4. Standard invoke endpoints
            
            invoke_endpoints = []
            
            # First, use the instance property if it exists
            if self.message_endpoint:
                invoke_endpoints.append(self.message_endpoint)
            
            # Then try the configured message_endpoint from the config
            elif message_endpoint:
                invoke_endpoints.append(message_endpoint)
                
            # Try to parse from the SSE URL if it looks like an SSE endpoint
            if "/sse" in self.url:
                # Try standard message endpoint patterns, with special handling for Crawl4AI
                messages_urls = [
                    self.url.replace("/sse", "/messages/"),  # Crawl4AI format with trailing slash
                    self.url.replace("/sse", "/messages"),   # Standard format without trailing slash
                    f"{self.url.replace('/sse', '')}/messages/",  # Alternative with base URL
                    f"{self.url.replace('/sse', '')}/messages"    # Alternative with base URL
                ]
                
                # For Crawl4AI, we need a session ID
                if "crawl4ai" in self.url.lower() and not self.session_id:
                    # Generate a random session ID for Crawl4AI
                    import uuid
                    self.session_id = str(uuid.uuid4())
                    logger.info(f"Generated session ID for Crawl4AI: {self.session_id}")
                
                # If we have a session_id, put the endpoints with session_id first
                # This ensures we try the session_id versions first
                if self.session_id:
                    for msg_url in messages_urls:
                        session_messages_url = f"{msg_url}?session_id={self.session_id}"
                        if session_messages_url not in invoke_endpoints:
                            invoke_endpoints.append(session_messages_url)
                
                # Then add the non-session versions as fallback
                for msg_url in messages_urls:
                    if msg_url not in invoke_endpoints:
                        invoke_endpoints.append(msg_url)
            
            # Add standard MCP endpoints
            standard_endpoints = [
                f"{self.url}/invoke",
                f"{self.url}/v1/invoke",
                f"{self.url}/api/invoke",
                self.url  # Direct base URL
            ]
            
            # Add any standard endpoints not already in our list
            for endpoint in standard_endpoints:
                if endpoint not in invoke_endpoints:
                    invoke_endpoints.append(endpoint)
            
            # Log the endpoints we'll try
            logger.info(f"Will try these endpoints: {invoke_endpoints}")
            
            for invoke_url in invoke_endpoints:
                try:
                    # Set up headers for this specific call
                    call_headers = {**self.headers}
                    # Ensure JSON content type
                    call_headers["Content-Type"] = "application/json"
                    
                    # Make the POST request with retry mechanism
                    max_retries = 2
                    retry_count = 0
                    
                    while retry_count <= max_retries:
                        try:
                            logger.info(f"Trying endpoint ({tool_name}): {invoke_url}")
                            # Add debug output for request
                            if tool_name == "crawl4ai_crawl" or tool_name == "crawl4ai_search":
                                logger.info(f"Request data: {json.dumps(request_data, indent=2)}")
                                
                            response = requests.post(
                                invoke_url,
                                headers=call_headers,
                                json=request_data,
                                timeout=self.timeout
                            )
                            
                            # Check if the response is successful
                            if response.status_code == 200:
                                try:
                                    result = response.json()
                                    
                                    # Handle standard JSON-RPC response format
                                    if "result" in result:
                                        logger.info(f"Tool {tool_name} call successful")
                                        # Extract actual result content from JSON-RPC wrapper
                                        return result.get("result")
                                    # Also handle non-standard but common formats
                                    elif "output" in result:
                                        return result.get("output")
                                    else:
                                        # Return the whole response if we can't find a specific result field
                                        return result
                                    
                                except json.JSONDecodeError:
                                    logger.warning(f"Invalid JSON response from tool {tool_name}")
                                    return {
                                        "result": response.text,
                                        "message": "Response was not valid JSON"
                                    }
                            
                            # Handle specific error cases
                            elif response.status_code == 404:
                                # Endpoint not found, try next one
                                logger.warning(f"Endpoint {invoke_url} not found (404)")
                                break
                            elif response.status_code >= 500:
                                # Server error, could be temporary
                                if retry_count < max_retries:
                                    retry_count += 1
                                    wait_time = 2 ** retry_count  # Exponential backoff
                                    logger.warning(f"Server error ({response.status_code}), retrying in {wait_time}s...")
                                    time.sleep(wait_time)
                                    continue
                            
                            # For any other error, log in detail and continue to next endpoint
                            logger.error(f"Error calling tool {tool_name} at {invoke_url}: {response.status_code}")
                            try:
                                # Try to parse error response as JSON
                                error_details = response.json()
                                logger.error(f"Error details: {json.dumps(error_details, indent=2)}")
                            except:
                                # Fall back to text response
                                logger.error(f"Error response: {response.text[:200]}...")
                            break
                            
                        except requests.Timeout:
                            if retry_count < max_retries:
                                retry_count += 1
                                wait_time = 2 ** retry_count
                                logger.warning(f"Request timeout, retrying in {wait_time}s...")
                                time.sleep(wait_time)
                            else:
                                logger.error(f"Tool call timed out after {max_retries} retries")
                                break
                        except requests.ConnectionError:
                            logger.error(f"Connection error to {invoke_url}")
                            break
                        except Exception as e:
                            logger.error(f"Unexpected error calling tool at {invoke_url}: {e}")
                            break
                
                except Exception as e:
                    logger.warning(f"Error setting up request to {invoke_url}: {e}")
            
            # If we get here, all endpoints failed
            logger.error(f"All invoke endpoints failed for tool {tool_name}")
            return {
                "error": f"Failed to call tool {tool_name}",
                "message": "All endpoints failed"
            }
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "error": f"Error calling tool {tool_name}",
                "message": str(e)
            }
            
    def _generate_request_id(self) -> str:
        """
        Generate a unique request ID for JSON-RPC calls.
        
        Returns:
            A unique ID string
        """
        import uuid
        return str(uuid.uuid4())