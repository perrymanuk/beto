#!/usr/bin/env python3
"""
MCP Crawl4AI Client

This module provides utilities for connecting to Crawl4AI from
within the radbot framework using the Model Context Protocol (MCP).
"""

import sys
import logging
import asyncio
import requests
from typing import Dict, Any, List, Optional, Tuple
from contextlib import AsyncExitStack

from dotenv import load_dotenv
import google.adk.tools as adk_tools
from google.adk.tools import FunctionTool
try:
    # Also try to import newer types
    import google.adk.types as adk_types
except ImportError:
    adk_types = None

# Import our own modules
from .utils import get_crawl4ai_config, run_async_safely
from .crawl4ai_query import crawl4ai_query, _call_crawl4ai_query_api
from .crawl4ai_ingest_url import crawl4ai_ingest_url, _call_crawl4ai_ingest_api
from .crawl4ai_ingest_and_read import crawl4ai_ingest_and_read

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def create_crawl4ai_toolset_async() -> Tuple[List[Any], Optional[AsyncExitStack]]:
    """
    Async function to create tools for Crawl4AI's API.
    
    Returns:
        Tuple[List[Any], AsyncExitStack]: The list of tools and exit stack
    """
    try:
        # Get connection parameters from environment variables
        api_url, api_token = get_crawl4ai_config()
            
        logger.info(f"Using Crawl4AI API URL: {api_url}")
        
        # Create an AsyncExitStack for resource management (empty for now)
        exit_stack = AsyncExitStack()

        # Skip trying to use decorators - go directly to manually created tools
        # Create simplest possible functions first
        
        # Create super simple functions following the pattern used in web_search_tools.py
        try:
            # Make sure the function names are correctly set
            crawl4ai_ingest_and_read.__name__ = "crawl4ai_ingest_and_read"
            crawl4ai_ingest_url.__name__ = "crawl4ai_ingest_url"
            crawl4ai_query.__name__ = "crawl4ai_query"
            
            # Create function tools (this works in ADK 0.3.0)
            try:
                # First try with explicit schemas for more reliable function calling
                from google.generativeai import types as genai_types
                
                # Define explicit schemas for our functions
                read_url_schema = {
                    "name": "crawl4ai_ingest_and_read",
                    "description": "Fetch a URL using Crawl4AI, show AND store content for future searching. Use this to both read and index web content.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL of the webpage to crawl (e.g. 'https://example.com')"
                            }
                        },
                        "required": ["url"]
                    }
                }
                
                ingest_url_schema = {
                    "name": "crawl4ai_ingest_url",
                    "description": "Ingest URLs with Crawl4AI for later searching (Step 1 of 2). Content will be stored but NOT returned in the response to save context space.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL or comma-separated list of URLs to crawl (e.g. 'https://example.com' or 'https://example.com,https://example.org')"
                            }
                        },
                        "required": ["url"]
                    }
                }
                
                query_schema = {
                    "name": "crawl4ai_query",
                    "description": "Search the Crawl4AI knowledge base (Step 2 of 2). Use this AFTER ingesting content with crawl4ai_ingest_url to search the stored web content.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to look for in the Crawl4AI knowledge base"
                            }
                        },
                        "required": ["query"]
                    }
                }
                
                # Try to create tools with explicit schemas
                try:
                    read_url_tool = FunctionTool(function=crawl4ai_ingest_and_read, function_schema=read_url_schema)
                    ingest_url_tool = FunctionTool(function=crawl4ai_ingest_url, function_schema=ingest_url_schema)
                    query_tool = FunctionTool(function=crawl4ai_query, function_schema=query_schema)
                    logger.info("Created all tools using FunctionTool with explicit schemas")
                except Exception as e:
                    logger.warning(f"FunctionTool with schema failed: {str(e)}, trying automatic")
                    # Fall back to automatic schema generation
                    read_url_tool = FunctionTool(crawl4ai_ingest_and_read)
                    ingest_url_tool = FunctionTool(crawl4ai_ingest_url)
                    query_tool = FunctionTool(crawl4ai_query)
                    logger.info("Created all tools using FunctionTool with automatic schemas")
            except Exception as e:
                logger.warning(f"FunctionTool creation failed: {str(e)}, using raw functions")
                # Fall back to raw functions if FunctionTool fails
                read_url_tool = crawl4ai_ingest_and_read
                ingest_url_tool = crawl4ai_ingest_url
                query_tool = crawl4ai_query
            
            logger.info("Created crawl4ai ingest and query tools")
            
        except Exception as e:
            logger.error(f"Failed to create tools with explicit declarations: {str(e)}")
            
            # Ultimate fallback - create super simple functions
            def crawl4ai_read_minimal(url):
                """Read a URL with Crawl4AI for immediate use."""
                print(f"Minimal crawl4ai_ingest_and_read function called with URL: {url}")
                return {"message": f"Reading {url} as markdown", "content": f"Unable to fetch content from {url}"}
            
            def crawl4ai_ingest_minimal(url):
                """Ingest a webpage URL into Crawl4AI knowledge base."""
                print(f"Minimal crawl4ai_ingest_url function called with URL: {url}")
                return {"message": f"Ingesting {url} (simulated)"}
            
            def crawl4ai_search_minimal(query):
                """Search the Crawl4AI knowledge base."""
                print(f"Minimal crawl4ai_query function called with query: {query}")
                return {"message": f"Searching for: {query}", "results": []}
            
            read_url_tool = crawl4ai_read_minimal
            ingest_url_tool = crawl4ai_ingest_minimal
            query_tool = crawl4ai_search_minimal
            logger.info("Created minimal fallback functions")

        # Return the tools and exit stack
        tools = [read_url_tool, ingest_url_tool, query_tool]
        logger.info(f"Successfully created {len(tools)} Crawl4AI tools")
        return tools, exit_stack
        
    except Exception as e:
        logger.error(f"Failed to create Crawl4AI toolset: {str(e)}")
        return [], None

