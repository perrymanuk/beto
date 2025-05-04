
#!/usr/bin/env python3
"""
Test the filesystem implementation.

This script is used to validate that the filesystem implementation works correctly.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import the filesystem implementation
from radbot.filesystem.integration import create_filesystem_tools
from radbot.filesystem.security import set_allowed_directories
from google.adk.tools import Tool

def test_filesystem_tools():
    """Test that the filesystem tools are created correctly."""
    # Set up allowed directories
    set_allowed_directories([os.getcwd()])
    
    # Create filesystem tools
    tools = create_filesystem_tools(
        allowed_directories=[os.getcwd()],
        enable_write=True,
        enable_delete=True
    )
    
    # Log information about each tool
    logger.info(f"Created {len(tools)} filesystem tools")
    
    for i, tool in enumerate(tools):
        logger.info(f"Tool {i+1}:")
        logger.info(f"  Name: {tool.name if hasattr(tool, 'name') else str(tool)}")
        logger.info(f"  Type: {type(tool).__name__}")
        
        # Check if it's an ADK Tool
        if isinstance(tool, Tool):
            logger.info("  Valid ADK Tool: Yes")
        else:
            logger.info("  Valid ADK Tool: No")
            
        # If it has a function, check its signature
        if hasattr(tool, 'func'):
            func = tool.func
            logger.info(f"  Function: {func.__name__}")
            logger.info(f"  Function docstring: {func.__doc__.strip()[:50]}...")
            
            # Log function annotations
            import inspect
            sig = inspect.signature(func)
            logger.info(f"  Function signature: {sig}")
            params = []
            for name, param in sig.parameters.items():
                params.append(f"{name}: {param.annotation}")
            logger.info(f"  Parameters: {', '.join(params)}")
            logger.info(f"  Return type: {sig.return_annotation}")

if __name__ == "__main__":
    test_filesystem_tools()
    logger.info("Filesystem tools test completed successfully")
