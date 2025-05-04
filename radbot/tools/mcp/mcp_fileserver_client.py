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
import atexit
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
    
    # Log configuration
    if root_dir:
        logger.info(f"MCP Fileserver Config: root_dir={root_dir}, allow_write={allow_write}, allow_delete={allow_delete}")
    else:
        logger.info("MCP Fileserver Config: root_dir not set (MCP_FS_ROOT_DIR environment variable not found)")
    
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

# Global variable to hold the exit stack so it doesn't get garbage collected
_global_exit_stack = None

def create_fileserver_toolset() -> Optional[List]:
    """
    Create an MCPToolset for connecting to the MCP fileserver.
    
    This function is a synchronous wrapper around create_fileserver_toolset_async.
    It handles both cases: when called from a synchronous context and when called
    from within an existing event loop.
    
    Returns:
        List: The list of MCP fileserver tools, or None if configuration fails
    """
    global _global_exit_stack
    
    print("SPECIAL DEBUG: Inside create_fileserver_toolset()")
    
    # Log current environment variables
    root_dir = os.environ.get("MCP_FS_ROOT_DIR")
    print(f"SPECIAL DEBUG: MCP_FS_ROOT_DIR={root_dir}")
    
    # Check if we're running in an event loop
    try:
        loop = asyncio.get_running_loop()
        print("SPECIAL DEBUG: Running in existing event loop, cannot create fileserver in async context")
        logger.warning("Cannot create fileserver toolset: Event loop is already running")
        logger.warning("This likely means you're using this in an async context")
        logger.warning("Using simplified mock fileserver tools")
        
        # Return a list of mock tools for compatibility
        # These tools will just return informative error messages
        from google.adk.tools import FunctionTool
        
        def mock_list_files(path: str = "."):
            """Mock implementation that explains why real tools aren't available."""
            return {
                "success": False,
                "error": "MCP Fileserver unavailable in async context",
                "message": "The MCP Fileserver cannot be initialized within an async context like the CLI's setup_agent. "
                           "Use make run-web for full fileserver functionality."
            }
            
        mock_tools = [
            FunctionTool(
                function=mock_list_files,
                function_schema={
                    "name": "list_files",
                    "description": "Mock list_files function - fileserver unavailable in async context",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to list files from"
                            }
                        }
                    }
                }
            )
        ]
        
        return mock_tools
        
    except RuntimeError:
        # Not in an event loop, we can create our own
        print("SPECIAL DEBUG: Not running in an event loop, creating a new one")
        logger.info("Not running in an event loop, creating a new one")
        # Run in a new asyncio event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If there is no event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        print("SPECIAL DEBUG: About to call loop.run_until_complete(create_fileserver_toolset_async())")
        tools, exit_stack = loop.run_until_complete(create_fileserver_toolset_async())
    
    # Check if we got valid tools and exit_stack
    if tools is None or exit_stack is None:
        logger.warning("Failed to create MCP fileserver tools or exit stack")
        return None
    
    # Store the exit stack in the global variable to keep the server alive
    _global_exit_stack = exit_stack
    logger.info(f"Stored MCP fileserver exit stack in global variable, {len(tools)} tools created")
    
    # Return the tools directly
    return tools

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
    # (this will also store the exit stack in the global variable)
    toolset = create_fileserver_toolset()
    
    if not toolset:
        return {
            "success": False,
            "status": "initialization_failed",
            "error": "Failed to create MCP fileserver toolset",
            "details": None
        }
    
    # Check if global exit stack was properly set
    if _global_exit_stack is None:
        logger.warning("MCP fileserver exit stack was not properly stored")
        # This shouldn't happen but let's handle it anyway
    
    # Try to list tools
    try:
        # toolset is now directly the list of tools
        tools = toolset
        
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

async def cleanup_fileserver():
    """Clean up the MCP fileserver connection."""
    global _global_exit_stack
    
    if _global_exit_stack is not None:
        logger.info("Closing MCP fileserver connection...")
        try:
            await _global_exit_stack.aclose()
            logger.info("MCP fileserver connection closed")
        except Exception as e:
            logger.error(f"Error closing MCP fileserver connection: {str(e)}")
        finally:
            _global_exit_stack = None
    else:
        logger.info("No active MCP fileserver connection to close")

def cleanup_fileserver_sync():
    """Synchronous version of cleanup_fileserver."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(cleanup_fileserver())

# Register cleanup function to run on exit
atexit.register(cleanup_fileserver_sync)

if __name__ == "__main__":
    sys.exit(main())
