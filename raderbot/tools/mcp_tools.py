"""
MCP integration tools for connecting to Home Assistant.

This module provides utilities for connecting to Home Assistant via the Model Context Protocol (MCP).
"""

import os
import logging
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
from google.adk.tools.mcp_tool import MCPToolset, SseServerParams

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def create_home_assistant_toolset() -> Optional[MCPToolset]:
    """
    Create an MCPToolset for connecting to Home Assistant's MCP Server.
    
    Uses environment variables for configuration (HA_MCP_SSE_URL, HA_AUTH_TOKEN).
    
    Returns:
        MCPToolset: The configured Home Assistant MCP toolset, or None if configuration fails
    """
    try:
        # Get connection parameters from environment variables
        ha_mcp_url = os.getenv("HA_MCP_SSE_URL")
        ha_auth_token = os.getenv("HA_AUTH_TOKEN")
        
        if not ha_mcp_url or not ha_auth_token:
            logger.error("Home Assistant MCP configuration missing. "
                         "Please set HA_MCP_SSE_URL and HA_AUTH_TOKEN environment variables.")
            return None
        
        # Configure the SSE parameters for Home Assistant MCP server
        ha_mcp_params = SseServerParams(
            url=ha_mcp_url,
            headers={
                "Authorization": f"Bearer {ha_auth_token}"
            }
        )
        
        # Create the MCPToolset
        ha_toolset = MCPToolset(
            server_params={"home_assistant_mcp": ha_mcp_params}
        )
        
        logger.info("Successfully created Home Assistant MCP toolset")
        return ha_toolset
        
    except Exception as e:
        logger.error(f"Failed to create Home Assistant MCP toolset: {str(e)}")
        return None