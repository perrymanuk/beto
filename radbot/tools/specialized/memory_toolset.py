"""Memory toolset for specialized agents.

This module provides tools for managing conversation history,
searching past conversations, and working with the knowledge base.
"""

import logging
from typing import List, Any, Optional

# Import memory tools
try:
    from radbot.tools.memory.memory_tools import (
        search_past_conversations,
        store_important_information
    )
except ImportError:
    # Define placeholder if not available
    search_past_conversations = None
    store_important_information = None

# Import enhanced memory tools if available
try:
    from radbot.memory.enhanced_memory.memory_manager import get_memory_tools
except ImportError:
    get_memory_tools = None

# Import base toolset for registration
from .base_toolset import register_toolset

logger = logging.getLogger(__name__)

def create_memory_toolset() -> List[Any]:
    """Create the set of tools for the memory specialized agent.
    
    Returns:
        List of tools for memory management and information retrieval
    """
    toolset = []
    
    # Add basic memory search tool
    if search_past_conversations:
        try:
            toolset.append(search_past_conversations)
            logger.info("Added search_past_conversations to memory toolset")
        except Exception as e:
            logger.error(f"Failed to add search_past_conversations: {e}")
    
    # Add store information tool
    if store_important_information:
        try:
            toolset.append(store_important_information)
            logger.info("Added store_important_information to memory toolset")
        except Exception as e:
            logger.error(f"Failed to add store_important_information: {e}")
    
    # Add enhanced memory tools if available
    if get_memory_tools:
        try:
            enhanced_tools = get_memory_tools()
            if enhanced_tools:
                toolset.extend(enhanced_tools)
                logger.info(f"Added {len(enhanced_tools)} enhanced memory tools to memory toolset")
        except Exception as e:
            logger.error(f"Failed to add enhanced memory tools: {e}")
    
    # Add memory-related MCP tools if available
    try:
        from radbot.tools.mcp.mcp_tools import get_mcp_tools
        memory_mcp_tools = get_mcp_tools("memory")
        if memory_mcp_tools:
            toolset.extend(memory_mcp_tools)
            logger.info(f"Added {len(memory_mcp_tools)} memory MCP tools to memory toolset")
    except Exception as e:
        logger.error(f"Failed to add memory MCP tools: {e}")
    
    return toolset

# Register the toolset with the system
register_toolset(
    name="memory",
    toolset_func=create_memory_toolset,
    description="Agent specialized in memory management and information retrieval",
    allowed_transfers=[]  # Only allows transfer back to main orchestrator
)