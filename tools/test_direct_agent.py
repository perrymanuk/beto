#\!/usr/bin/env python3
"""
Test direct interaction with the root agent to diagnose issues.

This script attempts to interact directly with the root agent 
without using the web interface or Runner.
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

def test_direct_agent_interaction():
    """
    Test direct interaction with the root agent.
    
    This function imports the root agent and attempts to interact with it
    directly using its generate_content method.
    """
    try:
        # Import root agent
        from radbot.agent import root_agent
        
        if not hasattr(root_agent, 'name'):
            logger.error("Root agent doesn't have a name attribute")
            return
            
        logger.info(f"Found root agent: {root_agent.name}")
        
        # Check if the agent has a generate_content method
        if not hasattr(root_agent, 'generate_content') or not callable(root_agent.generate_content):
            logger.error("Root agent doesn't have a generate_content method")
            return
            
        # Send a simple message to the agent
        message = "Hello, can you hear me? Please respond with a simple greeting."
        
        logger.info(f"Sending test message to agent: {message}")
        
        # Attempt to get a response - direct mode
        try:
            logger.info("Testing direct generate_content call...")
            response = root_agent.generate_content(message)
            
            # Extract response text
            response_text = None
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text = part.text
                        break
            elif hasattr(response, 'content') and hasattr(response.content, 'parts'):
                for part in response.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text = part.text
                        break
            
            if response_text:
                logger.info(f"Response from agent: {response_text[:100]}...")
            else:
                logger.error(f"No text in response: {response}")
        except Exception as e:
            logger.error(f"Error calling generate_content directly: {str(e)}")
            
        # Attempt with ADK Content object
        try:
            from google.genai.types import Content, Part
            
            logger.info("Testing with ADK Content object...")
            
            # Create a Content object with the message
            content_obj = Content(
                parts=[Part(text=message)],
                role="user"
            )
            
            # Send to the agent
            response = root_agent.generate_content(content_obj)
            
            # Extract response text
            response_text = None
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text = part.text
                        break
            elif hasattr(response, 'content') and hasattr(response.content, 'parts'):
                for part in response.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text = part.text
                        break
            
            if response_text:
                logger.info(f"Response from agent with Content object: {response_text[:100]}...")
            else:
                logger.error(f"No text in response with Content object: {response}")
                
        except Exception as e:
            logger.error(f"Error using Content object: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error in test_direct_agent_interaction: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_direct_agent_interaction()
