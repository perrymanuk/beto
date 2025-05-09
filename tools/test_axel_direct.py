#!/usr/bin/env python3
"""
Test script for direct Axel agent without specialized architecture.

This script creates an Axel agent directly using the AgentFactory
rather than through the specialized agent architecture.
"""

import logging
import os
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import radbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required components
from radbot.agent.agent_factory import AgentFactory
from radbot.config.settings import ConfigManager

def main():
    """Create and test Axel agent directly."""
    logger.info("Creating Axel agent directly...")
    
    # Load config
    config_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'radbot', 
        'config', 
        'default_configs', 
        'axel_direct.yaml'
    )
    
    if os.path.exists(config_path):
        logger.info(f"Loading config from {config_path}")
        config = ConfigManager(config_path)
    else:
        logger.error(f"Config file not found: {config_path}")
        return 1
    
    # Create Axel using standard AgentFactory
    axel = AgentFactory.create_sub_agent(
        name="axel_direct",
        description="Implementation-focused agent",
        instruction_name="axel",
        tools=[],  # No tools for simplicity
        model=config.get_agent_model("axel_agent_model"),
        config=config
    )
    
    # Test the agent with a simple task
    task = """
    You are Axel, an implementation-focused agent. Please describe your capabilities
    and how you would approach implementing a simple Python function to calculate 
    factorial numbers.
    """
    
    logger.info("Testing Axel with a simple task...")
    response = axel(task)
    
    # Display the response
    logger.info("Axel's response:")
    print("=" * 80)
    print(response)
    print("=" * 80)
    
    logger.info("Axel direct test completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())