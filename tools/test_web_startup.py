#!/usr/bin/env python3
"""
Test MCP fileserver tools in web startup.
"""

import os
import sys
import asyncio
import logging
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import agent creation function
from agent import create_agent

def main():
    """Test that MCP fileserver tools are properly integrated with the agent during web startup."""
    # Print environment variables
    logger.info(f"MCP_FS_ROOT_DIR: {os.environ.get('MCP_FS_ROOT_DIR', 'Not set')}")
    logger.info(f"MCP_FS_ALLOW_WRITE: {os.environ.get('MCP_FS_ALLOW_WRITE', 'Not set')}")
    logger.info(f"MCP_FS_ALLOW_DELETE: {os.environ.get('MCP_FS_ALLOW_DELETE', 'Not set')}")
    
    # Make sure nest_asyncio is available
    try:
        import nest_asyncio
        nest_asyncio.apply()
        logger.info("Successfully applied nest_asyncio")
    except ImportError:
        logger.error("nest_asyncio is not installed. Run: pip install nest_asyncio")
        return 1
    
    # Create the agent
    try:
        logger.info("Creating agent...")
        agent = create_agent()
        
        # Check if agent has tools
        logger.info(f"Agent created with {len(agent.tools)} tools")
        
        # Get all tool names
        tool_names = []
        for tool in agent.tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(type(tool)))
                
        logger.info(f"Tool names: {', '.join(tool_names)}")
        
        # Look for fileserver tools
        fs_tools = [t for t in tool_names if t in ['list_files', 'read_file', 'get_file_info']]
        logger.info(f"Found {len(fs_tools)} fileserver tools: {fs_tools}")
        
        # Check if fileserver tools exist
        if not fs_tools:
            logger.error("❌ No fileserver tools found in the agent")
            return 1
        else:
            print(f"✅ Found {len(fs_tools)} MCP fileserver tools in the agent")
            return 0
            
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())