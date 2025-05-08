"""
Test script to directly test memory tools with the global ToolContext approach.

This script directly tests the memory tool functionality using the global ToolContext.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_memory_tool():
    """Test memory tool with the global ToolContext approach."""
    try:
        # Import necessary modules
        from google.adk.tools.tool_context import ToolContext
        from radbot.memory.qdrant_memory import QdrantMemoryService
        from radbot.tools.memory.memory_tools import search_past_conversations, store_important_information
        from radbot.config.config_loader import config_loader
        
        # Get Qdrant settings from config_loader
        vector_db_config = config_loader.get_config().get("vector_db", {})
        url = vector_db_config.get("url")
        api_key = vector_db_config.get("api_key")
        host = vector_db_config.get("host", "localhost")
        port = vector_db_config.get("port", 6333)
        collection = vector_db_config.get("collection", "radbot_memories")
        
        # Create memory service
        logger.info(f"Initializing QdrantMemoryService with host={host}, port={port}, collection={collection}")
        memory_service = QdrantMemoryService(
            collection_name=collection,
            host=host,
            port=int(port) if isinstance(port, str) else port,
            url=url,
            api_key=api_key
        )
        logger.info(f"Successfully initialized QdrantMemoryService")
        
        # Set memory_service in global ToolContext
        setattr(ToolContext, "memory_service", memory_service)
        logger.info("Set memory_service in global ToolContext")
        
        # Set user_id in global ToolContext
        user_id = "test_user_direct"
        setattr(ToolContext, "user_id", user_id)
        logger.info(f"Set user_id '{user_id}' in global ToolContext")
        
        # Store some test information
        logger.info("Storing test information in memory")
        store_result = store_important_information(
            information="This is a test memory from user test_user_direct",
            memory_type="test_memory"
        )
        logger.info(f"Store result: {store_result}")
        
        # Search for the stored information
        logger.info("Searching for test memory")
        search_result = search_past_conversations(query="test memory")
        logger.info(f"Search result: {search_result}")
        
        return True
    except Exception as e:
        logger.error(f"Error in test_memory_tool: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_memory_tool()
    if success:
        logger.info("Memory tool test completed successfully!")
    else:
        logger.error("Memory tool test failed!")
        sys.exit(1)