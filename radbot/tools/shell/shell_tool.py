"""Shell Command Execution Tool registration for the Agent SDK.

This module registers the shell command execution tool with the Google Agent SDK,
allowing the bot to execute shell commands with proper security controls.
It supports both subprocess and Claude CLI MCP backends for command execution.
"""

import logging
from typing import Dict, List, Any, Optional, Union

from google.ai.generativelanguage import Tool, FunctionDeclaration, Schema, Type
from google.adk.tools import FunctionTool

from radbot.tools.shell.shell_command import execute_shell_command, ALLOWED_COMMANDS

logger = logging.getLogger(__name__)


def execute_command_with_claude(
    command: str,
    arguments: Optional[List[str]] = None,
    timeout: int = 120,
    strict_mode: bool = True
) -> Dict[str, Any]:
    """
    Execute a shell command using Claude CLI's MCP server.
    
    Args:
        command: The command to execute
        arguments: Command arguments (optional)
        timeout: Maximum execution time in seconds
        strict_mode: Whether to enforce command allowlisting
        
    Returns:
        Dict with execution results
    """
    try:
        # First try direct approach
        try:
            from radbot.tools.mcp.direct_claude_cli import execute_command_directly
            logger.info("Using direct Claude CLI execution")
            use_direct = True
        except ImportError:
            # Fall back to MCP client approach
            from radbot.tools.mcp.claude_cli import execute_command_via_claude
            logger.info("Using MCP client Claude CLI execution")
            use_direct = False
        
        # Perform command validation (similar to regular execute_shell_command)
        if strict_mode and command not in ALLOWED_COMMANDS:
            error_message = f"Error: Command '{command}' is not allowed in strict mode."
            logger.warning(error_message)
            return {
                "stdout": "",
                "stderr": error_message,
                "return_code": -1,
                "error": error_message,
            }
            
        # Log security warning if executing non-allow-listed command
        if not strict_mode and command not in ALLOWED_COMMANDS:
            logger.warning(
                f"SECURITY WARNING: Executing non-allow-listed command '{command}' with strict_mode=False"
            )
            
        # Build the full command string
        arguments = arguments or []
        full_command = f"{command} {' '.join(arguments)}".strip()
        
        # Execute via Claude CLI
        if use_direct:
            result = execute_command_directly(command=full_command)
        else:
            result = execute_command_via_claude(command=full_command)
        
        # Map the result keys to match the standard shell command output
        return {
            "stdout": result.get("output", ""),
            "stderr": result.get("error", ""),
            "return_code": result.get("exit_code", -1),
            "error": None if result.get("success", False) else result.get("error", "Command execution failed")
        }
        
    except ImportError:
        error_message = "Claude CLI integration not available (both direct and MCP client approaches failed)"
        logger.error(error_message)
        return {
            "stdout": "",
            "stderr": error_message,
            "return_code": -1,
            "error": error_message,
        }
        
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        logger.exception(f"Error executing command with Claude CLI: {e}")
        return {
            "stdout": "",
            "stderr": error_message,
            "return_code": -1,
            "error": error_message,
        }


def get_shell_tool(strict_mode: bool = True, use_claude_cli: bool = False) -> Any:
    """Get the shell command execution tool configured for the Google Agent SDK.
    
    Args:
        strict_mode: When True, only allow-listed commands are permitted.
                    When False, any command can be executed (SECURITY RISK).
        use_claude_cli: Whether to use Claude CLI for command execution (default: False)
    
    Returns:
        A tool object ready to be used with the agent.
    """
    # Dynamically generate the description based on the allowed commands
    allowed_commands_str = ", ".join(sorted(list(ALLOWED_COMMANDS)))
    
    if strict_mode:
        tool_description = (
            f"Executes an allow-listed shell command and returns its output. "
            f"Only the following commands are permitted: {allowed_commands_str}. "
            f"Provide the command name and a list of arguments."
        )
    else:
        tool_description = (
            "WARNING - SECURITY RISK: Executes any shell command and returns its output. "
            "This mode bypasses command allow-listing and permits execution of ANY command. "
            "Use with extreme caution. Provide the command name and a list of arguments."
        )
        logger.warning("Shell tool initialized in ALLOW ALL mode - SECURITY RISK")
    
    # Add execution backend information to the description
    backend = "Claude CLI" if use_claude_cli else "subprocess"
    tool_description += f" (Using {backend} for execution)"
    
    # Create a wrapper function for ADK compatibility
    def shell_command_tool(command: str, arguments: Optional[List[str]] = None, timeout: int = 60) -> Dict[str, Any]:
        """Execute a shell command securely.
        
        Args:
            command: The command to execute. In strict mode, must be in ALLOWED_COMMANDS.
            arguments: A list of arguments to pass to the command.
            timeout: Maximum execution time in seconds.
            
        Returns:
            A dictionary with stdout, stderr, return_code, and error information.
        """
        if arguments is None:
            arguments = []
        
        # Choose execution backend
        if use_claude_cli:
            logger.info(f"Executing command '{command}' using Claude CLI")
            return execute_command_with_claude(
                command=command,
                arguments=arguments,
                timeout=timeout,
                strict_mode=strict_mode
            )
        else:
            logger.info(f"Executing command '{command}' using subprocess")
            return execute_shell_command(
                command=command,
                arguments=arguments,
                timeout=timeout,
                strict_mode=strict_mode
            )
    
    # Set metadata for the function
    shell_command_tool.__name__ = "execute_shell_command"
    shell_command_tool.__doc__ = tool_description
    
    # Wrap in FunctionTool for ADK compatibility
    return FunctionTool(shell_command_tool)


