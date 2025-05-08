#!/usr/bin/env python3
"""
Debug script for the Claude CLI direct prompting functionality.

This script provides detailed debugging for the direct prompting function in the Claude CLI integration.
"""

import sys
import os
import logging
import json
import subprocess
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_claude_cli_version():
    """Check the version of Claude CLI installed."""
    try:
        print("Checking Claude CLI version...")
        process = subprocess.Popen(
            ["claude", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=10)
        exit_code = process.returncode
        
        if exit_code == 0:
            print(f"Claude CLI version: {stdout.strip()}")
            return True
        else:
            print(f"Error getting Claude CLI version: {stderr}")
            return False
    except Exception as e:
        print(f"Exception checking Claude CLI version: {e}")
        return False

def check_claude_cli_help():
    """Check Claude CLI help to understand available options."""
    try:
        print("Checking Claude CLI help...")
        process = subprocess.Popen(
            ["claude", "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=10)
        exit_code = process.returncode
        
        if exit_code == 0:
            print(f"Claude CLI help output:")
            print("-" * 40)
            print(stdout)
            print("-" * 40)
            return True
        else:
            print(f"Error getting Claude CLI help: {stderr}")
            return False
    except Exception as e:
        print(f"Exception checking Claude CLI help: {e}")
        return False

def check_claude_cli_config():
    """Check the Claude CLI configuration in the config.yaml file."""
    try:
        from radbot.tools.mcp.direct_claude_cli import get_claude_cli_config
        
        print("Getting Claude CLI configuration...")
        config = get_claude_cli_config()
        
        if config:
            print(f"Found Claude CLI configuration:")
            print(json.dumps(config, indent=2))
            return True
        else:
            print("No Claude CLI configuration found.")
            return False
    except Exception as e:
        print(f"Exception checking Claude CLI config: {e}")
        return False

def debug_prompt_claude(prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None):
    """Debug the prompt_claude_directly function."""
    try:
        from radbot.tools.mcp.direct_claude_cli import prompt_claude_directly
        from radbot.tools.mcp.direct_claude_cli import _check_claude_cli_support
        
        # First check feature support
        print("Checking Claude CLI feature support...")
        support = _check_claude_cli_support()
        print(f"Supported features: {json.dumps(support, indent=2)}")
        
        # Construct the command manually to see what's being executed
        from radbot.tools.mcp.direct_claude_cli import get_claude_cli_config
        config = get_claude_cli_config()
        claude_command = config.get("command", "claude")
        claude_args = ["--print"]
        
        if support.get("json_output", True):
            claude_args.extend(["--output-format", "json"])
        
        if system_prompt and support.get("system_prompt", False):
            claude_args.extend(["--system", system_prompt])
            
        if temperature is not None and support.get("temperature", False):
            claude_args.extend(["--temperature", str(temperature)])
            
        claude_args.append(prompt)
        
        print("\nCommand to execute:")
        print(f"{claude_command} {' '.join(claude_args)}\n")
        
        # Try running the prompt function with detailed logging
        print(f"Sending prompt to Claude: '{prompt[:50]}{'...' if len(prompt) > 50 else ''}'")
        
        # Execute the function
        result = prompt_claude_directly(prompt, system_prompt, temperature)
        
        print("\nResult:")
        print(json.dumps(result, indent=2))
        
        # Check the result
        if result.get("success", False):
            print("\n✅ Successfully got response from Claude")
            
            # Examine response structure
            response = result.get("response", "")
            if isinstance(response, dict):
                print("\nResponse is a dictionary with keys:")
                print(json.dumps(list(response.keys()), indent=2))
            else:
                print(f"\nResponse is a {type(response)}")
            
            # Print the raw output
            raw_output = result.get("raw_output", "")
            print("\nRaw output:")
            print(raw_output[:500] + "..." if len(raw_output) > 500 else raw_output)
            
            return True
        else:
            print(f"\n❌ Failed to get response from Claude")
            print(f"Error: {result.get('error', 'No error specified')}")
            return False
            
    except Exception as e:
        print(f"Exception in debug_prompt_claude: {e}")
        import traceback
        traceback.print_exc()
        return False

def try_direct_claude_command():
    """Try executing a Claude command directly using subprocess."""
    try:
        print("Trying to execute Claude command directly...")
        
        # Simple command with minimal options
        process = subprocess.Popen(
            ["claude", "--print", "Hello, Claude!"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=60)
        exit_code = process.returncode
        
        print(f"Exit code: {exit_code}")
        
        if exit_code == 0:
            print(f"Direct command execution successful:")
            print("-" * 40)
            print(stdout)
            print("-" * 40)
            return True
        else:
            print(f"Direct command execution failed:")
            print(f"Stderr: {stderr}")
            return False
    except Exception as e:
        print(f"Exception in try_direct_claude_command: {e}")
        return False

def main():
    """Main entry point."""
    print("=" * 50)
    print("CLAUDE CLI DIRECT PROMPTING DEBUG TOOL")
    print("=" * 50)
    
    # Check Claude CLI version
    if not check_claude_cli_version():
        print("\n⚠️ Could not determine Claude CLI version, this may indicate it's not properly installed.")
    
    # Check Claude CLI help
    if not check_claude_cli_help():
        print("\n⚠️ Could not get Claude CLI help, this may indicate it's not properly installed.")
    
    # Check Claude CLI config
    if not check_claude_cli_config():
        print("\n⚠️ Could not get Claude CLI configuration from config.yaml.")
    
    # Try direct command execution
    print("\n" + "=" * 50)
    print("TESTING DIRECT CLAUDE COMMAND EXECUTION")
    if not try_direct_claude_command():
        print("\n⚠️ Direct Claude command execution failed. This is a basic test and should work if Claude CLI is properly set up.")
    
    # Test the prompt function with a simple prompt
    print("\n" + "=" * 50)
    print("TESTING PROMPT_CLAUDE_DIRECTLY FUNCTION")
    prompt = "Write hello world. using bash"
    debug_prompt_claude(prompt)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())