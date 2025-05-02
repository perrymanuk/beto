"""
Memory tools for the radbot agent framework.

These tools allow agents to interact with the memory system.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

def search_past_conversations(
    query: str,
    max_results: int = 5,
    time_window_days: Optional[int] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """
    Search past conversations for relevant information.
    
    Use this tool when you need to recall previous interactions with the user
    that might be relevant to the current conversation.
    
    Args:
        query: The search query (what to look for in past conversations)
        max_results: Maximum number of results to return (default: 5)
        time_window_days: Optional time window to restrict search (e.g., 7 for last week)
        tool_context: Tool context for accessing memory service
        
    Returns:
        dict: A dictionary containing:
              'status' (str): 'success' or 'error'
              'memories' (list, optional): List of relevant past conversations
              'error_message' (str, optional): Description of the error if failed
    """
    try:
        # Check if tool_context is available (required for memory access)
        if not tool_context:
            return {
                "status": "error",
                "error_message": "Cannot access memory without tool context."
            }
        
        # Get the memory service from tool context
        memory_service = getattr(tool_context, "memory_service", None)
        if not memory_service:
            return {
                "status": "error",
                "error_message": "Memory service not available."
            }
        
        # Get user ID from the tool context
        user_id = getattr(tool_context, "user_id", None)
        if not user_id:
            return {
                "status": "error",
                "error_message": "User ID not available in tool context."
            }
        
        # Create filter conditions
        filter_conditions = {}
        
        # Add time window if specified
        if time_window_days:
            min_timestamp = (datetime.now() - timedelta(days=time_window_days)).isoformat()
            filter_conditions["min_timestamp"] = min_timestamp
        
        # Search memories
        results = memory_service.search_memory(
            app_name="radbot",
            user_id=user_id,
            query=query,
            limit=max_results,
            filter_conditions=filter_conditions
        )
        
        # Return formatted results
        if results:
            return {
                "status": "success",
                "memories": results
            }
        else:
            return {
                "status": "success",
                "memories": [],
                "message": "No relevant memories found."
            }
        
    except Exception as e:
        logger.error(f"Error searching past conversations: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to search memory: {str(e)}"
        }


def store_important_information(
    information: str,
    memory_type: str = "important_fact",
    metadata: Optional[Dict[str, Any]] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """
    Store important information in memory for future reference.
    
    Use this tool when the user provides important information that should be
    remembered for future interactions.
    
    Args:
        information: The text information to store
        memory_type: Type of memory (e.g., 'important_fact', 'user_preference')
        metadata: Additional metadata to store with the information
        tool_context: Tool context for accessing memory service
        
    Returns:
        dict: A dictionary with status information
    """
    try:
        # Check if tool_context is available
        if not tool_context:
            return {
                "status": "error",
                "error_message": "Cannot access memory without tool context."
            }
        
        # Get the memory service
        memory_service = getattr(tool_context, "memory_service", None)
        if not memory_service:
            return {
                "status": "error",
                "error_message": "Memory service not available."
            }
        
        # Get user ID
        user_id = getattr(tool_context, "user_id", None)
        if not user_id:
            return {
                "status": "error",
                "error_message": "User ID not available in tool context."
            }
        
        # Create metadata if not provided
        metadata = metadata or {}
        metadata["memory_type"] = memory_type
        
        # Create the memory point
        point = memory_service._create_memory_point(
            user_id=user_id,
            text=information,
            metadata=metadata
        )
        
        # Store in Qdrant
        memory_service.client.upsert(
            collection_name=memory_service.collection_name,
            points=[point],
            wait=True
        )
        
        return {
            "status": "success",
            "message": f"Successfully stored information as {memory_type}."
        }
        
    except Exception as e:
        logger.error(f"Error storing important information: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to store information: {str(e)}"
        }