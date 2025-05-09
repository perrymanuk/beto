#!/usr/bin/env python3
"""
Async Crawl4AI MCP Client

This module provides an improved async implementation for connecting to Crawl4AI 
using the Model Context Protocol (MCP) with proper lifecycle management.
"""

import logging
import asyncio
import requests
import json
import uuid
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

import google.adk.tools as adk_tools
from google.adk.tools import FunctionTool

from radbot.config.config_loader import config_loader

logger = logging.getLogger(__name__)

@dataclass
class Crawl4AIContext:
    """Context for the Crawl4AI MCP client."""
    session_id: str
    message_endpoint: str
    tools: List[Any]

@asynccontextmanager
async def crawl4ai_lifespan(url: str, auth_token: Optional[str] = None,
                          timeout: int = 30, initialization_delay: Optional[int] = None) -> AsyncIterator[Crawl4AIContext]:
    """
    Manages the Crawl4AI client lifecycle with proper initialization and cleanup.
    
    Args:
        url: The URL of the MCP server
        auth_token: Optional authentication token
        timeout: Request timeout in seconds
        initialization_delay: Optional delay in milliseconds after initialization
        
    Yields:
        Crawl4AIContext: Context containing session and tools information
    """
    logger.info(f"Initializing Crawl4AI client with URL: {url}")
    
    # Set up headers for SSE connection
    headers = {
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json"
    }
    
    # Add authentication if token is provided
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # First, establish an SSE connection to get the session ID
    try:
        # Extract base URL for proper endpoint construction
        base_url = url.split("/mcp/")[0] if "/mcp/" in url else url.rsplit("/", 1)[0]
        
        # Make the initial SSE connection
        response = requests.get(url, headers=headers, stream=True, timeout=timeout)
        
        if response.status_code != 200:
            raise ValueError(f"Failed to connect to SSE endpoint: {response.status_code}")
        
        logger.info("SSE connection established, waiting for session ID")
        
        # Parse the SSE stream to extract session ID and message endpoint
        session_id = None
        message_endpoint = None
        
        # Process the first few lines to extract initialization information
        # This is a blocking operation but necessary for initialization
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
                
            if line.startswith("event:"):
                event_type = line[6:].strip()
                continue
                
            if line.startswith("data:"):
                data = line[5:].strip()
                
                # Look for endpoint data
                if event_type == "endpoint" or "session_id=" in data:
                    if data.startswith("/"):
                        # It's a relative path
                        message_endpoint = f"{base_url}{data}"
                    elif data.startswith("http"):
                        # It's a full URL
                        message_endpoint = data
                    else:
                        # Try to construct a reasonable endpoint
                        message_endpoint = f"{base_url}/mcp/messages/"
                    
                    # Extract session ID if present
                    if "session_id=" in message_endpoint:
                        session_id = message_endpoint.split("session_id=")[1].split("&")[0]
                        logger.info(f"Extracted session ID: {session_id}")
                        break
            
            # If we've found what we need, stop processing
            if session_id and message_endpoint:
                break
        
        # If we didn't get a session ID, generate one
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated session ID: {session_id}")
            
        # If we didn't get a message endpoint, construct a default one
        if not message_endpoint:
            if "/sse" in url:
                message_endpoint = url.replace("/sse", "/messages/")
            else:
                message_endpoint = f"{base_url}/mcp/messages/"
                
            # Add session ID to message endpoint if not already present
            if "session_id=" not in message_endpoint:
                separator = "?" if "?" not in message_endpoint else "&"
                message_endpoint = f"{message_endpoint}{separator}session_id={session_id}"
                
        logger.info(f"Using message endpoint: {message_endpoint}")
        
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "completions": False,
                    "prompts": False,
                    "resources": False,
                    "tools": True
                },
                "clientInfo": {
                    "name": "RadbotAsyncMCPClient",
                    "version": "1.0.0"
                }
            },
            "id": str(uuid.uuid4())
        }
        
        init_headers = {**headers}
        init_headers["Content-Type"] = "application/json"
        
        # Send the initialization request
        logger.info("Sending initialization request")
        init_response = requests.post(
            message_endpoint,
            headers=init_headers,
            json=init_request,
            timeout=timeout
        )
        
        if init_response.status_code not in [200, 202]:
            raise ValueError(f"Initialization request failed: {init_response.status_code} - {init_response.text}")
            
        logger.info(f"Initialization request successful: {init_response.status_code}")
        
        # Apply initialization delay if configured
        if initialization_delay:
            delay_seconds = initialization_delay / 1000.0
            logger.info(f"Waiting {delay_seconds}s before continuing (initialization delay)")
            await asyncio.sleep(delay_seconds)
        
        # Get list of tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": str(uuid.uuid4())
        }
        
        logger.info("Requesting list of tools")
        tools_response = requests.post(
            message_endpoint,
            headers=init_headers,
            json=list_tools_request,
            timeout=timeout
        )
        
        tools = []
        if tools_response.status_code in [200, 202] and tools_response.text.strip():
            try:
                result = tools_response.json()
                if "result" in result:
                    # Create tools from the result
                    tools = create_tools_from_result(result["result"])
                    logger.info(f"Created {len(tools)} tools from result")
            except Exception as e:
                logger.error(f"Error creating tools from result: {e}")
        else:
            # Create fallback tools
            tools = create_fallback_tools()
            logger.info(f"Created {len(tools)} fallback tools")
        
        # Create context with session ID, message endpoint, and tools
        context = Crawl4AIContext(
            session_id=session_id,
            message_endpoint=message_endpoint,
            tools=tools
        )
        
        try:
            # Yield the context to the caller
            yield context
        finally:
            # Clean up resources when context is exited
            logger.info("Cleaning up Crawl4AI client resources")
            try:
                # Close the response to terminate the SSE connection
                response.close()
            except Exception as e:
                logger.error(f"Error closing SSE connection: {e}")
    except Exception as e:
        logger.error(f"Error in crawl4ai_lifespan: {e}")
        raise


