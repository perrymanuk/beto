# Shell Command Execution

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


## Feature Overview

This feature enables the agent to execute shell commands on the host system with robust security controls. It provides two modes of operation:

1. **Strict Mode (Default)**: Only pre-approved commands from an allow-list can be executed
2. **Allow All Mode**: Any command can be executed (significant security risk)

## Security Considerations

Shell command execution is inherently risky. This implementation uses multiple layers of security:

- **Command Allow-listing**: Only permits execution of whitelisted commands in strict mode
- **shell=False**: Prevents shell metacharacter interpretation
- **List Arguments**: Passes command and arguments as separate list elements
- **Argument Validation**: Basic checks for dangerous characters
- **Timeout Enforcement**: Prevents runaway processes
- **Comprehensive Error Handling**: Structured error reporting
- **Logging**: Detailed logging for security auditing

⚠️ **WARNING**: The "Allow All" mode bypasses the command allow-list, introducing significant security risks. Use this mode only in controlled environments with appropriate safeguards.

## Implementation Details

### Core Components

1. `execute_shell_command` function in `radbot/tools/shell_command.py`:
   - Implements the core shell execution functionality
   - Performs security checks and command execution
   - Returns structured results with stdout, stderr, return code, and errors

2. `get_shell_tool` and `handle_shell_function_call` in `radbot/tools/shell_tool.py`:
   - Registers the tool with the Google Agent SDK
   - Handles function calls from the agent
   - Validates arguments before execution

### Configuration Options

- **ALLOWED_COMMANDS**: Set of commands permitted in strict mode
- **DEFAULT_TIMEOUT**: Default timeout for command execution (60 seconds)
- **strict_mode**: Boolean flag to enable/disable strict mode

## Usage Examples

### Agent Integration

```python
from radbot.tools.shell_tool import get_shell_tool, handle_shell_function_call

# Get tool in strict mode (default)
shell_tool = get_shell_tool(strict_mode=True)

# Add tool to agent configuration
tools = [shell_tool]  # Plus other tools

# When processing function calls from the agent
result = await handle_shell_function_call(
    function_name="execute_shell_command",
    arguments={"command": "ls", "arguments": ["-la"]},
    strict_mode=True
)

# To use in allow-all mode (SECURITY RISK)
shell_tool_unrestricted = get_shell_tool(strict_mode=False)
```

### Expected Results Structure

The result of a command execution is a dictionary with:

```python
{
    "stdout": "command output...",  # Standard output as string
    "stderr": "error output...",    # Standard error as string
    "return_code": 0,               # Return code (0 for success)
    "error": None                   # Error message or None on success
}
```

## Customization

### Adding Allowed Commands

To add new commands to the allow-list, update the `ALLOWED_COMMANDS` set in `radbot/tools/shell_command.py`:

```python
ALLOWED_COMMANDS = {
    "ls", "echo", "pwd", "cat", "grep", "find", 
    "head", "tail", "new_command1", "new_command2"
}
```

### Enhancing Argument Validation

The current implementation includes basic argument validation. For production use, consider implementing command-specific validation rules.

## Security Best Practices

1. Run the agent with the minimum required permissions
2. Default to strict mode in production environments
3. Consider running the agent in a container or sandboxed environment
4. Regularly audit command execution logs
5. Review and minimize the allowed commands list

## Future Enhancements

1. Command-specific argument validation
2. Integration with containerization for additional isolation
3. Support for environment variable control
4. Working directory restrictions
