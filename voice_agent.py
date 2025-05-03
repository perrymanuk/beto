"""
Voice-enabled agent for ADK web interface.

This file is an alternative to the standard agent.py, specifically configured
for voice interaction using ElevenLabs for TTS.
"""

import asyncio
import base64
import json
import logging
import os
import sys
from typing import Optional, Any, List, Dict, Union

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import ADK components
from google.adk.agents import Agent
from radbot.config import config_manager

# Log configuration
logger.info(f"Voice agent: Config manager loaded. Model config: {config_manager.model_config}")
logger.info(f"Voice agent: Main model from config: '{config_manager.get_main_model()}'")
logger.info(f"Voice agent: Environment RADBOT_MAIN_MODEL: '{os.environ.get('RADBOT_MAIN_MODEL')}'")
logger.info(f"Voice agent: Using Vertex AI: {config_manager.is_using_vertex_ai()}")

# Import tools
from radbot.tools.basic_tools import get_current_time, get_weather
from radbot.tools.memory_tools import search_past_conversations, store_important_information
from radbot.tools.web_search_tools import create_tavily_search_tool
from radbot.tools.mcp_fileserver_client import create_fileserver_toolset
from radbot.tools.mcp_crawl4ai_client import create_crawl4ai_toolset, test_crawl4ai_connection

# Import Home Assistant REST API tools
from radbot.tools.ha_tools_impl import (
    list_ha_entities,
    get_ha_entity_state,
    turn_on_ha_entity,
    turn_off_ha_entity,
    toggle_ha_entity,
    search_ha_entities
)

# Ensure the Home Assistant client is properly initialized
from radbot.tools.ha_client_singleton import get_ha_client

# Import ElevenLabs TTS - we'll implement simplified callbacks that don't depend on ADK internals
from radbot.voice.elevenlabs_client import create_elevenlabs_client, ElevenLabsClient

# Log startup
logger.info("Voice agent.py loaded - specialized for voice interaction")

# Global TTS client
elevenlabs_client = create_elevenlabs_client()
if elevenlabs_client:
    logger.info("ElevenLabs TTS client initialized")
else:
    logger.warning("ElevenLabs TTS not available - check ELEVEN_LABS_API_KEY")

# Global state for tracking the last processed text
last_processed_text = ""
current_websocket = None

