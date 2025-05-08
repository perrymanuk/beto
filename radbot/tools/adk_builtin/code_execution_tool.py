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
        name: Name for the agent (should be "code_execution_agent" for consistent transfers)
        model: Optional model override (defaults to config's main_model)
        config: Optional config manager (uses global if not provided)
        instruction_name: Name of instruction to load from config
        
    Returns:
        Agent with Code Execution tool
    """
    # Ensure agent name is always "code_execution_agent" for consistent transfers
    if name != "code_execution_agent":
        logger.warning(f"Agent name '{name}' changed to 'code_execution_agent' for consistent transfers")
        name = "code_execution_agent"
        
    # Use provided config or default
    cfg = config or config_manager
    
    # Get the model name (must be a Gemini 2 model)
    # First try to get agent-specific model, then fall back to provided model or defaults
    model_name = model or cfg.get_agent_model("code_execution_agent")
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
            "and return the results. Always explain the code you write and its output. "
            "When your task is complete, say 'TRANSFER_BACK_TO_BETO' to return to the main agent."
        )
    
    # Vertex AI only supports one tool at a time, so just use the code execution tool
    tools = [built_in_code_execution]
    
    # Create the agent with just the code execution tool
    # Add instructions for how to transfer back
    transfer_instructions = "\n\nWhen you're done, say 'TRANSFER_BACK_TO_BETO' to return to the main agent."
    
    code_agent = Agent(
        name=name,
        model=model_name,
        instruction=instruction + transfer_instructions,
        description="A specialized agent that can execute Python code securely.",
        tools=tools
    )
    
    # Enable code execution explicitly if using Vertex AI
    if cfg.is_using_vertex_ai():
        try:
            from google.genai import types
            
            # Handle different import paths for ToolCodeExecution
            try:
                # Try to import from types directly (newer versions)
                ToolCodeExecution = types.ToolCodeExecution
            except AttributeError:
                try:
                    # Try to import from separate types classes (older versions)
                    from google.genai.types.tool_types import ToolCodeExecution
                except ImportError:
                    # Define a minimal wrapper if not available
                    class ToolCodeExecution:
                        def __init__(self):
                            pass
            
            # In ADK 0.4.0+, we should always use set_config method
            # The "config" attribute no longer exists directly on Agent class
            
            # Initialize a Code Execution tool config with Vertex AI
            code_execution_config = types.GenerateContentConfig()
            code_execution_config.tools = [types.Tool(code_execution=ToolCodeExecution())]
            
            # Use set_config if available (ADK 0.4.0+)
            if hasattr(code_agent, "set_config"):
                code_agent.set_config(code_execution_config)
                logger.info("Set code execution config via set_config method for Vertex AI")
            else:
                # Fall back to direct attribute setting as a last resort
                try:
                    code_agent.config = code_execution_config
                    logger.info("Added config attribute directly for code execution with Vertex AI")
                except Exception as e:
                    logger.warning(f"Unable to set code execution config: {str(e)}")
        except Exception as e:
            logger.warning(f"Failed to configure code execution for Vertex AI: {str(e)}")
    
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
    current_sub_agents = list(parent_agent.sub_agents) if hasattr(parent_agent, 'sub_agents') and parent_agent.sub_agents else []
    
    # Check if we already have a code execution agent
    code_agent_exists = False
    for existing_agent in current_sub_agents:
        if hasattr(existing_agent, 'name') and existing_agent.name == agent_to_register.name:
            logger.warning(f"Code execution agent '{agent_to_register.name}' already registered")
            code_agent_exists = True
            agent_to_register = existing_agent  # Use the existing agent for further updates
            break
    
    # Add the code execution agent to the sub-agents list if not already there
    if not code_agent_exists:
        current_sub_agents.append(agent_to_register)
        parent_agent.sub_agents = current_sub_agents
        logger.info(f"Registered code execution agent '{agent_to_register.name}' with parent agent '{parent_agent.name if hasattr(parent_agent, 'name') else 'unnamed'}'")
    
    # For ADK 0.4.0+, bidirectional navigation requires the parent to be in the
    # code execution agent's sub_agents list as well (for transfers back)
    try:
        # Set up bidirectional navigation
        code_sub_agents = list(agent_to_register.sub_agents) if hasattr(agent_to_register, 'sub_agents') and agent_to_register.sub_agents else []
        
        # Check if parent is already in code agent's sub_agents
        parent_exists = False
        for existing_agent in code_sub_agents:
            if hasattr(existing_agent, 'name') and existing_agent.name == parent_agent.name:
                parent_exists = True
                break
        
        # Add parent to code agent's sub_agents if not already there
        if not parent_exists:
            from google.adk.agents import Agent
            # Create a proxy for the parent (minimal version without tools for Vertex AI compatibility)
            parent_proxy = Agent(
                name=parent_agent.name if hasattr(parent_agent, 'name') else "beto",
                model=parent_agent.model if hasattr(parent_agent, 'model') else None,
                instruction="Main coordinating agent",
                description="Main agent for coordinating tasks",
                tools=[]  # No tools for Vertex AI compatibility
            )
            
            code_sub_agents.append(parent_proxy)
            agent_to_register.sub_agents = code_sub_agents
            logger.info(f"Added parent agent '{parent_proxy.name}' to code execution agent sub_agents for bidirectional navigation")
    except Exception as e:
        logger.warning(f"Failed to add parent to code agent's sub_agents: {str(e)}")
    
    # For Vertex AI compatibility, ensure we're only using one tool
    # as Vertex AI only supports one tool at a time
    if hasattr(agent_to_register, 'tools') and len(agent_to_register.tools) > 1:
        # Restrict to only built_in_code_execution tool
        agent_to_register.tools = [built_in_code_execution]
        logger.info(
            f"Restricted code execution agent '{agent_to_register.name}' to only "
            "built_in_code_execution tool for Vertex AI compatibility"
        )
    
    # Ensure the agent has the transfer_back instruction
    if hasattr(agent_to_register, 'instruction') and "TRANSFER_BACK_TO_BETO" not in agent_to_register.instruction:
        transfer_instructions = "\n\nWhen you're done, say 'TRANSFER_BACK_TO_BETO' to return to the main agent."
        agent_to_register.instruction += transfer_instructions
        logger.info(f"Added transfer_back instructions to agent '{agent_to_register.name}'")
