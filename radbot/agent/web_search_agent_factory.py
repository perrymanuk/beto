"""
Factory functions for creating agents with web search capabilities.

This module provides specialized factory functions for creating agents
with Tavily search integration.
"""

import logging
from typing import Any, Dict, List, Optional

from google.adk.agents import Agent

from radbot.agent.agent import AgentFactory, RadBotAgent, create_agent
from radbot.config.settings import ConfigManager
from radbot.tools.web_search import (
    create_tavily_search_tool,
    create_tavily_search_enabled_agent
)

logger = logging.getLogger(__name__)


def create_websearch_agent(
    model: Optional[str] = None,
    base_tools: Optional[List[Any]] = None,
    instruction_name: str = "main_agent",
    config: Optional[ConfigManager] = None,
    max_results: int = 5,
    search_depth: str = "advanced",
) -> RadBotAgent:
    """
    Create a RadBot agent with web search capabilities.
    
    This factory function creates an agent with the Tavily search tool
    for web search capabilities.
    
    Args:
        model: Optional model to use
        base_tools: Optional list of base tools to include
        instruction_name: Name of instruction to load from config
        config: Optional ConfigManager instance
        max_results: Maximum number of search results (default: 5)
        search_depth: Search depth, either "basic" or "advanced" (default: "advanced")
        
    Returns:
        A RadBotAgent with web search capabilities
    """
    # Start with base tools or empty list
    tools = list(base_tools or [])
    
    # Create the Tavily search tool
    tavily_tool = create_tavily_search_tool(
        max_results=max_results,
        search_depth=search_depth,
        include_answer=True,
        include_raw_content=True,
        include_images=False  # Default to no images to save tokens
    )
    
    if tavily_tool:
        # Add the Tavily search tool at the start for higher priority
        tools.insert(0, tavily_tool)
        logger.info("Added Tavily search tool to agent tools")
    else:
        logger.warning("Could not create Tavily search tool for agent")
    
    # Create the agent with all the specified parameters and tools
    agent = create_agent(
        tools=tools,
        model=model,
        instruction_name=instruction_name,
        config=config
    )
    
    # Log tools information
    if agent and agent.root_agent and agent.root_agent.tools:
        tool_names = []
        for tool in agent.root_agent.tools:
            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', str(tool))
            tool_names.append(tool_name)
        
        web_tools = [t for t in tool_names if 'tavily' in t.lower() or 'search' in t.lower()]
        if web_tools:
            logger.info(f"Web search tools available: {', '.join(web_tools)}")
        else:
            logger.warning("No web search tools found in the agent!")
    
    return agent


def create_websearch_enabled_root_agent(
    model: Optional[str] = None,
    base_tools: Optional[List[Any]] = None,
    instruction_name: str = "main_agent",
    name: str = "web_search_agent",
    config: Optional[ConfigManager] = None,
    max_results: int = 5,
    search_depth: str = "advanced",
) -> Agent:
    """
    Create a root agent with web search capabilities.
    
    This factory function creates an ADK Agent with the Tavily search tool.
    
    Args:
        model: Optional model to use
        base_tools: Optional list of base tools to include
        instruction_name: Name of instruction to load from config
        name: Name of the agent (default: "web_search_agent")
        config: Optional ConfigManager instance
        max_results: Maximum number of search results (default: 5)
        search_depth: Search depth, either "basic" or "advanced" (default: "advanced")
        
    Returns:
        An Agent with web search capabilities
    """
    # Start with base tools or empty list
    tools = list(base_tools or [])
    
    # Create the Tavily search tool
    tavily_tool = create_tavily_search_tool(
        max_results=max_results,
        search_depth=search_depth,
        include_answer=True,
        include_raw_content=True,
        include_images=False  # Default to no images to save tokens
    )
    
    if tavily_tool:
        # Add the Tavily search tool at the start for higher priority
        tools.insert(0, tavily_tool)
        logger.info("Added Tavily search tool to agent tools")
    else:
        logger.warning("Could not create Tavily search tool for agent")
    
    # Create the root agent
    root_agent = AgentFactory.create_root_agent(
        name=name,
        model=model,
        tools=tools,
        instruction_name=instruction_name,
        config=config
    )
    
    return root_agent