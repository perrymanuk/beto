"""
Simple direct test for the Tavily web search tool.

This script directly creates and invokes the web_search tool without using the agent.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables (including TAVILY_API_KEY)
load_dotenv()

# Add project root to sys.path to ensure imports work
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

def main():
    # Verify Tavily API key
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("ERROR: TAVILY_API_KEY environment variable not set.")
        print("Please set this variable in your .env file or export it before running this script.")
        print("You can get an API key from https://tavily.com/")
        return 1
    
    print(f"TAVILY_API_KEY is set: {bool(api_key)}")
    
    try:
        # Import the create_tavily_search_tool function
        from radbot.tools.web_search_tools import create_tavily_search_tool
        
        # Create the search tool
        print("\nCreating Tavily search tool...")
        tool = create_tavily_search_tool(
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
        
        if tool is None:
            print("ERROR: Failed to create Tavily search tool!")
            return 1
        
        print(f"Tool created successfully: {tool}")
        print(f"Tool type: {type(tool).__name__}")
        
        # Prepare a test query
        query = "What is the current weather in New York City?"
        print(f"\nTesting search with query: '{query}'")
        
        # For FunctionTool in ADK 0.3.0, we can access the function directly
        if hasattr(tool, 'func'):
            print("Using tool.func directly...")
            try:
                result = tool.func(query)
                print("\nSearch successful! Result:")
                print("=" * 80)
                print(result)
                print("=" * 80)
                return 0
            except Exception as e:
                print(f"ERROR invoking tool.func: {e}")
                import traceback
                traceback.print_exc()
        
        # If that doesn't work, try the advanced method of processing an LLM request
        if hasattr(tool, 'process_llm_request'):
            print("Using process_llm_request method...")
            try:
                # Create a simple dict that mimics an LLM request with arguments
                fake_request = {
                    "arguments": {
                        "query": query
                    }
                }
                result = tool.process_llm_request(fake_request)
                print("\nSearch successful! Result:")
                print("=" * 80)
                print(result)
                print("=" * 80)
                return 0
            except Exception as e:
                print(f"ERROR invoking process_llm_request: {e}")
                import traceback
                traceback.print_exc()
        
        # Last resort: attempt to call the tool directly like a function
        print("Attempting to call tool as a function...")
        try:
            result = tool(query)
            print("\nSearch successful! Result:")
            print("=" * 80)
            print(result)
            print("=" * 80)
            return 0
        except Exception as e:
            print(f"ERROR calling tool directly: {e}")
            import traceback
            traceback.print_exc()
        
        # If all attempts fail, print available methods for debugging
        print("\nCould not invoke tool. Available attributes:")
        for attr in dir(tool):
            if not attr.startswith('__'):
                print(f"- {attr}")
        
        return 1
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
