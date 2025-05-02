# MCP Fileserver Integration

This document details the implementation of a Model Context Protocol (MCP) fileserver for the radbot agent framework.

## MCP Fileserver Architecture

The integration consists of several key components:

1. **MCP Server Setup**: A Python script that runs as an MCP server providing filesystem operations
2. **MCP Client Configuration**: Setup for connecting to the MCP fileserver
3. **MCPToolset Integration**: Integration with ADK's built-in MCP tooling
4. **Error Handling & Security**: Robust error handling and security considerations

## MCP Fileserver Implementation

### MCP Fileserver Server Script (`radbot/tools/mcp_fileserver_server.py`)

This script implements a standalone MCP server that provides filesystem operations. It uses the `model-context-protocol` library (version 1.7.0+) to create an MCP server and exposes filesystem operations as tools.

Key features:
- Runs as a standalone process
- Exposes filesystem operations as MCP tools (list_files, read_file, write_file, etc.)
- Configurable root directory for security 
- Compatible with MCP SDK version 1.7.0+

### MCP Fileserver Client Integration (`radbot/tools/mcp_fileserver_client.py`)

This module provides utilities for connecting to the MCP fileserver from within the radbot framework.

Key features:
- Creates an MCPToolset for connecting to the MCP fileserver
- Configurable through environment variables
- Error handling and logging

## Tool Operations

The MCP fileserver provides the following operations:

1. **List Files**: List files and directories in a specified path
2. **Read File**: Read the contents of a file
3. **Write File**: Write content to a file
4. **Delete File**: Delete a file or directory
5. **Copy File**: Copy a file or directory
6. **Move/Rename File**: Move or rename a file or directory
7. **Get File Info**: Get information about a file or directory

## Integration with Agent Configuration

To add the MCP fileserver tools to an agent:

```python
from radbot.tools.mcp_fileserver_client import create_fileserver_toolset

# Create basic tools list
tools = [get_current_time, get_weather]

# Add MCP Fileserver tools
try:
    fs_tools = create_fileserver_toolset()
    if fs_tools:
        # fs_tools is a list of tools, so extend basic_tools with it
        tools.extend(fs_tools)
        logger.info(f"Successfully added {len(fs_tools)} MCP fileserver tools")
    else:
        logger.warning("MCP fileserver tools not available")
except Exception as e:
    logger.warning(f"Failed to create MCP fileserver tools: {str(e)}")

# Create the agent with tools
agent = Agent(
    name="radbot_web",
    model="gemini-2.5-pro",
    instruction=instruction,
    tools=tools
)
```

The `create_fileserver_toolset()` function returns a list of individual MCP fileserver tools rather than an MCPToolset object. This list should be extended into your tools list.

### Lifecycle Management

The MCP fileserver client includes automatic cleanup to ensure that the server process is properly terminated when your application exits:

```python
# Global variable to hold the exit stack
_global_exit_stack = None

# Register cleanup function to run on exit
atexit.register(cleanup_fileserver_sync)
```

## MCP Fileserver Configuration

### Environment Variables

Set these variables in your `.env` file:

```
# MCP Fileserver Configuration
MCP_FS_ROOT_DIR=/path/to/root/directory   # Root directory for filesystem operations
MCP_FS_ALLOW_WRITE=true                   # Allow write operations (default: false)
MCP_FS_ALLOW_DELETE=false                 # Allow delete operations (default: false)
```

### Security Considerations

1. **Root Directory**: The MCP fileserver only allows access to files within the configured root directory
2. **Write Protection**: By default, write operations are disabled
3. **Delete Protection**: By default, delete operations are disabled
4. **Error Handling**: Robust error handling to prevent security issues

## Starting the MCP Fileserver

### Command Line

To start the MCP fileserver server from the command line:

```bash
python -m radbot.tools.mcp_fileserver_server /path/to/root/directory
```

### Programmatically

To start the MCP fileserver server programmatically:

```python
from radbot.tools.mcp_fileserver_server import start_server

# Start the server
start_server(root_dir="/path/to/root/directory")
```

## Agent Instructions for MCP Fileserver Tools

The agent needs to be instructed on how to use the MCP fileserver tools. Add the following to the agent's instruction:

```
You can access the filesystem through the MCP fileserver tools. Here are some examples:

- To list files: Use the fileserver_mcp.list_files tool with the path parameter
- To read a file: Use the fileserver_mcp.read_file tool with the path parameter
- To write to a file: Use the fileserver_mcp.write_file tool with the path and content parameters

Always tell the user what action you're taking, and report back the results. If a filesystem operation fails, inform the user politely about the issue.
```

## Error Handling

The MCP fileserver provides detailed error messages for common issues:
- File not found
- Permission denied
- Invalid path (outside root directory)
- Invalid operation (e.g., writing to a directory)

## Testing

The MCP fileserver includes utilities for testing the connection and operations.

## MCP Version Compatibility

The MCP fileserver has been updated to work with MCP SDK version 1.7.0+. Key compatibility changes include:

1. **Tool Schema Changes**: 
   - Changed `parameters` to `inputSchema` for tool definitions
   - Using JSON schema format for input parameters
   - Properly specified required parameters in the schema

2. **Response Format Changes**:
   - All responses use `TextContent` with required `type="text"` field
   - Return value handling through the `.contents[0].text` property in client code

3. **Proper Error Handling**:
   - Exceptions are re-raised instead of returning ErrorContent objects
   - Error types are encoded in the exception message

4. **MCPToolset API Changes**:
   - Return individual tools from `create_fileserver_toolset()` instead of an MCPToolset object
   - Properly manage lifecycle with global exit stack
   - Added automatic cleanup using atexit handler
   - Added proper error handling for AsyncExitStack management

## Next Steps

1. Add more filesystem operations (e.g., file search, file compression)
2. Implement caching to improve performance
3. Add more security features (e.g., file type restrictions, size limits)
4. Consider adding support for binary file operations
