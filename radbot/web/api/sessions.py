"""
Sessions API endpoints for RadBot web interface.

This module provides API endpoints for managing multiple chat sessions.
"""
import logging
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from radbot.web.api.session import (
    SessionManager,
    get_session_manager,
    get_or_create_runner_for_session,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class SessionMetadata(BaseModel):
    """Session metadata for API responses."""
    id: str
    name: str
    created_at: int
    last_message_at: Optional[int] = None
    preview: Optional[str] = None

class CreateSessionRequest(BaseModel):
    """Request model for creating a new session."""
    name: Optional[str] = None

class RenameSessionRequest(BaseModel):
    """Request model for renaming a session."""
    name: str

class SessionsListResponse(BaseModel):
    """Response model for listing sessions."""
    sessions: List[SessionMetadata]
    active_session_id: Optional[str] = None

# Register the router with FastAPI
def register_sessions_router(app):
    """Register the sessions router with the FastAPI app."""
    router = APIRouter(
        prefix="/api/sessions",
        tags=["sessions"],
    )
    
    @router.get("/", response_model=SessionsListResponse)
    async def list_sessions(
        user_id: Optional[str] = None,
        session_manager: SessionManager = Depends(get_session_manager)
    ):
        """List all sessions for the current user."""
        logger.info("Listing sessions for user %s", user_id or "anonymous")
        
        # Create the response with placeholder data - in a real system
        # we would query a database for user's sessions
        sessions = []
        active_session_id = None
        
        try:
            # Get all sessions from session manager
            for session_id, session_runner in session_manager.sessions.items():
                if user_id and session_runner.user_id != user_id:
                    continue
                
                # Get session data - app_name can be used as active session indicator
                app_name = getattr(session_runner.runner, "app_name", "beto")
                created_at = int(session_id.split("-")[0]) if "-" in session_id else 0
                
                # Create session metadata
                session_meta = SessionMetadata(
                    id=session_id,
                    name=f"Session {created_at}",
                    created_at=created_at,
                    last_message_at=created_at,
                    preview="Session data"
                )
                
                sessions.append(session_meta)
            
            # Sort sessions by creation time (newest first)
            sessions.sort(key=lambda s: s.created_at, reverse=True)
            
            # If there's at least one session, use the first as active
            if sessions:
                active_session_id = sessions[0].id
                
            logger.info("Found %d sessions for user", len(sessions))
            
            return SessionsListResponse(
                sessions=sessions,
                active_session_id=active_session_id
            )
        except Exception as e:
            logger.error("Error listing sessions: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")
    
    @router.post("/create", response_model=SessionMetadata)
    async def create_session(
        request: CreateSessionRequest,
        session_manager: SessionManager = Depends(get_session_manager)
    ):
        """Create a new session."""
        logger.info("Creating new session with name: %s", request.name)
        
        try:
            # Generate a new session ID
            session_id = str(uuid.uuid4())
            user_id = f"web_user_{session_id}"
            
            # Create the session in the backend
            runner = await get_or_create_runner_for_session(session_id, session_manager)
            
            # Default name if not provided
            session_name = request.name or f"Session {uuid.uuid4().hex[:8]}"
            created_at = int(session_id.split("-")[0]) if "-" in session_id else 0
            
            # Return session metadata
            return SessionMetadata(
                id=session_id,
                name=session_name,
                created_at=created_at,
                last_message_at=created_at,
                preview="New session started"
            )
        except Exception as e:
            logger.error("Error creating session: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")
    
    @router.put("/{session_id}/rename", response_model=SessionMetadata)
    async def rename_session(
        session_id: str,
        request: RenameSessionRequest,
        session_manager: SessionManager = Depends(get_session_manager)
    ):
        """Rename a session."""
        logger.info("Renaming session %s to %s", session_id, request.name)
        
        try:
            # Check if session exists
            runner = await session_manager.get_runner(session_id)
            if not runner:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            
            # In a real implementation, you would update the session name in a database
            # For this prototype, we'll just return the updated metadata
            created_at = int(session_id.split("-")[0]) if "-" in session_id else 0
            
            return SessionMetadata(
                id=session_id,
                name=request.name,
                created_at=created_at,
                last_message_at=created_at,
                preview="Session renamed"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error renaming session: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error renaming session: {str(e)}")
    
    @router.delete("/{session_id}")
    async def delete_session(
        session_id: str,
        session_manager: SessionManager = Depends(get_session_manager)
    ):
        """Delete a session."""
        logger.info("Deleting session %s", session_id)
        
        try:
            # Check if session exists
            runner = await session_manager.get_runner(session_id)
            if not runner:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            
            # Remove the session
            await session_manager.remove_session(session_id)
            
            return {"status": "success", "message": f"Session {session_id} deleted"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error deleting session: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")
    
    @router.get("/{session_id}")
    async def get_session(
        session_id: str,
        session_manager: SessionManager = Depends(get_session_manager)
    ):
        """Get session details."""
        logger.info("Getting details for session %s", session_id)
        
        try:
            # Check if session exists
            runner = await session_manager.get_runner(session_id)
            if not runner:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            
            # Get session data - in a real implementation, you would get this from a database
            created_at = int(session_id.split("-")[0]) if "-" in session_id else 0
            
            return {
                "id": session_id,
                "name": f"Session {created_at}",
                "created_at": created_at,
                "last_message_at": created_at,
                "preview": "Session data"
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error getting session: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error getting session: {str(e)}")
    
    # Register the router with the app
    app.include_router(router)
    logger.info("Sessions router registered")