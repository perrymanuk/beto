"""
Main FastAPI application for RadBot web interface.

This module defines the FastAPI application for the RadBot web interface.
"""
import asyncio
import logging
import os
import uuid
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from radbot.config import config_manager
from radbot.web.api.session import (
    SessionManager,
    get_session_manager,
    get_or_create_runner_for_session,
)

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RadBot Web Interface",
    description="Web interface for interacting with RadBot agent",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files directory
app.mount(
    "/static", 
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), 
    name="static"
)

# Set up Jinja2 templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json({
                "type": "message",
                "content": message
            })

    async def send_status(self, session_id: str, status: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json({
                "type": "status",
                "content": status
            })

# Create connection manager
manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main chat interface."""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Process a user message and return the agent's response.
    
    Args:
        message: The user's message
        session_id: Optional session ID (if not provided, a new one will be created)
        
    Returns:
        JSON response with session_id and agent's response
    """
    # Generate a session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"Created new session ID: {session_id}")
    else:
        logger.info(f"Using existing session ID: {session_id}")
    
    # Get or create a runner for this session
    runner = await get_or_create_runner_for_session(session_id, session_manager)
    
    try:
        # Process the message
        logger.info(f"Processing message for session {session_id}: {message[:50]}{'...' if len(message) > 50 else ''}")
        response = runner.process_message(message)
        
        # Return the response with session information
        return {
            "session_id": session_id,
            "response": response
        }
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, session_manager: SessionManager = Depends(get_session_manager)):
    """WebSocket endpoint for real-time chat.
    
    Args:
        websocket: The WebSocket connection
        session_id: The session ID
    """
    await manager.connect(websocket, session_id)
    
    try:
        # Get or create a runner for this session
        runner = await get_or_create_runner_for_session(session_id, session_manager)
        
        # Send ready status
        await manager.send_status(session_id, "ready")
        
        while True:
            # Wait for a message from the client
            data = await websocket.receive_json()
            
            if "message" not in data:
                await manager.send_status(session_id, "error: Invalid message format")
                continue
            
            user_message = data["message"]
            
            # Send "thinking" status
            await manager.send_status(session_id, "thinking")
            
            try:
                # Process the message
                logger.info(f"Processing WebSocket message for session {session_id}")
                response = runner.process_message(user_message)
                
                # Send the response
                await manager.send_message(session_id, response)
                await manager.send_status(session_id, "ready")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}", exc_info=True)
                await manager.send_status(session_id, f"error: {str(e)}")
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        manager.disconnect(session_id)

@app.get("/api/sessions/{session_id}/reset")
async def reset_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Reset a session's conversation history.
    
    Args:
        session_id: The session ID to reset
        
    Returns:
        JSON response with status
    """
    try:
        await session_manager.reset_session(session_id)
        return {"status": "ok", "message": "Session reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error resetting session: {str(e)}")

def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Whether to reload on code changes
    """
    logger.info(f"Starting RadBot web server on {host}:{port}")
    uvicorn.run("radbot.web.app:app", host=host, port=port, reload=reload)