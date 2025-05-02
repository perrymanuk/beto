"""
Root agent.py file for ADK web interface.

This file is used by the ADK web interface to create the agent with all needed tools.
"""

import logging
import os
from typing import Optional, Any, List

from dotenv import load_dotenv
from google.adk.tools import FunctionTool
from google.adk.agents import Agent

# Import agent factories and tools
from raderbot.tools.basic_tools import get_current_time, get_weather
from raderbot.tools.memory_tools import search_past_conversations, store_important_information
from raderbot.tools.mcp_tools import search_home_assistant_entities
from raderbot.tools.web_search_tools import create_tavily_search_tool
from raderbot.config import config_manager

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def create_agent(tools: Optional[List[Any]] = None):
    """
    Create the agent with all necessary tools.
    
    This is the entry point used by ADK web to create the agent.
    
    Args:
        tools: Optional list of additional tools to include
        
    Returns:
        An ADK BaseAgent instance
    """
    logger.info("Creating agent for ADK web interface")
    
    # Start with basic tools
    basic_tools = [get_current_time, get_weather]
    
    # Always include memory tools
    memory_tools = [search_past_conversations, store_important_information]
    logger.info(f"Including memory tools: {[t.__name__ for t in memory_tools]}")
    
    # Add Home Assistant entity search
    basic_tools.append(search_home_assistant_entities)
    
    # Add Tavily web search tool
    try:
        web_search_tool = create_tavily_search_tool(
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
        if web_search_tool:
            basic_tools.insert(0, web_search_tool)  # Add as highest priority
            logger.info("Successfully added web_search tool to base tools")
    except Exception as e:
        logger.warning(f"Failed to create Tavily search tool: {str(e)}")
        
        # If the function tool creation failed, try a simple direct function approach
        try:
            # Define a simple function without decorators
            def web_search(query: str) -> str:
                """Search the web for current information on a topic."""
                from raderbot.tools.web_search_tools import HAVE_TAVILY, TavilySearchResults
                import os
                
                logger.info(f"Running fallback web search for query: {query}")
                
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
                    logger.error(f"Error in fallback web_search: {str(e)}")
                    return f"Error searching for '{query}': {str(e)}"
            
            # Try to wrap it with FunctionTool (ADK 0.3.0 version)
            try:
                from google.adk.tools import FunctionTool
                # In ADK 0.3.0, FunctionTool only takes a single function parameter
                web_search.__name__ = "web_search"  # Ensure function name is correct for LLM
                search_tool = FunctionTool(web_search)
                basic_tools.insert(0, search_tool)
            except Exception:
                # If FunctionTool fails, just add the raw function
                basic_tools.insert(0, web_search)
                
            logger.info("Added fallback web_search tool to base tools")
        except Exception as e:
            logger.error(f"Failed to create fallback web search tool: {str(e)}")
    
    # Add any additional tools if provided
    all_tools = list(basic_tools) + memory_tools
    if tools:
        all_tools.extend(tools)
    
    # Log all tools being added
    tool_names = []
    for tool in all_tools:
        if hasattr(tool, '__name__'):
            tool_names.append(tool.__name__)
        elif hasattr(tool, 'name'):
            tool_names.append(tool.name)
        else:
            tool_names.append(str(type(tool)))
    logger.info(f"Creating web agent with tools: {', '.join(tool_names)}")
    
    # Get the instruction
    try:
        instruction = config_manager.get_instruction("main_agent")
    except Exception as e:
        logger.warning(f"Failed to load main_agent instruction: {str(e)}")
        instruction = """You are a helpful assistant. Your goal is to understand the user's request and fulfill it by using available tools."""
    
    # Create an ADK Agent directly - this is what the web UI expects
    agent = Agent(
        name="raderbot_web",
        model=config_manager.get_main_model(),
        instruction=instruction,
        description="The main agent that handles user requests with memory capabilities.",
        tools=all_tools
    )
    
    # Initialize memory service for the web UI and store API keys
    # We'll add this to the context so tools can access it
    try:
        from raderbot.memory.qdrant_memory import QdrantMemoryService
        memory_service = QdrantMemoryService()
        logger.info("Successfully initialized QdrantMemoryService for web agent")
        
        # Store memory service in ADK's global tool context
        # ADK web will use this Runner automatically
        from google.adk.runners import Runner, InvocationContext
        from google.adk.sessions import InMemorySessionService
        
        # Create a Runner with memory service
        runner = Runner(
            agent=agent,
            app_name="raderbot",
            session_service=InMemorySessionService(),
            memory_service=memory_service
        )
        
        # Directly use setattr to add memory service to tool context
        # This makes it accessible in tool implementations
        from google.adk.tools.tool_context import ToolContext
        setattr(ToolContext, "memory_service", memory_service)
        logger.info("Added memory service to tool context")
        
        # Store API keys in ToolContext for tools to access
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        if tavily_api_key:
            setattr(ToolContext, "tavily_api_key", tavily_api_key)
            logger.info("Stored Tavily API key in global ToolContext")
            
    except Exception as e:
        logger.warning(f"Failed to initialize memory service for web agent: {str(e)}")
    
    logger.info(f"Created ADK BaseAgent for web UI with {len(all_tools)} tools")
    return agent