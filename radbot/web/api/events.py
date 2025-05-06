"""
Events API endpoints for RadBot web interface.

This module provides API endpoints for retrieving events associated with a session.
Events include tool calls, agent transfers, planner events, and model responses.
"""
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Path

from radbot.web.api.session import get_or_create_runner_for_session, SessionRunner

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/events",
    tags=["events"],
)

# In-memory storage for events (session_id -> events)
# This would be replaced with a proper database in a production system
session_events: Dict[str, List[Dict[str, Any]]] = {}

# Add event to storage
def add_event(session_id: str, event: Dict[str, Any]) -> None:
    """Add an event to session's event storage.
    
    Args:
        session_id: Session identifier
        event: Event data to store
    """
    if session_id not in session_events:
        session_events[session_id] = []
    
    # Check for duplicate events
    # We check for identical type, timestamp, and summary to identify duplicates
    is_duplicate = False
    for existing_event in session_events[session_id]:
        # Compare essential fields
        if (existing_event.get('type') == event.get('type') and
            existing_event.get('summary') == event.get('summary') and
            existing_event.get('timestamp') == event.get('timestamp')):
            is_duplicate = True
            logger.info(f"Skipping duplicate event: {event.get('type')} - {event.get('summary')}")
            break
    
    # Only add if not a duplicate
    if not is_duplicate:
        session_events[session_id].append(event)
        logger.info(f"Added event to session {session_id}: {event.get('type')} - {event.get('summary')}")

# Get events for session
@router.get("/{session_id}", response_model=List[Dict[str, Any]])
async def get_events(
    session_id: str = Path(..., description="Session ID"),
    session_runner: SessionRunner = Depends(get_or_create_runner_for_session)
) -> List[Dict[str, Any]]:
    """Get events for a session.
    
    Args:
        session_id: Session identifier
        session_runner: Session runner for this session
    
    Returns:
        List of events for the session
    
    Raises:
        HTTPException: If session not found
    """
    # Get events for this session
    events = session_events.get(session_id, [])
    
    # If no events exist yet, create welcome and sample events
    if not events:
        logger.info(f"No events found for session {session_id}, creating welcome events")
        
        # Create a welcome message
        welcome_event = {
            "type": "model_response",
            "category": "model_response",
            "timestamp": _get_current_timestamp(),
            "summary": "Welcome Message",
            "text": "Welcome to RadBot! I'm ready to assist you. Try asking me a question or giving me a task to work on.",
            "is_final": True,
            "details": {
                "session_id": session_id
            }
        }
        add_event(session_id, welcome_event)
        
        # Create a sample weather tool call event
        from datetime import datetime, timedelta
        
        # Tool call event (the request)
        tool_call_time = (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        weather_tool_call = {
            "type": "tool_call",
            "category": "tool_call",
            "timestamp": tool_call_time,
            "summary": "Tool Call: get_weather",
            "tool_name": "get_weather",
            "input": {"location": "Santa Barbara, CA"},
            "details": {
                "session_id": session_id,
                "tool": "get_weather",
                "event_type": "function_call"
            }
        }
        add_event(session_id, weather_tool_call)
        
        # Tool result event (the response)
        tool_result_time = (datetime.now() - timedelta(minutes=1, seconds=58)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        weather_tool_result = {
            "type": "tool_call",
            "category": "tool_call",
            "timestamp": tool_result_time,
            "summary": "Tool Result: get_weather",
            "tool_name": "get_weather",
            "output": {
                "temperature": 22,
                "temperature_feels_like": 21,
                "humidity": 65,
                "wind_speed": 3.5,
                "condition": "clear",
                "location": "Santa Barbara, CA"
            },
            "details": {
                "session_id": session_id,
                "tool": "get_weather",
                "event_type": "function_response"
            }
        }
        add_event(session_id, weather_tool_result)
        
        # Refresh events list
        events = session_events.get(session_id, [])
    
    # Return the events
    logger.info(f"Retrieved {len(events)} events for session {session_id}")
    return events

# Helper to get timestamp in consistent format
def _get_current_timestamp():
    """Get current timestamp in consistent format."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

# Register events router in the main FastAPI app
def register_events_router(app):
    """Register events router with the FastAPI app.
    
    Args:
        app: FastAPI application
    """
    app.include_router(router)
    logger.info("Registered events router")