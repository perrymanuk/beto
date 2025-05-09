#\!/usr/bin/env python3
"""
Add a generate_content method to the root agent.

This script adds a generate_content method to the root agent to make it compatible
with the older code that expects this method to be available.
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

def add_generate_content_method():
    """
    Add a generate_content method to the root agent.
    
    This function imports the root agent and adds a generate_content method
    to make it compatible with the older code that expects this method.
    """
    try:
        # Import root agent
        from radbot.agent import root_agent
        
        # Check if generate_content method already exists
        if hasattr(root_agent, 'generate_content') and callable(root_agent.generate_content):
            logger.info("Root agent already has a generate_content method")
            return True
            
        # Add generate_content method
        def generate_content(prompt):
            """
            Generate content by forwarding to the model's generate_content method.
            
            Args:
                prompt: The prompt to generate content for
            
            Returns:
                The generated content
            """
            if not hasattr(root_agent, '_model') or not root_agent._model:
                logger.error("Root agent has no _model attribute")
                return "Error: No model available for content generation"
                
            # Import Content and Part types if needed
            from google.genai.types import Content, Part
            
            # Convert prompt to Content object if it's a string
            if isinstance(prompt, str):
                content = Content(
                    parts=[Part(text=prompt)],
                    role="user"
                )
            else:
                content = prompt
                
            # Forward to model's generate_content method
            response = root_agent._model.generate_content(content)
            return response
            
        # Set the method on the agent
        root_agent.generate_content = generate_content
        
        logger.info("Successfully added generate_content method to root agent")
        return True
        
    except Exception as e:
        logger.error(f"Error adding generate_content method: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Run the script."""
    success = add_generate_content_method()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
