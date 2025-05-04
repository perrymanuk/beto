#!/usr/bin/env python3
"""
Fix script for the Tavily tool registration issue.

This script:
1. Tests if the Tavily tool is being created correctly
2. Patches the main agent.py file to properly register the Tavily search tool
3. Verifies the fix worked by inspecting the agent's tools
"""

import os
import sys
import logging
import importlib
from pprint import pformat
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def verify_tool_creation():
    """Verify that the Tavily search tool can be created properly."""
    print("\n=== Testing Tavily Tool Creation ===")
    
    try:
        from radbot.tools.web_search_tools import create_tavily_search_tool
        
        # Attempt to create the Tavily search tool
        tool = create_tavily_search_tool(
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
        
        if tool is None:
            print("ERROR: create_tavily_search_tool returned None!")
            return False
        
        # Check the type and attributes of the tool
        tool_type = type(tool).__name__
        print(f"Tool created successfully. Type: {tool_type}")
        
        # Check if it has a name attribute or __name__
        if hasattr(tool, 'name'):
            print(f"Tool name: {tool.name}")
        elif hasattr(tool, '__name__'):
            print(f"Function name: {tool.__name__}")
        else:
            print(f"Tool has no name attribute: {str(tool)}")
        
        return True, tool
    except Exception as e:
        print(f"ERROR in tool creation: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def apply_fix_to_agent():
    """Apply fix to ensure the tool is properly registered with the agent."""
    print("\n=== Applying Fix to Root Agent ===")
    
    # First verify we can create the tool
    tool_created, tool = verify_tool_creation()
    if not tool_created:
        print("Cannot proceed with fix since tool creation failed")
        return False
    
    try:
        # Now try to fix the root agent directly
        import agent
        from importlib import reload
        
        # Reload to get the most current version
        reload(agent)
        
        # Check if the root agent has the tool already
        if hasattr(agent, 'root_agent') and hasattr(agent.root_agent, 'tools'):
            original_tools = agent.root_agent.tools if agent.root_agent.tools else []
            print(f"Original root_agent has {len(original_tools)} tools")
            
            # Check if Tavily tool is already in the tools
            tavily_found = False
            for t in original_tools:
                tool_name = getattr(t, 'name', None) or getattr(t, '__name__', str(t))
                if 'web_search' in str(tool_name).lower() or 'tavily' in str(tool_name).lower():
                    tavily_found = True
                    print(f"Tavily tool already found in root_agent: {tool_name}")
                    break
            
            if not tavily_found:
                print("Tavily tool not found in root_agent - adding it now")
                
                # Add the tool to the root agent
                new_tools = list(original_tools)
                
                # Insert the Tavily tool at the beginning for higher priority
                new_tools.insert(0, tool)
                agent.root_agent.tools = new_tools
                
                print(f"Added Tavily tool to root_agent. Now has {len(new_tools)} tools")
                
                # Verify the tool was added
                tool_found = False
                for t in agent.root_agent.tools:
                    tool_name = getattr(t, 'name', None) or getattr(t, '__name__', str(t))
                    if 'web_search' in str(tool_name).lower() or 'tavily' in str(tool_name).lower():
                        tool_found = True
                        print(f"Verified Tavily tool is now in root_agent: {tool_name}")
                        break
                
                if not tool_found:
                    print("ERROR: Tavily tool still not found after attempted fix!")
                    return False
                
                return True
            else:
                print("Tavily tool already present in root_agent - no fix needed")
                return True
        else:
            print("ERROR: root_agent or tools attribute not found!")
            return False
    except Exception as e:
        print(f"ERROR applying fix: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_fix():
    """Verify that the fix worked by running a test query through the agent."""
    print("\n=== Verifying Fix with Test Query ===")
    
    try:
        import agent
        
        # Check if root_agent exists
        if not hasattr(agent, 'root_agent'):
            print("ERROR: root_agent not found in agent module!")
            return False
        
        # Attempt to process a message that would use web search
        test_query = "What is the current weather in New York City?"
        print(f"Testing query: {test_query}")
        
        # Try different ways to process the message
        try:
            # Test if direct processing works
            if hasattr(agent.root_agent, 'process'):
                print("Trying root_agent.process()...")
                result = agent.root_agent.process(test_query)
                print(f"Success! Got response from agent ({len(result)} chars)")
                print("First 200 chars of response:")
                print("="*50)
                print(result[:200] + "..." if len(result) > 200 else result)
                print("="*50)
                return True
        except Exception as e:
            print(f"Error using root_agent.process(): {e}")
            
        # Try alternate ways to process the message
        try:
            # Get the create_agent function
            if hasattr(agent, 'create_agent'):
                print("Trying agent.create_agent()...")
                test_agent = agent.create_agent()
                
                # Check if the tool is in this agent
                if hasattr(test_agent, 'tools'):
                    for t in test_agent.tools:
                        tool_name = getattr(t, 'name', None) or getattr(t, '__name__', str(t))
                        if 'web_search' in str(tool_name).lower() or 'tavily' in str(tool_name).lower():
                            print(f"Found Tavily tool in test_agent: {tool_name}")
                            break
                elif hasattr(test_agent, 'root_agent') and hasattr(test_agent.root_agent, 'tools'):
                    for t in test_agent.root_agent.tools:
                        tool_name = getattr(t, 'name', None) or getattr(t, '__name__', str(t))
                        if 'web_search' in str(tool_name).lower() or 'tavily' in str(tool_name).lower():
                            print(f"Found Tavily tool in test_agent.root_agent: {tool_name}")
                            break
                            
                print("Testing query with newly created agent...")
                if hasattr(test_agent, 'process_message'):
                    result = test_agent.process_message(user_id="test_user", message=test_query)
                    print(f"Success! Got response from test_agent ({len(result)} chars)")
                    print("First 200 chars of response:")
                    print("="*50)
                    print(result[:200] + "..." if len(result) > 200 else result)
                    print("="*50)
                    return True
                elif hasattr(test_agent, 'process'):
                    result = test_agent.process(test_query)
                    print(f"Success! Got response from test_agent ({len(result)} chars)")
                    print("First 200 chars of response:")
                    print("="*50)
                    print(result[:200] + "..." if len(result) > 200 else result)
                    print("="*50)
                    return True
        except Exception as e:
            print(f"Error using agent.create_agent(): {e}")
        
        print("Could not verify fix by running a test query")
        return False
    except Exception as e:
        print(f"ERROR verifying fix: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_all_agent_tools():
    """List all tools in the agent to help diagnose the issue."""
    print("\n=== Listing All Agent Tools ===")
    
    try:
        import agent
        
        if hasattr(agent, 'root_agent'):
            if hasattr(agent.root_agent, 'tools') and agent.root_agent.tools:
                print(f"root_agent has {len(agent.root_agent.tools)} tools:")
                for i, tool in enumerate(agent.root_agent.tools):
                    tool_name = None
                    if hasattr(tool, 'name'):
                        tool_name = tool.name
                    elif hasattr(tool, '__name__'):
                        tool_name = tool.__name__
                    else:
                        tool_name = str(tool)
                    print(f"  Tool {i+1}: {tool_name}")
            else:
                print("root_agent has no tools or tools attribute")
        else:
            print("No root_agent found in agent module")
        
        # Also check the create_agent function
        if hasattr(agent, 'create_agent'):
            print("\nTesting tools in agent.create_agent():")
            try:
                test_agent = agent.create_agent()
                if hasattr(test_agent, 'root_agent') and hasattr(test_agent.root_agent, 'tools') and test_agent.root_agent.tools:
                    print(f"agent.create_agent().root_agent has {len(test_agent.root_agent.tools)} tools:")
                    for i, tool in enumerate(test_agent.root_agent.tools):
                        tool_name = None
                        if hasattr(tool, 'name'):
                            tool_name = tool.name
                        elif hasattr(tool, '__name__'):
                            tool_name = tool.__name__
                        else:
                            tool_name = str(tool)
                        print(f"  Tool {i+1}: {tool_name}")
                else:
                    print("agent.create_agent().root_agent has no tools or tools attribute")
            except Exception as e:
                print(f"Error creating test agent: {e}")
    except Exception as e:
        print(f"ERROR listing tools: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the fix for the Tavily tool registration issue."""
    print("=== Tavily Tool Registration Fix ===")
    
    # Step 1: Verify if the tool can be created
    tool_created, _ = verify_tool_creation()
    if not tool_created:
        print("ERROR: Failed to create Tavily tool. Please check dependencies and API key.")
        return 1
    
    # Step 2: Apply the fix
    fix_applied = apply_fix_to_agent()
    if not fix_applied:
        print("ERROR: Failed to apply fix to agent.")
        
        # List tools to diagnose
        list_all_agent_tools()
        return 1
    
    # Step 3: Verify that the fix worked
    fix_verified = verify_fix()
    
    # Step 4: Print summary
    print("\n=== Fix Summary ===")
    print(f"Tool creation: {'SUCCEEDED' if tool_created else 'FAILED'}")
    print(f"Fix application: {'SUCCEEDED' if fix_applied else 'FAILED'}")
    print(f"Fix verification: {'SUCCEEDED' if fix_verified else 'FAILED'}")
    
    if tool_created and fix_applied and fix_verified:
        print("\nSuccess! The Tavily web search tool is now correctly registered with the agent.")
        print("When you run the web interface or CLI, the tool should be available.")
        return 0
    else:
        # Even if verification failed, list all tools to help diagnose
        list_all_agent_tools()
        
        print("\nWarning: Some steps failed. The fix might not be complete.")
        print("Please check the error messages above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
