#!/usr/bin/env python3
"""
Test script to check FunctionTool constructor parameters in ADK 0.4.0
"""

import logging
import inspect
from google.adk.tools import FunctionTool

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_function(param1: str, param2: int = 42):
    """Test function for FunctionTool."""
    return f"You called with {param1} and {param2}"

if __name__ == "__main__":
    # First, log the signature of FunctionTool class
    logger.info(f"FunctionTool init signature: {inspect.signature(FunctionTool.__init__)}")
    
    # Try to create a FunctionTool with the 'function' parameter (old style)
    try:
        logger.info("Trying to create FunctionTool with 'function' parameter")
        tool1 = FunctionTool(function=test_function)
        logger.info("Success! Created tool with 'function' parameter: %s", tool1)
    except Exception as e:
        logger.error(f"Error creating FunctionTool with 'function' parameter: {e}")
    
    # Try to create a FunctionTool with the 'func' parameter (potential new style)
    try:
        logger.info("Trying to create FunctionTool with 'func' parameter")
        tool2 = FunctionTool(func=test_function)
        logger.info("Success! Created tool with 'func' parameter: %s", tool2)
    except Exception as e:
        logger.error(f"Error creating FunctionTool with 'func' parameter: {e}")
    
    # Try other parameter names that might be used
    for param_name in ['fn', 'callback', 'callable', 'target']:
        try:
            logger.info(f"Trying to create FunctionTool with '{param_name}' parameter")
            kwargs = {param_name: test_function}
            tool = FunctionTool(**kwargs)
            logger.info(f"Success! Created tool with '{param_name}' parameter: {tool}")
        except Exception as e:
            logger.error(f"Error creating FunctionTool with '{param_name}' parameter: {e}")
    
    # Try to create the tool with positional argument
    try:
        logger.info("Trying to create FunctionTool with positional argument")
        tool3 = FunctionTool(test_function)
        logger.info("Success! Created tool with positional argument: %s", tool3)
    except Exception as e:
        logger.error(f"Error creating FunctionTool with positional argument: {e}")
    
    # Get available attributes/methods of FunctionTool class
    logger.info(f"FunctionTool attributes/methods: {dir(FunctionTool)}")