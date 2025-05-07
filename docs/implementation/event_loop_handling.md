# Event Loop Handling in RadBot

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


## Overview

The RadBot application uses asyncio event loops for asynchronous operations, particularly with the Google ADK and MCP (Model Context Protocol) server integrations. This document explains how event loops are managed and how to avoid common issues.

## Common Issues

### "Cannot run the event loop while another loop is running"

This error occurs when code attempts to create and run a new event loop within a context where an event loop is already running. This is a common issue when:

- Using `asyncio.run_until_complete()` inside an async function
- Creating a new event loop inside an already-running async context
- Using synchronous wrappers for async functions incorrectly

### "coroutine 'function_name' was never awaited"

This warning indicates that an async function was called without being awaited, meaning that the coroutine object was created but never executed. This can lead to unexpected behavior as the async function's code never actually runs.

## MCP Tools and Event Loops

The Model Context Protocol (MCP) tools, particularly for Home Assistant integration and Fileserver access, use asynchronous functions underneath. There are two key components that need proper event loop handling:

### 1. Home Assistant MCP Tools

The `create_home_assistant_toolset()` function uses an async helper function `_create_home_assistant_toolset_async()` and tries to run it in a new event loop.

### 2. MCP Fileserver Tools

The `create_fileserver_toolset()` function similarly uses an async helper function `create_fileserver_toolset_async()` to initialize the MCP fileserver connection.

### Problem

In asynchronous contexts like the CLI's `setup_agent()` function, which is already running in an event loop, attempting to create another event loop results in the error "Cannot run the event loop while another loop is running".

### Solution

We've implemented specialized handling for both components:

1. **Home Assistant MCP Tools**: The `create_home_assistant_toolset()` function now checks if it's being called within a running event loop, and if so, returns an empty list with a warning message instead of attempting to create a new event loop.

```python
# Check if we're already in an event loop
try:
    existing_loop = asyncio.get_event_loop()
    if existing_loop.is_running():
        logger.warning("Cannot create Home Assistant toolset: Event loop is already running")
        logger.warning("This likely means you're using this in an async context")
        logger.warning("Try using 'await _create_home_assistant_toolset_async()' instead")
        return []
except RuntimeError:
    # No event loop exists, create a new one
    pass
```

2. **MCP Fileserver Tools**: The `create_fileserver_toolset()` function now checks for a running event loop and, if found, returns mock tools that provide informative error messages rather than trying to initialize the real tools.

```python
try:
    loop = asyncio.get_running_loop()
    logger.warning("Cannot create fileserver toolset: Event loop is already running")
    logger.warning("This likely means you're using this in an async context")
    logger.warning("Using simplified mock fileserver tools")
    
    # Return a list of mock tools for compatibility
    # [Mock tool implementation...]
    
    return mock_tools
    
except RuntimeError:
    # Not in an event loop, we can create our own
    # [Original implementation...]
```

3. **Fallback to Legacy or Mock Tools**: In both cases, we provide a fallback mechanism that allows the application to continue functioning, even if with reduced functionality:
   - For Home Assistant, we fall back to using the legacy (non-MCP) Home Assistant integration
   - For the MCP Fileserver, we provide mock tools that explain why the real functionality isn't available

This approach ensures that the CLI can start and function properly, even if some MCP-based functionality is limited compared to the web interface.

## Best Practices

When working with async code in RadBot, follow these guidelines:

1. **Use await for async functions**: Always use `await` with async functions in async contexts.

2. **Check for running event loops**: Before creating a new event loop, check if one is already running.

   ```python
   try:
       loop = asyncio.get_event_loop()
       if loop.is_running():
           # Handle the case where a loop is already running
       else:
           # Use the existing loop
   except RuntimeError:
       # Create a new loop
       loop = asyncio.new_event_loop()
       asyncio.set_event_loop(loop)
   ```

3. **Use event loop explicitly**: When working with event loops, be explicit about which loop you're using.

4. **Close event loops when done**: Always close event loops when you're finished with them to free resources.

   ```python
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   try:
       result = loop.run_until_complete(async_function())
   finally:
       loop.close()
   ```

5. **Consider using asyncio.run()**: For top-level async code, use `asyncio.run()` which handles loop creation and cleanup automatically.

## Debugging Event Loop Issues

If you encounter event loop issues, the following strategies can help:

1. Enable asyncio debug mode:
   ```python
   import asyncio
   asyncio.get_event_loop().set_debug(True)
   ```

2. Log detailed event loop information:
   ```python
   current_loop = asyncio.get_event_loop()
   logger.debug(f"Current event loop: {id(current_loop)}, running: {current_loop.is_running()}")
   ```

3. Use proper exception handling with informative error messages.

By following these practices, you can avoid common event loop issues in the RadBot application.
