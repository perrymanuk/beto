#!/usr/bin/env python3
"""
Test script for the Claude CLI direct prompting functionality in the web interface.

This script tests the integration of Claude CLI direct prompting with the web interface
by simulating how the API would use it.
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

def test_claude_web_prompt():
    """Test the Claude CLI direct prompting from web interface."""
    try:
        # Import the SessionRunner class
        from radbot.web.api.session import SessionRunner
        
        # Create a test session
        session_id = "test-claude-prompt-session"
        user_id = f"web_user_{session_id}"
        
        # Create a session runner
        runner = SessionRunner(user_id=user_id, session_id=session_id)
        
        # Check if the root agent has tools
        if hasattr(runner.runner.agent, "tools"):
            # Find the Claude CLI direct prompt tool
            prompt_tool = None
            for tool in runner.runner.agent.tools:
                tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
                if "prompt_claude" in str(tool_name).lower():
                    prompt_tool = tool
                    print(f"✅ Found Claude direct prompt tool: {tool_name}")
                    break
            
            if prompt_tool:
                # Try to call the module function directly
                try:
                    print("\nTesting direct import of prompt_claude_directly...")
                    
                    # Import the function directly
                    from radbot.tools.mcp.direct_claude_cli import prompt_claude_directly
                    
                    # Call the function with a simple prompt
                    result = prompt_claude_directly("What is the capital of France?")
                    
                    if result and isinstance(result, dict) and result.get("success", False):
                        print("✅ Successfully called prompt_claude_directly directly")
                        print("\n=== CLAUDE RESPONSE ===")
                        response = result.get("response", "")
                        if isinstance(response, dict):
                            print(json.dumps(response, indent=2))
                        else:
                            print(response)
                        return True
                    else:
                        print(f"❌ Function call failed: {result}")
                        return False
                except Exception as e:
                    print(f"❌ Error calling function: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                print("❌ Could not find Claude prompt tool in agent tools")
                print(f"Available tools: {[getattr(t, 'name', None) or getattr(t, '__name__', str(t)) for t in runner.runner.agent.tools]}")
                return False
        else:
            print("❌ Agent has no tools attribute")
            return False
    
    except ImportError as e:
        print(f"❌ Could not import required module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in test_claude_web_prompt: {e}")
        return False

def main():
    """Main entry point."""
    print("=" * 50)
    print("CLAUDE CLI DIRECT PROMPTING WEB INTERFACE TEST")
    print("=" * 50)
    
    success = test_claude_web_prompt()
    
    if success:
        print("\n✅ Claude CLI direct prompting web interface test successful")
    else:
        print("\n❌ Claude CLI direct prompting web interface test failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())