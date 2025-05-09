#!/usr/bin/env python3
"""
Simple test script for the Claude CLI.

This script tests the Claude CLI command directly without using the MCP SDK.
"""

import os
import sys
import json
import subprocess
import argparse

def run_claude_command(args=None):
    """Run the claude command and return the output."""
    try:
        # Run the command
        cmd = ["claude"]
        if args:
            cmd.extend(args)
            
        print(f"Running: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # Print result
        print("\n== STDOUT ==")
        print(result.stdout)
        
        if result.stderr:
            print("\n== STDERR ==")
            print(result.stderr)
            
        print(f"\nExit code: {result.returncode}")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Simple Claude CLI Test")
    parser.add_argument("--version", action="store_true", help="Display Claude CLI version")
    parser.add_argument("--help-tools", action="store_true", help="Display Claude CLI tool help")
    parser.add_argument("--cmd", type=str, help="Run a Claude CLI command")
    
    args = parser.parse_args()
    
    if args.version:
        run_claude_command(["--version"])
    elif args.help_tools:
        run_claude_command(["tool", "--help"])
    elif args.cmd:
        cmd_args = args.cmd.split()
        run_claude_command(cmd_args)
    else:
        parser.print_help()
        
    return 0

if __name__ == "__main__":
    sys.exit(main())