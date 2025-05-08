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

# Import API routers for registration
from radbot.web.api.events import register_events_router
from radbot.web.api.agent_info import register_agent_info_router

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

# Register API routers immediately after app creation
register_events_router(app)
register_agent_info_router(app)
logger.info("API routers registered during app initialization")

# Define a startup event to initialize MCP servers
@app.on_event("startup")
async def initialize_mcp_servers():
    """Initialize MCP server tools on application startup."""
    try:
        logger.info("Initializing MCP servers at application startup...")
        from radbot.tools.mcp.mcp_client_factory import MCPClientFactory
        from radbot.config.config_loader import config_loader
        
        # Just check if servers are enabled and can connect
        servers = config_loader.get_enabled_mcp_servers()
        logger.info(f"Found {len(servers)} enabled MCP servers in configuration")
        
        for server in servers:
            server_id = server.get("id", "unknown")
            server_name = server.get("name", server_id)
            logger.info(f"MCP server enabled: {server_name} (ID: {server_id})")
            
        # Don't attempt to create tools here - we'll do that in the session
        # when a new client connects, which is safer and more reliable
        
    except Exception as e:
        logger.error(f"Failed to check MCP servers: {str(e)}", exc_info=True)

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
            
    async def send_events(self, session_id: str, events: list):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json({
                "type": "events",
                "content": events
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
        result = runner.process_message(message)
        
        # Extract response and events
        response = result.get("response", "")
        events = result.get("events", [])
        
        # Return the response with session information and events
        return {
            "session_id": session_id,
            "response": response,
            "events": events
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
                result = runner.process_message(user_message)
                
                # Extract response and events
                response = result.get("response", "")
                events = result.get("events", [])
                
                # Send events first (if any)
                if events:
                    logger.info(f"Sending {len(events)} events to client")
                    await manager.send_events(session_id, events)
                
                # Send the text response
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

@app.get("/api/tasks")
async def get_tasks():
    """Get all tasks from the database directly.
    
    Returns:
        JSON list of tasks
    """
    try:
        # Import task listing function
        from radbot.tools.todo.api.list_tools import list_all_tasks
        
        # Call the function directly
        tasks = list_all_tasks()
        
        # Convert tasks to a serializable format
        serializable_tasks = []
        for task in tasks:
            # Check if task is already a dict
            if isinstance(task, dict):
                serializable_tasks.append(task)
            else:
                # Convert task object to dict
                task_dict = {
                    "task_id": str(task.task_id) if hasattr(task, "task_id") else "unknown",
                    "description": str(task.description) if hasattr(task, "description") else "",
                    "status": str(task.status) if hasattr(task, "status") else "backlog",
                    "category": str(task.category) if hasattr(task, "category") else None,
                    "project_id": str(task.project_id) if hasattr(task, "project_id") else None,
                    "project_name": str(task.project_name) if hasattr(task, "project_name") else "Default",
                    "created_at": str(task.created_at) if hasattr(task, "created_at") else None,
                    "updated_at": str(task.updated_at) if hasattr(task, "updated_at") else None,
                    "origin": str(task.origin) if hasattr(task, "origin") else None,
                }
                serializable_tasks.append(task_dict)
        
        # Return the tasks
        return serializable_tasks
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting tasks: {str(e)}")

@app.get("/api/projects")
async def get_projects():
    """Get all projects from the database directly.
    
    Returns:
        JSON list of projects
    """
    try:
        # Import project listing function
        from radbot.tools.todo.api.list_tools import list_projects
        
        # Call the function directly
        projects = list_projects()
        
        # Convert projects to a serializable format
        serializable_projects = []
        for project in projects:
            # Check if project is already a dict
            if isinstance(project, dict):
                serializable_projects.append(project)
            else:
                # Convert project object to dict
                project_dict = {
                    "project_id": str(project.project_id) if hasattr(project, "project_id") else "unknown",
                    "name": str(project.name) if hasattr(project, "name") else "Default",
                    "description": str(project.description) if hasattr(project, "description") else "",
                    "created_at": str(project.created_at) if hasattr(project, "created_at") else None,
                    "updated_at": str(project.updated_at) if hasattr(project, "updated_at") else None,
                }
                serializable_projects.append(project_dict)
        
        # Return the projects
        return serializable_projects
    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting projects: {str(e)}")

@app.get("/api/tools")
async def get_available_tools(session_id: Optional[str] = None, session_manager: SessionManager = Depends(get_session_manager)):
    """Get the list of available tools from the root agent.
    
    Args:
        session_id: Optional session ID to get tools from a specific session
        
    Returns:
        JSON list of tools with their details
    """
    try:
        # Import the root_agent directly
        from agent import root_agent
        
        # Use the specific session's runner if a session_id is provided
        if session_id:
            runner = await get_or_create_runner_for_session(session_id, session_manager)
            if hasattr(runner, "runner") and hasattr(runner.runner, "agent"):
                agent = runner.runner.agent
            else:
                agent = root_agent
        else:
            agent = root_agent
            
        # Check if agent has tools
        if not hasattr(agent, "tools") or not agent.tools:
            logger.warning("Agent has no tools attribute or tools list is empty")
            return []
            
        # Convert tools to a serializable format
        serializable_tools = []
        for tool in agent.tools:
            tool_dict = {
                "name": str(tool.name) if hasattr(tool, "name") else "unknown",
                "description": str(tool.description) if hasattr(tool, "description") else "",
            }
            
            # Add schema information if available
            if hasattr(tool, "input_schema"):
                if hasattr(tool.input_schema, "schema"):
                    tool_dict["input_schema"] = tool.input_schema.schema()
                elif hasattr(tool.input_schema, "to_dict"):
                    tool_dict["input_schema"] = tool.input_schema.to_dict()
                else:
                    tool_dict["input_schema"] = str(tool.input_schema)
                    
            # Add any other tool attributes that might be useful
            if hasattr(tool, "metadata"):
                tool_dict["metadata"] = tool.metadata
                
            serializable_tools.append(tool_dict)
        
        logger.info(f"Retrieved {len(serializable_tools)} tools")
        return serializable_tools
    except Exception as e:
        logger.error(f"Error getting tools: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting tools: {str(e)}")

# Mock events endpoint has been replaced with the real events API
# provided by radbot.web.api.events

def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Whether to reload on code changes
    """
    # Events router is already registered during module initialization
    
    logger.info(f"Starting RadBot web server on {host}:{port}")
    uvicorn.run("radbot.web.app:app", host=host, port=port, reload=reload)