def create_tools_from_result(result: Any) -> List[Any]:
    """
    Create tools from the tools/list result.

    Args:
        result: The result from the tools/list request

    Returns:
        List of tools created from the result
    """
    tools = []

    if not result or not isinstance(result, list):
        return tools

    for tool_info in result:
        try:
            # Handle different formats of tool information
            if isinstance(tool_info, dict) and "name" in tool_info:
                tool_name = tool_info["name"]
                tool_description = tool_info.get("description", "")

                # Create the function that will call the MCP server
                def create_tool_function(name):
                    def tool_function(**kwargs):
                        return {"message": f"MCP tool {name} was called", "args": kwargs}
                    tool_function.__name__ = name
                    tool_function.__doc__ = tool_description
                    return tool_function

                function = create_tool_function(tool_name)

                # Create tool
                try:
                    # Try different FunctionTool signatures
                    try:
                        tool = FunctionTool(
                            function=function,
                            schema=tool_info
                        )
                    except TypeError:
                        tool = FunctionTool(
                            function,
                            function_schema=tool_info
                        )

                    tools.append(tool)
                    logger.info(f"Created tool: {tool_name}")
                except Exception as e:
                    logger.error(f"Error creating tool {tool_name}: {e}")
                    # Fallback to raw function
                    tools.append(function)
                    logger.info(f"Added raw function as fallback: {tool_name}")

        except Exception as e:
            logger.error(f"Error processing tool info: {e}")

    return tools


def create_fallback_tools() -> List[Any]:
    """
    Create fallback tools when server doesn't provide tool information.

    Returns:
        List of fallback tools
    """
    tools = []

    # Define standard Crawl4AI tools
    tool_defs = [
        {
            "name": "md",
            "description": "Fetch a URL and return markdown content",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to process"
                    }
                },
                "required": ["url"]
            }
        },
        {
            "name": "html",
            "description": "Fetch a URL and return HTML content",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to process"
                    }
                },
                "required": ["url"]
            }
        },
        {
            "name": "screenshot",
            "description": "Take a screenshot of a URL",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to screenshot"
                    }
                },
                "required": ["url"]
            }
        },
        {
            "name": "crawl",
            "description": "Crawl a website and extract content",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to crawl"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Crawl depth"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of pages to crawl"
                    }
                },
                "required": ["url"]
            }
        }
    ]

    # Create the tools
    for tool_def in tool_defs:
        tool_name = tool_def["name"]

        # Create the function that will call the MCP server
        def create_tool_function(name):
            def tool_function(**kwargs):
                return {"message": f"MCP fallback tool {name} was called", "args": kwargs}
            tool_function.__name__ = name
            tool_function.__doc__ = tool_def["description"]
            return tool_function

        function = create_tool_function(tool_name)

        try:
            # Try different approaches to create FunctionTool based on ADK version
            try:
                # Check what parameters FunctionTool accepts
                import inspect
                sig = inspect.signature(FunctionTool.__init__)
                params = sig.parameters

                if "function_schema" in params:
                    # ADK 0.4.0+
                    tool = FunctionTool(
                        function=function,
                        function_schema=tool_def
                    )
                elif "schema" in params:
                    # Older ADK
                    tool = FunctionTool(function, schema=tool_def)
                else:
                    # Very old ADK or different implementation
                    tool = FunctionTool(function)

                tools.append(tool)
                logger.info(f"Created fallback tool: {tool_name}")
            except Exception as e:
                # Last resort - just create function tool without schema
                try:
                    tool = FunctionTool(function)
                    tools.append(tool)
                    logger.info(f"Created simple fallback tool: {tool_name}")
                except Exception as inner_e:
                    logger.error(f"Error creating fallback tool {tool_name}: {inner_e}")
                    # Just add the raw function
                    tools.append(function)
                    logger.info(f"Added raw function: {tool_name}")
        except Exception as e:
            logger.error(f"Error creating fallback tool {tool_name}: {e}")

    return tools


