#!/usr/bin/env python3
"""
Example CLI agent using Claude CLI for shell command execution.

This example creates a simple command-line interface agent that uses Claude CLI's MCP server
for executing shell commands, demonstrating integration with Claude CLI's capabilities.

Usage:
    python -m examples.claude_cli_agent
    
    # Use allow-all mode (SECURITY RISK)
    RADBOT_ENABLE_SHELL=all python -m examples.claude_cli_agent
"""

import os
import sys
import logging
import argparse
import asyncio
from typing import Optional, List, Any

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import required modules
from radbot.agent.shell_agent_factory import create_shell_agent
from radbot.agent.agent import create_runner
from radbot.tools.basic.basic_tools import get_current_time
from radbot.config.settings import ConfigManager

# Parse arguments
parser = argparse.ArgumentParser(description="Claude CLI MCP Shell Command Execution Agent")
parser.add_argument(
    "--allow-all", 
    action="store_true", 
    help="Enable allow-all mode (SECURITY RISK)"
)
parser.add_argument(
    "--model", 
    type=str, 
    default=None,
    help="Specify the model to use"
)


async def main():
    """Run the Claude CLI shell command execution agent."""
    args = parser.parse_args()
    
    # Check for environment variable override
    enable_shell = os.environ.get("RADBOT_ENABLE_SHELL", "strict").lower()
    strict_mode = True
    
    if args.allow_all or enable_shell in ["true", "1", "yes", "enable", "all", "allow"]:
        strict_mode = False
        logger.warning(
            "⚠️ SECURITY WARNING: Running in ALLOW ALL mode. "
            "This allows execution of ANY command without restrictions! ⚠️"
        )
    else:
        logger.info("Running in STRICT mode (only allow-listed commands)")
    
    # Test Claude CLI connection
    try:
        from radbot.tools.mcp.claude_cli import test_claude_cli_connection
        
        print("Testing connection to Claude CLI MCP server...")
        result = test_claude_cli_connection()
        
        if result.get("success", False):
            print(f"✅ Connected to Claude CLI MCP server: {result.get('output', '')}")
        else:
            print(f"❌ Failed to connect to Claude CLI MCP server: {result.get('error', 'Unknown error')}")
            logger.error(f"Claude CLI connection error: {result}")
            return 1
            
    except ImportError:
        print("❌ Claude CLI integration not available")
        logger.error("Could not import Claude CLI module")
        return 1
    
    # Get basic tools
    base_tools = [get_current_time]
    
    # Create the shell agent with Claude CLI backend
    agent = create_shell_agent(
        model=args.model,
        base_tools=base_tools,
        instruction_name="main_agent",
        strict_mode=strict_mode,
        use_claude_cli=True,  # This is the key difference - use Claude CLI backend
    )
    
    if not agent:
        logger.error("Failed to create shell agent")
        return 1
    
    # Create runner
    runner = create_runner(agent)
    
    # Welcome message
    mode_str = "ALLOW ALL" if not strict_mode else "STRICT"
    print(f"\n📟 Claude CLI Shell Command Execution Agent (Mode: {mode_str})")
    print("Type 'exit' or 'quit' to end the session.")
    
    # Get Claude CLI security config
    from radbot.config.config_loader import config_loader
    claude_config = config_loader.get_mcp_server("claude-cli") or {}
    security_config = claude_config.get("security", {})
    allowed_commands = security_config.get("command_allowlist", [])
    
    if strict_mode and allowed_commands:
        allowed_cmds = ", ".join(sorted(allowed_commands))
        print(f"\nAllowed commands via Claude CLI: {allowed_cmds}")
    elif strict_mode:
        from radbot.tools.shell.shell_command import ALLOWED_COMMANDS
        allowed_cmds = ", ".join(sorted(list(ALLOWED_COMMANDS)))
        print(f"\nAllowed commands (default): {allowed_cmds}")
    else:
        print("\n⚠️ WARNING: Running in ALLOW ALL mode - any command can be executed! ⚠️")
    
    print("\nEnter your prompt:")
    
    # Start conversation loop
    while True:
        try:
            # Get user input
            user_input = input("\n> ")
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            
            # Process user input
            response = await runner.run_dialog(user_input)
            
            # Print response
            print(f"\n{response}")
            
        except KeyboardInterrupt:
            print("\nKeyboard interrupt detected. Exiting...")
            break
        except Exception as e:
            logger.error(f"Error in conversation loop: {e}")
            print(f"\nAn error occurred: {str(e)}")
    
    return 0


if __name__ == "__main__":
    asyncio.run(main())