"""
Diagnostic script to test the Tavily web search tool.

This script isolates the Tavily tool to check its functionality and diagnose issues.
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
logger.info(f"TAVILY_API_KEY set: {bool(os.environ.get('TAVILY_API_KEY'))}")

# Add project root to sys.path to ensure imports work
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)
logger.info(f"Added project root to sys.path: {project_root}")

# First, check if langchain-community is installed
try:
    import importlib
    langchain_spec = importlib.util.find_spec("langchain_community")
    if langchain_spec is None:
        logger.error("langchain-community package not found!")
        print("ERROR: langchain-community package is not installed.")
        print("Try running: pip install 'langchain-community>=0.2.16'")
        sys.exit(1)
    else:
        logger.info(f"langchain-community package found: {langchain_spec.origin}")
        # Also check for the TavilySearchResults class
        try:
            from langchain_community.tools import TavilySearchResults
            logger.info("TavilySearchResults class found in langchain-community")
        except ImportError as e:
            logger.error(f"Failed to import TavilySearchResults: {e}")
            print("ERROR: TavilySearchResults not found in langchain-community package.")
            print("You may need to update your langchain-community package.")
            sys.exit(1)
except Exception as e:
    logger.error(f"Error checking langchain-community: {e}")
    sys.exit(1)

# Check if tavily-python is installed
try:
    import importlib
    tavily_spec = importlib.util.find_spec("tavily")
    if tavily_spec is None:
        logger.error("tavily-python package not found!")
        print("ERROR: tavily-python package is not installed.")
        print("Try running: pip install 'tavily-python>=0.3.8'")
        sys.exit(1)
    else:
        logger.info(f"tavily-python package found: {tavily_spec.origin}")
        # Let's also check the version
        import tavily
        logger.info(f"tavily-python version: {getattr(tavily, '__version__', 'unknown')}")
except Exception as e:
    logger.error(f"Error checking tavily-python: {e}")
    sys.exit(1)

# Now import our own Tavily tool implementation
try:
    from radbot.tools.web_search_tools import (
        create_tavily_search_tool, 
        HAVE_TAVILY
    )
    logger.info(f"HAVE_TAVILY from web_search_tools: {HAVE_TAVILY}")
except Exception as e:
    logger.error(f"Error importing web_search_tools: {e}")
    print(f"ERROR importing web_search_tools: {e}")
    sys.exit(1)

# Test different versions of the tool creation
def test_direct_tavily():
    """Test direct instantiation of LangChain's TavilySearchResults"""
    logger.info("Testing direct TavilySearchResults instantiation...")
    
    try:
        from langchain_community.tools import TavilySearchResults
        
        # Check if TAVILY_API_KEY is set
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            logger.warning("TAVILY_API_KEY environment variable not set")
            print("WARNING: TAVILY_API_KEY environment variable not set")
        
        # Create the tool anyway (for diagnostic purposes)
        tool = TavilySearchResults(
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True,
            include_images=False,
        )
        logger.info(f"TavilySearchResults tool created successfully: {tool}")
        
        # Try to run a search if API key is available
        if api_key:
            logger.info("Attempting search with direct TavilySearchResults tool...")
            result = tool.invoke("What is the current weather in New York?")
            logger.info(f"Search successful! Result length: {len(str(result))} chars")
            print("\nDirect TavilySearchResults search result:")
            print("="*50)
            print(result)
            print("="*50)
        else:
            logger.warning("Skipping search test due to missing API key")
        
        return True
    except Exception as e:
        logger.error(f"Error in direct TavilySearchResults test: {e}")
        print(f"ERROR in direct TavilySearchResults test: {e}")
        return False