async def handle_shell_function_call(
    function_name: str, arguments: Dict[str, Any], strict_mode: bool = True, use_claude_cli: bool = False
) -> Dict[str, Any]:
    """Handle function calls from the agent to the shell command execution tool.
    
    Args:
        function_name: The name of the function being called.
        arguments: The arguments passed to the function.
        strict_mode: Whether to enforce command allow-listing.
        use_claude_cli: Whether to use Claude CLI for command execution (default: False)
    
    Returns:
        The result of executing the shell command.
    """
    if function_name != "execute_shell_command":
        error_message = f"Unknown function: {function_name}"
        logger.error(error_message)
        return {
            "stdout": "",
            "stderr": error_message,
            "return_code": -1,
            "error": error_message
        }
    
    # Extract and validate arguments
    command = arguments.get("command", "")
    if not command:
        error_message = "No command specified"
        logger.error(error_message)
        return {
            "stdout": "",
            "stderr": error_message,
            "return_code": -1,
            "error": error_message
        }
    
    # Extract optional arguments with defaults
    arg_list = arguments.get("arguments", [])
    timeout = arguments.get("timeout", 60)
    
    # Type validation for arguments
    if not isinstance(arg_list, list):
        error_message = "Arguments must be a list"
        logger.error(error_message)
        return {
            "stdout": "",
            "stderr": error_message,
            "return_code": -1,
            "error": error_message
        }
    
    if not isinstance(timeout, int) or timeout <= 0:
        error_message = "Timeout must be a positive integer"
        logger.error(error_message)
        return {
            "stdout": "",
            "stderr": error_message,
            "return_code": -1,
            "error": error_message
        }
    
    # Choose execution backend
    if use_claude_cli:
        logger.info(f"Function call: Executing command '{command}' using Claude CLI")
        return execute_command_with_claude(
            command=command,
            arguments=arg_list,
            timeout=timeout,
            strict_mode=strict_mode
        )
    else:
        logger.info(f"Function call: Executing command '{command}' using subprocess")
        return execute_shell_command(
            command=command,
            arguments=arg_list,
            timeout=timeout,
            strict_mode=strict_mode
        )


def get_genai_shell_tool(strict_mode: bool = True, use_claude_cli: bool = False) -> Tool:
    """Get the shell command execution tool for the Google GenAI SDK.
    
    This is used when working directly with the GenAI SDK instead of ADK.
    
    Args:
        strict_mode: When True, only allow-listed commands are permitted.
                    When False, any command can be executed (SECURITY RISK).
        use_claude_cli: Whether to use Claude CLI for command execution (default: False)
    
    Returns:
        A Tool object for the GenAI SDK.
    """
    # Dynamically generate the description based on the allowed commands
    allowed_commands_str = ", ".join(sorted(list(ALLOWED_COMMANDS)))
    
    if strict_mode:
        tool_description = (
            f"Executes an allow-listed shell command and returns its output. "
            f"Only the following commands are permitted: {allowed_commands_str}. "
            f"Provide the command name and a list of arguments."
        )
    else:
        tool_description = (
            "WARNING - SECURITY RISK: Executes any shell command and returns its output. "
            "This mode bypasses command allow-listing and permits execution of ANY command. "
            "Use with extreme caution. Provide the command name and a list of arguments."
        )
        logger.warning("Shell tool initialized in ALLOW ALL mode - SECURITY RISK")
    
    # Add execution backend information to the description
    backend = "Claude CLI" if use_claude_cli else "subprocess"
    tool_description += f" (Using {backend} for execution)"
        
    return Tool(
        function_declarations=[
            FunctionDeclaration(
                name="execute_shell_command",
                description=tool_description,
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        'command': Schema(
                            type=Type.STRING, 
                            description="The command to execute.",
                        ),
                        'arguments': Schema(
                            type=Type.ARRAY,
                            description="A list of arguments to pass to the command. Optional.",
                            items=Schema(type=Type.STRING)
                        ),
                        'timeout': Schema(
                            type=Type.INTEGER,
                            description="Maximum execution time in seconds. Must be positive.",
                        ),
                    },
                    required=['command']
                )
            )
        ]
    )
