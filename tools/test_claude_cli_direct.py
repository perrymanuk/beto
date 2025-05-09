#!/usr/bin/env python3
"""
Test script for direct interaction with Claude CLI.

This script provides a simple way to run commands directly via Claude CLI
without going through the more complex RadBot agent system.

Usage:
  python -m tools.test_claude_cli_direct "your command here"
"""

import sys
import os
import logging
import json
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def run_command(command: str) -> None:
    """Run a command via Claude CLI."""
    try:
        from radbot.tools.mcp.direct_claude_cli import execute_command_directly
        
        # Run the command
        logger.info(f"Executing command: {command}")
        result = execute_command_directly(command)
        
        # Print result
        if result["success"]:
            print("\n=== OUTPUT ===")
            print(result["output"])
            if result["error"]:
                print("\n=== ERROR ===")
                print(result["error"])
            print(f"\nExit code: {result['exit_code']}")
        else:
            print(f"Command failed: {result['error']}")
            print(f"Exit code: {result['exit_code']}")
            
    except ImportError:
        logger.error("Could not import direct Claude CLI module")
        print("Error: Could not import direct Claude CLI module")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def list_tools() -> None:
    """List available Claude CLI tools."""
    try:
        from radbot.tools.mcp.direct_claude_cli import list_claude_cli_tools
        
        # List tools
        logger.info("Listing Claude CLI tools")
        result = list_claude_cli_tools()
        
        # Print result
        if result["success"]:
            print("\n=== AVAILABLE TOOLS ===")
            for tool in result["tools"]:
                print(f"{tool['name']}: {tool['description']}")
            print(f"\nTotal: {len(result['tools'])} tools")
        else:
            print(f"Failed to list tools: {result['error']}")
            
    except ImportError:
        logger.error("Could not import direct Claude CLI module")
        print("Error: Could not import direct Claude CLI module")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def main() -> int:
    """Main entry point."""
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m tools.test_claude_cli_direct \"your command here\"")
        print("  python -m tools.test_claude_cli_direct --list-tools")
        return 1
    
    # Check for --list-tools flag
    if sys.argv[1] == "--list-tools":
        list_tools()
        return 0
    
    # Run the command
    command = sys.argv[1]
    run_command(command)
    return 0

if __name__ == "__main__":
    sys.exit(main())