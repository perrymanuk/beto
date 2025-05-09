"""
Test script to validate memory functionality in the web interface.

This script directly tests the memory functionality by simulating the web interface.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_web_memory():
    """Test memory initialization and functionality in web interface context."""
    try:
        # Import the root agent to initialize everything
        logger.info("Importing root_agent from agent.py")
        from agent import root_agent
        
        # Import web session components
        from radbot.web.api.session import SessionRunner
        
        # Create a unique session and user ID
        session_id = "test_memory_session"
        user_id = f"test_user_{session_id}"
        
        # Create a session runner directly
        logger.info("Creating SessionRunner")
        runner = SessionRunner(user_id=user_id, session_id=session_id)
        
        # Check if the agent has memory service
        if hasattr(root_agent, '_memory_service') and root_agent._memory_service:
            logger.info("Memory service found on root_agent._memory_service")
            memory_service = root_agent._memory_service
        elif hasattr(root_agent, 'memory_service') and root_agent.memory_service:
            logger.info("Memory service found on root_agent.memory_service")
            memory_service = root_agent.memory_service
        else:
            logger.error("No memory service found on root_agent")
            return
        
        # Verify the memory service has a client
        if hasattr(memory_service, 'client') and memory_service.client:
            logger.info(f"Memory service has a client: {memory_service.client}")
        else:
            logger.error("Memory service has no client")
            return
        
        # Check if the runner has memory service available
        if hasattr(runner.runner, 'memory_service') and runner.runner.memory_service:
            logger.info("Memory service found on runner.runner.memory_service")
        else:
            logger.error("No memory service found on runner.runner.memory_service")
            return
        
        # Try a basic memory operations
        test_messages = [
            "My name is Perry Manuk and I'm testing the memory system",
            "Save this memory: The capital of France is Paris",
            "What can you recall about my name?"
        ]
        
        for i, message in enumerate(test_messages):
            logger.info(f"Testing with message {i+1}/{len(test_messages)}: {message}")
            result = runner.process_message(message)
            logger.info(f"Response: {result.get('response', 'No response')[:100]}")
            
            # Wait a bit between messages to let memory processing complete
            await asyncio.sleep(1)
        
        logger.info("Memory test complete")
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_web_memory())