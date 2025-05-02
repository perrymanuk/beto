"""
Web search tools for radbot agents.

This module provides tools for web search capabilities using various search APIs.
"""

import os
import logging
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
from google.adk.tools.langchain_tool import LangchainTool

# Try to import Tavily search tool from LangChain
try:
    from langchain_community.tools import TavilySearchResults
    HAVE_TAVILY = True
except ImportError:
    HAVE_TAVILY = False

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def create_tavily_search_tool(max_results=5, search_depth="advanced", include_answer=True, include_raw_content=True, include_images=False):
    """
    Create a Tavily search tool that can be used by the agent.
    
    This tool allows the agent to search the web via Tavily's search API.
    
    Args:
        max_results: Maximum number of search results to return (default: 5)
        search_depth: Search depth, either "basic" or "advanced" (default: "advanced")
        include_answer: Whether to include an AI-generated answer (default: True) 
        include_raw_content: Whether to include the raw content of search results (default: True)
        include_images: Whether to include images in search results (default: False)
        
    Returns:
        The created Tavily search tool wrapped for ADK, or None if creation fails
    """
    if not HAVE_TAVILY:
        logger.error("Tavily search tool requires langchain-community package with TavilySearchResults")
        return None
        
    # Check that TAVILY_API_KEY environment variable is set
    if not os.environ.get("TAVILY_API_KEY"):
        logger.error("TAVILY_API_KEY environment variable not set. The Tavily search tool will not function correctly.")
        # We don't return None here to allow for testing/development without credentials
    
    try:
        # Create a direct function tool for web search instead of using LangChain wrapper
        from google.adk.tools import FunctionTool
        
        def web_search(query: str, tool_context=None):
            """
            Search the web for information about the query.
            
            Args:
                query: The search query
                tool_context: Optional tool context for accessing memory
                
            Returns:
                Search results as text
            """
            logger.info(f"Running web search for query: {query}")
            
            try:
                # Ensure we have the Tavily API key, either from environment or a tool context
                api_key = os.environ.get("TAVILY_API_KEY")
                
                if not api_key and tool_context:
                    # Try to get from tool context
                    api_key = getattr(tool_context, "tavily_api_key", None)
                
                # If we still don't have an API key, check for a global one
                if not api_key:
                    try:
                        from google.adk.tools.tool_context import ToolContext
                        api_key = getattr(ToolContext, "tavily_api_key", None)
                    except Exception:
                        pass
                        
                if HAVE_TAVILY and api_key:
                    # Set the API key explicitly
                    os.environ["TAVILY_API_KEY"] = api_key
                    
                    # Instantiate LangChain's Tavily search tool
                    tavily_search = TavilySearchResults(
                        max_results=max_results,
                        search_depth=search_depth,
                        include_answer=include_answer,
                        include_raw_content=include_raw_content,
                        include_images=include_images,
                    )
                    # Use the tool directly
                    results = tavily_search.invoke(query)
                    return results
                else:
                    logger.warning(f"Tavily search unavailable: API={bool(api_key)}, imports={HAVE_TAVILY}")
                    return f"Unable to search for '{query}'. Tavily search is not available. Please ensure TAVILY_API_KEY is set."
            except Exception as e:
                logger.error(f"Error in web_search: {str(e)}")
                return f"Error searching for '{query}': {str(e)}"
        
        # Create a function tool for ADK 0.3.0
        # In ADK 0.3.0, FunctionTool only takes a single function parameter
        try:
            # ADK 0.3.0 approach - FunctionTool with just the function
            search_tool = FunctionTool(web_search)
            # Make sure the function name is correct for the LLM to find
            web_search.__name__ = "web_search"
            
            logger.info("Created web search tool using ADK 0.3.0 FunctionTool approach")
        except Exception as e:
            # If that doesn't work, just use the function directly
            logger.warning(f"Function tool creation error: {str(e)}, returning raw function")
            search_tool = web_search
        
        logger.info(f"Successfully created direct web search tool with max_results={max_results}, search_depth={search_depth}")
        return search_tool
        
    except Exception as e:
        logger.error(f"Failed to create Tavily search tool: {str(e)}")
        return None


def create_tavily_search_enabled_agent(agent_factory, base_tools=None, max_results=5, search_depth="advanced"):
    """
    Create an agent with Tavily web search capabilities.
    
    Args:
        agent_factory: Function to create an agent (like AgentFactory.create_root_agent or create_memory_enabled_agent)
        base_tools: Optional list of base tools to include
        max_results: Maximum number of search results to return (default: 5)
        search_depth: Search depth, either "basic" or "advanced" (default: "advanced")
        
    Returns:
        Agent: The created agent with Tavily search tool, or None if creation fails
    """
    try:
        # Start with base tools or empty list
        tools = list(base_tools or [])
        
        # Create the Tavily search tool
        tavily_tool = create_tavily_search_tool(
            max_results=max_results,
            search_depth=search_depth,
            include_answer=True,
            include_raw_content=True,
            include_images=False  # Default to no images to save tokens
        )
        
        if tavily_tool:
            # Add the Tavily search tool at the start of the list for higher priority
            tools.insert(0, tavily_tool)
            logger.info("Added Tavily search tool to agent tools")
        else:
            logger.warning("Could not create Tavily search tool for agent")
        
        # Create the agent with the tools
        logger.info(f"Creating agent with {len(tools)} total tools")
        agent = agent_factory(tools=tools)
        
        # Verify tool was added
        if hasattr(agent, 'tools'):
            tavily_tools = [t for t in agent.tools if hasattr(t, 'name') and 'tavily' in str(t.name).lower()]
            if tavily_tools:
                logger.info("Successfully added Tavily search tool to agent")
            else:
                logger.warning("Could not verify Tavily tool was added to agent")
        elif hasattr(agent, 'root_agent') and hasattr(agent.root_agent, 'tools'):
            tavily_tools = [t for t in agent.root_agent.tools if hasattr(t, 'name') and 'tavily' in str(t.name).lower()]
            if tavily_tools:
                logger.info("Successfully added Tavily search tool to agent wrapper")
            else:
                logger.warning("Could not verify Tavily tool was added to agent wrapper")
        
        return agent
    except Exception as e:
        logger.error(f"Error creating agent with Tavily search tool: {str(e)}")
        return None