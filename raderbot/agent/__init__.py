"""
Agent package for the RaderBot framework.
"""

from raderbot.agent.agent import (
    RaderBotAgent, 
    AgentFactory, 
    create_agent,
    create_runner
)
from raderbot.agent.memory_agent_factory import create_memory_enabled_agent
from raderbot.agent.web_search_agent_factory import (
    create_websearch_agent,
    create_websearch_enabled_root_agent
)

# Create a default root_agent for ADK web interface
from raderbot.tools.basic_tools import get_current_time, get_weather
from raderbot.tools.memory_tools import search_past_conversations, store_important_information
from raderbot.tools.web_search_tools import create_tavily_search_tool
import logging
from raderbot.config import config_manager
from google.adk.agents import Agent

# Get the instruction for the web agent
try:
    instruction = config_manager.get_instruction("main_agent")
except Exception as e:
    logging.warning(f"Failed to load main_agent instruction: {str(e)}")
    instruction = """You are a helpful assistant. Your goal is to understand the user's request and fulfill it by using available tools."""

# Add memory tools to base tools
base_tools = [get_current_time, get_weather, search_past_conversations, store_important_information]

# Add Tavily web search tool
try:
    web_search_tool = create_tavily_search_tool(
        max_results=3,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True
    )
    if web_search_tool:
        base_tools.insert(0, web_search_tool)  # Add as highest priority
        logging.info("Successfully added web_search tool to base tools")
except Exception as e:
    logging.warning(f"Failed to create Tavily search tool: {str(e)}")
    
    # If the function tool creation failed, try a simple direct function approach
    try:
        # Define a simple function without decorators
        def web_search(query: str) -> str:
            """Search the web for current information on a topic."""
            from raderbot.tools.web_search_tools import HAVE_TAVILY, TavilySearchResults
            import os
            
            logging.info(f"Running fallback web search for query: {query}")
            
            try:
                if HAVE_TAVILY and os.environ.get("TAVILY_API_KEY"):
                    # Instantiate LangChain's Tavily search tool
                    tavily_search = TavilySearchResults(
                        max_results=3,
                        search_depth="advanced",
                        include_answer=True,
                        include_raw_content=True,
                        include_images=False,
                    )
                    # Use the tool directly
                    results = tavily_search.invoke(query)
                    return results
                else:
                    return f"Unable to search for '{query}'. Tavily search is not available."
            except Exception as e:
                logging.error(f"Error in fallback web_search: {str(e)}")
                return f"Error searching for '{query}': {str(e)}"
        
        # Try to wrap it with FunctionTool (ADK 0.3.0 version)
        try:
            from google.adk.tools import FunctionTool
            # In ADK 0.3.0, FunctionTool only takes a single function parameter
            web_search.__name__ = "web_search"  # Ensure function name is correct for LLM
            search_tool = FunctionTool(web_search)
            base_tools.insert(0, search_tool)
        except Exception:
            # If FunctionTool fails, just add the raw function
            base_tools.insert(0, web_search)
            
        logging.info("Added fallback web_search tool to base tools")
    except Exception as e:
        logging.error(f"Failed to create fallback web search tool: {str(e)}")

logging.info(f"Creating web agent with tools: {[t.__name__ if hasattr(t, '__name__') else t.name if hasattr(t, 'name') else str(t) for t in base_tools]}")

# Create the BaseAgent directly - this is what ADK web expects
root_agent = Agent(
    name="raderbot_web",
    model=config_manager.get_main_model(),
    instruction=instruction,
    description="The main agent that handles user requests with memory capabilities.",
    tools=base_tools
)

logging.info(f"Created ADK BaseAgent for web UI with {len(base_tools)} tools")

# Initialize a global memory service and store API keys that will be accessible to tools
try:
    from raderbot.memory.qdrant_memory import QdrantMemoryService
    from google.adk.tools.tool_context import ToolContext
    import os

    # Create memory service
    memory_service = QdrantMemoryService()
    logging.info(f"Created memory service with collection: {memory_service.collection_name}")
    
    # Store in ToolContext class (important: this is a class attribute!)
    setattr(ToolContext, "memory_service", memory_service)
    logging.info("Successfully stored memory service in global ToolContext")
    
    # Store API keys in ToolContext for tools to access
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if tavily_api_key:
        setattr(ToolContext, "tavily_api_key", tavily_api_key)
        logging.info("Stored Tavily API key in global ToolContext")
    
    # For extra safety, store it in our custom global for the whole module
    import sys
    sys.modules[__name__]._memory_service = memory_service
    
except Exception as e:
    logging.error(f"Failed to initialize memory service: {str(e)}")
    import traceback
    logging.error(f"Traceback: {traceback.format_exc()}")

# Export classes and functions for easy import
__all__ = [
    'RaderBotAgent',
    'AgentFactory',
    'create_agent',
    'create_runner',
    'create_memory_enabled_agent',
    'create_websearch_agent',
    'create_websearch_enabled_root_agent',
    'root_agent'
]