def create_crawl4ai_toolset() -> List[Any]:
    """
    Create Crawl4AI tools using ADK 0.3.0 API.
    
    Uses environment variables for configuration (CRAWL4AI_API_URL, CRAWL4AI_API_TOKEN).
    
    Returns:
        List[MCPTool]: List of Crawl4AI tools, or empty list if configuration fails
    """
    exit_stack = None
    try:
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tools, exit_stack = loop.run_until_complete(create_crawl4ai_toolset_async())
        
        # We don't need to close the exit_stack here as it's minimal
        # and doesn't have resources that need cleanup
        
        # Close only the event loop
        loop.close()
        
        return tools
    except Exception as e:
        logger.error(f"Error creating Crawl4AI tools: {str(e)}")
        if exit_stack:
            try:
                # We need to close the exit stack if an error occurred
                # Create a new event loop for this
                cleanup_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(cleanup_loop)
                cleanup_loop.run_until_complete(exit_stack.aclose())
                cleanup_loop.close()
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {str(cleanup_error)}")
        return []

def test_crawl4ai_connection() -> Dict[str, Any]:
    """
    Test the connection to the Crawl4AI API.
    
    Returns:
        Dictionary with test results
    """
    # Get configuration
    api_url, api_token = get_crawl4ai_config()
        
    # Test the connection with a simple request
    try:
        # Build URL for a simple status check - using the root path which returns the status
        test_url = f"{api_url}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add authentication if token is provided
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        
        # Make the request
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        return {
            "success": True,
            "status": "connected",
            "api_url": api_url,
            "api_version": result.get("version", "unknown"),
            "details": result
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "status": "connection_error",
            "error": str(e),
            "api_url": api_url
        }
        
def create_crawl4ai_enabled_agent(agent_factory, base_tools=None, **kwargs):
    """
    Create an agent with Crawl4AI tools enabled.
    
    Args:
        agent_factory: Function to create an agent (like create_agent)
        base_tools: Optional list of base tools to include
        **kwargs: Additional arguments to pass to agent_factory
        
    Returns:
        Agent: The created agent with Crawl4AI tools
    """
    try:
        # Start with base tools or empty list
        tools = list(base_tools or [])
        
        # Create Crawl4AI tools
        crawl4ai_tools = create_crawl4ai_toolset()
        
        if crawl4ai_tools and len(crawl4ai_tools) > 0:
            # Add the tools to our list
            tools.extend(crawl4ai_tools)
            logger.info(f"Added {len(crawl4ai_tools)} Crawl4AI tools to agent")
        else:
            logger.warning("No Crawl4AI tools were created")
            
        # Create the agent with the tools
        agent = agent_factory(tools=tools, **kwargs)
        return agent
    except Exception as e:
        logger.error(f"Error creating agent with Crawl4AI tools: {str(e)}")
        # Create agent without Crawl4AI tools as fallback
        return agent_factory(tools=base_tools, **kwargs)

def main():
    """Command line entry point for testing."""
    print("Crawl4AI MCP Client Test\n")
    
    # Test the connection
    result = test_crawl4ai_connection()
    
    if result["success"]:
        print(f"✅ Connection successful!")
        print(f"API URL: {result.get('api_url')}")
        print(f"API Version: {result.get('api_version', 'unknown')}")
        
        # Get the tools
        tools = create_crawl4ai_toolset()
        if tools and len(tools) > 0:
            print(f"✅ Created {len(tools)} tools:")
            for tool in tools:
                print(f"  - {getattr(tool, 'name', str(tool))}")
        else:
            print("❌ Failed to create tools")
    else:
        print(f"❌ Connection failed!")
        print(f"Status: {result.get('status')}")
        print(f"Error: {result.get('error')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
