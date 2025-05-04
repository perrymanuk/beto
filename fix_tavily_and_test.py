#!/usr/bin/env python3
"""
This script fixes the Tavily web search tool and RadBotAgent compatibility issues,
then runs a test to verify the fix works.

It:
1. Applies the fix to the RadBotAgent class
2. Creates a direct test of the Tavily web search tool
3. Tests the web search functionality through the agent
"""

import os
import sys
import shutil
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def backup_file(path):
    """Create a backup of a file."""
    backup_path = f"{path}.bak"
    if os.path.exists(path):
        print(f"Creating backup of {path} to {backup_path}")
        shutil.copy2(path, backup_path)
    return backup_path

def apply_agent_fix():
    """Apply the fix to the RadBotAgent class."""
    # Paths to the original and fixed files
    original_path = "/Users/perry.manuk/git/perrymanuk/radbot/radbot/agent/agent.py"
    fixed_path = "/Users/perry.manuk/git/perrymanuk/radbot/radbot/agent/agent.py.fixed"
    
    # Create a backup of the original file
    backup_path = backup_file(original_path)
    
    # Copy the fixed file to the original location
    if os.path.exists(fixed_path):
        print(f"Applying fix from {fixed_path} to {original_path}")
        shutil.copy2(fixed_path, original_path)
        print("Fix applied successfully.")
        return True
    else:
        print(f"ERROR: Fixed file {fixed_path} not found!")
        return False

def test_direct_tavily_tool():
    """Test the Tavily web search tool directly."""
    print("\n=== Testing Tavily Web Search Tool Directly ===")
    
    # Check for Tavily API key
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("ERROR: TAVILY_API_KEY environment variable not set.")
        print("Please set this variable in your .env file.")
        return False
    
    try:
        # Import the create_tavily_search_tool function
        from radbot.tools.web_search_tools import create_tavily_search_tool
        
        # Create the search tool
        print("Creating Tavily search tool...")
        tool = create_tavily_search_tool(
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
        
        if tool is None:
            print("ERROR: Failed to create Tavily search tool!")
            return False
        
        print(f"Tool created successfully: {tool}")
        print(f"Tool type: {type(tool).__name__}")
        
        # Access the function directly and use it
        if hasattr(tool, 'func') and callable(tool.func):
            print("Using tool.func directly...")
            query = "What is the current weather in New York City?"
            
            print(f"Searching for: {query}")
            result = tool.func(query)
            
            if result:
                print("\nSearch successful! Result:")
                print("=" * 80)
                print(result[:500] + "..." if len(result) > 500 else result)
                print("=" * 80)
                return True
            else:
                print("ERROR: Search returned None or empty result")
                return False
        else:
            print("ERROR: Tool does not have a callable func attribute")
            print(f"Available attributes: {[attr for attr in dir(tool) if not attr.startswith('__')]}")
            return False
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_with_tavily():
    """Test the RadBotAgent with the Tavily web search tool."""
    print("\n=== Testing RadBotAgent with Tavily Web Search ===")
    
    try:
        # Import the radbot modules
        from radbot.agent import create_websearch_agent
        
        # Create an agent with web search capabilities
        print("Creating agent with web search capabilities...")
        agent = create_websearch_agent(
            max_results=3,
            search_depth="advanced"
        )
        
        if agent is None:
            print("ERROR: Failed to create agent!")
            return False
        
        print(f"Agent created successfully: {agent}")
        
        # Process a message that requires web search
        query = "What is the current weather in New York City?"
        print(f"Processing message: '{query}'")
        
        # Use process_message method which should now work with the fix
        try:
            response = agent.process_message(
                user_id="test_user",
                message=query
            )
            
            if response:
                print("\nAgent response:")
                print("=" * 80)
                print(response[:500] + "..." if len(response) > 500 else response)
                print("=" * 80)
                return True
            else:
                print("ERROR: Agent returned None or empty response")
                return False
            
        except Exception as e:
            print(f"ERROR processing message: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the fix and tests."""
    print("=== Tavily Web Search Fix and Test ===")
    
    # Step 1: Apply the RadBotAgent fix
    if not apply_agent_fix():
        print("Failed to apply RadBotAgent fix. Exiting.")
        return 1
    
    # Step 2: Test the Tavily search tool directly
    direct_test_result = test_direct_tavily_tool()
    
    # Step 3: Test the agent with Tavily search
    agent_test_result = test_agent_with_tavily()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Direct Tavily tool test: {'PASSED' if direct_test_result else 'FAILED'}")
    print(f"Agent with Tavily test: {'PASSED' if agent_test_result else 'FAILED'}")
    
    if direct_test_result and agent_test_result:
        print("\nAll tests PASSED! The Tavily web search tool is now working correctly.")
        return 0
    else:
        print("\nSome tests FAILED. Check the error messages above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
