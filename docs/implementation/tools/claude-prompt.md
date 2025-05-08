# Claude CLI Direct Prompting

This document describes the simplified Claude CLI direct prompting integration for RadBot, which focuses exclusively on the prompting capability.

## Overview

The Claude CLI Direct Prompting integration allows RadBot to send prompts directly to Claude's models via the Claude CLI tool, providing a simple and efficient way to leverage Claude's capabilities without the complexity of a full MCP server implementation.

## Implementation

The implementation consists of a streamlined module that directly executes the Claude CLI command with appropriate arguments and parses the response. It includes:

1. A direct prompting function with fallback mechanism
2. Support for optional parameters like system prompts and temperature
3. Feature detection to ensure compatibility with different Claude CLI versions
4. Integration with the RadBot web interface

## Configuration

The Claude CLI integration is configured in the RadBot `config.yaml` file:

```yaml
integrations:
  mcp:
    servers:
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
        tags:
          - shell
          - command
```

Note that despite the MCP server configuration, this implementation does not use the MCP protocol. It simply uses the configuration to find the Claude CLI command and its arguments.

## Usage

### Direct Prompting

```python
from radbot.tools.claude_prompt import prompt_claude_directly

# Basic usage
result = prompt_claude_directly("What is the capital of France?")
if result["success"]:
    print(f"Claude says: {result['response']}")
else:
    print(f"Error: {result['error']}")

# With optional parameters (if supported by your Claude CLI version)
result = prompt_claude_directly(
    prompt="Write a haiku about programming",
    system_prompt="You are a creative writing assistant specialized in poetry",
    temperature=0.7
)
```

### Tool Creation

For use with the Google ADK:

```python
from radbot.tools.claude_prompt import create_claude_prompt_tool

# Create a FunctionTool for the Claude prompt
claude_tool = create_claude_prompt_tool()

# Add to an agent's tools
agent.tools.append(claude_tool)
```

## Fallback Mechanism

The implementation includes a smart fallback mechanism:

1. First tries with JSON output format (`--output-format json`) for structured responses
2. If that returns "(no content)" or empty content, automatically falls back to raw text mode
3. Handles different Claude CLI versions by detecting supported features at runtime

This ensures reliability across different types of prompts and Claude CLI versions.

## Web Interface Integration

The web interface automatically detects and loads the Claude prompt tool when the server is configured in `config.yaml`. No additional configuration is needed.

## Dependencies

This integration requires:

1. Claude CLI to be installed and accessible in the system PATH
2. Google ADK Python package for tool integration

## Testing

Test scripts are provided to verify the functionality:

- `tools/test_simplified_claude_prompt.py`: Tests the basic prompting functionality and web integration

## Limitations

This simplified integration focuses exclusively on the prompting capability and:

1. Does not support other Claude CLI features like file read/write
2. Does not implement a full MCP server
3. Requires the Claude CLI to be installed on the system

## FAQ

**Q: Why use this instead of the full MCP integration?**
A: This implementation is simpler, more reliable, and focuses on the core prompting capability which is the most valuable feature of Claude.

**Q: Can I use this to execute shell commands?**
A: No, the shell command execution capability has been removed. Use the standard subprocess-based shell tools instead.

**Q: What Claude CLI versions are supported?**
A: The implementation includes feature detection to work with different Claude CLI versions, but requires at minimum the `--print` argument to be supported.