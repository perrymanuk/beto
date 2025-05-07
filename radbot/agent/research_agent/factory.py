"""
Research agent factory.

This module provides factory functions for creating research agents.
"""

import logging
import os
from typing import Optional, List, Dict, Any, Union

# Set up logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Import ADK components
from google.adk.tools import FunctionTool

# Import project components
from radbot.agent.research_agent.agent import ResearchAgent
from radbot.config import config_manager

def create_research_agent(
    name: str = "technical_research_agent",
    model: Optional[str] = None,
    custom_instruction: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    as_subagent: bool = True,
    enable_google_search: bool = False,
    enable_code_execution: bool = False,
    app_name: str = "beto"
) -> Union[ResearchAgent, Any]:
    """
    Create a research agent with the specified configuration.
    
    Args:
        name: Name of the agent
        model: LLM model to use (defaults to config setting)
        custom_instruction: Optional custom instruction to override the default
        tools: List of tools to provide to the agent
        as_subagent: Whether to return the ResearchAgent or the underlying ADK agent
        enable_google_search: Whether to enable Google Search capability
        enable_code_execution: Whether to enable Code Execution capability
        app_name: Application name for the agent, should match the parent agent name for ADK 0.4.0+ agent transfers
        
    Returns:
        Union[ResearchAgent, Any]: The created agent instance
    """
    logger.info(f"Creating research agent with name: {name}")
    
    # Use default model from config if not specified
    if model is None:
        model = config_manager.get_main_model()
        logger.info(f"Using model from config: {model}")
    
    # Log tools if provided
    if tools:
        tool_names = []
        for tool in tools:
            if hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            elif hasattr(tool, 'name'):
                tool_names.append(tool.name)
            else:
                tool_names.append(str(type(tool)))
        
        logger.info(f"Creating research agent with tools: {', '.join(tool_names)}")
    else:
        logger.warning("No tools provided to research agent")
    
    # Log if built-in tools are enabled
    if enable_google_search:
        logger.info("Google Search ADK built-in tool is enabled for research agent")

    if enable_code_execution:
        logger.info("Code Execution ADK built-in tool is enabled for research agent")
    
    # Create the research agent with explicit name logging
    logger.info(f"EXPLICIT NAME ASSIGNMENT: Creating research agent with name='{name}', app_name='{app_name}'")
    research_agent = ResearchAgent(
        name=name,
        model=model,
        instruction=custom_instruction,  # Will use default if None
        tools=tools,
        enable_google_search=enable_google_search,
        enable_code_execution=enable_code_execution,
        app_name=app_name  # CRITICAL for ADK 0.4.0+ transfers
    )
    
    logger.info(f"Successfully created research agent: {name}")
    
    # Return either the ResearchAgent wrapper or the underlying ADK agent
    if as_subagent:
        return research_agent
    else:
        # Get the ADK agent but ensure name is preserved correctly for agent tree registry
        adk_agent = research_agent.get_adk_agent()
        
        # CRITICAL: Make 100% sure the agent name is set correctly for agent transfers in ADK 0.4.0
        if hasattr(adk_agent, 'name') and adk_agent.name != name:
            logger.warning(f"ADK Agent name mismatch: '{adk_agent.name}' not '{name}' - fixing")
            adk_agent.name = name
            logger.info(f"Fixed ADK agent name to '{adk_agent.name}'")
        
        # Log this critical value for debugging
        logger.info(f"Returning ADK agent with name='{getattr(adk_agent, 'name', 'unknown')}'")
        
        return adk_agent