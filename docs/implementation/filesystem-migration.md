# Migrating from MCP Fileserver to Direct Filesystem Access

This guide describes how to migrate existing code from the MCP fileserver implementation to the new direct filesystem access implementation.

## Overview

The MCP fileserver implementation had several disadvantages:
- Required managing a separate MCP server process
- Complicated error handling due to process management
- Had threading and async context limitations
- Performance overhead from inter-process communication

The new direct filesystem implementation addresses these issues by:
- Eliminating the need for a separate server process
- Providing a cleaner, more reliable API
- Using native Python standard library functions for better performance
- Supporting both synchronous and asynchronous contexts

## Migration Steps

### 1. Update Imports

**Old MCP-based implementation:**
```python
from radbot.tools.mcp.mcp_fileserver_client import create_fileserver_toolset
# or async version:
from radbot.tools.mcp.mcp_fileserver_client import create_fileserver_toolset_async
```

**New direct implementation:**
```python
# For compatibility with previous environment variables and API:
from radbot.filesystem.adapter import create_fileserver_toolset

# OR for more control:
from radbot.filesystem.integration import create_filesystem_tools
```

### 2. Tool Creation

**Old MCP-based implementation:**
```python
# Synchronous:
fs_tools = create_fileserver_toolset()

# Asynchronous:
fs_tools, exit_stack = await create_fileserver_toolset_async()
# Remember to cleanup: await exit_stack.aclose()
```

**New direct implementation:**
```python
# Using compatibility adapter (maintains environment variable behavior):
fs_tools = create_fileserver_toolset()

# OR using direct integration with more control:
fs_tools = create_filesystem_tools(
    allowed_directories=["/path/to/directory"],
    enable_write=True,
    enable_delete=False
)
```

### 3. Environment Variables

Both implementations support the same environment variables, so you can keep using them:

- `MCP_FS_ROOT_DIR`: Root directory for filesystem access (default: home directory)
- `MCP_FS_ALLOW_WRITE`: Set to "true" to enable write operations (default: "false")
- `MCP_FS_ALLOW_DELETE`: Set to "true" to enable delete operations (default: "false")

### 4. Available Tools

All tools from the previous implementation remain available, though the internal implementation has changed:

- `read_file`: Read the contents of a file
- `write_file`: Write content to a file (if write operations enabled)
- `list_directory`: List files and directories in a path
- `get_file_info`: Get information about a file or directory
- `copy`: Copy a file or directory (if write operations enabled)
- `delete`: Delete a file or directory (if delete operations enabled)
- `edit_file`: Edit a file by applying text replacements (if write operations enabled)
- `search`: Search for files or directories matching a pattern (new tool!)

### 5. Error Handling

The new implementation provides more consistent error handling:

- `PermissionError`: Raised when attempting to access a path outside allowed directories or perform a disallowed operation
- `FileNotFoundError`: Raised when a path doesn't exist
- `FileExistsError`: Raised when attempting to create a file that already exists without overwrite permission
- `ValueError`: Raised for invalid arguments or operations
- `IOError`: Raised for general I/O errors

### 6. Direct API Access

You can now also access the filesystem operations directly if needed:

```python
from radbot.filesystem.tools import read_file, write_file, list_directory
from radbot.filesystem.security import set_allowed_directories

# Configure security
set_allowed_directories(["/path/to/directory"])

# Use operations directly
content = read_file("/path/to/directory/file.txt")
files = list_directory("/path/to/directory")
```

### 7. Using the Edit File Tool

The edit_file tool provides a powerful way to make targeted changes to files. It works by specifying "oldText" and "newText" pairs:

```python
edits = [
    {"oldText": "Line to replace", "newText": "New line content"},
    {"oldText": "Another part to change", "newText": "Updated content"}
]

diff = edit_file("/path/to/file.txt", edits)
print(diff)  # Shows a unified diff of the changes
```

You can also use dry_run=True to preview changes without applying them:

```python
diff = edit_file("/path/to/file.txt", edits, dry_run=True)
```

### 8. Example Migration

**Old MCP-based code:**
```python
from radbot.tools.mcp.mcp_fileserver_client import create_fileserver_toolset

# Get filesystem tools
fs_tools = create_fileserver_toolset()

# Add tools to agent
agent = Agent(
    tools=fs_tools,
    system_prompt="You are a helpful assistant with filesystem access.",
    model="gemini-1.5-pro"
)
```

**Migrated code:**
```python
from radbot.filesystem.adapter import create_fileserver_toolset

# Get filesystem tools (same function name, different implementation)
fs_tools = create_fileserver_toolset()

# Add tools to agent (unchanged)
agent = Agent(
    tools=fs_tools,
    system_prompt="You are a helpful assistant with filesystem access.",
    model="gemini-1.5-pro"
)
```

## Troubleshooting

### Common Issues

1. **"No allowed directories configured" error**
   - Solution: Ensure you've set allowed directories with `set_allowed_directories(["/path/to/dir"])` or use the compatibility adapter

2. **Missing tools**
   - Solution: Check that write/delete operations are enabled if you need those tools

3. **PermissionError when accessing a path**
   - Solution: Ensure the path is within an allowed directory

4. **Type annotation error with `Optional[List[str]]`**
   - Solution: This has been fixed in the implementation. If you're creating custom tools using the filesystem functions, make sure to use `Optional[List[str]]` instead of `List[str] = None` for optional list parameters

## Conclusion

The migration to direct filesystem access should be straightforward in most cases. The compatibility adapter provides backward compatibility with the MCP fileserver API while offering better reliability and performance.

For new code, we recommend using the direct integration API through `radbot.filesystem.integration.create_filesystem_tools` for more explicit control over allowed directories and permissions.
