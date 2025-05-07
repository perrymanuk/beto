"""
Code Execution tool integration for ADK.

This module provides factory functions to create and register agents
that use the ADK built-in built_in_code_execution tool.
"""

import logging
from typing import Optional, Any

from google.adk.agents import Agent, LlmAgent
from google.adk.tools import built_in_code_execution

from radbot.config import config_manager
from radbot.config.settings import ConfigManager

# Set up logging
logger = logging.getLogger(__name__)

def create_code_execution_agent(
    name: str = "code_execution_agent",
    model: Optional[str] = None,
    config: Optional[ConfigManager] = None,
    instruction_name: str = "code_execution_agent",
) -> Agent:
    """
    Create an agent with Code Execution capabilities.
    
    Args:
        name: Name for the agent
        model: Optional model override (defaults to config's main_model)
        config: Optional config manager (uses global if not provided)
        instruction_name: Name of instruction to load from config
        
    Returns:
        Agent with Code Execution tool
    """
    # Use provided config or default
    cfg = config or config_manager
    
    # Get the model name (must be a Gemini 2 model)
    model_name = model or cfg.get_main_model()
    if not any(name in model_name.lower() for name in ["gemini-2", "gemini-2.0", "gemini-2.5"]):
        logger.warning(
            f"Model {model_name} may not be compatible with built_in_code_execution tool. "
            "Code Execution tool requires Gemini 2 models."
        )
    
    # Get the instruction
    try:
        instruction = cfg.get_instruction(instruction_name)
    except FileNotFoundError:
        # Use a minimal instruction if the named one isn't found
        logger.warning(
            f"Instruction '{instruction_name}' not found for code execution agent, "
            "using minimal instruction"
        )
        instruction = (
            "You are a code execution agent. You can help users by writing and executing "
            "Python code to perform calculations, data manipulation, or solve problems. "
            "When asked to write code, use the built_in_code_execution tool to run the code "
            "and return the results. Always explain the code you write and its output."
        )
    
    # Create the code execution agent
    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
    code_agent = Agent(
        name=name,
        model=model_name,
        instruction=instruction,
        description="A specialized agent that can execute Python code securely.",
        tools=[built_in_code_execution, transfer_to_agent]
    )
    
    # Enable code execution explicitly if using Vertex AI
    if cfg.is_using_vertex_ai():
        from google.genai import types
        code_agent.config = types.GenerateContentConfig()
        code_agent.config.tools = [types.Tool(code_execution=types.ToolCodeExecution())]
        logger.info("Explicitly configured code execution tool for Vertex AI")
    
    logger.info(f"Created code execution agent '{name}' with built_in_code_execution tool")
    return code_agent

def register_code_execution_agent(parent_agent: Agent, code_agent: Optional[Agent] = None) -> None:
    """
    Register a code execution agent as a sub-agent to the parent.
    
    Args:
        parent_agent: The parent agent to register the code execution agent with
        code_agent: Optional existing code execution agent (creates one if None)
    """
    # Create a code execution agent if one isn't provided
    agent_to_register = code_agent or create_code_execution_agent()
    
    # Get current sub-agents
    current_sub_agents = list(parent_agent.sub_agents) if parent_agent.sub_agents else []
    
    # Check if we already have a code execution agent
    for existing_agent in current_sub_agents:
        if existing_agent.name == agent_to_register.name:
            logger.warning(f"Code execution agent '{agent_to_register.name}' already registered")
            return
    
    # Add the code execution agent to the sub-agents list
    current_sub_agents.append(agent_to_register)
    parent_agent.sub_agents = current_sub_agents
    
    # Set parent relationship for agent transfers
    if hasattr(agent_to_register, 'parent'):
        agent_to_register.parent = parent_agent
    elif hasattr(agent_to_register, '_parent'):
        agent_to_register._parent = parent_agent
            
    logger.info(f"Registered code execution agent '{agent_to_register.name}' with parent agent '{parent_agent.name}'")
