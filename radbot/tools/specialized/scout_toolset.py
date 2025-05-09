"""Scout toolset for specialized agents.

This module provides tools specific to the Scout agent, which focuses on
research and design planning capabilities.
"""

import logging
from typing import List, Any, Optional

# Import research agent tools if available
try:
    from radbot.agent.research_agent.tools import get_research_tools
except ImportError:
    get_research_tools = None

# Import sequential thinking tools if available
try:
    from radbot.agent.research_agent.sequential_thinking import create_sequential_thinking_tool
except ImportError:
    create_sequential_thinking_tool = None

# Import base toolset for registration
from .base_toolset import register_toolset

logger = logging.getLogger(__name__)

def create_scout_toolset() -> List[Any]:
    """Create the set of tools for the Scout specialized agent.
    
    Returns:
        List of tools for research and planning
    """
    toolset = []
    
    # Add research agent tools if available
    if get_research_tools:
        try:
            research_tools = get_research_tools()
            if research_tools:
                toolset.extend(research_tools)
                logger.info(f"Added {len(research_tools)} research tools to Scout toolset")
        except Exception as e:
            logger.error(f"Failed to add research tools: {e}")
    
    # Add sequential thinking tool if available
    if create_sequential_thinking_tool:
        try:
            seq_thinking_tool = create_sequential_thinking_tool()
            if seq_thinking_tool:
                toolset.append(seq_thinking_tool)
                logger.info("Added sequential_thinking tool to Scout toolset")
        except Exception as e:
            logger.error(f"Failed to add sequential_thinking tool: {e}")
    
    # Add MCP tools for research if available
    try:
        from radbot.tools.mcp.mcp_tools import get_mcp_tools
        
        # Get sequential thinking MCP tools
        sequential_thinking_tools = get_mcp_tools("sequentialthinking")
        if sequential_thinking_tools:
            toolset.extend(sequential_thinking_tools)
            logger.info(f"Added {len(sequential_thinking_tools)} sequential thinking MCP tools")
        
        # Get web research MCP tools - Scout can use web research tools directly
        webresearch_tools = get_mcp_tools("webresearch")
        if webresearch_tools:
            toolset.extend(webresearch_tools)
            logger.info(f"Added {len(webresearch_tools)} web research MCP tools to Scout toolset")
    except Exception as e:
        logger.error(f"Failed to add Scout MCP tools: {e}")
    
    return toolset

# Register the toolset with the system
register_toolset(
    name="scout",
    toolset_func=create_scout_toolset,
    description="Agent specialized in research and design planning",
    allowed_transfers=["axel", "web_research"]  # Scout can transfer to these agents
)