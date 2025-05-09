#!/usr/bin/env python3
"""
Test script for the improved Claude CLI direct prompting functionality.

This script tests the improved prompt_claude_directly function which now handles
the "(no content)" case by falling back to non-JSON mode.
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

def test_claude_prompt(prompt):
    """Test the Claude CLI direct prompting functionality with a specific prompt."""
    try:
        # Import the direct prompting function
        from radbot.tools.mcp.direct_claude_cli import prompt_claude_directly
        
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
    print("CLAUDE CLI DIRECT PROMPTING TEST (IMPROVED)")
    print("=" * 50)
    
    # Test case 1: Previously problematic prompt
    print("\nTest Case 1: Previously problematic prompt")
    success1 = test_claude_prompt("Write hello world. using bash")
    
    # Test case 2: More explicit programming prompt
    print("\nTest Case 2: More explicit programming prompt")
    success2 = test_claude_prompt("Write a bash script that prints 'Hello World'")
    
    # Test case 3: Creative prompt
    print("\nTest Case 3: Creative prompt")
    success3 = test_claude_prompt("Write a haiku about programming")
    
    # Test case 4: Question prompt
    print("\nTest Case 4: Question prompt")
    success4 = test_claude_prompt("What's the capital of France?")
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Test Case 1 (Previously problematic prompt): {'✅ Success' if success1 else '❌ Failed'}")
    print(f"Test Case 2 (Explicit programming prompt): {'✅ Success' if success2 else '❌ Failed'}")
    print(f"Test Case 3 (Creative prompt): {'✅ Success' if success3 else '❌ Failed'}")
    print(f"Test Case 4 (Question prompt): {'✅ Success' if success4 else '❌ Failed'}")
    
    if all([success1, success2, success3, success4]):
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())