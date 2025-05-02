#!/usr/bin/env python3
"""
MCP Fileserver Client

This module provides utilities for connecting to the MCP fileserver from
within the radbot framework.
"""

import os
import sys
import logging
import asyncio
import contextlib
from typing import Dict, Any, List, Optional, Tuple

from dotenv import load_dotenv
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_fileserver_config() -> Tuple[Optional[str], bool, bool]:
    """
    Get MCP fileserver configuration from environment variables.
    
    Returns:
        Tuple of (root_dir, allow_write, allow_delete)
    """
    # Get environment variables
    root_dir = os.getenv("MCP_FS_ROOT_DIR")
    allow_write_str = os.getenv("MCP_FS_ALLOW_WRITE", "false").lower()
    allow_delete_str = os.getenv("MCP_FS_ALLOW_DELETE", "false").lower()
    
    # Convert to boolean
    allow_write = allow_write_str in ("true", "yes", "1", "t", "y")
    allow_delete = allow_delete_str in ("true", "yes", "1", "t", "y")
    
    return root_dir, allow_write, allow_delete

async def create_fileserver_toolset_async() -> Tuple[Optional[List], Optional[contextlib.AsyncExitStack]]:
    """
    Create an MCPToolset for connecting to the MCP fileserver.
    
    Returns:
        Tuple of (tools, exit_stack)
    """
    try:
        # Get configuration
        root_dir, allow_write, allow_delete = get_fileserver_config()
        
        if not root_dir:
            logger.error("MCP fileserver root directory not configured. "
                         "Please set MCP_FS_ROOT_DIR environment variable.")
            return None, None
        
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get the path to the MCP fileserver server script
        server_script = os.path.join(script_dir, "mcp_fileserver_server.py")
        
        # Check if the server script exists
        if not os.path.exists(server_script):
            logger.error(f"MCP fileserver server script not found: {server_script}")
            return None, None
        
        # Configure the parameters for the MCP fileserver
        cmd_args = [
            server_script,
            root_dir
        ]
        
        # Add optional arguments
        if allow_write:
            cmd_args.append("--allow-write")
        if allow_delete:
            cmd_args.append("--allow-delete")
        
        # Create the MCPToolset
        tools, exit_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command='python3',
                args=cmd_args,
            )
        )
        
        logger.info(f"Successfully created MCP fileserver toolset with {len(tools)} tools")
        return tools, exit_stack
        
    except Exception as e:
        logger.error(f"Failed to create MCP fileserver toolset: {str(e)}")
        return None, None

def create_fileserver_toolset() -> Optional[MCPToolset]:
    """
    Create an MCPToolset for connecting to the MCP fileserver.
    
    This function is a synchronous wrapper around create_fileserver_toolset_async.
    
    Returns:
        MCPToolset: The configured MCP fileserver toolset, or None if configuration fails
    """
    # Run in an asyncio event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # If there is no event loop, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    tools, exit_stack = loop.run_until_complete(create_fileserver_toolset_async())
    
    if tools is None or exit_stack is None:
        return None
    
    # Create an MCPToolset
    return MCPToolset(
        tools=tools,
        exit_stack=exit_stack
    )

def test_fileserver_connection() -> Dict[str, Any]:
    """
    Test the connection to the MCP fileserver.
    
    Returns:
        Dictionary with the test results and information
    """
    # Get configuration
    root_dir, allow_write, allow_delete = get_fileserver_config()
    
    if not root_dir:
        return {
            "success": False,
            "status": "not_configured",
            "error": "MCP fileserver root directory not configured. "
                     "Please set MCP_FS_ROOT_DIR environment variable.",
            "details": None
        }
    
    # Initialize the fileserver MCP
    toolset = create_fileserver_toolset()
    
    if not toolset:
        return {
            "success": False,
            "status": "initialization_failed",
            "error": "Failed to create MCP fileserver toolset",
            "details": None
        }
    
    # Try to list tools
    try:
        tools = toolset.tools
        
        return {
            "success": True,
            "status": "connected",
            "tools_count": len(tools),
            "root_dir": root_dir,
            "allow_write": allow_write,
            "allow_delete": allow_delete
        }
    except Exception as e:
        return {
            "success": False,
            "status": "connection_error",
            "error": str(e),
            "details": None
        }

def main():
    """Command line entry point."""
    print("MCP Fileserver Client Test\n")
    
    # Test the connection
    result = test_fileserver_connection()
    
    if result["success"]:
        print(f"✅ Connection successful!")
        print(f"Root directory: {result.get('root_dir')}")
        print(f"Allow write: {result.get('allow_write')}")
        print(f"Allow delete: {result.get('allow_delete')}")
        print(f"Tools count: {result.get('tools_count')}")
    else:
        print(f"❌ Connection failed!")
        print(f"Status: {result.get('status')}")
        print(f"Error: {result.get('error')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