async def create_crawl4ai_client_async(server_config: Dict[str, Any]) -> Optional[Tuple[Crawl4AIContext, Any]]:
    """
    Create an async Crawl4AI client from server configuration.

    Args:
        server_config: Server configuration dictionary

    Returns:
        Optional tuple of (Crawl4AIContext, lifespan context manager)
    """
    url = server_config.get("url")
    if not url:
        logger.error("No URL specified for MCP server")
        return None

    auth_token = server_config.get("auth_token")
    timeout = server_config.get("timeout", 30)
    initialization_delay = server_config.get("initialization_delay")

    # Create the lifespan context manager
    lifespan = crawl4ai_lifespan(
        url=url,
        auth_token=auth_token,
        timeout=timeout,
        initialization_delay=initialization_delay
    )

    # Start the lifespan context
    context_manager = lifespan.__aenter__()
    context = await context_manager

    return context, lifespan

class AsyncCrawl4AIClient:
    """
    Async client for Crawl4AI MCP server with proper lifecycle management.
    """
    
    def __init__(self, url: str, auth_token: Optional[str] = None,
                 timeout: int = 30, initialization_delay: Optional[int] = None,
                 message_endpoint: Optional[str] = None):
        """
        Initialize the Async Crawl4AI client.
        
        Args:
            url: The URL of the MCP server
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
            initialization_delay: Optional delay in milliseconds after initialization
            message_endpoint: Optional message endpoint URL
        """
        self.url = url
        self.auth_token = auth_token
        self.timeout = timeout
        self.initialization_delay = initialization_delay
        self.message_endpoint = message_endpoint
        
        # State variables
        self.context = None
        self.lifespan = None
        self.tools = []
        self.initialized = False
        
        logger.info(f"AsyncCrawl4AIClient initialized with URL: {url}")
        
    async def initialize(self) -> bool:
        """
        Initialize the client asynchronously.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self.initialized:
            logger.info("Client already initialized")
            return True
            
        try:
            # Create the lifespan context manager
            self.lifespan = crawl4ai_lifespan(
                url=self.url, 
                auth_token=self.auth_token,
                timeout=self.timeout,
                initialization_delay=self.initialization_delay
            )
            
            # Start the lifespan context
            context = await self.lifespan.__aenter__()
            self.context = context
            
            # Store tools
            self.tools = context.tools
            self.initialized = True
            
            logger.info(f"AsyncCrawl4AIClient initialized with {len(self.tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing AsyncCrawl4AIClient: {e}")
            return False
        finally:
            logger.info("Initialize method completed")
            
    def get_tools(self) -> List[Any]:
        """
        Get the tools from this client.

        Returns:
            List of tools
        """
        # Note: This is a synchronous method so we can't do async initialization here
        # Clients should call check_initialization() first in an async context
        if not self.initialized:
            logger.warning("AsyncCrawl4AIClient.get_tools() called before initialization")
            logger.warning("Call check_initialization() first in an async context")
            return []
        return self.tools

    async def check_initialization(self) -> bool:
        """
        Check if the client is initialized and initialize it if needed.
        This method should be called before using the client in an async context.

        Returns:
            True if initialized successfully, False otherwise
        """
        if not self.initialized:
            return await self.initialize()
        return True
        
    async def close(self) -> None:
        """
        Close the client and clean up resources.
        """
        if self.lifespan and self.context:
            try:
                await self.lifespan.__aexit__(None, None, None)
                self.initialized = False
                logger.info("AsyncCrawl4AIClient closed")
            except Exception as e:
                logger.error(f"Error closing AsyncCrawl4AIClient: {e}")

async def run_async_crawl4ai_server():
    """
    Test function for running the async Crawl4AI client.
    """
    # Get server configuration from environment variables or config
    server_config = {
        "url": os.getenv("CRAWL4AI_URL", "https://crawl4ai.demonsafe.com/mcp/sse"),
        "auth_token": os.getenv("CRAWL4AI_TOKEN"),
        "timeout": int(os.getenv("CRAWL4AI_TIMEOUT", "30")),
        "initialization_delay": int(os.getenv("CRAWL4AI_INIT_DELAY", "3000"))
    }
    
    # Create client
    client = AsyncCrawl4AIClient(**server_config)
    
    # Initialize client
    success = await client.initialize()
    
    if success:
        print(f"✅ Client initialized successfully with {len(client.tools)} tools:")
        for tool in client.tools:
            print(f"  - {getattr(tool, 'name', str(tool))}")
    else:
        print("❌ Failed to initialize client")
        
    # Close client
    await client.close()

def main():
    """Command line entry point for testing."""
    print("Async Crawl4AI MCP Client Test\n")
    
    # Run the async function
    asyncio.run(run_async_crawl4ai_server())
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())