"""
Memory tools for the radbot agent framework.

These tools allow agents to interact with the memory system.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from google.adk.tools.tool_context import ToolContext
from qdrant_client import models

logger = logging.getLogger(__name__)

def search_past_conversations(
    query: str,
    max_results: int = 5,
    time_window_days: Optional[int] = None,
    tool_context: Optional[ToolContext] = None,
    memory_type: Optional[str] = None,
    limit: Optional[int] = None,
    return_stats_only: bool = False
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
        memory_type: Type of memory to filter by (e.g., 'conversation_turn', 'user_query')
                     If "all", no filtering by memory type is applied
        limit: Alternative way to specify maximum results (overrides max_results if provided)
        return_stats_only: If True, returns statistics about memory content instead of search results
        
    Returns:
        dict: A dictionary containing:
              'status' (str): 'success' or 'error'
              'memories' (list, optional): List of relevant past conversations
              'error_message' (str, optional): Description of the error if failed
              'total_memories' (int, optional): If return_stats_only=True, count of all memories
              'memory_types' (list, optional): If return_stats_only=True, list of available memory types
    """
    try:
        # Check if tool_context is available
        if not tool_context:
            logger.warning("Tool context not available, checking for global memory_service")
            # Try to get memory service from global ToolContext class
            from google.adk.tools.tool_context import ToolContext
            memory_service = getattr(ToolContext, "memory_service", None)
            if not memory_service:
                # Try to create memory service if not available
                try:
                    from radbot.memory.qdrant_memory import QdrantMemoryService
                    memory_service = QdrantMemoryService()
                    logger.info("Created QdrantMemoryService on demand")
                    # Store in global ToolContext
                    setattr(ToolContext, "memory_service", memory_service)
                except Exception as e:
                    logger.error(f"Failed to create memory service: {str(e)}")
                    return {
                        "status": "error",
                        "error_message": "Cannot access memory without tool context, and failed to create memory service."
                    }
            else:
                logger.info("Found memory_service in global ToolContext")
        else:
            # Get the memory service from tool context
            memory_service = getattr(tool_context, "memory_service", None)
            if not memory_service:
                logger.warning("Memory service not available in tool_context, checking global")
                # Try getting from global ToolContext
                from google.adk.tools.tool_context import ToolContext
                memory_service = getattr(ToolContext, "memory_service", None)
                if not memory_service:
                    return {
                        "status": "error",
                        "error_message": "Memory service not available in tool context."
                    }
                else:
                    logger.info("Found memory_service in global ToolContext")
        
        # Get user ID from the tool context
        user_id = getattr(tool_context, "user_id", None)
        if not user_id:
            # Try getting it from the session
            session = getattr(tool_context, "session", None)
            if session:
                user_id = getattr(session, "user_id", None)
            
            if not user_id:
                # In web UI context, use a default user ID for testing
                logger.warning("No user ID found in tool context, using default 'web_user'")
                user_id = "web_user"
        
        # Create filter conditions
        filter_conditions = {}
        
        # Add time window if specified
        if time_window_days:
            min_timestamp = (datetime.now() - timedelta(days=time_window_days)).isoformat()
            filter_conditions["min_timestamp"] = min_timestamp
            
        # Add memory_type filter if specified and not "all"
        if memory_type and memory_type.lower() != "all":
            filter_conditions["memory_type"] = memory_type
        
        # Handle return_stats_only to provide memory statistics
        if return_stats_only:
            try:
                # Get collection info to calculate stats
                collection_info = memory_service.client.get_collection(memory_service.collection_name)
                
                # Get a count of all points where user_id matches
                count_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                )
                
                count_result = memory_service.client.count(
                    collection_name=memory_service.collection_name,
                    count_filter=count_filter
                )
                
                # Get sample of different memory types
                sample_results = memory_service.client.scroll(
                    collection_name=memory_service.collection_name,
                    scroll_filter=count_filter,
                    limit=100,  # Sample size to analyze types
                    with_payload=True
                )
                
                # Extract unique memory types
                memory_types = set()
                if sample_results and sample_results[0]:
                    for point in sample_results[0]:
                        if point.payload and "memory_type" in point.payload:
                            memory_types.add(point.payload["memory_type"])
                
                return {
                    "status": "success",
                    "total_memories": count_result.count,
                    "memory_types": sorted(list(memory_types)),
                    "collection_size": collection_info.points_count
                }
            except Exception as e:
                logger.error(f"Error getting memory stats: {str(e)}")
                return {
                    "status": "error",
                    "error_message": f"Failed to get memory statistics: {str(e)}"
                }
        
        # Use limit parameter if provided, otherwise use max_results
        result_limit = limit if limit is not None else max_results
        
        # Search memories
        results = memory_service.search_memory(
            app_name="beto",  # Changed from "radbot" to match agent name
            user_id=user_id,
            query=query,
            limit=result_limit,
            filter_conditions=filter_conditions
        )
        
        # Return formatted results
        if results:
            # Format each memory entry for readability
            formatted_results = []
            for entry in results:
                # Basic memory info
                memory_text = entry.get("text", "")
                memory_type = entry.get("memory_type", "unknown")
                relevance = entry.get("relevance_score", 0)
                
                # Format timestamp if present
                timestamp = entry.get("timestamp", "")
                date_str = ""
                if timestamp:
                    try:
                        # Try to parse the ISO format timestamp
                        dt = datetime.fromisoformat(timestamp)
                        date_str = dt.strftime("%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        date_str = timestamp  # Keep original if parsing fails
                
                # Add formatted entry
                formatted_entry = {
                    "text": memory_text,
                    "type": memory_type,
                    "relevance_score": relevance,
                    "date": date_str
                }
                
                # Add additional fields if present
                if "user_message" in entry:
                    formatted_entry["user_message"] = entry["user_message"]
                if "agent_response" in entry:
                    formatted_entry["agent_response"] = entry["agent_response"]
                
                formatted_results.append(formatted_entry)
            
            return {
                "status": "success",
                "memories": formatted_results
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
            logger.warning("Tool context not available, checking for global memory_service")
            # Try to get memory service from global ToolContext class
            from google.adk.tools.tool_context import ToolContext
            memory_service = getattr(ToolContext, "memory_service", None)
            if not memory_service:
                # Try to create memory service if not available
                try:
                    from radbot.memory.qdrant_memory import QdrantMemoryService
                    memory_service = QdrantMemoryService()
                    logger.info("Created QdrantMemoryService on demand")
                    # Store in global ToolContext
                    setattr(ToolContext, "memory_service", memory_service)
                except Exception as e:
                    logger.error(f"Failed to create memory service: {str(e)}")
                    return {
                        "status": "error",
                        "error_message": "Cannot access memory without tool context, and failed to create memory service."
                    }
            else:
                logger.info("Found memory_service in global ToolContext")
        else:
            # Get the memory service from tool context
            memory_service = getattr(tool_context, "memory_service", None)
            if not memory_service:
                logger.warning("Memory service not available in tool_context, checking global")
                # Try getting from global ToolContext
                from google.adk.tools.tool_context import ToolContext
                memory_service = getattr(ToolContext, "memory_service", None)
                if not memory_service:
                    return {
                        "status": "error",
                        "error_message": "Memory service not available in tool context."
                    }
                else:
                    logger.info("Found memory_service in global ToolContext")
        
        # Get user ID
        user_id = getattr(tool_context, "user_id", None)
        if not user_id:
            # Try getting it from the session
            session = getattr(tool_context, "session", None)
            if session:
                user_id = getattr(session, "user_id", None)
            
            if not user_id:
                # In web UI context, use a default user ID for testing
                logger.warning("No user ID found in tool context, using default 'web_user'")
                user_id = "web_user"
        
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