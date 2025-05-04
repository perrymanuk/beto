#!/usr/bin/env python3
"""
Debug script to verify tools in the root agent.

This script loads the root agent and prints details about its tools,
helping to diagnose if the Tavily search tool is properly attached.
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def inspect_tool(tool, index):
    """Inspect a tool and print its details."""
    print(f"Tool {index}:")
    
    # Basic info
    tool_type = type(tool).__name__
    print(f"  Type: {tool_type}")
    
    # Try different attributes that might contain the name
    name = None
    if hasattr(tool, 'name'):
        name = tool.name
    elif hasattr(tool, '__name__'):
        name = tool.__name__
    elif callable(tool) and hasattr(tool, '__qualname__'):
        name = tool.__qualname__
    
    print(f"  Name: {name or 'Unknown'}")
    
    # For FunctionTool, check the wrapped function
    if hasattr(tool, 'func'):
        func = tool.func
        func_name = getattr(func, '__name__', str(func))
        print(f"  Wrapped function: {func_name}")
        
        # Check if function has docstring
        if func.__doc__:
            print(f"  Function docstring: {func.__doc__.strip().split('\n')[0]}")
    
    # Check for description
    if hasattr(tool, 'description'):
        print(f"  Description: {tool.description}")
    
    # Check for other important attributes
    for attr in ['is_long_running', 'process_llm_request', '_get_declaration']:
        if hasattr(tool, attr):
            print(f"  Has {attr}: Yes")
    
    print()

def main():
    try:
        print("Loading root agent from agent.py...")
        
        # Import the root agent
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agent import root_agent
        
        print(f"Root agent loaded successfully: {root_agent}")
        print(f"Agent type: {type(root_agent).__name__}")
        print(f"Model: {getattr(root_agent, 'model', 'Unknown')}")
        
        # Get all tools
        tools = getattr(root_agent, 'tools', [])
        tool_count = len(tools) if tools else 0
        print(f"\nAgent has {tool_count} tools:")
        
        # Check specifically for web_search or tavily tools
        web_search_tools = []
        
        # Inspect each tool
        for i, tool in enumerate(tools):
            inspect_tool(tool, i+1)
            
            # Check if this looks like a web search tool
            tool_name = None
            if hasattr(tool, 'name'):
                tool_name = tool.name
            elif hasattr(tool, '__name__'):
                tool_name = tool.__name__
            
            if tool_name and ('web_search' in tool_name.lower() or 'tavily' in tool_name.lower()):
                web_search_tools.append((i, tool_name))
        
        # Print summary of web search tools
        if web_search_tools:
            print(f"\nFound {len(web_search_tools)} web search tools:")
            for idx, name in web_search_tools:
                print(f"  - Tool {idx+1}: {name}")
        else:
            print("\nNo web search tools found in the agent's tools list!")
            
            # Try to recreate the Tavily search tool
            print("\nAttempting to create Tavily search tool directly...")
            from radbot.tools.web_search_tools import create_tavily_search_tool
            
            tool = create_tavily_search_tool(
                max_results=3,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=True
            )
            
            if tool:
                print("Successfully created Tavily search tool:")
                inspect_tool(tool, "New")
                
                # Test if the tool works
                print("\nTesting Tavily search tool...")
                try:
                    if hasattr(tool, 'func') and callable(tool.func):
                        result = tool.func("What is the current weather in New York City?")
                        print(f"Search successful! Result length: {len(str(result))} chars")
                        print(f"First 100 chars: {str(result)[:100]}...")
                    else:
                        print("Tool doesn't have a callable func attribute, can't test")
                except Exception as e:
                    print(f"Error testing tool: {e}")
            else:
                print("Failed to create Tavily search tool")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
