#!/usr/bin/env python3
"""
Script to register specialized agents with the RadBot system.

This ensures that all specialized agents, including Axel, are properly registered
even if there are issues with some MCP servers.
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
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
from radbot.agent.agent_factory import AgentFactory
from radbot.tools.specialized.base_toolset import register_toolset, get_toolset
from radbot.tools.specialized.transfer_controller import TransferController, get_transfer_controller

# Import required toolsets to ensure they're loaded
from radbot.tools.specialized import (
    filesystem_toolset,
    web_research_toolset,
    memory_toolset,
    todo_toolset,
    calendar_toolset,
    homeassistant_toolset,
    code_execution_toolset,
    agentic_coder_toolset,
    utility_toolset,
    scout_toolset
)

# Import our special Axel toolset that doesn't depend on sequential thinking
from radbot.tools.specialized.simple_axel_toolset import create_simple_axel_toolset

def manually_register_axel(root_agent: Agent, axel_name: str = "axel_agent") -> Optional[Agent]:
    """Manually create and register Axel agent.
    
    Args:
        root_agent: Main agent to connect Axel to
        axel_name: Name for the Axel agent
        
    Returns:
        The created Axel agent, or None if registration failed
    """
    try:
        # Get Axel toolset
        axel_tools = get_toolset("axel")
        
        # Create the agent with AgentFactory
        axel_agent = AgentFactory.create_sub_agent(
            name=axel_name,
            description="Agent specialized in implementation and execution",
            instruction_name="axel",
            tools=axel_tools
        )
        
        # Add to root agent
        root_agent.add_sub_agent(axel_agent)
        logger.info(f"Successfully created and registered Axel agent: {axel_name}")
        
        # Register with transfer controller for bi-directional links
        transfer_controller = get_transfer_controller()
        transfer_controller.register_specialized_agent(
            agent=axel_agent,
            specialization="axel",
            allowed_transfers=["scout_agent", "code_execution_agent"]
        )
        
        # Setup scout-to-axel transfer if scout exists
        agents = transfer_controller.get_all_agents()
        if "scout_agent" in agents:
            scout_agent = agents["scout_agent"]
            # Make Scout aware of Axel
            scout_agent.add_sub_agent(axel_agent)
            logger.info("Added bidirectional link: Scout → Axel")
            
            # Make Axel aware of Scout
            axel_agent.add_sub_agent(scout_agent)
            logger.info("Added bidirectional link: Axel → Scout")
        
        return axel_agent
    except Exception as e:
        logger.error(f"Failed to create and register Axel agent: {e}")
        return None

def main():
    """Register Axel and other specialized agents."""
    # Import the root agent - should already be initialized
    try:
        from radbot.agent import root_agent
        logger.info(f"Found root agent: {root_agent.name}")
    except ImportError:
        logger.error("Root agent not found. Run this after initializing the main agent.")
        return 1
    
    # Check if Axel needs to be registered
    transfer_controller = get_transfer_controller()
    agents = transfer_controller.get_all_agents()
    
    if "axel_agent" in agents:
        logger.info("Axel agent is already registered")
    else:
        logger.info("Axel agent not found. Manually registering...")
        axel_agent = manually_register_axel(root_agent)
        if axel_agent:
            logger.info("Successfully registered Axel agent")
        else:
            logger.error("Failed to register Axel agent")
            return 1
    
    # Display all registered agents
    agents = transfer_controller.get_all_agents()
    logger.info(f"Registered agents ({len(agents)}): {', '.join(agents.keys())}")
    
    # Display transfer rules
    transfer_rules = transfer_controller.get_transfer_rules()
    logger.info("Transfer rules:")
    for agent_name, targets in transfer_rules.items():
        logger.info(f"  {agent_name} -> {', '.join(targets)}")
    
    logger.info("Agent registration complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())