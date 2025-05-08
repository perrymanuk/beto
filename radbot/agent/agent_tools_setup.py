"""
Agent tools setup for RadBot.

This module handles the setup and initialization of tools used by the RadBot agent.
It creates the tools list and manages callback functions.
"""

import logging
import os
from typing import List, Any, Optional
from datetime import date

# Import from our initialization module
from radbot.agent.agent_initializer import (
    logger,
    Agent,
    CallbackContext,
    types,
    config_manager,
    
    # Import tool factories
    call_search_agent,
    call_code_execution_agent,
    call_scout_agent,
    create_search_agent,
    create_code_execution_agent,
    create_research_agent,
    
    # Import built-in tools
    load_artifacts,
    get_current_time,
    get_weather,
    search_past_conversations,
    store_important_information,
    create_tavily_search_tool,
    create_fileserver_toolset,
    create_crawl4ai_toolset,
    get_shell_tool,
    ALL_TOOLS,
    init_database,
    
    # Import calendar tools
    list_calendar_events_tool,
    create_calendar_event_tool,
    update_calendar_event_tool,
    delete_calendar_event_tool,
    check_calendar_availability_tool,
    
    # Import Home Assistant tools
    list_ha_entities,
    get_ha_entity_state,
    turn_on_ha_entity,
    turn_off_ha_entity,
    toggle_ha_entity,
    search_ha_entities,
    get_ha_client
)

def setup_before_agent_call(callback_context: CallbackContext):
    """Setup agent before each call."""
    # Initialize Todo database schema if needed
    if "todo_init" not in callback_context.state:
        try:
            init_database()
            callback_context.state["todo_init"] = True
            logger.info("Todo database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Todo database: {str(e)}")
            callback_context.state["todo_init"] = False
    
    # Initialize Home Assistant client if not already done
    if "ha_client_init" not in callback_context.state:
        try:
            ha_client = get_ha_client()
            if ha_client:
                try:
                    entities = ha_client.list_entities()
                    if entities:
                        logger.info(f"Successfully connected to Home Assistant. Found {len(entities)} entities.")
                        callback_context.state["ha_client_init"] = True
                    else:
                        logger.warning("Connected to Home Assistant but no entities were returned")
                        callback_context.state["ha_client_init"] = False
                except Exception as e:
                    logger.error(f"Error testing Home Assistant connection: {e}")
                    callback_context.state["ha_client_init"] = False
            else:
                logger.warning("Home Assistant client could not be initialized")
                callback_context.state["ha_client_init"] = False
        except Exception as e:
            logger.error(f"Error initializing Home Assistant client: {e}")
            callback_context.state["ha_client_init"] = False


# Create all the sub-agents we'll need
search_agent = create_search_agent(name="search_agent")
code_execution_agent = create_code_execution_agent(name="code_execution_agent")
scout_agent = create_research_agent(name="scout", as_subagent=False)

# Create all the tools we'll use
tools = []

# Add AgentTool functions first (high priority)
tools.extend([
    call_search_agent,
    call_code_execution_agent,
    call_scout_agent
])

# Add Tavily web search tool
try:
    web_search_tool = create_tavily_search_tool(
        max_results=3,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True
    )
    if web_search_tool:
        tools.append(web_search_tool)
        logger.info("Added web_search tool")
except Exception as e:
    logger.warning(f"Failed to create Tavily search tool: {e}")

# Add basic tools
tools.extend([
    get_current_time,
    get_weather
])

# Add calendar tools
tools.extend([
    list_calendar_events_tool,
    create_calendar_event_tool,
    update_calendar_event_tool,
    delete_calendar_event_tool,
    check_calendar_availability_tool
])

# Add Home Assistant tools
tools.extend([
    search_ha_entities,
    list_ha_entities,
    get_ha_entity_state,
    turn_on_ha_entity,
    turn_off_ha_entity,
    toggle_ha_entity
])

# Add filesystem tools using the direct implementation
# We're avoiding the MCP tools at import time due to async initialization issues
try:
    fs_tools = create_fileserver_toolset()
    if fs_tools:
        tools.extend(fs_tools)
        logger.info(f"Added {len(fs_tools)} filesystem tools")
except Exception as e:
    logger.warning(f"Failed to create filesystem tools: {e}")

# For Crawl4AI, we'll use the compatibility stub which will output deprecation warnings
try:
    # This function now returns [] but logs a deprecation warning
    crawl4ai_tools = create_crawl4ai_toolset()
    # No need to extend tools since the stub returns empty list
    logger.info("Crawl4AI direct integration is deprecated - use MCP server instead")
except Exception as e:
    logger.warning(f"Failed to create Crawl4AI tools: {e}")

# Add Shell Command Execution tool
try:
    # Default to strict mode
    shell_tool = get_shell_tool(strict_mode=True)
    tools.append(shell_tool)
    logger.info("Added shell command execution tool in STRICT mode")
except Exception as e:
    logger.warning(f"Failed to create shell command execution tool: {e}")

# Add Todo Tools
try:
    tools.extend(ALL_TOOLS)
    logger.info(f"Added {len(ALL_TOOLS)} Todo tools")
except Exception as e:
    logger.warning(f"Failed to add Todo tools: {e}")

# Add memory tools
tools.extend([
    search_past_conversations,
    store_important_information
])

# Add artifacts loading tool
tools.append(load_artifacts)