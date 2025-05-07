"""
Google Search tool integration for ADK.

This module provides factory functions to create and register agents
that use the ADK built-in google_search tool.
"""

import logging
from typing import Optional, Any

from google.adk.agents import Agent, LlmAgent
from google.adk.tools import google_search
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent

from radbot.config import config_manager
from radbot.config.settings import ConfigManager

# Set up logging
logger = logging.getLogger(__name__)

def create_search_agent(
    name: str = "search_agent",
    model: Optional[str] = None,
    config: Optional[ConfigManager] = None,
    instruction_name: str = "search_agent",
    include_transfer_tool: bool = True,
) -> Agent:
    """
    Create an agent with Google Search capabilities.
    
    Args:
        name: Name for the agent (should be "search_agent" for consistent transfers)
        model: Optional model override (defaults to config's main_model)
        config: Optional config manager (uses global if not provided)
        instruction_name: Name of instruction to load from config
        include_transfer_tool: Whether to include transfer_to_agent tool (default: True)
                              Set to False for standalone usage with Vertex AI
        
    Returns:
        Agent with Google Search tool
    """
    # Ensure agent name is always "search_agent" for consistent transfers
    if name != "search_agent":
        logger.warning(f"Agent name '{name}' changed to 'search_agent' for consistent transfers")
        name = "search_agent"
        
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
            "When you don't need to search, answer from your knowledge. "
            "When your task is complete, transfer back to the main agent using "
            "transfer_to_agent(agent_name='beto') or transfer to another agent "
            "if needed using transfer_to_agent(agent_name='agent_name')."
        )
    
    # Import transfer_to_agent
    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
    
    # Due to Vertex AI limitations, we can only use one tool at a time
    # Prioritize the google_search tool for this agent
    tools = [google_search]
    
    # Create the agent with just the search tool
    # Add instructions for how to transfer back
    transfer_instructions = "\n\nWhen you're done, say 'TRANSFER_BACK_TO_BETO' to return to the main agent."
    
    search_agent = Agent(
        name=name,
        model=model_name,
        instruction=instruction + transfer_instructions,
        description="A specialized agent that can search the web using Google Search.",
        tools=tools
    )
    
    # Enable search explicitly if using Vertex AI
    if cfg.is_using_vertex_ai():
        try:
            from google.genai import types
            
            # Handle different import paths for ToolGoogleSearch
            try:
                # Try to import from types directly (newer versions)
                ToolGoogleSearch = types.ToolGoogleSearch
            except AttributeError:
                try:
                    # Try to import from separate types classes (older versions)
                    from google.genai.types.tool_types import ToolGoogleSearch
                except ImportError:
                    # Define a minimal wrapper if not available
                    class ToolGoogleSearch:
                        def __init__(self):
                            pass
            
            # Check if the agent has a config attribute already
            if not hasattr(search_agent, "config"):
                # For LlmAgent type in ADK 0.4.0+
                if hasattr(search_agent, "set_config"):
                    # Use set_config method if available
                    config = types.GenerateContentConfig()
                    config.tools = [types.Tool(google_search=ToolGoogleSearch())]
                    search_agent.set_config(config)
                    logger.info("Set Google Search config via set_config method for Vertex AI")
                else:
                    # Try to add config attribute directly
                    search_agent.config = types.GenerateContentConfig()
                    search_agent.config.tools = [types.Tool(google_search=ToolGoogleSearch())]
                    logger.info("Added config attribute directly for Google Search with Vertex AI")
            else:
                # Update existing config
                if not hasattr(search_agent.config, "tools"):
                    search_agent.config.tools = []
                search_agent.config.tools.append(types.Tool(google_search=ToolGoogleSearch()))
                logger.info("Updated existing config with Google Search tool for Vertex AI")
        except Exception as e:
            logger.warning(f"Failed to configure Google Search for Vertex AI: {str(e)}")
    
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
    current_sub_agents = list(parent_agent.sub_agents) if hasattr(parent_agent, 'sub_agents') and parent_agent.sub_agents else []
    
    # Check if we already have a search agent
    search_agent_exists = False
    for existing_agent in current_sub_agents:
        if hasattr(existing_agent, 'name') and existing_agent.name == agent_to_register.name:
            logger.warning(f"Search agent '{agent_to_register.name}' already registered")
            search_agent_exists = True
            agent_to_register = existing_agent  # Use the existing agent for further updates
            break
    
    # Add the search agent to the sub-agents list if not already there
    if not search_agent_exists:
        current_sub_agents.append(agent_to_register)
        parent_agent.sub_agents = current_sub_agents
        logger.info(f"Registered search agent '{agent_to_register.name}' with parent agent '{parent_agent.name if hasattr(parent_agent, 'name') else 'unnamed'}'")
    
    # For ADK 0.4.0+, bidirectional navigation requires the parent to be in the
    # search agent's sub_agents list as well (for transfers back)
    try:
        # Set up bidirectional navigation
        search_sub_agents = list(agent_to_register.sub_agents) if hasattr(agent_to_register, 'sub_agents') and agent_to_register.sub_agents else []
        
        # Check if parent is already in search agent's sub_agents
        parent_exists = False
        for existing_agent in search_sub_agents:
            if hasattr(existing_agent, 'name') and existing_agent.name == parent_agent.name:
                parent_exists = True
                break
        
        # Add parent to search agent's sub_agents if not already there
        if not parent_exists:
            from google.adk.agents import Agent
            # Create a proxy for the parent (minimal version with just enough for transfers)
            parent_proxy = Agent(
                name=parent_agent.name if hasattr(parent_agent, 'name') else "beto",
                model=parent_agent.model if hasattr(parent_agent, 'model') else None,
                instruction="Main coordinating agent",
                description="Main agent for coordinating tasks",
                tools=[transfer_to_agent]  # Critical to have transfer_to_agent
            )
            
            search_sub_agents.append(parent_proxy)
            agent_to_register.sub_agents = search_sub_agents
            logger.info(f"Added parent agent '{parent_proxy.name}' to search agent sub_agents for bidirectional navigation")
    except Exception as e:
        logger.warning(f"Failed to add parent to search agent's sub_agents: {str(e)}")
    
    # For Vertex AI compatibility, we don't add transfer_to_agent tool
    # as Vertex AI only supports one tool at a time.
    # Instead, we rely on the instruction to tell the agent to say "TRANSFER_BACK_TO_BETO"
    
    # Check if agent is already using more than one tool
    if hasattr(agent_to_register, 'tools') and len(agent_to_register.tools) > 1:
        # If we're using Vertex AI, restrict to only google_search
        if config_manager.is_using_vertex_ai():
            # Keep only the google_search tool
            agent_to_register.tools = [google_search]
            logger.warning(
                f"Restricted search agent '{agent_to_register.name}' to only "
                "google_search tool for Vertex AI compatibility"
            )
    
    # Ensure the agent has the transfer_back instruction
    if hasattr(agent_to_register, 'instruction') and "TRANSFER_BACK_TO_BETO" not in agent_to_register.instruction:
        transfer_instructions = "\n\nWhen you're done, say 'TRANSFER_BACK_TO_BETO' to return to the main agent."
        agent_to_register.instruction += transfer_instructions
        logger.info(f"Added transfer_back instructions to agent '{agent_to_register.name}'")
