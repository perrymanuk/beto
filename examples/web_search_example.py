"""
Example script demonstrating the web search functionality using Tavily API.

This script shows how to create an agent with web search capabilities
and process a simple message requiring web search.

Make sure to set the TAVILY_API_KEY environment variable before running this script.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level to see more information
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Main function
def main():
    # Verify environment
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("ERROR: TAVILY_API_KEY environment variable not set.")
        print("Please set this variable in your .env file or export it before running this script.")
        print("You can get an API key from https://tavily.com/")
        return 1
    
    # Import radbot modules
    try:
        from radbot.agent import create_websearch_agent
    except ImportError as e:
        print(f"ERROR: Failed to import required modules: {e}")
        print("Make sure you have all dependencies installed.")
        return 1
    
    # Create an agent with web search capabilities
    print("Creating agent with web search capabilities...")
    agent = create_websearch_agent(
        max_results=3,  # Limit to 3 results for brevity
        search_depth="advanced"  # Use advanced search for better results
    )
    
    # Check if the agent was created successfully
    if not agent:
        print("ERROR: Failed to create agent with web search capabilities.")
        return 1
    
    print("Agent created successfully.")
    print(f"Agent type: {type(agent).__name__}")
    
    # Examine the agent to find the right methods
    print("\nExamining agent attributes...")
    if hasattr(agent, 'root_agent'):
        print(f"Agent has root_agent of type: {type(agent.root_agent).__name__}")
        for method_name in ['process_message', 'process', 'run', '__call__']:
            if hasattr(agent.root_agent, method_name):
                print(f"  root_agent has method: {method_name}")
    
    # Print all methods on the agent
    methods = [method for method in dir(agent) if callable(getattr(agent, method)) and not method.startswith('__')]
    print(f"Available methods on agent: {', '.join(methods)}")
    
    # Try to use the most common method
    query_text = "What is the current weather in New York City?"
    print(f"\nProcessing message: '{query_text}'")
    print("This may take a few moments as it involves making API calls...\n")
    
    try:
        # First check if it's a RadBotAgent (our custom wrapper)
        if hasattr(agent, 'process_message') and callable(agent.process_message):
            print("Using agent.process_message()...")
            response = agent.process_message(
                user_id="example_user",
                message=query_text
            )
            if response:
                print_response(response)
                return 0
        
        # Try to find any callable method that could work
        for method_name in ['process_text', 'process', 'run', '__call__']:
            if hasattr(agent, method_name):
                method = getattr(agent, method_name)
                if callable(method):
                    print(f"Trying agent.{method_name}()...")
                    try:
                        # Try different argument combinations
                        try:
                            response = method(query_text)
                        except TypeError:
                            try:
                                response = method(message=query_text)
                            except TypeError:
                                try:
                                    response = method(user_id="example_user", message=query_text)
                                except TypeError:
                                    continue
                                    
                        if response:
                            print_response(response)
                            return 0
                    except Exception as e:
                        print(f"Error with {method_name}: {e}")
        
        # Try using the Tavily tool directly as a last resort
        print("\nAll agent methods failed. Trying to use the Tavily tool directly...")
        
        # Find the Tavily tool in the agent
        tavily_tool = None
        if hasattr(agent, 'tools'):
            print("Checking agent.tools...")
            for tool in agent.tools:
                if hasattr(tool, 'name') and 'web_search' in str(tool.name).lower():
                    tavily_tool = tool
                    break
        
        if not tavily_tool and hasattr(agent, 'root_agent') and hasattr(agent.root_agent, 'tools'):
            print("Checking agent.root_agent.tools...")
            for tool in agent.root_agent.tools:
                if hasattr(tool, 'name') and 'web_search' in str(tool.name).lower():
                    tavily_tool = tool
                    break
        
        if tavily_tool:
            print(f"Found Tavily tool: {tavily_tool}")
            print(f"Tool type: {type(tavily_tool).__name__}")
            
            # Try to invoke the tool directly
            result = None
            
            # Try different ways to invoke the tool
            if hasattr(tavily_tool, 'func') and callable(tavily_tool.func):
                print("Using tavily_tool.func directly...")
                result = tavily_tool.func(query_text)
            elif callable(tavily_tool):
                print("Using tavily_tool as callable...")
                result = tavily_tool(query_text)
            
            if result:
                print_response(result)
                return 0
            else:
                print("Failed to get results from the Tavily tool directly.")
                return 1
        else:
            print("Could not find the Tavily tool in the agent.")
            return 1
        
        print("All attempts to process the message failed.")
        return 1
    
    except Exception as e:
        print(f"ERROR processing message: {e}")
        import traceback
        traceback.print_exc()
        return 1

def print_response(response):
    """Print the response with a nice format."""
    print("=" * 80)
    print("RESPONSE:")
    print("-" * 80)
    print(response)
    print("=" * 80)

if __name__ == "__main__":
    sys.exit(main())
