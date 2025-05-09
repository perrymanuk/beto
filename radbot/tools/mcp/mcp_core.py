"""
MCP core functions for connecting to various servers.

This module provides core utilities for connecting to external services 
via the Model Context Protocol (MCP).
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from contextlib import AsyncExitStack

from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams

from radbot.config.config_loader import config_loader
from radbot.tools.mcp.mcp_client_factory import MCPClientFactory, MCPClientError

logger = logging.getLogger(__name__)

# Flag to track if we have Tavily search capabilities
HAVE_TAVILY = False

# Check for either environment variable method or MCP server method
tavily_mcp_configured = False
try:
    # First check if TAVILY_API_KEY is in the environment
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if tavily_api_key:
        logger.info("TAVILY_API_KEY found in environment, web search will be available")
        HAVE_TAVILY = True
        tavily_mcp_configured = True
    else:
        # Check for MCP Tavily server configuration
        mcp_config = config_loader.get_config().get("integrations", {}).get("mcp", {})
        if mcp_config:
            servers = mcp_config.get("servers", [])
            for server in servers:
                if server.get("enabled", False) and ("tavily" in server.get("id", "") or "tavily" in server.get("description", "")):
                    tavily_mcp_configured = True
                    HAVE_TAVILY = True
                    logger.info(f"Tavily MCP server configured: {server.get('id')}")
                    break
    
    if not tavily_mcp_configured:
        logger.warning("No Tavily MCP server configured. Add it to your config.yaml to enable web search.")
        logger.warning("See config/mcp_proxy.yaml.example for examples and https://docs.tavily.com/documentation/mcp for setup instructions")
except Exception as e:
    logger.warning(f"Error checking for Tavily MCP configuration: {e}")

def get_available_mcp_tools() -> List[Any]:
    """
    Get a list of all available MCP tools.
    
    This function returns a consolidated list of all available MCP tools
    including Home Assistant, FileServer, Crawl4AI, and other MCP integrations.
    
    Returns:
        List of available MCP tools
    """
    tools = []
    
    # Get all tools from configured MCP servers
    try:
        # Get MCP server tools using ConfigLoader and MCPClientFactory
        mcp_tools = create_mcp_tools()
        if mcp_tools:
            tools.extend(mcp_tools)
            logger.info(f"Added {len(mcp_tools)} tools from MCP servers configured in config.yaml")
    except Exception as e:
        logger.warning(f"Failed to get tools from MCP servers in config.yaml: {str(e)}")
    
    # If no tools were added from config, try the legacy approach
    if not tools:
        logger.info("No MCP tools found from config.yaml, falling back to legacy approach")
        
        # Try to get Home Assistant tools
        try:
            from radbot.tools.mcp.mcp_homeassistant import create_home_assistant_toolset
            ha_tools = create_home_assistant_toolset()
            if ha_tools:
                if isinstance(ha_tools, list):
                    tools.extend(ha_tools)
                    logger.info(f"Added {len(ha_tools)} Home Assistant MCP tools")
                else:
                    tools.append(ha_tools)
                    logger.info("Added Home Assistant MCP toolset")
        except Exception as e:
            logger.warning(f"Failed to get Home Assistant MCP tools: {str(e)}")
        
        # Try to get FileServer tools if available
        try:
            # Import here to avoid circular imports
            from radbot.tools.mcp.mcp_fileserver_client import create_fileserver_toolset
            fs_tools = create_fileserver_toolset()
            if fs_tools:
                if isinstance(fs_tools, list):
                    tools.extend(fs_tools)
                    logger.info(f"Added {len(fs_tools)} FileServer MCP tools")
                else:
                    tools.append(fs_tools)
                    logger.info("Added FileServer MCP toolset")
        except Exception as e:
            logger.warning(f"Failed to get FileServer MCP tools: {str(e)}")
    
    return tools

def create_mcp_tools() -> List[Any]:
    """
    Create tools for all enabled MCP servers defined in the configuration.
    
    Returns:
        List of MCP tools created from the configuration
    """
    tools = []
    
    # Get all enabled MCP servers from configuration
    servers = config_loader.get_enabled_mcp_servers()
    
    if not servers:
        logger.info("No enabled MCP servers found in configuration")
        return tools
    
    logger.info(f"Found {len(servers)} enabled MCP servers in configuration")
    
    # Create tools for each enabled server
    for server in servers:
        server_id = server.get("id")
        server_name = server.get("name", server_id)
        
        try:
            # Get or create the MCP client for this server
            client = MCPClientFactory.get_client(server_id)
            
            # Create tools from the client
            server_tools = _create_tools_from_client(client, server)
            
            if server_tools:
                logger.info(f"Created {len(server_tools)} tools for MCP server '{server_name}'")
                tools.extend(server_tools)
            else:
                logger.warning(f"No tools created for MCP server '{server_name}'")
                
        except MCPClientError as e:
            logger.warning(f"Failed to create client for MCP server '{server_name}': {e}")
        except Exception as e:
            logger.error(f"Error creating tools for MCP server '{server_name}': {e}")
    
    return tools

def _create_tools_from_client(client: Any, server_config: Dict[str, Any]) -> List[Any]:
    """
    Create tools from an MCP client.
    
    Args:
        client: The MCP client instance
        server_config: The server configuration dictionary
        
    Returns:
        List of tools created from the client
    """
    tools = []
    server_id = server_config.get("id")
    
    try:
        # Different MCP clients might have different APIs for getting tools
        # Try common patterns
        
        # 1. Check if client has get_tools method
        if hasattr(client, "get_tools") and callable(client.get_tools):
            server_tools = client.get_tools()
            if server_tools:
                tools.extend(server_tools)
                return tools
        
        # 2. Check if client has a tools attribute that's a list
        if hasattr(client, "tools") and isinstance(client.tools, list):
            tools.extend(client.tools)
            return tools
            
        # 3. Check if client has a create_tools method
        if hasattr(client, "create_tools") and callable(client.create_tools):
            server_tools = client.create_tools()
            if server_tools:
                tools.extend(server_tools)
                return tools
        
        # 4. Check if client is a descriptor class with tools attribute
        if hasattr(client, "descriptor") and hasattr(client.descriptor, "tools"):
            tools.extend(client.descriptor.tools)
            return tools
        
        # If we get here, we couldn't find tools through standard methods
        logger.warning(f"Could not determine how to get tools from MCP server '{server_id}'")
        return tools
        
    except Exception as e:
        logger.error(f"Error creating tools from MCP client for '{server_id}': {e}")
        return tools