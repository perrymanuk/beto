#!/usr/bin/env python3
"""
Test script for the simplified Claude CLI direct prompting functionality.

This script tests our streamlined implementation that focuses only on the 
prompt functionality of Claude CLI.
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
    """Test the simplified Claude CLI prompting functionality."""
    try:
        # Import the prompting function
        from radbot.tools.claude_prompt import prompt_claude, create_claude_prompt_tool
        
        # Define a simple prompt
        prompt = "What is the capital of France? Give a short answer."
        
        # Test 1: Direct function call
        print(f"Test 1: Sending prompt to Claude CLI: {prompt}")
        result = prompt_claude(prompt)
        
        if result.get("success", False):
            print("\n=== CLAUDE RESPONSE ===")
            response = result.get("response", "")
            if isinstance(response, dict):
                print(json.dumps(response, indent=2))
            else:
                print(response)
                
            print("\nTest 1: ✅ Success")
        else:
            print(f"\nTest 1: ❌ Failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
            
        # Test 2: Tool creation
        print("\nTest 2: Creating Claude prompt tool")
        tool = create_claude_prompt_tool()
        
        if tool:
            print(f"Created tool: {getattr(tool, 'name', None) or getattr(tool, '__name__', str(tool))}")
            print("\nTest 2: ✅ Success")
        else:
            print(f"\nTest 2: ❌ Failed")
            print("Could not create Claude prompt tool")
            return False
        
        return True
            
    except ImportError as e:
        print(f"Error importing module: {e}")
        return False
    except Exception as e:
        print(f"Error testing Claude prompt: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_integration():
    """Test the web interface integration with the simplified approach."""
    try:
        # Import the SessionRunner class
        from radbot.web.api.session import SessionRunner
        
        # Create a test session
        session_id = "test-claude-prompt-session"
        user_id = f"web_user_{session_id}"
        
        # Create a session runner
        print("\nTest 3: Testing web integration")
        runner = SessionRunner(user_id=user_id, session_id=session_id)
        
        # Check if the root agent has tools
        if hasattr(runner.runner.agent, "tools"):
            # Find the Claude prompt tool
            claude_tools = []
            for tool in runner.runner.agent.tools:
                tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
                if "claude" in str(tool_name).lower() or "prompt" in str(tool_name).lower():
                    claude_tools.append(tool_name)
            
            if claude_tools:
                print(f"✅ Found {len(claude_tools)} Claude tools in the agent: {', '.join(claude_tools)}")
                print("\nTest 3: ✅ Success")
                return True
            else:
                print(f"❌ No Claude tools found in the agent")
                print(f"Available tools: {[getattr(t, 'name', None) or getattr(t, '__name__', str(t)) for t in runner.runner.agent.tools]}")
                print("\nTest 3: ❌ Failed")
                return False
        else:
            print("❌ Agent has no tools attribute")
            print("\nTest 3: ❌ Failed")
            return False
    
    except ImportError as e:
        print(f"❌ Could not import required module: {e}")
        print("\nTest 3: ❌ Failed")
        return False
    except Exception as e:
        print(f"❌ Error in test_web_integration: {e}")
        print("\nTest 3: ❌ Failed")
        return False

def main():
    """Main entry point."""
    print("=" * 50)
    print("SIMPLIFIED CLAUDE CLI PROMPTING TEST")
    print("=" * 50)
    
    success1 = test_claude_prompt()
    success2 = test_web_integration()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Direct Prompt Test: {'✅ Success' if success1 else '❌ Failed'}")
    print(f"Web Integration Test: {'✅ Success' if success2 else '❌ Failed'}")
    
    if success1 and success2:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())