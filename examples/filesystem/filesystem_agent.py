#!/usr/bin/env python3
"""
Filesystem Agent Example

This script demonstrates the new direct filesystem implementation in radbot.
It creates an agent with filesystem access capabilities and allows interactive
use of these tools.

Usage:
    python filesystem_agent.py [options]

Options:
    --allow-write    Allow write operations (default: read-only)
    --allow-delete   Allow delete operations (requires --allow-write)
    --root-dir DIR   Root directory for filesystem access (default: current directory)
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root to the path to ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from radbot.agent import Agent
from radbot.prompts import load_prompt
from radbot.filesystem.integration import create_filesystem_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_filesystem_agent(
    allowed_directories: list[str],
    enable_write: bool = False,
    enable_delete: bool = False,
) -> Agent:
    """
    Create an agent with filesystem access capabilities.

    Args:
        allowed_directories: List of directories to allow access to
        enable_write: If True, enable write operations
        enable_delete: If True, enable delete operations

    Returns:
        Agent instance with filesystem tools
    """
    # Create the filesystem tools
    filesystem_tools = create_filesystem_tools(
        allowed_directories=allowed_directories,
        enable_write=enable_write,
        enable_delete=enable_delete,
    )

    # Load agent prompts
    system_prompt = load_prompt("default")

    # Add information about filesystem permissions to the prompt
    fs_permissions = (
        "\n\nYou have access to filesystem operations with the following permissions:\n"
        f"- Allowed directories: {', '.join(allowed_directories)}\n"
        f"- Write operations: {'Enabled' if enable_write else 'Disabled'}\n"
        f"- Delete operations: {'Enabled' if enable_delete else 'Disabled'}\n\n"
        "You can help users with file management tasks. Remember to respect the permissions "
        "configured and always inform users if an operation is not allowed."
    )
    
    system_prompt += fs_permissions
    
    # Create the agent
    agent = Agent(
        tools=filesystem_tools,
        system_prompt=system_prompt,
        model="gemini-1.5-pro",  # Adjust as needed
    )
    
    return agent


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Filesystem Agent Example")
    parser.add_argument(
        "--allow-write",
        action="store_true",
        help="Allow write operations (default: read-only)",
    )
    parser.add_argument(
        "--allow-delete",
        action="store_true",
        help="Allow delete operations (requires --allow-write)",
    )
    parser.add_argument(
        "--root-dir",
        type=str,
        default=os.getcwd(),
        help="Root directory for filesystem access (default: current directory)",
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.allow_delete and not args.allow_write:
        logger.error("--allow-delete requires --allow-write")
        parser.print_help()
        sys.exit(1)
    
    root_dir = os.path.abspath(os.path.expanduser(args.root_dir))
    if not os.path.isdir(root_dir):
        logger.error(f"Root directory does not exist: {root_dir}")
        sys.exit(1)
    
    logger.info(f"Creating filesystem agent with root directory: {root_dir}")
    logger.info(f"Write operations: {'Enabled' if args.allow_write else 'Disabled'}")
    logger.info(f"Delete operations: {'Enabled' if args.allow_delete else 'Disabled'}")
    
    # Create the agent
    agent = create_filesystem_agent(
        allowed_directories=[root_dir],
        enable_write=args.allow_write,
        enable_delete=args.allow_delete,
    )
    
    # Interactive loop
    print("\nFilesystem Agent\n")
    print(f"Root directory: {root_dir}")
    print(f"Write operations: {'Enabled' if args.allow_write else 'Disabled'}")
    print(f"Delete operations: {'Enabled' if args.allow_delete else 'Disabled'}\n")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    while True:
        try:
            # Get user input
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break
            
            # Process the message
            response = agent.process_message(user_input)
            print(f"\nAgent: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting due to keyboard interrupt.")
            break
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
