#!/usr/bin/env python3
"""
Simple script to register Axel with the RadBot system.
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

# Import required components
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
from radbot.agent.agent_factory import AgentFactory

# Import our special Axel toolset directly, skipping the problematic imports
def create_minimal_axel_toolset() -> List[Any]:
    """Create a minimal set of tools for Axel."""
    toolset = []
    
    # Try to add shell command execution
    try:
        from radbot.tools.shell.shell_tool import execute_shell_command
        toolset.append(execute_shell_command)
        logger.info("Added execute_shell_command to minimal Axel toolset")
    except Exception as e:
        logger.error(f"Failed to add execute_shell_command: {e}")
    
    return toolset

def register_axel(root_agent: Agent, axel_name: str = "axel_agent") -> Optional[Agent]:
    """Create and register Axel with minimal tools.
    
    Args:
        root_agent: Main agent to connect Axel to
        axel_name: Name for the Axel agent
        
    Returns:
        The created Axel agent, or None if registration failed
    """
    try:
        # Create a minimal toolset for Axel
        axel_tools = create_minimal_axel_toolset()
        
        # Create the agent
        axel_agent = AgentFactory.create_sub_agent(
            name=axel_name,
            description="Agent specialized in implementation and execution",
            instruction_name="axel",
            tools=axel_tools
        )
        
        # Get current sub-agents list
        current_sub_agents = list(root_agent.sub_agents) if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents else []
        
        # Add Axel to the sub-agents list
        current_sub_agents.append(axel_agent)
        
        # Update the list of sub-agents
        root_agent.sub_agents = current_sub_agents
        
        logger.info(f"Successfully created and registered Axel agent: {axel_name}")
        
        # Setup Scout-to-Axel transfer if Scout exists
        scout_agent = None
        for sub_agent in root_agent.sub_agents:
            if hasattr(sub_agent, 'name') and sub_agent.name == "scout_agent":
                scout_agent = sub_agent
                break
                
        if scout_agent:
            # Make Scout aware of Axel
            scout_sub_agents = list(scout_agent.sub_agents) if hasattr(scout_agent, 'sub_agents') and scout_agent.sub_agents else []
            scout_sub_agents.append(axel_agent)
            scout_agent.sub_agents = scout_sub_agents
            logger.info("Added bidirectional link: Scout → Axel")
            
            # Make Axel aware of Scout
            axel_sub_agents = list(axel_agent.sub_agents) if hasattr(axel_agent, 'sub_agents') and axel_agent.sub_agents else []
            axel_sub_agents.append(scout_agent)
            axel_agent.sub_agents = axel_sub_agents
            logger.info("Added bidirectional link: Axel → Scout")
        
        return axel_agent
    except Exception as e:
        logger.error(f"Failed to create and register Axel agent: {e}")
        return None

def main():
    """Register Axel agent."""
    # Import the root agent - should already be initialized
    try:
        from radbot.agent import root_agent
        logger.info(f"Found root agent: {root_agent.name}")
    except ImportError:
        logger.error("Root agent not found. Run this after initializing the main agent.")
        return 1
    
    # Check if Axel already exists
    axel_exists = False
    if hasattr(root_agent, 'sub_agents'):
        for sub_agent in root_agent.sub_agents:
            if hasattr(sub_agent, 'name') and sub_agent.name == "axel_agent":
                logger.info("Axel agent is already registered")
                axel_exists = True
                break
    
    if not axel_exists:
        logger.info("Axel agent not found. Registering...")
        axel_agent = register_axel(root_agent)
        if axel_agent:
            logger.info("Successfully registered Axel agent")
        else:
            logger.error("Failed to register Axel agent")
            return 1
    
    # Display all registered agents
    agent_names = []
    if hasattr(root_agent, 'sub_agents'):
        for agent in root_agent.sub_agents:
            if hasattr(agent, 'name'):
                agent_names.append(agent.name)
    
    logger.info(f"Registered agents: {', '.join(agent_names)}")
    
    logger.info("Agent registration complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())