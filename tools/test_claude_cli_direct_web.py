#!/usr/bin/env python3
"""
Test script for the direct Claude CLI web integration.

This script tests the direct Claude CLI integration approach in the web interface
by checking if the tools are properly attached to the agent.
"""

import sys
import os
import logging
import time
import subprocess
import json
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_direct_claude_cli():
    """Test the direct Claude CLI implementation."""
    try:
        # Import the functions
        from radbot.tools.mcp.direct_claude_cli import (
            execute_command_directly,
            test_direct_claude_cli_connection
        )
        
        # First test basic connection
        result = test_direct_claude_cli_connection()
        
        if result.get("success", False):
            print(f"✅ Direct Claude CLI connection test successful")
            print(f"Output: {result.get('output', '')}")
            return True
        else:
            print(f"❌ Direct Claude CLI connection test failed")
            print(f"Error: {result.get('error', '')}")
            return False
    
    except ImportError as e:
        print(f"❌ Could not import direct_claude_cli module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing direct Claude CLI: {e}")
        return False

def test_direct_command():
    """Test direct command execution through execute_command_directly function."""
    try:
        from radbot.tools.mcp.direct_claude_cli import execute_command_directly
        
        # Execute a simple command
        result = execute_command_directly("echo 'Direct command test'")
        
        if result.get("success", False):
            print(f"✅ Direct command execution successful")
            print(f"Output: {result.get('output', '')}")
            return True
        else:
            print(f"❌ Direct command execution failed")
            print(f"Error: {result.get('error', '')}")
            return False
    
    except ImportError as e:
        print(f"❌ Could not import direct_claude_cli module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error executing direct command: {e}")
        return False

def test_command_through_shell_tool():
    """Test command execution through the shell tool with direct Claude CLI."""
    try:
        from radbot.tools.shell.shell_tool import execute_shell_command
        
        # Execute a simple command through the shell tool
        result = execute_shell_command("echo 'Shell tool command test'")
        
        if isinstance(result, dict) and result.get("success", False):
            print(f"✅ Shell tool command execution successful")
            print(f"Output: {result.get('output', '')}")
            return True
        else:
            print(f"❌ Shell tool command execution failed")
            print(f"Result: {result}")
            return False
    
    except ImportError as e:
        print(f"❌ Could not import shell_tool module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error executing shell tool command: {e}")
        return False

def test_agent_tool_creation():
    """Test that the agent tools are created successfully."""
    try:
        from radbot.tools.mcp.direct_claude_cli import create_direct_claude_cli_tools
        
        # Create the tools
        tools = create_direct_claude_cli_tools()
        
        if tools and len(tools) > 0:
            print(f"✅ Successfully created {len(tools)} direct Claude CLI tools")
            for tool in tools:
                tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
                print(f"  - {tool_name}")
                
            # Check if the prompt tool is included
            prompt_tool_found = False
            for tool in tools:
                tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
                if "prompt" in str(tool_name).lower():
                    prompt_tool_found = True
                    print(f"  ✅ Found direct prompting tool: {tool_name}")
                    break
                    
            if not prompt_tool_found:
                print(f"  ❌ Direct prompting tool not found")
                
            return True
        else:
            print(f"❌ Failed to create direct Claude CLI tools")
            return False
    
    except ImportError as e:
        print(f"❌ Could not import direct_claude_cli module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating agent tools: {e}")
        return False

def test_session_tool_loading():
    """Test that the SessionRunner can load the Claude CLI tools."""
    try:
        from radbot.web.api.session import SessionRunner
        
        # Create a test session
        session_id = "test-claude-cli-session"
        user_id = f"web_user_{session_id}"
        
        # Create a session runner
        runner = SessionRunner(user_id=user_id, session_id=session_id)
        
        # Check if the root agent has tools
        if hasattr(runner.runner.agent, "tools"):
            # Check for Claude CLI tools
            claude_tools = []
            for tool in runner.runner.agent.tools:
                tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
                if "claude" in str(tool_name).lower():
                    claude_tools.append(tool_name)
            
            if claude_tools:
                print(f"✅ Found {len(claude_tools)} Claude CLI tools in the agent")
                for tool in claude_tools:
                    print(f"  - {tool}")
                return True
            else:
                print(f"❌ No Claude CLI tools found in the agent")
                print(f"Agent has {len(runner.runner.agent.tools)} tools, but none are Claude CLI tools")
                return False
        else:
            print(f"❌ Agent has no tools attribute")
            return False
    
    except ImportError as e:
        print(f"❌ Could not import SessionRunner: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing session tool loading: {e}")
        return False

def main():
    """Main function to run the tests."""
    print("===== DIRECT CLAUDE CLI WEB INTEGRATION TEST =====\n")
    
    # Test direct Claude CLI
    print("\nTesting direct Claude CLI implementation...")
    direct_result = test_direct_claude_cli()
    
    # Test direct command execution
    print("\nTesting direct command execution...")
    command_result = test_direct_command()
    
    # Test command execution through shell tool
    print("\nTesting command execution through shell tool...")
    shell_result = test_command_through_shell_tool()
    
    # Test agent tool creation
    print("\nTesting agent tool creation...")
    tools_result = test_agent_tool_creation()
    
    # Test session tool loading
    print("\nTesting session tool loading...")
    session_result = test_session_tool_loading()
    
    # Summarize results
    print("\n===== TEST SUMMARY =====")
    results = {
        "Direct Claude CLI": direct_result,
        "Direct Command": command_result,
        "Shell Tool Command": shell_result,
        "Agent Tool Creation": tools_result,
        "Session Tool Loading": session_result
    }
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"Passed: {passed}/{total} tests")
    for test, result in results.items():
        print(f"  - {test}: {'✅ Passed' if result else '❌ Failed'}")
    
    print("\n===========================")
    
    # Return 0 if all tests passed, or 1 if any failed
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())