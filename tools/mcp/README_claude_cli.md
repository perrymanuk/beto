# Claude CLI MCP Integration

This directory contains the integration between RadBot and Claude CLI's MCP server capabilities.

## Overview

The Claude CLI MCP integration allows RadBot agents to execute commands and perform operations using Claude CLI's powerful environment and tools.

## Files

- `mcp_stdio_client.py` - MCP client implementation for stdio transport used by Claude CLI
- `claude_cli.py` - High-level functions for interacting with Claude CLI MCP server

## Usage

### Configuration

Add the following to your `config.yaml`:

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

### Direct API Usage

```python
from radbot.tools.mcp.claude_cli import execute_command_via_claude

# Execute a command
result = execute_command_via_claude("ls -la")
if result["success"]:
    print(f"Output: {result['output']}")
else:
    print(f"Error: {result['error']}")

# Test connection
from radbot.tools.mcp.claude_cli import test_claude_cli_connection
connection_result = test_claude_cli_connection()
if connection_result["success"]:
    print("Connected to Claude CLI MCP server")
```

### Shell Agent Integration

```python
from radbot.agent.shell_agent_factory import create_shell_agent

# Create a shell agent with Claude CLI backend
agent = create_shell_agent(
    model="gemini-pro",
    base_tools=[],
    instruction_name="main_agent",
    strict_mode=True,
    use_claude_cli=True,  # Use Claude CLI backend
)
```

## Examples

See these examples for detailed usage:

- `examples/claude_cli_agent.py` - CLI agent using Claude CLI for command execution
- `tools/test_claude_cli_web.py` - Test script for web interface integration

## Testing

You can test the Claude CLI integration with:

```bash
python -m tools.test_claude_cli_web.py
```

## Documentation

For more detailed information, see:

- `docs/implementation/tools/claude-cli.md` - Comprehensive documentation
- `docs/implementation/fixes/claude_cli_web_integration_fix.md` - Web integration fixes