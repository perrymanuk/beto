#\!/usr/bin/env python3
"""
Fix syntax error in specialized_agent_factory.py.

This script fixes a syntax error in the specialized_agent_factory.py file
caused by improper closing of the function.
"""

import logging
import os
import sys
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import radbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def fix_syntax_error():
    """
    Fix syntax error in specialized_agent_factory.py.
    
    This function fixes a syntax error in the create_axel_agent function
    in specialized_agent_factory.py, which has incorrect function closing.
    """
    # Find the specialized_agent_factory.py file
    factory_py_path = os.path.join(os.path.dirname(__file__), '..', 'radbot', 'agent', 'specialized_agent_factory.py')
    
    if not os.path.exists(factory_py_path):
        logger.error(f"Could not find specialized_agent_factory.py at {factory_py_path}")
        return False
    
    logger.info(f"Found specialized_agent_factory.py at {factory_py_path}")
    
    # Simplest approach: rewrite the entire file with proper syntax
    with open(factory_py_path, 'w') as f:
        f.write('''"""
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
            axel_model = "gemini-2.5-pro-preview-05-06"
            logger.info(f"Using fallback model for Axel: {axel_model}")
        else:
            logger.info(f"Using configured model for Axel: {axel_model}")
        
        # Get the instruction
        instruction = config_manager.get_instruction("axel")
        if not instruction:
            logger.warning("Could not find Axel instruction, using default")
            instruction = """# Axel - Implementation Agent

You are Axel, a specialized agent focused on implementation details and execution.
Your primary responsibility is carrying out specific tasks with precision and providing
detailed solutions to implementation problems.

## Capabilities
1. Execute shell commands and programs
2. Read and write files in allowed directories
3. Implement solutions based on specifications
4. Debug and fix implementation issues

## Response Style
- Be precise and efficient in your responses
- Provide detailed step-by-step instructions when implementing solutions
- Include code snippets with clear explanations
- For executable actions, show commands and explain what they do

## Interaction Pattern
1. When given a task, first validate your understanding
2. Break down complex tasks into manageable steps
3. Execute steps methodically, providing updates on progress
4. Summarize results and any issues encountered

Remember that you are an implementation specialist. Your focus is on execution, 
technical details, and turning plans into reality."""
        
        # Create a minimal toolset for Axel
        axel_tools = create_minimal_axel_toolset()
        
        # Create the Axel agent with the configured model
        axel_agent = Agent(
            name="axel_agent",
            model=axel_model,
            instruction=instruction,
            description="Agent specialized in implementation and execution",
            tools=axel_tools
        )
        
        # Get current sub-agents list from root agent
        current_sub_agents = list(root_agent.sub_agents) if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents else []
        
        # Add Axel to the sub-agents list
        current_sub_agents.append(axel_agent)
        
        # Update the list of sub-agents
        root_agent.sub_agents = current_sub_agents
        
        logger.info(f"Successfully created and registered Axel agent with {len(axel_tools)} tools")
        
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
                if hasattr(agent, 'name') and agent.name == "axel_agent":
                    axel_already_added = True
                    break
                    
            if not axel_already_added:
                # Add a weak reference to avoid strong circular refs
                scout_sub_agents.append(proxy(axel_agent))
                scout_agent.sub_agents = scout_sub_agents
                logger.info("Added Scout → Axel reference (using proxy)")
                
            # Store Axel's scout reference separately
            # Note: We don't create a full bidirectional link to avoid serialization issues
            if not hasattr(axel_agent, '_associated_agents'):
                axel_agent._associated_agents = {}
            
            axel_agent._associated_agents['scout'] = scout_agent.name
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
            
            # Add the helper to axel agent
            axel_agent.find_agent_by_name = find_agent_by_name
            logger.info("Added find_agent_by_name helper to Axel agent")
        
        return axel_agent
        
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
''')
    
    logger.info(f"Fixed syntax error in {factory_py_path}")
    return True

def main():
    """Fix syntax error."""
    success = fix_syntax_error()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
