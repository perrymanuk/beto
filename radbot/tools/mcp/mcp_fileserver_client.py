import asyncio
import atexit
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, AsyncExitStack
from functools import partial
from threading import Thread, RLock, local
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Import from ADK 0.3.0 locations
from google.adk.events import Event
from google.adk.tools import FunctionTool
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import Tool as MCPTool

from radbot.tools.mcp.mcp_fileserver_server import (
    start_server,
    start_server_async,
)


logger = logging.getLogger(__name__)

_global_exit_stack: Optional[AsyncExitStack] = None
_global_lock = RLock()
_thread_local = local()


def cleanup_fileserver_sync() -> None:
    """Cleanup function to be called on exit.
    Properly closes the MCP server and any associated resources.
    """
    global _global_exit_stack

    logger.info("Cleaning up MCP fileserver resources")
    
    # Handle global exit stack
    if _global_exit_stack is not None:
        try:
            # Close the AsyncExitStack synchronously
            asyncio.run(_global_exit_stack.aclose())
            logger.info("Closed global exit stack")
        except Exception as e:
            logger.warning(f"Error closing global exit stack: {e}")
        finally:
            _global_exit_stack = None
    
    # Handle thread-local exit stacks
    if hasattr(_thread_local, 'mcp_exit_stacks'):
        for thread_id, exit_stack in _thread_local.mcp_exit_stacks.items():
            try:
                asyncio.run(exit_stack.aclose())
                logger.info(f"Closed thread-local exit stack for thread {thread_id}")
            except Exception as e:
                logger.warning(f"Error closing thread-local exit stack for thread {thread_id}: {e}")
    
    logger.info("MCP fileserver cleanup completed")


def get_mcp_fileserver_config() -> Tuple[str, bool, bool]:
    """Get the MCP fileserver configuration from environment variables."""
    root_dir = os.environ.get("MCP_FS_ROOT_DIR", os.path.expanduser("~"))
    allow_write = os.environ.get("MCP_FS_ALLOW_WRITE", "false").lower() == "true"
    allow_delete = os.environ.get("MCP_FS_ALLOW_DELETE", "false").lower() == "true"
    logger.info(
        f"MCP Fileserver Config: root_dir={root_dir}, allow_write={allow_write}, allow_delete={allow_delete}"
    )
    return root_dir, allow_write, allow_delete


async def _create_fileserver_toolset_async() -> List[FunctionTool]:
    """Create the MCP fileserver toolset asynchronously."""
    global _global_exit_stack
    
    root_dir, allow_write, allow_delete = get_mcp_fileserver_config()
    
    # Initialize thread-local storage if not already done
    if not hasattr(_thread_local, 'mcp_exit_stacks'):
        _thread_local.mcp_exit_stacks = {}
    
    # Create an AsyncExitStack to manage resources
    exit_stack = AsyncExitStack()
    current_thread_id = threading.get_ident()
    _thread_local.mcp_exit_stacks[current_thread_id] = exit_stack
    
    try:
        # Start the server and get the tools
        server_process = await start_server_async(
            exit_stack, root_dir, allow_write, allow_delete
        )
        
        # Create and initialize the client session
        client_transport = await exit_stack.enter_async_context(stdio_client(StdioServerParameters(command='python')))
        client = await exit_stack.enter_async_context(ClientSession(*client_transport))
        await client.initialize()
        
        # Set the global exit stack for cleanup if needed
        with _global_lock:
            if _global_exit_stack is None:
                _global_exit_stack = exit_stack
        
        # Convert MCP tools to FunctionTool
        tools = []
        for tool in await client.list_tools():
            if isinstance(tool, MCPTool):
                tools.append(
                    FunctionTool(
                        name=tool.name,
                        description=tool.description,
                        parameters=tool.parameters_schema,
                    )
                )
        
        logger.info(f"Successfully created MCP fileserver toolset with {len(tools)} tools")
        return tools
    except Exception as e:
        # Clean up if there's an error
        logger.error(f"Error creating MCP fileserver toolset: {e}")
        await exit_stack.aclose()
        _thread_local.mcp_exit_stacks.pop(current_thread_id, None)
        raise


def run_async_in_thread(coro):
    """Run an asynchronous coroutine in a separate thread."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


def create_fileserver_toolset() -> List[FunctionTool]:
    """Create the MCP fileserver toolset."""
    try:
        # Special debug for when we're already in an event loop
        try:
            asyncio.get_running_loop()
            logger.warning("SPECIAL DEBUG: Running in existing event loop, cannot create fileserver in async context")
            logger.warning("This likely means you're using this in an async context")
            # Run in a separate thread to avoid event loop conflicts
            return run_async_in_thread(_create_fileserver_toolset_async())
        except RuntimeError:
            # No event loop running, we can create our own
            return asyncio.run(_create_fileserver_toolset_async())
    except Exception as e:
        logger.warning(f"Cannot create fileserver toolset: {e}")
        # Return empty list as fallback
        return []


async def _handle_fileserver_tool_call_async(tool_name: str, params: Dict[str, Any]) -> Event:
    """Handle a fileserver tool call asynchronously."""
    try:
        # Get thread-local exit stack or create a new one
        current_thread_id = threading.get_ident()
        if (
            not hasattr(_thread_local, 'mcp_exit_stacks') or 
            current_thread_id not in _thread_local.mcp_exit_stacks
        ):
            # Initialize thread-local storage if not already done
            if not hasattr(_thread_local, 'mcp_exit_stacks'):
                _thread_local.mcp_exit_stacks = {}
            
            # Create an AsyncExitStack to manage resources
            exit_stack = AsyncExitStack()
            _thread_local.mcp_exit_stacks[current_thread_id] = exit_stack
            
            # Start the server
            root_dir, allow_write, allow_delete = get_mcp_fileserver_config()
            await start_server_async(exit_stack, root_dir, allow_write, allow_delete)
        else:
            exit_stack = _thread_local.mcp_exit_stacks[current_thread_id]
        
        # Create and initialize the client session
        client_transport = await exit_stack.enter_async_context(stdio_client(StdioServerParameters(command='python')))
        async with ClientSession(*client_transport) as client:
            # Initialize the client
            await client.initialize()
            
            # Call the tool
            response = await client.call_tool(tool_name, params)
            
            # ADK 0.3.0 - Create a proper Event with function_response
            return Event(
                function_call_event={"name": tool_name, "response": response}
            )
    except Exception as e:
        logger.error(f"Error handling fileserver tool call: {e}")
        return Event(
            function_call_event={"name": tool_name, "error": f"Error handling fileserver tool call: {e}"}
        )


def handle_fileserver_tool_call(tool_name: str, params: Dict[str, Any]) -> Event:
    """Handle a fileserver tool call."""
    try:
        # Check if we're already in an event loop
        try:
            asyncio.get_running_loop()
            # Run in a separate thread to avoid event loop conflicts
            return run_async_in_thread(
                partial(_handle_fileserver_tool_call_async, tool_name, params)
            )
        except RuntimeError:
            # No event loop running, we can create our own
            return asyncio.run(_handle_fileserver_tool_call_async(tool_name, params))
    except Exception as e:
        logger.error(f"Error handling fileserver tool call: {e}")
        return Event(
            function_call_event={"name": tool_name, "error": f"Error handling fileserver tool call: {e}"}
        )


# Register the cleanup function to be called on exit
atexit.register(cleanup_fileserver_sync)
