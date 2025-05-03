#!/usr/bin/env python3
"""
Example CLI agent with shell command execution capabilities.

This example creates a simple command-line interface agent with shell command execution
capabilities, demonstrating both strict mode and allow-all mode usage.

Usage:
    python -m examples.shell_cli_agent
    
    # Use allow-all mode (SECURITY RISK)
    RADBOT_ENABLE_SHELL=all python -m examples.shell_cli_agent
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
from radbot.tools.basic_tools import get_current_time, get_weather
from radbot.config.settings import ConfigManager

# Parse arguments
parser = argparse.ArgumentParser(description="Shell Command Execution CLI Agent")
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
    """Run the shell command execution CLI agent."""
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
    
    # Get basic tools
    base_tools = [get_current_time, get_weather]
    
    # Create the shell agent
    agent = create_shell_agent(
        model=args.model,
        base_tools=base_tools,
        instruction_name="main_agent",
        strict_mode=strict_mode,
    )
    
    if not agent:
        logger.error("Failed to create shell agent")
        return 1
    
    # Create runner
    runner = create_runner(agent)
    
    # Welcome message
    mode_str = "ALLOW ALL" if not strict_mode else "STRICT"
    print(f"\n📟 Shell Command Execution Agent (Mode: {mode_str})")
    print("Type 'exit' or 'quit' to end the session.")
    if strict_mode:
        from radbot.tools.shell_command import ALLOWED_COMMANDS
        allowed_cmds = ", ".join(sorted(list(ALLOWED_COMMANDS)))
        print(f"\nAllowed commands: {allowed_cmds}")
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
