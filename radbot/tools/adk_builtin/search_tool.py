"""
Google Search tool integration for ADK.

This module provides factory functions to create and register agents
that use the ADK built-in google_search tool.
"""

import logging
from typing import Optional, Any

from google.adk.agents import Agent, LlmAgent
from google.adk.tools import google_search

from radbot.config import config_manager
from radbot.config.settings import ConfigManager

# Set up logging
logger = logging.getLogger(__name__)

def create_search_agent(
    name: str = "search_agent",
    model: Optional[str] = None,
    config: Optional[ConfigManager] = None,
    instruction_name: str = "search_agent",
) -> Agent:
    """
    Create an agent with Google Search capabilities.
    
    Args:
        name: Name for the agent
        model: Optional model override (defaults to config's main_model)
        config: Optional config manager (uses global if not provided)
        instruction_name: Name of instruction to load from config
        
    Returns:
        Agent with Google Search tool
    """
    # Use provided config or default
    cfg = config or config_manager
    
    # Get the model name (must be a Gemini 2 model)
    model_name = model or cfg.get_main_model()
    if not any(name in model_name.lower() for name in ["gemini-2", "gemini-2.0", "gemini-2.5"]):
        logger.warning(
            f"Model {model_name} may not be compatible with google_search tool. "
            "Google Search tool requires Gemini 2 models."
        )
    
    # Get the instruction
    try:
        instruction = cfg.get_instruction(instruction_name)
    except FileNotFoundError:
        # Use a minimal instruction if the named one isn't found
        logger.warning(
            f"Instruction '{instruction_name}' not found for search agent, "
            "using minimal instruction"
        )
        instruction = (
            "You are a web search agent. When asked about recent events, news, "
            "or facts that may have changed since your training, use the Google Search "
            "tool to find current information. Always cite your sources clearly. "
            "When you don't need to search, answer from your knowledge."
        )
    
    # Create the search agent
    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
    search_agent = Agent(
        name=name,
        model=model_name,
        instruction=instruction,
        description="A specialized agent that can search the web using Google Search.",
        tools=[google_search, transfer_to_agent]
    )
    
    # Enable search explicitly if using Vertex AI
    if cfg.is_using_vertex_ai():
        from google.genai import types
        search_agent.config = types.GenerateContentConfig()
        search_agent.config.tools = [types.Tool(google_search=types.ToolGoogleSearch())]
        logger.info("Explicitly configured Google Search tool for Vertex AI")
    
    logger.info(f"Created search agent '{name}' with google_search tool")
    return search_agent

def register_search_agent(parent_agent: Agent, search_agent: Optional[Agent] = None) -> None:
    """
    Register a search agent as a sub-agent to the parent.
    
    Args:
        parent_agent: The parent agent to register the search agent with
        search_agent: Optional existing search agent (creates one if None)
    """
    # Create a search agent if one isn't provided
    agent_to_register = search_agent or create_search_agent()
    
    # Get current sub-agents
    current_sub_agents = list(parent_agent.sub_agents) if parent_agent.sub_agents else []
    
    # Check if we already have a search agent
    for existing_agent in current_sub_agents:
        if existing_agent.name == agent_to_register.name:
            logger.warning(f"Search agent '{agent_to_register.name}' already registered")
            return
    
    # Add the search agent to the sub-agents list
    current_sub_agents.append(agent_to_register)
    parent_agent.sub_agents = current_sub_agents
    
    # Set parent relationship for agent transfers
    if hasattr(agent_to_register, 'parent'):
        agent_to_register.parent = parent_agent
    elif hasattr(agent_to_register, '_parent'):
        agent_to_register._parent = parent_agent
            
    logger.info(f"Registered search agent '{agent_to_register.name}' with parent agent '{parent_agent.name}'")
