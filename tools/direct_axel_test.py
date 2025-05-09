#!/usr/bin/env python3
"""
Directly test Axel agent with zero dependencies.

This script creates and runs a minimal Axel agent without relying
on any specialized agent architecture. It uses Vertex AI's ADK directly.
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

def main():
    """Create and directly test Axel agent with minimal dependencies."""
    # Get the instruction file path
    instruction_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'radbot', 
        'config', 
        'default_configs', 
        'instructions',
        'axel.md'
    )
    
    if not os.path.exists(instruction_path):
        logger.error(f"Instruction file not found: {instruction_path}")
        return 1
    
    # Read the instruction file
    with open(instruction_path, 'r') as f:
        instruction = f.read()
    
    logger.info(f"Read instruction file: {len(instruction)} characters")
    
    # Import ADK Agent directly
    try:
        from google.adk.agents import Agent
        from google.adk.runners import Runner
        from google.adk.session import MemorySession
        from google.adk.types import Content, Part
    except ImportError:
        logger.error("Failed to import Agent and Runner from ADK. Make sure ADK is installed.")
        return 1
    
    # Create Axel agent directly with ADK
    try:
        # Set up Vertex AI credentials
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser(
            "/Users/perry.manuk/Downloads/htg-infra-241817ba8aed.json"
        )
        
        # Create Axel with minimal tools
        axel = Agent(
            name="axel_direct",
            model="gemini-2.5-pro-preview-05-06",
            instruction=instruction,
            description="Implementation-focused agent",
            tools=[]  # No tools for simplicity
        )
        
        logger.info("Created Axel agent directly with ADK")
        
        # Create a session service (required by Runner)
        class SimpleSessionService:
            def get_session(self, app_name, user_id, session_id):
                return MemorySession(app_name=app_name, user_id=user_id, session_id=session_id)
                
            def create_session(self, app_name, user_id, session_id):
                return MemorySession(app_name=app_name, user_id=user_id, session_id=session_id)
        
        # Create a runner with the required parameters
        runner = Runner(
            agent=axel,
            app_name="axel_test",
            session_service=SimpleSessionService()
        )
        
        # Test the agent with a simple task
        prompt = """
        Hello Axel. I need you to explain how you would implement a Python utility 
        function for validating email addresses. Please outline the approach you would take,
        the regular expressions or validation logic you would use, and how you would 
        handle edge cases.
        """
        
        logger.info("Running Axel with test prompt...")
        
        # Create a proper message content object
        message = Content(
            parts=[Part(text=prompt)],
            role="user"
        )
        
        # Run the agent
        events = list(runner.run(user_id="test_user", session_id="test_session", new_message=message))
        
        # Process the response
        response = None
        for event in reversed(events):
            if hasattr(event, 'content'):
                content = event.content
                if hasattr(content, 'parts') and content.parts:
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            response = part.text
                            break
                elif hasattr(content, 'text') and content.text:
                    response = content.text
                    break
            
            if response:
                break
        
        if not response:
            logger.error("No response received from Axel agent")
            return 1
        
        # Display the response
        logger.info("Axel's response:")
        print("=" * 80)
        print(response)
        print("=" * 80)
        
        logger.info("Direct Axel test completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Error in direct Axel test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())