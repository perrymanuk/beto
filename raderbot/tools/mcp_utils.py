"""
Utility functions for working with the Model Context Protocol (MCP).

This module provides helper functions for testing and debugging MCP connections.
"""

import os
import logging
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv

from raderbot.tools.mcp_tools import create_home_assistant_toolset

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def test_home_assistant_connection() -> Dict[str, Any]:
    """
    Test the connection to the Home Assistant MCP server.
    
    This function attempts to connect to the Home Assistant MCP server and
    retrieve basic information about available entities.
    
    Returns:
        Dictionary with the test results and information
    """
    # Initialize the Home Assistant MCP
    ha_toolset = create_home_assistant_toolset()
    
    if not ha_toolset:
        return {
            "success": False,
            "status": "initialization_failed",
            "error": "Failed to create Home Assistant MCP toolset",
            "details": None
        }
    
    # Try to list available tools
    try:
        # Get available MCP tools from the toolset
        tools = ha_toolset.get_tools_info()
        
        # Extract relevant information for display
        tool_names = [tool.name for tool in tools] if tools else []
        
        return {
            "success": True,
            "status": "connected",
            "tools_count": len(tool_names),
            "tools": tool_names
        }
    except Exception as e:
        logger.error(f"Error connecting to Home Assistant MCP: {str(e)}")
        return {
            "success": False,
            "status": "connection_error",
            "error": str(e),
            "details": None
        }


def check_home_assistant_entity(entity_id: str) -> Dict[str, Any]:
    """
    Check if a specific Home Assistant entity exists and get its state.
    
    Args:
        entity_id: The entity ID to check (e.g., "light.living_room")
        
    Returns:
        Dictionary with entity information or error details
    """
    ha_toolset = create_home_assistant_toolset()
    
    if not ha_toolset:
        return {
            "success": False,
            "status": "initialization_failed",
            "error": "Failed to create Home Assistant MCP toolset",
            "details": None
        }
    
    try:
        # Use MCP's get_state tool to check the entity
        # Note: This is an example - actual implementation depends on Home Assistant MCP API
        response = ha_toolset.invoke_tool(
            "home_assistant_mcp.get_state", 
            {"entity_id": entity_id}
        )
        
        return {
            "success": True,
            "status": "found",
            "entity_id": entity_id,
            "state": response.get("state"),
            "attributes": response.get("attributes", {})
        }
    except Exception as e:
        logger.error(f"Error checking Home Assistant entity {entity_id}: {str(e)}")
        return {
            "success": False,
            "status": "entity_error",
            "error": str(e),
            "entity_id": entity_id
        }