#!/usr/bin/env python3
"""
Test script to verify that all specialized agents are properly configured and loaded.
"""

import logging
import os
import sys
import argparse
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import radbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required modules
from radbot.config.settings import ConfigManager
from radbot.agent.specialized_agent_factory import SpecializedAgentFactory
from radbot.tools.specialized.transfer_controller import get_transfer_controller

# Import toolset registration functions to ensure all toolsets are loaded
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
    scout_toolset,
    axel_toolset
)

def parse_args():
    parser = argparse.ArgumentParser(description='Test specialized agents configuration')
    parser.add_argument(
        '--config', 
        default='config/specialized_agents.yaml',
        help='Path to the configuration file'
    )
    parser.add_argument(
        '--include', 
        nargs='+',
        help='Specialized agents to include (comma-separated list)'
    )
    parser.add_argument(
        '--all', 
        action='store_true',
        help='Test all specialized agents'
    )
    return parser.parse_args()

def main():
    """Test specialized agents configuration."""
    args = parse_args()
    
    # Load configuration
    if os.path.exists(args.config):
        logger.info(f"Loading configuration from {args.config}")
        config = ConfigManager(args.config)
    else:
        logger.warning(f"Configuration file {args.config} not found, using default config")
        from radbot.config import config_manager
        config = config_manager
    
    # Determine which specializations to include
    include_specializations = None
    if args.all:
        # Include all available toolsets
        from radbot.tools.specialized.base_toolset import get_all_toolsets
        include_specializations = list(get_all_toolsets().keys())
        logger.info(f"Testing all available specialized agents: {', '.join(include_specializations)}")
    elif args.include:
        # Parse comma-separated list of specializations
        if isinstance(args.include, list):
            include_specializations = []
            for item in args.include:
                if ',' in item:
                    include_specializations.extend(item.split(','))
                else:
                    include_specializations.append(item)
        else:
            include_specializations = args.include.split(',')
        logger.info(f"Testing specified specialized agents: {', '.join(include_specializations)}")
    
    # Create orchestrator with specialized agents
    logger.info("Creating orchestrator with specialized agents")
    main_agent = SpecializedAgentFactory.create_orchestrator_with_specialized_agents(
        name="beto",
        instruction_name="main_agent",
        config=config,
        include_specializations=include_specializations
    )
    
    # Get the transfer controller to see what agents are registered
    transfer_controller = get_transfer_controller()
    agents = transfer_controller.get_all_agents()
    
    # Display all registered agents
    logger.info(f"Registered agents ({len(agents)}): {', '.join(agents.keys())}")
    
    # Display transfer rules
    transfer_rules = transfer_controller.get_transfer_rules()
    logger.info("Transfer rules:")
    for agent_name, targets in transfer_rules.items():
        logger.info(f"  {agent_name} -> {', '.join(targets)}")
    
    # Special check for Scout-Axel bidirectional link
    if 'scout_agent' in agents and 'axel_agent' in agents:
        logger.info("Scout-Axel bidirectional link is properly configured")
        
        if 'axel_agent' in transfer_rules.get('scout_agent', []):
            logger.info("✅ Scout can transfer to Axel")
        else:
            logger.error("❌ Scout cannot transfer to Axel")
            
        if 'scout_agent' in transfer_rules.get('axel_agent', []):
            logger.info("✅ Axel can transfer to Scout")
        else:
            logger.error("❌ Axel cannot transfer to Scout")
    
    logger.info("Specialized agents test completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())