def create_agent(tools: Optional[List[Any]] = None):
    """
    Create the agent with all necessary tools.
    
    This is an alternative to the standard agent.py, specifically configured
    for voice interaction.
    
    Args:
        tools: Optional list of additional tools to include
        
    Returns:
        An ADK BaseAgent instance
    """
    logger.info("Creating voice-enabled agent")
    
    # Start with basic tools
    basic_tools = [get_current_time, get_weather]
    
    # Always include memory tools
    memory_tools = [search_past_conversations, store_important_information]
    logger.info(f"Including memory tools: {[t.__name__ for t in memory_tools]}")
    
    # Add Home Assistant REST API integration
    logger.info("Using Home Assistant REST API integration in agent creation")
    
    # Initialize Home Assistant client
    ha_client = get_ha_client()
    if ha_client:
        logger.info(f"Home Assistant client initialized: {ha_client.base_url}")
        
        # Test connection by listing entities
        try:
            entities = ha_client.list_entities()
            if entities:
                logger.info(f"Successfully connected to Home Assistant. Found {len(entities)} entities.")
            else:
                logger.warning("Connected to Home Assistant but no entities were returned")
        except Exception as e:
            logger.error(f"Error testing Home Assistant connection: {e}")
    else:
        logger.warning("Home Assistant client could not be initialized - check HA_URL and HA_TOKEN")
    
    # Add Home Assistant REST API tools
    ha_tools = [
        search_ha_entities,
        list_ha_entities,
        get_ha_entity_state,
        turn_on_ha_entity,
        turn_off_ha_entity,
        toggle_ha_entity
    ]
    basic_tools.extend(ha_tools)
    logger.info(f"Added {len(ha_tools)} Home Assistant REST API tools")
    
    # Add MCP Fileserver tools
    try:
        # Print MCP fileserver configuration
        mcp_fs_root_dir = os.environ.get("MCP_FS_ROOT_DIR")
        if mcp_fs_root_dir:
            logger.info(f"MCP Fileserver: Using root directory {mcp_fs_root_dir}")
        else:
            logger.info("MCP Fileserver: Root directory not set (MCP_FS_ROOT_DIR not found in environment)")
            
        logger.info("Creating MCP fileserver toolset...")
        fs_tools = create_fileserver_toolset()
        if fs_tools:
            # Add tools to basic_tools
            basic_tools.extend(fs_tools)
            
            # Log tools individually for better debugging
            fs_tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in fs_tools]
            logger.info(f"Successfully added {len(fs_tools)} MCP fileserver tools: {', '.join(fs_tool_names)}")
        else:
            logger.warning("MCP fileserver tools not available (returned None)")
    except Exception as e:
        logger.warning(f"Failed to create MCP fileserver tools: {str(e)}")
        
    # Add Crawl4AI tools
    try:
        logger.info("Creating Crawl4AI toolset...")
        crawl4ai_tools = create_crawl4ai_toolset()
        
        if crawl4ai_tools:
            # Add tools to basic_tools
            basic_tools.extend(crawl4ai_tools)
            
            # Log tools individually for better debugging
            crawl4ai_tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in crawl4ai_tools]
            logger.info(f"Successfully added {len(crawl4ai_tools)} Crawl4AI tools: {', '.join(crawl4ai_tool_names)}")
        else:
            logger.warning("Crawl4AI tools not available (returned None)")
    except Exception as e:
        logger.warning(f"Failed to create Crawl4AI tools: {str(e)}")
    
    # Add Tavily web search tool
    try:
        web_search_tool = create_tavily_search_tool(
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
        if web_search_tool:
            basic_tools.insert(0, web_search_tool)  # Add as highest priority
            logger.info("Successfully added web_search tool to base tools")
    except Exception as e:
        logger.warning(f"Failed to create Tavily search tool: {str(e)}")
    
    # Add any additional tools if provided
    all_tools = list(basic_tools) + memory_tools
    if tools:
        all_tools.extend(tools)
    
    # Get the instruction
    try:
        instruction = config_manager.get_instruction("voice_agent")
        if not instruction:
            # Fall back to main_agent instruction if voice_agent isn't defined
            instruction = config_manager.get_instruction("main_agent")
            
        # Add voice-specific instructions
        voice_instruction = """
        You are a voice-enabled assistant using ElevenLabs for text-to-speech.
        
        Important guidelines for voice output:
        1. Keep responses concise and conversational. People are listening, not reading.
        2. Avoid markdown formatting, code blocks, tables, or any other formatted text.
        3. Use simple, clear language. Mention when something would be better shown visually.
        4. Break complex information into shorter sentences and chunks.
        5. Be mindful of pacing - don't list many options all at once.
        
        Respond naturally as if you're having a spoken conversation.
        """
        instruction = instruction + "\n\n" + voice_instruction
        
        # Add MCP fileserver instructions if available
        if any("file" in str(tool).lower() for tool in all_tools):
            fs_instruction = """
            You can access files on the system through the file tools. Here are some examples:
            - To list files: Use the list_files tool with the path parameter
            - To read a file: Use the read_file tool with the path parameter
            - To get file info: Use the get_file_info tool with the path parameter
            
            Always tell the user what action you're taking, and report back the results. If a filesystem operation fails, inform the user politely about the issue.
            """
            instruction += "\n\n" + fs_instruction
            logger.info("Added MCP fileserver instructions to agent instruction")
            
        # Add Home Assistant REST API instructions
        if any("home_assistant" in str(tool).lower() for tool in all_tools):
            ha_instruction = """
            You have access to Home