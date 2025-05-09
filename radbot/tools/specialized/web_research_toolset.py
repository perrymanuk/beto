"""Web research toolset for specialized agents.

This module provides tools for web searching, content retrieval,
and information extraction from online sources.
"""

import logging
from typing import List, Any, Optional

# Import web search tools
try:
    from radbot.tools.web_search.web_search_tools_fixed import web_search
except ImportError:
    from radbot.tools.web_search.web_search_tools import web_search

# Import MCP tools for web research
from radbot.tools.mcp.mcp_tools import get_mcp_tools

# Import base toolset for registration
from .base_toolset import register_toolset

logger = logging.getLogger(__name__)

def create_web_research_toolset() -> List[Any]:
    """Create the set of tools for the web research specialized agent.
    
    Returns:
        List of tools for web search and information retrieval
    """
    toolset = []
    
    # Add basic web search tool
    try:
        toolset.append(web_search)
        logger.info("Added web_search to web research toolset")
    except Exception as e:
        logger.error(f"Failed to add web_search: {e}")
    
    # Add Tavily search and extract MCP tools
    try:
        tavily_tools = get_mcp_tools("tavily")
        if tavily_tools:
            toolset.extend(tavily_tools)
            logger.info(f"Added {len(tavily_tools)} Tavily MCP tools to web research toolset")
    except Exception as e:
        logger.error(f"Failed to add Tavily MCP tools: {e}")
    
    # Add Crawl4AI MCP tools
    try:
        crawl4ai_tools = get_mcp_tools("crawl4ai")
        if crawl4ai_tools:
            toolset.extend(crawl4ai_tools)
            logger.info(f"Added {len(crawl4ai_tools)} Crawl4AI MCP tools to web research toolset")
    except Exception as e:
        logger.error(f"Failed to add Crawl4AI MCP tools: {e}")
    
    # Add WebResearch MCP tools
    try:
        webresearch_tools = get_mcp_tools("webresearch")
        if webresearch_tools:
            toolset.extend(webresearch_tools)
            logger.info(f"Added {len(webresearch_tools)} WebResearch MCP tools to web research toolset")
    except Exception as e:
        logger.error(f"Failed to add WebResearch MCP tools: {e}")
    
    return toolset

# Register the toolset with the system
register_toolset(
    name="web_research",
    toolset_func=create_web_research_toolset,
    description="Agent specialized in web research and information retrieval",
    allowed_transfers=[]  # Scout can transfer to this agent, handled elsewhere
)