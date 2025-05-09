#!/usr/bin/env python3
"""
Test script for different Claude CLI command formats.

This script tests various formats for Claude CLI commands to determine
which ones are properly supported and which formats work best.
"""

import sys
import os
import logging
import json
import subprocess
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def run_command(command: List[str]) -> Dict[str, Any]:
    """Run a command and capture the output."""
    try:
        print(f"Executing: {' '.join(command)}")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=60)
        exit_code = process.returncode
        
        result = {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "success": exit_code == 0
        }
        
        return result
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }

def test_format_1():
    """Test basic format with --print"""
    command = ["claude", "--print", "Write a bash script that prints 'Hello World'"]
    result = run_command(command)
    
    print(f"\nFormat 1 result (exit code: {result['exit_code']}):")
    if result["success"]:
        print("Success!")
        print("-" * 40)
        output = result["stdout"]
        # Only print the first 500 characters to keep it manageable
        print(output[:500] + "..." if len(output) > 500 else output)
        print("-" * 40)
    else:
        print("Failed!")
        print(f"Error: {result['stderr']}")
    
    return result["success"]

def test_format_2():
    """Test with --print and --output-format json"""
    command = ["claude", "--print", "--output-format", "json", "Write a bash script that prints 'Hello World'"]
    result = run_command(command)
    
    print(f"\nFormat 2 result (exit code: {result['exit_code']}):")
    if result["success"]:
        print("Success!")
        print("-" * 40)
        try:
            # Try to parse as JSON
            output_json = json.loads(result["stdout"])
            print(json.dumps(output_json, indent=2))
        except json.JSONDecodeError:
            print(result["stdout"][:500] + "..." if len(result["stdout"]) > 500 else result["stdout"])
        print("-" * 40)
    else:
        print("Failed!")
        print(f"Error: {result['stderr']}")
    
    return result["success"]

def test_format_3():
    """Test with shell script specific prompt"""
    command = ["claude", "--print", "Could you write a simple bash script that prints 'Hello World' to the console?"]
    result = run_command(command)
    
    print(f"\nFormat 3 result (exit code: {result['exit_code']}):")
    if result["success"]:
        print("Success!")
        print("-" * 40)
        output = result["stdout"]
        print(output[:500] + "..." if len(output) > 500 else output)
        print("-" * 40)
    else:
        print("Failed!")
        print(f"Error: {result['stderr']}")
    
    return result["success"]

def test_format_4():
    """Test with code-focused prompt"""
    command = ["claude", "--print", "Write a bash command or script to echo 'Hello World'"]
    result = run_command(command)
    
    print(f"\nFormat 4 result (exit code: {result['exit_code']}):")
    if result["success"]:
        print("Success!")
        print("-" * 40)
        output = result["stdout"]
        print(output[:500] + "..." if len(output) > 500 else output)
        print("-" * 40)
    else:
        print("Failed!")
        print(f"Error: {result['stderr']}")
    
    return result["success"]

def main():
    """Main function to run the tests."""
    print("=" * 50)
    print("CLAUDE CLI COMMAND FORMAT TEST")
    print("=" * 50)
    
    # Get Claude version
    version_result = run_command(["claude", "--version"])
    if version_result["success"]:
        print(f"Claude CLI version: {version_result['stdout'].strip()}")
    else:
        print(f"Could not determine Claude CLI version: {version_result['stderr']}")
    
    # Test each format
    format_1_success = test_format_1()
    format_2_success = test_format_2()
    format_3_success = test_format_3()
    format_4_success = test_format_4()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Format 1 (basic --print): {'✅ Success' if format_1_success else '❌ Failed'}")
    print(f"Format 2 (--print --output-format json): {'✅ Success' if format_2_success else '❌ Failed'}")
    print(f"Format 3 (shell script prompt): {'✅ Success' if format_3_success else '❌ Failed'}")
    print(f"Format 4 (code-focused prompt): {'✅ Success' if format_4_success else '❌ Failed'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())