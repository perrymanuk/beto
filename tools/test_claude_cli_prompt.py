#!/usr/bin/env python3
"""
Test script for the Claude CLI direct prompting functionality.

This script sends a simple prompt to Claude CLI using the direct prompting function
and displays the result.
"""

import sys
import os
import logging
import json
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_claude_prompt():
    """Test the Claude CLI direct prompting functionality."""
    try:
        # Import the direct prompting function
        from radbot.tools.mcp.direct_claude_cli import prompt_claude_directly
        
        # Define a simple prompt
        prompt = "What is the capital of France? Give a short answer."
        
        # Use minimal parameters (just the prompt) for maximum compatibility
        print(f"Sending prompt to Claude CLI: {prompt}")
        
        # Send the prompt with no optional parameters
        result = prompt_claude_directly(prompt)
        
        # Process the result
        if result.get("success", False):
            response = result.get("response", "")
            print("\n=== CLAUDE RESPONSE ===")
            if isinstance(response, dict):
                # Pretty-print the JSON response
                print(json.dumps(response, indent=2))
            else:
                # Print raw response
                print(response)
                
            return True
        else:
            print(f"\n=== ERROR ===")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
            
    except ImportError as e:
        print(f"Error importing module: {e}")
        return False
    except Exception as e:
        print(f"Error testing Claude prompt: {e}")
        return False

def main():
    """Main entry point."""
    print("=" * 50)
    print("CLAUDE CLI DIRECT PROMPTING TEST")
    print("=" * 50)
    
    success = test_claude_prompt()
    
    if success:
        print("\n✅ Claude CLI direct prompting test successful")
    else:
        print("\n❌ Claude CLI direct prompting test failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())