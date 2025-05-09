#!/usr/bin/env python3
"""
Example demonstrating the specialized agent architecture.

This example shows how to create and use specialized agents according to
the "Modified Hub-and-Spoke Pattern with Directed Transfers" architecture.
"""

import logging
import os
import sys
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import radbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required modules
from radbot.config import config_manager
from radbot.agent.specialized_agent_factory import SpecializedAgentFactory
from radbot.config.settings import ConfigManager
from google.adk.agents import Agent

# Import toolset registration functions to ensure all toolsets are loaded
from radbot.tools.specialized import filesystem_toolset
from radbot.tools.specialized import web_research_toolset
from radbot.tools.specialized import memory_toolset
from radbot.tools.specialized import todo_toolset
from radbot.tools.specialized import calendar_toolset
from radbot.tools.specialized import homeassistant_toolset
from radbot.tools.specialized import code_execution_toolset
from radbot.tools.specialized import agentic_coder_toolset
from radbot.tools.specialized import utility_toolset
from radbot.tools.specialized import scout_toolset
from radbot.tools.specialized import axel_toolset

def main():
    """Run the specialized agent architecture example."""
    logger.info("Starting specialized agent architecture example")
    
    # Load config from file if provided
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    if os.path.exists(config_path):
        logger.info(f"Loading config from {config_path}")
        config = ConfigManager(config_path)
    else:
        logger.info("Using default config")
        config = config_manager
    
    # Create specialized agents with the factory
    logger.info("Creating specialized agent system with Hub-and-Spoke architecture")
    
    # Option 1: Create all specialized agents at once
    # main_agent = SpecializedAgentFactory.create_orchestrator_with_specialized_agents(
    #     name="beto",
    #     instruction_name="main_agent",
    #     config=config
    # )
    
    # Option 2: Create just the ones we need (for this example, Scout and Axel)
    logger.info("Creating Scout and Axel agents for design and implementation")
    
    # Create the main orchestrator
    main_agent = SpecializedAgentFactory.create_orchestrator_with_specialized_agents(
        name="beto",
        instruction_name="main_agent",
        config=config,
        include_specializations=["scout", "axel", "web_research", "code_execution"]
    )
    
    # Now we can interact with the specialized agents via the main agent
    user_input = "Create a Python function to calculate the Fibonacci sequence"
    logger.info(f"Sending user request to main agent: {user_input}")
    
    # The main agent will handle the request and transfer to specialized agents as needed
    response = main_agent(user_input)
    
    # Print the final response
    logger.info(f"Response from agent: {response}")
    
    # In a real application, this would be part of a continuous interaction loop
    logger.info("Example completed successfully")

if __name__ == "__main__":
    main()