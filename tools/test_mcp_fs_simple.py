#!/usr/bin/env python3
"""
Simple test for MCP fileserver initialization.
"""

import os
import sys
import logging
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import fileserver client
from radbot.tools.mcp_fileserver_client import create_fileserver_toolset

def main():
    """Test MCP fileserver toolset creation."""
    # Check if MCP_FS_ROOT_DIR is set
    root_dir = os.environ.get("MCP_FS_ROOT_DIR")
    if not root_dir:
        logger.error("MCP_FS_ROOT_DIR environment variable is not set")
        return 1
    
    logger.info(f"MCP_FS_ROOT_DIR: {root_dir}")
    
    # Create the MCP fileserver toolset
    try:
        fs_tools = create_fileserver_toolset()
        
        if fs_tools:
            # Log detailed information about each fileserver tool
            logger.info(f"FileServerMCP returned {len(fs_tools)} tools")
            for i, tool in enumerate(fs_tools):
                tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                tool_type = type(tool).__name__
                logger.info(f"  Tool {i+1}: {tool_name} (type: {tool_type})")
            
            print(f"✅ Successfully created {len(fs_tools)} MCP fileserver tools")
            return 0
        else:
            logger.error("MCP fileserver tools not available (returned None)")
            print("❌ Failed to create MCP fileserver tools")
            return 1
    except Exception as e:
        logger.error(f"Error creating MCP fileserver tools: {str(e)}", exc_info=True)
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())