def test_our_tavily_tool():
    """Test our wrapped Tavily search tool implementation"""
    logger.info("Testing our create_tavily_search_tool implementation...")
    
    try:
        # Create our tool
        tool = create_tavily_search_tool(
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
        
        if tool is None:
            logger.error("Our create_tavily_search_tool returned None!")
            print("ERROR: create_tavily_search_tool returned None!")
            return False
        
        logger.info(f"Our tool created successfully: {tool}")
        
        # Get the tool type
        tool_type = type(tool).__name__
        logger.info(f"Tool type: {tool_type}")
        
        # Print some tool attributes for debugging
        try:
            if hasattr(tool, 'name'):
                logger.info(f"Tool name: {tool.name}")
            elif hasattr(tool, '__name__'):
                logger.info(f"Function name: {tool.__name__}")
            else:
                logger.info(f"Tool has no name attribute: {str(tool)}")
        except Exception as e:
            logger.warning(f"Error accessing tool attributes: {e}")
        
        # Try to run a search if API key is available
        api_key = os.environ.get("TAVILY_API_KEY")
        if api_key:
            logger.info("Attempting search with our tool...")
            
            # The way to invoke depends on the tool type
            result = None
            
            # Try different ways to invoke the tool
            if hasattr(tool, "invoke"):
                logger.info("Using tool.invoke() method...")
                result = tool.invoke("What is the current weather in New York?")
            elif callable(tool):
                logger.info("Using tool as callable...")
                result = tool("What is the current weather in New York?")
            elif hasattr(tool, "function"):
                logger.info("Using tool.function attribute...")
                result = tool.function("What is the current weather in New York?")
            elif hasattr(tool, "__call__"):
                logger.info("Using tool.__call__ method...")
                result = tool.__call__("What is the current weather in New York?")
            else:
                tool_dir = dir(tool)
                logger.error(f"Don't know how to invoke tool. Available attributes: {tool_dir}")
                print(f"ERROR: Don't know how to invoke this tool type: {tool_type}")
                return False
            
            if result:
                logger.info(f"Search successful! Result length: {len(str(result))} chars")
                print("\nOur tool search result:")
                print("="*50)
                print(result)
                print("="*50)
            else:
                logger.warning("Search returned None or empty result")
        else:
            logger.warning("Skipping search test due to missing API key")
        
        return True
    except Exception as e:
        logger.error(f"Error in our tool test: {e}")
        print(f"ERROR in our tool test: {e}")
        return False

def test_adk_agent_with_tavily():
    """Test creating an ADK agent with our Tavily tool"""
    logger.info("Testing ADK agent with Tavily tool...")
    
    try:
        from google.adk.agents import Agent
        
        # Create our tool
        tavily_tool = create_tavily_search_tool(
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
        
        if tavily_tool is None:
            logger.error("create_tavily_search_tool returned None, can't create agent!")
            return False
        
        # Create a simple agent with the tool
        agent = Agent(
            name="test_tavily_agent",
            instruction="You are a helpful assistant that can search the web.",
            description="Test agent for Tavily search tool",
            tools=[tavily_tool]
        )
        
        logger.info(f"Agent created successfully: {agent}")
        
        # Try to explore the agent's tools
        if hasattr(agent, "tools") and agent.tools:
            logger.info(f"Agent has {len(agent.tools)} tools:")
            for i, tool in enumerate(agent.tools):
                tool_name = None
                if hasattr(tool, 'name'):
                    tool_name = tool.name
                elif hasattr(tool, '__name__'):
                    tool_name = tool.__name__
                else:
                    tool_name = str(tool)
                logger.info(f"  Tool {i+1}: {tool_name}")
        else:
            logger.warning("Agent doesn't have any tools or tools attribute!")
        
        # We won't try to process a message here as that requires more setup
        logger.info("Agent with Tavily tool created successfully")
        return True
    except Exception as e:
        logger.error(f"Error in ADK agent test: {e}")
        print(f"ERROR in ADK agent test: {e}")
        return False

def test_raw_tavily_api():
    """Test the raw Tavily API directly to isolate issues"""
    logger.info("Testing raw Tavily API directly...")
    
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        logger.warning("TAVILY_API_KEY environment variable not set, skipping test")
        print("WARNING: TAVILY_API_KEY environment variable not set, skipping test")
        return False
    
    try:
        from tavily import TavilyClient
        
        # Create a client
        client = TavilyClient(api_key=api_key)
        logger.info("TavilyClient created successfully")
        
        # Try a search
        logger.info("Attempting search with raw TavilyClient...")
        response = client.search(
            query="What is the current weather in New York?",
            search_depth="advanced",
            max_results=3,
            include_answer=True,
            include_raw_content=True,
            include_images=False
        )
        
        logger.info(f"Raw search successful! Result: {response}")
        print("\nRaw Tavily API search result:")
        print("="*50)
        print(response)
        print("="*50)
        
        return True
    except Exception as e:
        logger.error(f"Error in raw Tavily API test: {e}")
        print(f"ERROR in raw Tavily API test: {e}")
        return False

if __name__ == "__main__":
    print("\n------- TAVILY SEARCH TOOL DIAGNOSTIC SCRIPT --------")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Run all tests
    print("\n1. Testing direct LangChain TavilySearchResults...")
    direct_result = test_direct_tavily()
    print(f"Direct LangChain test {'PASSED' if direct_result else 'FAILED'}")
    
    print("\n2. Testing our create_tavily_search_tool implementation...")
    our_result = test_our_tavily_tool()
    print(f"Our tool test {'PASSED' if our_result else 'FAILED'}")
    
    print("\n3. Testing ADK agent with Tavily tool...")
    agent_result = test_adk_agent_with_tavily()
    print(f"ADK agent test {'PASSED' if agent_result else 'FAILED'}")
    
    print("\n4. Testing raw Tavily API...")
    raw_result = test_raw_tavily_api()
    print(f"Raw Tavily API test {'PASSED' if raw_result else 'FAILED'}")
    
    # Print summary
    print("\n------- TEST SUMMARY --------")
    all_passed = direct_result and our_result and agent_result and raw_result
    print(f"Direct LangChain test: {'PASSED' if direct_result else 'FAILED'}")
    print(f"Our tool test: {'PASSED' if our_result else 'FAILED'}")
    print(f"ADK agent test: {'PASSED' if agent_result else 'FAILED'}")
    print(f"Raw Tavily API test: {'PASSED' if raw_result else 'FAILED'}")
    
    if all_passed:
        print("\nAll tests PASSED! The Tavily search tool seems to be working correctly in isolation.")
        print("If it's still not working in the main application, the issue might be with how it's being attached to the agent.")
    else:
        print("\nSome tests FAILED. Check the error messages above for details.")
