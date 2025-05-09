"""
Factory for creating specialized agents in the RadBot system.

This module implements the specialized agent pattern as described in
the agent_specialization.md documentation.
"""

import logging
import os
from typing import Dict, List, Any, Optional

from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent

from radbot.config import config_manager
from radbot.agent.execution_agent import ExecutionAgent, create_execution_agent
from radbot.agent.execution_agent.tools import execution_tools

# Configure logging
logger = logging.getLogger(__name__)

def create_minimal_axel_toolset() -> List[Any]:
    """
    Create a minimal set of tools for Axel.
    
    This function creates a minimal set of tools for the Axel agent,
    focusing on essential implementation and execution tools.
    
    Returns:
        List of tools for the Axel agent
    """
    toolset = []
    
    # Add the shell command execution tool
    try:
        # Try the normal import first
        from radbot.tools.shell.shell_tool import execute_shell_command
        toolset.append(execute_shell_command)
        logger.info("Added execute_shell_command to minimal Axel toolset")
    except ImportError:
        # If that fails, try the old path
        try:
            from radbot.tools.shell.shell_command import execute_shell_command
            toolset.append(execute_shell_command)
            logger.info("Added execute_shell_command to minimal Axel toolset (legacy path)")
        except ImportError:
            logger.warning("Could not import execute_shell_command from any known path")
    
    # Add filesystem tools
    try:
        from radbot.filesystem.tools import (
            read_file_func, 
            list_directory_func, 
            search_func,
            write_file_func,
            edit_file_func
        )
        
        # Add filesystem read tools
        toolset.append(read_file_func)
        toolset.append(list_directory_func)
        toolset.append(search_func)
        
        # Add filesystem write tools if enabled
        toolset.append(write_file_func)
        toolset.append(edit_file_func)
        
        logger.info("Added filesystem tools to minimal Axel toolset")
    except ImportError:
        logger.warning("Could not import filesystem tools")
    
    return toolset

def create_axel_agent(root_agent: Agent) -> Optional[Agent]:
    """
    Create the Axel agent for implementation tasks.
    
    Args:
        root_agent: The root agent to attach Axel to
        
    Returns:
        The created Axel agent or None if creation failed
    """
    try:
        # Get the model from config
        axel_model = config_manager.get_agent_model("axel_agent_model")
        if not axel_model:
            # Fallback to the high-quality model
            axel_model = config_manager.get_agent_model("axel_agent")
            if not axel_model:
                axel_model = "gemini-1.5-pro"
                logger.info(f"Using fallback model for Axel: {axel_model}")
            else:
                logger.info(f"Using configured model for Axel: {axel_model}")
        else:
            logger.info(f"Using configured model for Axel: {axel_model}")
        
        # Create the Axel agent using our factory function
        adk_agent = create_execution_agent(
            name="axel",
            model=axel_model,
            tools=execution_tools,
            as_subagent=True,
            enable_code_execution=True,
            app_name=root_agent.name if hasattr(root_agent, 'name') else "beto"
        )
        
        # Get current sub-agents list from root agent
        current_sub_agents = list(root_agent.sub_agents) if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents else []
        
        # Add Axel to the sub-agents list
        current_sub_agents.append(adk_agent)
        
        # Update the list of sub-agents
        root_agent.sub_agents = current_sub_agents
        
        logger.info(f"Successfully created and registered Axel agent with {len(execution_tools)} tools")
        
        # Setup Scout-to-Axel transfer if Scout exists
        scout_agent = None
        for sub_agent in root_agent.sub_agents:
            if hasattr(sub_agent, 'name') and sub_agent.name == "scout":
                scout_agent = sub_agent
                break
        
        if scout_agent:
            # Create bidirectional links more safely
            # First, create weak references to avoid full circular references
            from weakref import proxy
            
            # Make Scout aware of Axel
            scout_sub_agents = list(scout_agent.sub_agents) if hasattr(scout_agent, 'sub_agents') and scout_agent.sub_agents else []
            
            # Check if Axel is already in Scout's sub_agents
            axel_already_added = False
            for agent in scout_sub_agents:
                if hasattr(agent, 'name') and agent.name == "axel":
                    axel_already_added = True
                    break
                    
            if not axel_already_added:
                # Add a weak reference to avoid strong circular refs
                scout_sub_agents.append(proxy(adk_agent))
                scout_agent.sub_agents = scout_sub_agents
                logger.info("Added Scout → Axel reference (using proxy)")
                
            # Store Axel's scout reference separately
            # Note: We don't create a full bidirectional link to avoid serialization issues
            if not hasattr(adk_agent, '_associated_agents'):
                adk_agent._associated_agents = {}
            
            adk_agent._associated_agents['scout'] = scout_agent.name
            logger.info("Added Axel → Scout reference (using named reference)")
            
            # Also create a helper function to find associated agents at runtime
            def find_agent_by_name(agent_tree, name, visited=None):
                if visited is None:
                    visited = set()
                
                agent_id = id(agent_tree)
                if agent_id in visited:
                    return None
                
                visited.add(agent_id)
                
                if hasattr(agent_tree, 'name') and agent_tree.name == name:
                    return agent_tree
                
                if hasattr(agent_tree, 'sub_agents') and agent_tree.sub_agents:
                    for sub_agent in agent_tree.sub_agents:
                        result = find_agent_by_name(sub_agent, name, visited)
                        if result:
                            return result
                
                return None
            
            # We can't add find_agent_by_name to the axel agent directly (LlmAgent is Pydantic model)
            # Instead, we'll store it as a module function for reuse if needed
            logger.info("Created find_agent_by_name helper function for Axel agent")
            
            # Also set up the bidirectional link in the ExecutionAgent wrapper
            if hasattr(adk_agent, '_execution_agent'):
                execution_agent_wrapper = adk_agent._execution_agent
                execution_agent_wrapper.add_specific_transfer_target(scout_agent)
                logger.info("Added ExecutionAgent Scout transfer target")
            
            # Add Axel as a transfer target for Scout as well
            if hasattr(scout_agent, 'add_specific_transfer_target'):
                scout_agent.add_specific_transfer_target(adk_agent)
                logger.info("Added Scout's Axel transfer target using add_specific_transfer_target")
        
        return adk_agent
        
    except Exception as e:
        logger.error(f"Failed to create Axel agent: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def create_specialized_agents(root_agent: Agent) -> List[Agent]:
    """
    Create all specialized agents and register them with the root agent.
    
    Args:
        root_agent: The root agent to attach specialized agents to
        
    Returns:
        List of created specialized agents
    """
    specialized_agents = []
    
    # Create and register Axel agent
    axel_agent = create_axel_agent(root_agent)
    if axel_agent:
        specialized_agents.append(axel_agent)
    
    # Future specialized agents would be created here
    
    return specialized_agents
