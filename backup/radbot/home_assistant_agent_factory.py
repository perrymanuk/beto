"""
Home Assistant agent factory for creating agents with Home Assistant capabilities.

This module provides factory functions for creating agents with Home Assistant
integration using either WebSocket or MCP approach.
"""

import logging
from typing import Any, Dict, List, Optional

from google.adk import Agent
from google.generativeai import types as genai_types
from google.generativeai.types import Tool as GenAITool

from radbot.config.settings import ConfigManager
from radbot.tools.ha_tool_schemas import get_home_assistant_tool_schemas
from radbot.tools.ha_tools_impl import (
    setup_home_assistant_tools,
    cleanup_home_assistant_tools,
    tool_function_map as ha_tool_function_map,
)

# MCP imports for native Home Assistant integration
from radbot.tools.mcp_tools import create_ha_mcp_enabled_agent

logger = logging.getLogger(__name__)

async def setup_websocket_home_assistant(
    config_manager: Optional[ConfigManager] = None
) -> bool:
    """
    Set up the Home Assistant WebSocket connection and tools.
    
    Args:
        config_manager: Optional configuration manager instance
        
    Returns:
        True if setup was successful, False otherwise
    """
    if not config_manager:
        config_manager = ConfigManager()
    
    if not config_manager.is_home_assistant_enabled():
        logger.warning("Home Assistant is not enabled in configuration")
        return False
    
    if not config_manager.is_home_assistant_using_websocket():
        logger.warning("Home Assistant is configured to use MCP, not WebSocket")
        return False
    
    websocket_url = config_manager.get_home_assistant_websocket_url()
    websocket_token = config_manager.get_home_assistant_websocket_token()
    
    if not websocket_url or not websocket_token:
        logger.error("Missing WebSocket URL or token for Home Assistant")
        return False
    
    try:
        await setup_home_assistant_tools(websocket_url, websocket_token)
        logger.info("Successfully set up Home Assistant WebSocket tools")
        return True
    except Exception as e:
        logger.error(f"Failed to set up Home Assistant WebSocket tools: {str(e)}", exc_info=True)
        return False

async def cleanup_websocket_home_assistant() -> None:
    """Clean up the Home Assistant WebSocket connection and tools."""
    try:
        await cleanup_home_assistant_tools()
        logger.info("Home Assistant WebSocket tools cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up Home Assistant WebSocket tools: {str(e)}", exc_info=True)

def create_home_assistant_agent_factory(
    base_agent_factory,
    config_manager: Optional[ConfigManager] = None,
    base_tools: Optional[List[Any]] = None,
):
    """
    Create a factory function that adds Home Assistant capabilities to agents.
    
    Args:
        base_agent_factory: Base agent factory function to extend
        config_manager: Optional configuration manager instance
        base_tools: Optional list of base tools to include
        
    Returns:
        A factory function that creates agents with Home Assistant capabilities
    """
    if not config_manager:
        config_manager = ConfigManager()
        
    def factory_function(*args, **kwargs) -> Agent:
        """
        Factory function to create an agent with Home Assistant capabilities.
        
        Args:
            *args: Positional arguments to pass to the base agent factory
            **kwargs: Keyword arguments to pass to the base agent factory
            
        Returns:
            An agent with Home Assistant capabilities
        """
        # Determine which approach to use (WebSocket or MCP)
        use_websocket = config_manager.is_home_assistant_using_websocket()
        ha_enabled = config_manager.is_home_assistant_enabled()
        
        if not ha_enabled:
            logger.info("Home Assistant integration not enabled, using base agent")
            return base_agent_factory(*args, **kwargs)
        
        if use_websocket:
            # WebSocket approach - create agent with Google GenAI function calling
            logger.info("Creating agent with Home Assistant WebSocket integration")
            
            # Get existing tools or create empty list
            tools = list(kwargs.get("tools", []))
            if base_tools:
                tools.extend(base_tools)
                
            # Add the Home Assistant tool definition
            genai_tools = kwargs.get("genai_tools", [])
            if not genai_tools:
                genai_tools = []
                
            # Add the Home Assistant tool schema
            ha_tool = get_home_assistant_tool_schemas()
            genai_tools.append(ha_tool)
            
            # Update kwargs with the modified tools
            kwargs["genai_tools"] = genai_tools
            kwargs["tools"] = tools
            
            # Add the tool function map to context for the agent executor to use
            kwargs["tool_function_map"] = {
                **kwargs.get("tool_function_map", {}),
                **ha_tool_function_map
            }
            
            return base_agent_factory(*args, **kwargs)
        else:
            # MCP approach (preferred native integration)
            logger.info("Creating agent with Home Assistant native MCP integration")
            
            # Include any existing tools
            tools = list(kwargs.pop("tools", []))
            if base_tools:
                tools.extend(base_tools)
                
            return create_ha_mcp_enabled_agent(
                base_agent_factory,
                base_tools=tools,
                ensure_memory_tools=True
            )
    
    return factory_function