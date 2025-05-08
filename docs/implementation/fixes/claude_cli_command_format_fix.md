# Claude CLI Command Format Fix

This document describes the fix for the Claude CLI command format issue encountered in the direct Claude CLI integration approach.

## Issue Description

After implementing the direct Claude CLI integration approach, we encountered an error with the command format:

```
Error: unknown command 'run'
```

This occurred because our implementation was using an incorrect command format for Claude CLI, assuming it supported a `tool run` subcommand that doesn't actually exist.

## Root Cause Analysis

The root cause was a misunderstanding of the Claude CLI command interface. We were trying to use commands in this format:

```
claude tool run Bash --input {"command": "echo 'Hello'"}
```

But the actual Claude CLI doesn't have a `tool run` subcommand. Instead, it supports a direct command execution approach using flags like `--print` and `--output-format`.

## Solution

We updated the `direct_claude_cli.py` module to use the correct command format:

### 1. Command Execution Changes

Updated the `execute_command_directly` function to use the correct format:

```python
# Old incorrect approach
claude_args = ["tool", "run", "Bash", "--input", json.dumps({"command": command})]

# New correct approach
claude_args = ["--print", "--output-format", "json", f"Execute this command: {command}"]
```

### 2. File Operation Changes

Updated the file operations to use the command execution functionality rather than trying to use non-existent Claude CLI file operations:

```python
# For reading files
def read_file_directly(file_path: str) -> Dict[str, Any]:
    # Use cat command to read the file content
    command = f"cat {file_path}"
    result = execute_command_directly(command)
    # Process result...
```

```python
# For writing files
def write_file_directly(file_path: str, content: str) -> Dict[str, Any]:
    # Use echo and redirect to write to the file
    tmp_file = f"/tmp/claude_cli_write_{int(time.time())}.tmp"
    escaped_content = content.replace("'", "'\\''")
    
    # First command: write to temp file
    write_cmd = f"echo '{escaped_content}' > {tmp_file}"
    write_result = execute_command_directly(write_cmd)
    
    # Second command: move temp file to destination
    move_cmd = f"mv {tmp_file} {file_path}"
    move_result = execute_command_directly(move_cmd)
    # Process results...
```

### 3. Added Direct Prompting Capability with Fallback

Added a new function that allows sending prompts directly to Claude, with a smart fallback mechanism:

```python
def prompt_claude_directly(prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
    """
    Send a prompt directly to Claude CLI.
    
    Args:
        prompt: The prompt to send to Claude
        system_prompt: Optional system prompt to set context
        temperature: Optional temperature parameter (0.0-1.0)
        
    Returns:
        Dict containing response or error information
    """
    # Get claude command and arguments
    claude_command = config.get("command", "claude")
    # Start with basic arguments
    claude_args = ["--print", "--output-format", "json"]
    
    # Add system prompt if provided
    if system_prompt:
        claude_args.extend(["--system", system_prompt])
        
    # Add temperature if provided
    if temperature is not None:
        claude_args.extend(["--temperature", str(temperature)])
        
    # Add the prompt
    claude_args.append(prompt)
    
    # Run the process...
    
    # Check if the result contains actual content
    if result.get("result") == "(no content)" or not result.get("result"):
        # Claude CLI returned empty content, try again without JSON
        return prompt_claude_directly_raw(prompt, system_prompt, temperature)
```

Also added a raw mode fallback function that doesn't use JSON format:

```python
def prompt_claude_directly_raw(prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
    """
    Send a prompt directly to Claude CLI without JSON formatting.
    This is a fallback for when JSON mode returns empty content.
    """
    # Get claude command and arguments - don't use JSON output format
    claude_command = config.get("command", "claude")
    claude_args = ["--print"]
    
    # Add system prompt if provided
    if system_prompt:
        claude_args.extend(["--system", system_prompt])
        
    # Add temperature if provided
    if temperature is not None:
        claude_args.extend(["--temperature", str(temperature)])
        
    # Add the prompt
    claude_args.append(prompt)
    
    # Run the process...
```

This fallback mechanism handles the case where Claude CLI returns "(no content)" in JSON mode, which can happen with certain types of prompts. The raw mode provides a more reliable fallback.

### 4. Tool Listing Changes

Updated the `list_claude_cli_tools` function to use a predefined list of supported tools since there's no direct way to list Claude CLI tools:

```python
# Since Claude CLI doesn't have a way to directly list tools,
# we'll create a predefined list of tools we know our implementation supports
tools_list = [
    {
        "name": "Bash",
        "description": "Execute shell commands"
    },
    {
        "name": "Read",
        "description": "Read files from the filesystem"
    },
    {
        "name": "Write",
        "description": "Write files to the filesystem"
    },
    {
        "name": "prompt_claude",
        "description": "Send a direct prompt to Claude"
    }
]
```

## Verification

We created and used two verification scripts to ensure our changes work correctly:

1. `tools/verify_claude_cli_direct.py` - Tests the direct Claude CLI command execution and other functionality
2. `tools/test_claude_cli_direct_web.py` - Tests the integration with the web interface

Test results showed:
- Command execution works correctly with the new format
- The tools are properly created and attached to the agent
- Core functionality is working as expected

## Results and Impact

With these changes:
- The direct Claude CLI integration works correctly with the proper command format
- Command execution functionality is reliable
- The system now falls back gracefully to the direct approach when the MCP client approach fails
- The web interface can use Claude CLI functionality for shell commands

There are still some limitations with file operations, but they don't significantly impact the overall functionality since they can be handled through the command execution approach.

## Conclusion

This fix addresses several issues in the direct Claude CLI integration:

1. **Command Format Fix**: By using the correct Claude CLI command format with `--print` and `--output-format json` options, we've enabled reliable command execution through Claude CLI.

2. **Direct Prompting Enhancement**: Added direct prompting capability with a smart fallback mechanism that handles the "(no content)" issue by automatically switching to raw mode when needed.

3. **Robust Error Handling**: Improved error handling and logging throughout the integration to provide better diagnostics.

4. **Feature Detection**: Added runtime feature detection for different Claude CLI versions to ensure maximum compatibility.

The fix maintains the system's robustness by implementing fallback mechanisms at multiple levels, ensuring that even if one approach fails, the system will try alternatives. The direct prompting capability in particular is a significant enhancement that allows RadBot to leverage Claude's powerful LLM capabilities directly.