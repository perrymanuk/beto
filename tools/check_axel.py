#!/usr/bin/env python3
"""
Simple script to check that Axel is properly configured and available.
"""

import logging
import os
import sys
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import radbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required modules
from radbot.agent.specialized_agent_factory import SpecializedAgentFactory
from radbot.tools.specialized.transfer_controller import get_transfer_controller

def main():
    """Check that Axel is properly configured and available."""
    logger.info("Checking Axel configuration...")
    
    # Create orchestrator with specialized agents
    main_agent = SpecializedAgentFactory.create_orchestrator_with_specialized_agents(
        name="beto", 
        include_specializations=["scout", "axel"]
    )
    
    # Get the transfer controller
    transfer_controller = get_transfer_controller()
    agents = transfer_controller.get_all_agents()
    
    # Check if Axel is registered
    if 'axel_agent' in agents:
        logger.info("✅ Axel agent is properly registered")
    else:
        logger.error("❌ Axel agent is NOT registered")
        return 1
    
    # Check Scout-Axel bidirectional link
    transfer_rules = transfer_controller.get_transfer_rules()
    if 'scout_agent' in agents:
        if 'axel_agent' in transfer_rules.get('scout_agent', []):
            logger.info("✅ Scout can transfer to Axel")
        else:
            logger.error("❌ Scout cannot transfer to Axel")
        
        if 'scout_agent' in transfer_rules.get('axel_agent', []):
            logger.info("✅ Axel can transfer to Scout")
        else:
            logger.error("❌ Axel cannot transfer to Scout")
    
    logger.info("Axel configuration check completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())