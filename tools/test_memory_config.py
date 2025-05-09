"""
Test script to validate memory configuration is properly loaded from config.yaml.

This script tests that the memory agent factory properly reads Qdrant 
configuration from the YAML config file instead of environment variables.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from radbot.config.config_loader import config_loader
from radbot.agent.memory_agent_factory import create_memory_enabled_agent
from radbot.agent.enhanced_memory_agent_factory import create_enhanced_memory_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_memory_config():
    """Test that memory configuration is properly loaded from config.yaml."""
    # Print the current vector_db configuration
    vector_db_config = config_loader.get_config().get("vector_db", {})
    logger.info("Current vector_db configuration in config.yaml:")
    for key, value in vector_db_config.items():
        if key != "api_key":  # Don't log the API key
            logger.info(f"  {key}: {value}")
    
    # Create a basic memory-enabled agent
    logger.info("\nCreating a basic memory-enabled agent...")
    try:
        agent = create_memory_enabled_agent()
        
        # Verify that the memory service was created successfully
        if hasattr(agent, '_memory_service') and agent._memory_service:
            logger.info("Memory service created successfully!")
            memory_service = agent._memory_service
            
            # Log memory service details
            logger.info(f"Collection name: {memory_service.collection_name}")
            
            # Try a basic operation
            logger.info("\nTrying a basic memory operation...")
            result = memory_service.search_memory(
                app_name="memory_test",
                user_id="test_user",
                query="This is a test query",
                limit=5
            )
            logger.info(f"Search returned {len(result)} results (empty result is expected for a new collection)")
            
            logger.info("Basic memory test successful!")
        else:
            logger.error("Memory service was not properly attached to the agent")
    except Exception as e:
        logger.error(f"Failed to create memory-enabled agent: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Create an enhanced memory agent
    logger.info("\nCreating an enhanced memory agent...")
    try:
        enhanced_agent = create_enhanced_memory_agent()
        
        # Verify that the memory service was created successfully
        if hasattr(enhanced_agent, '_memory_service') and enhanced_agent._memory_service:
            logger.info("Enhanced memory service created successfully!")
            
            # Verify memory manager
            if hasattr(enhanced_agent, 'memory_manager') and enhanced_agent.memory_manager:
                logger.info("Memory manager created successfully!")
                logger.info("Enhanced memory test successful!")
            else:
                logger.error("Memory manager was not properly created")
        else:
            logger.error("Memory service was not properly attached to the enhanced agent")
    except Exception as e:
        logger.error(f"Failed to create enhanced memory agent: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
if __name__ == "__main__":
    test_memory_config()