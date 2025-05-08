# Claude CLI Integration via MCP

This document outlines the integration of [Claude CLI](https://github.com/anthropics/claude-cli) with RadBot via the Model Context Protocol (MCP).

## Overview

Claude CLI provides a command-line interface to interact with Claude models. It includes an MCP server mode that allows agents to use Claude's tools through a standard protocol. This integration enables RadBot to delegate command execution and other operations to Claude CLI's environment.

## Architecture

The integration is built on the existing MCP client infrastructure, with additional components specific to Claude CLI:

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │
│     RadBot     │────▶│   MCP Client   │────▶│   Claude CLI   │
│     Agent      │     │   Factory      │     │   MCP Server   │
│                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘
                               │                      │
                               ▼                      ▼
                       ┌────────────────┐     ┌────────────────┐
                       │                │     │                │
                       │  Stdio Client  │─────│ Shell Command  │
                       │                │     │   Execution    │
                       └────────────────┘     └────────────────┘
```

Key components:

1. **MCP Stdio Client**: A custom client for communicating with MCP servers via standard input/output streams. This client manages the lifecycle of the Claude CLI process and communicates with it through stdin/stdout.

2. **Claude CLI Module**: Provides high-level functions for executing commands and other operations through Claude CLI's MCP server.

3. **Shell Tool Integration**: Extends the existing shell command execution tool to support using Claude CLI as an alternative backend.

4. **Web Interface Integration**: Ensures that Claude CLI tools are properly attached to agents in the web interface.

## Configuration

The Claude CLI MCP server is configured in the RadBot `config.yaml` file:

```yaml
mcp_servers:
  - id: claude-cli
    name: Claude CLI MCP Server
    enabled: true
    transport: stdio
    command: claude
    args:
      - mcp
      - serve
    working_directory: /path/to/working/directory
    timeout: 60
    security:
      command_allowlist:
        - ls
        - pwd
        - echo
        - cat
        - git
        - python
        - pip
        - uv
    tags:
      - shell
      - command
```

Configuration parameters:

- `id`: Unique identifier for the server (must be "claude-cli")
- `name`: Display name for the server
- `enabled`: Whether the server is enabled
- `transport`: Must be "stdio" for Claude CLI
- `command`: The command to execute (typically "claude")
- `args`: Command arguments (typically ["mcp", "serve"])
- `working_directory`: Working directory for the command
- `timeout`: Request timeout in seconds
- `security.command_allowlist`: List of allowed shell commands (when using strict mode)
- `tags`: Tags for categorizing the server

## Usage

### Using Claude CLI for Shell Command Execution

```python
from radbot.agent.shell_agent_factory import create_shell_agent

# Create a shell agent with Claude CLI backend
agent = create_shell_agent(
    model="gemini-pro",
    base_tools=[],
    instruction_name="main_agent",
    strict_mode=True,  # Only allow-listed commands
    use_claude_cli=True,  # Use Claude CLI backend instead of subprocess
)
```

### Direct API Usage

```python
from radbot.tools.mcp.claude_cli import execute_command_via_claude

# Execute a command via Claude CLI
result = execute_command_via_claude("ls -la")
if result["success"]:
    print(f"Command output: {result['output']}")
else:
    print(f"Error: {result['error']}")
```

### Web Interface Usage

The web interface automatically detects and loads Claude CLI tools when the server is configured in `config.yaml`. No additional configuration is needed.

## Tools Provided

The Claude CLI integration provides the following tools:

1. **Bash Tool**: Executes shell commands using Claude CLI's powerful command execution capabilities.
2. **Read Tool**: Reads files using Claude CLI's file access.
3. **Write Tool**: Writes files using Claude CLI's file access.
4. **Prompt Tool**: Sends prompts directly to Claude's model.

Additionally, RadBot wraps these in higher-level tools:

1. **claude_execute_command_direct**: A FunctionTool that executes shell commands via Claude CLI.
2. **claude_read_file_direct**: A FunctionTool that reads files via Claude CLI.
3. **claude_write_file_direct**: A FunctionTool that writes files via Claude CLI.
4. **prompt_claude_direct**: A FunctionTool that sends prompts directly to Claude, with optional system prompt and temperature settings.

### Using the Direct Prompting Tool

The `prompt_claude_direct` tool is particularly useful for sending prompts directly to Claude's model and getting responses:

```python
# Import the tool
from radbot.tools.mcp.direct_claude_cli import prompt_claude_directly

# Send a simple prompt
result = prompt_claude_directly("What is the capital of France?")
if result["success"]:
    print(f"Claude says: {result['response']}")
else:
    print(f"Error: {result['error']}")

# Use optional parameters (if supported by your Claude CLI version)
result = prompt_claude_directly(
    prompt="Write a haiku about programming",
    system_prompt="You are a creative writing assistant specialized in poetry",
    temperature=0.7
)
```

The function implements a smart fallback mechanism:
- First tries with `--output-format json` for structured responses
- If that returns "(no content)", automatically falls back to raw mode
- Handles different Claude CLI versions with feature detection

## Security Considerations

1. **Command Allowlisting**: When `strict_mode=True`, only commands in the allowlist can be executed.
2. **Environment Isolation**: Commands are executed in Claude CLI's environment, which may have different permissions than the RadBot process.
3. **Process Management**: The integration includes proper lifecycle management for the Claude CLI subprocess.

## Examples

See the following examples for practical usage:

- `examples/claude_cli_agent.py`: A CLI agent that uses Claude CLI for command execution.
- `tools/test_claude_cli_web.py`: A test script for the web interface integration.

## Dependencies

This integration requires:

1. Claude CLI to be installed and accessible in the system PATH.
2. The MCP Python SDK: `pip install mcp`

## Implementation Approaches

There are two main approaches for integrating with Claude CLI:

### 1. MCP Client Approach

The original implementation uses the MCP Protocol's client-server model:

- **MCPStdioClient**: Manages the process lifecycle for the Claude CLI subprocess
- **Advantages**: Full MCP protocol compatibility, access to all tools
- **Disadvantages**: More complex, potential transport-related issues

### 2. Direct CLI Execution Approach

An alternative, more straightforward approach uses direct subprocess execution:

- **direct_claude_cli.py**: Directly calls `claude mcp run tool` commands
- **Advantages**: Simpler, more reliable, fewer dependencies
- **Disadvantages**: Limited tool discovery capabilities

Both approaches are supported, with the system automatically trying the direct approach first, then falling back to the MCP client approach if needed.

## Troubleshooting

Common issues:

1. **Connection Failures**: Ensure Claude CLI is installed and working correctly by running `claude mcp serve` manually.
2. **Tool Availability**: If tools aren't showing up in the web interface, check that the Claude CLI MCP server is properly configured and enabled in `config.yaml`.
3. **Permission Issues**: Commands may fail due to different permissions in the Claude CLI environment.
4. **FileIO Error**: If you see `FileIO object has no attribute command` errors, try using the direct CLI execution approach instead of the MCP client approach.

## Future Enhancements

Potential future improvements include:

1. Support for additional Claude CLI tools beyond shell commands.
2. Integration with Claude CLI's file upload capabilities.
3. Support for Claude CLI's imaging and vision capabilities.