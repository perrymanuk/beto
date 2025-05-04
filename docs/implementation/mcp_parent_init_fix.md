# MCP Parent __init__.py Fix

## Issue

After fixing the imports in the MCP package's `__init__.py`, we encountered another error when importing from the parent package:

```
cannot import name 'MCPFileServer' from 'radbot.tools.mcp' (/Users/perry.manuk/git/perrymanuk/radbot/radbot/tools/mcp/__init__.py)
```

## Root Cause

The parent tools package's `__init__.py` file was still attempting to re-export `MCPFileServer` from the MCP subpackage. However, we had renamed this class to `FileServerMCP` in our earlier fixes.

Specifically, in `/Users/perry.manuk/git/perrymanuk/radbot/radbot/tools/__init__.py`, the import statement was still referencing the old class name:

```python
from radbot.tools.mcp import (
    create_fileserver_toolset,
    MCPFileServer,  # This name no longer exists
    get_available_mcp_tools,
    convert_to_adk_tool,
)
```

The `__all__` list also included the old name:

```python
__all__ = [
    # ...
    # MCP tools
    "create_fileserver_toolset",
    "MCPFileServer",  # This name no longer exists
    "get_available_mcp_tools", 
    "convert_to_adk_tool",
    # ...
]
```

## Solution

Updated the parent tools package's `__init__.py` file to use the correct class name:

1. Updated the import statement:
```python
from radbot.tools.mcp import (
    create_fileserver_toolset,
    FileServerMCP,  # Using correct class name
    get_available_mcp_tools,
    convert_to_adk_tool,
)
```

2. Updated the `__all__` list:
```python
__all__ = [
    # ...
    # MCP tools
    "create_fileserver_toolset",
    "FileServerMCP",  # Using correct class name
    "get_available_mcp_tools", 
    "convert_to_adk_tool",
    # ...
]
```

## Lessons Learned

When refactoring code and renaming classes:

1. Use search tools to find all references to the class name throughout the codebase
2. Remember to check not just direct imports, but also re-exports in package `__init__.py` files
3. Check both import statements and `__all__` declarations in package files
4. Consider using automated refactoring tools or IDEs that can automatically update all references when renaming 

This fix completes the series of changes needed to resolve the import errors with the MCP modules after code restructuring.
