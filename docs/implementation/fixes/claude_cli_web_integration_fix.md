# Claude CLI Web Integration Fix

## Issue Description

The Claude CLI MCP server integration was not working correctly with the web interface. Specifically, the tools provided by the Claude CLI MCP server were not being properly attached to the agent in the web interface. This resulted in a warning message:

```
Unsupported transport 'stdio' for MCP server Claude CLI MCP Server
```

Additionally, when trying to use the MCP client approach, we encountered issues with the stdio transport:

```
Error in stdio_client: '_io.FileIO' object has no attribute 'command'
```

Later, we also discovered that our direct approach was using an incorrect command format:

```
Error: unknown command 'run'
```

## Root Cause Analysis

The issue had several components:

1. In the `_try_load_mcp_tools` method of the `SessionRunner` class in `/radbot/web/api/session.py`, the method handled SSE transport correctly, but for the stdio transport (used by Claude CLI), it attempted to use the MCP client directly to get tools, which didn't work properly.

2. The MCP stdio client implementation was using the `stdio_client` function from the MCP SDK incorrectly. The function expects a `StdioServerParameters` object, but we were passing file objects directly.

3. The direct command execution approach was using an incorrect command format with "run" and "tool" subcommands that don't exist in the Claude CLI.

## Solution

Our solution involved a multi-layered approach:

### 1. Create a Direct CLI Execution Alternative

We implemented a more reliable direct approach in `direct_claude_cli.py` that bypasses the MCP client entirely, using the correct Claude CLI command format:

```python
def execute_command_directly(command: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
    # Get claude CLI config
    config = get_claude_cli_config()
    
    # Get claude command and arguments - use the correct format
    claude_command = config.get("command", "claude")
    # Use direct command with --print to get non-interactive output
    claude_args = ["--print", "--output-format", "json", f"Execute this command: {command}"]
    
    # Execute the command
    process = subprocess.Popen(
        [claude_command] + claude_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=working_dir or config.get("working_directory", os.getcwd()),
        text=True
    )
    
    # Process the results
    stdout, stderr = process.communicate(timeout=60)
    # ...parse results and return
```

### 2. Fix the Original MCP Client Approach

We fixed the stdio client implementation to properly create an MCP session:

```python
# Wrap the file objects for use with async I/O
stdin_stream = wrap_file(self.process.stdin, mode="wb")
stdout_stream = wrap_file(self.process.stdout, mode="rb")

# Create JSON-RPC client for communication
json_rpc_client = JsonRpcBase(stdin_stream, stdout_stream)

# Create a client session directly
from mcp import ClientSession
self.session = ClientSession(json_rpc_client)
```

### 3. Implement a Fallback Strategy in the Web Interface

We modified the web interface to try multiple approaches in sequence:

1. First, try the direct CLI execution approach
2. If that fails, try the regular Claude CLI tools module
3. If that fails, fall back to the MCP client factory

This ensures that at least one method will work for attaching the tools.

### 4. Add Better Error Handling and Logging

We improved error handling and added detailed logging to help diagnose issues:

```python
except Exception as e:
    logger.error(f"Error in stdio_client: {e}")
    # Log more detailed error information
    import traceback
    logger.error(f"Detailed error: {traceback.format_exc()}")
```

## Testing

The fix was extensively tested with the following steps:

1. Manual testing of both approaches (direct and MCP client) with simple commands
2. Running the example script to confirm direct Claude CLI integration
3. Starting the web server and verifying that the Claude CLI tools are properly attached to the agent
4. Testing command execution through the web interface

## Results

After implementing the fix:
- The warning message no longer appears
- Claude CLI tools are properly attached to the agent in the web interface
- Commands can be successfully executed through the Claude CLI backend
- The direct approach now uses the correct Claude CLI command format with `--print` and `--output-format json` options
- The system is more robust, automatically falling back to alternative approaches if one fails
- Both file operations and command execution work consistently

## Related Files

- `/radbot/web/api/session.py` - Modified to use a fallback strategy for stdio transport
- `/radbot/tools/mcp/mcp_stdio_client.py` - Fixed to properly create an MCP session
- `/radbot/tools/mcp/direct_claude_cli.py` - Created new direct approach implementation with correct command format
- `/radbot/tools/mcp/claude_cli.py` - Fixed function call bugs
- `/radbot/tools/shell/shell_tool.py` - Updated to try direct approach first, then fall back
- `/examples/claude_cli_agent.py` - Created new example
- `/tools/test_claude_cli_web.py` - Created test script for web interface integration
- `/tools/test_claude_cli_direct.py` - Created test script for direct command execution
- `/tools/verify_claude_cli_direct.py` - Created verification script for the command format fix
- `/docs/implementation/tools/claude-cli.md` - Updated documentation with both approaches