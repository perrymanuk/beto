# MCP Fileserver Import Error Fix

## Issue

After restructuring the tools into their own folders, an import error occurred when trying to use the MCP Fileserver functionality:

```
cannot import name 'MCPFileServer' from 'radbot.tools.mcp.mcp_fileserver_server' (/Users/perry.manuk/git/perrymanuk/radbot/radbot/tools/mcp/mcp_fileserver_server.py)
```

## Root Cause

There was a name mismatch between the class referenced in the `radbot/tools/mcp/__init__.py` and the actual implementation in `mcp_fileserver_server.py`:

1. The `__init__.py` file was trying to import a class called `MCPFileServer` 
2. The actual class in the `mcp_fileserver_server.py` file was named `FileServerMCP`

## Solution

The issue was fixed by updating the `__init__.py` file to import the correct class name:

```python
# Before
from radbot.tools.mcp.mcp_fileserver_server import MCPFileServer

# After
from radbot.tools.mcp.mcp_fileserver_server import FileServerMCP
```

Similarly, the `__all__` list was updated to reference the correct class name.

## Potential Additional Improvements

If maintaining backward compatibility is important, another approach would be to keep the original import name by adding an alias in the `mcp_fileserver_server.py` file:

```python
# At the end of mcp_fileserver_server.py
MCPFileServer = FileServerMCP  # Alias for backward compatibility
```

But for clean code, it's better to use the correct class name throughout the codebase.

## Lessons Learned

When restructuring code:
1. Ensure consistent class/function naming across modules
2. Check all imports and references after moving files
3. Consider using find/grep tools to identify all references to renamed elements
