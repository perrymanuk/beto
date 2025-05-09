"""
Main FastAPI application for RadBot web interface.

This module defines the FastAPI application for the RadBot web interface.
"""
import asyncio
import logging
import os
import uuid
import time
from datetime import datetime
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
    memory_router,
)

# Import API routers for registration
from radbot.web.api.events import register_events_router
from radbot.web.api.agent_info import register_agent_info_router
from radbot.web.api.sessions import register_sessions_router
from radbot.web.api.messages import register_messages_router

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the FastAPI application.
    
    Returns:
        FastAPI: The configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="RadBot Web Interface",
        description="Web interface for interacting with RadBot agent",
        version="0.1.0",
    )
    
    # Register API routers immediately after app creation
    register_events_router(app)
    register_agent_info_router(app)
    register_sessions_router(app)
    register_messages_router(app)
    app.include_router(memory_router)
    logger.info("API routers registered during app initialization")
    
    return app

# Create the FastAPI app instance
app = create_app()

# Define a startup event to initialize database schema and MCP servers
@app.on_event("startup")
async def initialize_app_startup():
    """Initialize database schema and MCP server tools on application startup."""
    try:
        # First initialize the chat history database schema
        logger.info("Initializing chat history database schema...")
        try:
            from radbot.web.db import chat_operations
            success = chat_operations.create_schema_if_not_exists()
            if success:
                logger.info("Chat history database schema initialized successfully")
            else:
                logger.warning("Failed to initialize chat history database schema")
        except Exception as db_error:
            logger.error(f"Error initializing chat history database: {str(db_error)}", exc_info=True)
            # Continue app startup even if database initialization fails
            
        # Then initialize MCP servers
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
        logger.error(f"Failed during application startup: {str(e)}", exc_info=True)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files directory
# Create a custom class that only handles HTTP requests, not WebSocket
class HTTPOnlyStaticFiles(StaticFiles):
    """StaticFiles class that only handles HTTP requests, not WebSocket."""
    async def __call__(self, scope, receive, send):
        """Handle request or return 404 for non-HTTP requests."""
        if scope["type"] != "http":
            # Log and ignore non-HTTP requests (like WebSocket)
            logger.info(f"Ignoring non-HTTP request to static files: {scope['type']}")
            return
        await super().__call__(scope, receive, send)

def mount_static_files():
    """Mount static files after all routes have been defined."""
    try:
        app.mount(
            "/static",
            HTTPOnlyStaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
            name="static"
        )
        logger.info("Static files mounted successfully")
    except Exception as e:
        logger.error(f"Error mounting static files: {str(e)}", exc_info=True)

# Schedule static files mounting after all other routes are registered
@app.on_event("startup")
async def mount_static_files_on_startup():
    """Mount static files during application startup after routes are registered."""
    mount_static_files()

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
            # Check for excessively large messages
            import json
            events_json = json.dumps({"type": "events", "content": events})
            max_size = 1024 * 1024  # 1MB limit
            
            if len(events_json) > max_size:
                # Log the oversized message
                logger.warning(f"Event payload too large: {len(events_json)} bytes. Splitting into chunks.")
                
                # Process events individually to find large ones
                for event in events:
                    single_event_json = json.dumps({"type": "events", "content": [event]})
                    event_size = len(single_event_json)
                    event_type = event.get('type', 'unknown')
                    event_summary = event.get('summary', 'no summary')
                    
                    if event_size > max_size:
                        # This event is too large - truncate any text content
                        logger.warning(f"Oversized event: {event_type} - {event_summary}: {event_size} bytes")
                        if 'text' in event and isinstance(event['text'], str) and len(event['text']) > 100000:
                            # Truncate text and add indicator
                            original_length = len(event['text'])
                            event['text'] = event['text'][:100000] + f"\n\n[Message truncated due to size constraints. Original length: {original_length} characters]"
                            logger.info(f"Truncated event text from {original_length} to {len(event['text'])} characters")
                            
                            # Send this single truncated event
                            await self.active_connections[session_id].send_json({
                                "type": "events",
                                "content": [event]
                            })
                    else:
                        # Send normal-sized events individually
                        await self.active_connections[session_id].send_json({
                            "type": "events",
                            "content": [event]
                        })
            else:
                # Send as normal if not oversized
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
        
        # Process events for size constraints to match WebSocket behavior
        max_size = 1024 * 1024  # 1MB limit
        processed_events = []
        
        for event in events:
            if 'text' in event and isinstance(event['text'], str) and len(event['text']) > 100000:
                # Truncate large text events
                event_copy = event.copy()  # Create a copy to avoid modifying the original
                original_length = len(event_copy['text'])
                event_copy['text'] = event_copy['text'][:100000] + f"\n\n[Message truncated due to size constraints. Original length: {original_length} characters]"
                logger.info(f"Truncated REST API event text from {original_length} to {len(event_copy['text'])} characters")
                processed_events.append(event_copy)
            else:
                processed_events.append(event)
        
        # Return the response with session information and processed events
        return {
            "session_id": session_id,
            "response": response,
            "events": processed_events
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

        # Reset the session to ensure new connection starts with Beto
        if hasattr(runner, 'reset_session'):
            logger.info(f"Resetting session {session_id} to ensure starting with Beto agent")
            runner.reset_session()

        # Send ready status
        await manager.send_status(session_id, "ready")
        
        # Helper function to get events from a session
        def get_events_from_session(session):
            if not hasattr(session, 'events') or not session.events:
                return []
            
            messages = []
            for event in session.events:
                if hasattr(event, 'content') and event.content:
                    # Try to extract text content for different ADK versions
                    text_content = ""
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_content += part.text
                    elif hasattr(event.content, 'text') and event.content.text:
                        text_content = event.content.text
                    
                    # Determine the role/author
                    role = getattr(event, 'author', 'assistant')
                    
                    # Create a message object if we have content
                    if text_content:
                        message = {
                            "id": getattr(event, 'id', str(uuid.uuid4())),
                            "role": role,
                            "content": text_content,
                            "timestamp": int(getattr(event, 'timestamp', time.time()) * 1000),  # Convert to JS timestamp
                            "agent": getattr(event, 'agent_name', None) or getattr(event, 'agent', None)
                        }
                        messages.append(message)
            
            return messages
        
        # Process heartbeat messages
        async def handle_heartbeat():
            await websocket.send_json({
                "type": "heartbeat"
            })
            logger.debug(f"Sent heartbeat response for session {session_id}")
        
        # Process sync_request messages
        async def handle_sync_request(last_message_id, timestamp=None):
            logger.info(f"Handling sync request for session {session_id} since message {last_message_id}")
            
            # Get app name for this session
            app_name = runner.runner.app_name if hasattr(runner, 'runner') and hasattr(runner.runner, 'app_name') else "beto"
            
            # Retrieve the session from ADK
            session = runner.session_service.get_session(
                app_name=app_name,
                user_id=runner.user_id,
                session_id=session_id
            )
            
            if not session:
                logger.warning(f"No session found for sync request with ID {session_id}")
                await websocket.send_json({
                    "type": "sync_response",
                    "messages": []
                })
                return
            
            # Get all messages from the session
            all_messages = get_events_from_session(session)
            
            # Find the index of the last known message
            last_index = -1
            for i, msg in enumerate(all_messages):
                if msg.get("id") == last_message_id:
                    last_index = i
                    break
            
            # Extract messages after the last known one
            messages = []
            if last_index >= 0 and last_index < len(all_messages) - 1:
                messages = all_messages[last_index + 1:]
            
            # Send the sync response
            await websocket.send_json({
                "type": "sync_response",
                "messages": messages
            })
            
            logger.info(f"Sent sync response with {len(messages)} messages for session {session_id}")
        
        # Process history_request messages
        async def handle_history_request(limit=50):
            logger.info(f"Handling history request for session {session_id}, limit={limit}")
            
            # Get app name for this session
            app_name = runner.runner.app_name if hasattr(runner, 'runner') and hasattr(runner.runner, 'app_name') else "beto"
            
            # Retrieve the session from ADK
            session = runner.session_service.get_session(
                app_name=app_name,
                user_id=runner.user_id,
                session_id=session_id
            )
            
            if not session:
                logger.warning(f"No session found for history request with ID {session_id}")
                await websocket.send_json({
                    "type": "history",
                    "messages": []
                })
                return
            
            # Get all messages from the session
            all_messages = get_events_from_session(session)
            
            # Limit the number of messages if needed
            messages = all_messages[-limit:] if limit and len(all_messages) > limit else all_messages
            
            # Send the history response
            await websocket.send_json({
                "type": "history",
                "messages": messages
            })
            
            logger.info(f"Sent history response with {len(messages)} messages for session {session_id}")
        
        while True:
            # Wait for a message from the client
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "heartbeat":
                await handle_heartbeat()
                continue
            
            elif data.get("type") == "sync_request":
                last_message_id = data.get("lastMessageId")
                timestamp = data.get("timestamp")
                if last_message_id:
                    await handle_sync_request(last_message_id, timestamp)
                else:
                    await manager.send_status(session_id, "error: Missing lastMessageId in sync_request")
                continue
            
            elif data.get("type") == "history_request":
                limit = data.get("limit", 50)
                await handle_history_request(limit)
                continue
            
            # Handle regular chat messages
            if "message" not in data:
                await manager.send_status(session_id, "error: Invalid message format")
                continue

            user_message = data["message"]

            # Check for special command to reset session to Beto
            if user_message.lower() in ["reset to beto", "use beto", "start beto"]:
                logger.info(f"Explicit request to reset session to Beto agent")
                if hasattr(runner, 'reset_session'):
                    runner.reset_session()
                    await manager.send_status(session_id, "reset")
                    await manager.send_events(session_id, [{
                        "type": "system",
                        "category": "system",
                        "text": "Session reset to Beto agent",
                        "timestamp": datetime.now().isoformat()
                    }])
                    await manager.send_status(session_id, "ready")
                    continue

            # Check for special agent targeting message format (AGENT:NAME:actual message)
            target_agent = None
            if user_message.startswith("AGENT:"):
                parts = user_message.split(":", 2)
                if len(parts) >= 3:
                    target_agent = parts[1].strip().lower()
                    user_message = parts[2].strip()
                    logger.info(f"Detected explicit agent targeting: {target_agent}")

            # Send "thinking" status
            await manager.send_status(session_id, "thinking")

            try:
                # Process the message
                logger.info(f"Processing WebSocket message for session {session_id}")

                # Handle explicit agent targeting if present
                if target_agent:
                    # Import agent transfer tool
                    from radbot.tools.agent_transfer import process_request, find_agent_by_name
                    from agent import root_agent  # Import from root module

                    # Debug the agent tree
                    logger.info("DEBUG: Agent tree structure:")
                    if hasattr(root_agent, 'name'):
                        logger.info(f"Root agent name: {root_agent.name}")
                    else:
                        logger.info("Root agent has no name attribute")

                    if hasattr(root_agent, 'sub_agents'):
                        sub_agents = [sa.name for sa in root_agent.sub_agents if hasattr(sa, 'name')]
                        logger.info(f"Sub-agents: {sub_agents}")
                    else:
                        logger.info("Root agent has no sub_agents attribute")

                    # Make case-insensitive check for scout
                    if target_agent.lower() == 'scout':
                        # Try direct access to scout agent
                        for sub_agent in root_agent.sub_agents:
                            if hasattr(sub_agent, 'name') and sub_agent.name.lower() == 'scout':
                                logger.info(f"Found Scout agent directly: {sub_agent.name}")
                                # Process the request directly with the Scout agent's generate_content method
                                # This bypasses the transfer mechanism completely to avoid context bleed
                                try:
                                    # First try direct generation to bypass any transfer issues
                                    if hasattr(sub_agent, 'generate_content') and callable(sub_agent.generate_content):
                                        logger.info("Calling Scout's generate_content method directly")
                                        logger.info(f"Direct message to Scout: {user_message[:50]}...")
                                        response = sub_agent.generate_content(user_message)

                                        # Extract text from response
                                        if hasattr(response, 'text'):
                                            response_text = response.text
                                        elif hasattr(response, 'parts') and response.parts:
                                            response_text = ''
                                            for part in response.parts:
                                                if hasattr(part, 'text') and part.text:
                                                    response_text += part.text
                                        else:
                                            # Fallback to string representation
                                            response_text = str(response)

                                        logger.info(f"Direct Scout response received, length: {len(response_text)}")
                                    else:
                                        # Fallback to process_request
                                        logger.info("Fallback to process_request for Scout")
                                        response_text = process_request(sub_agent, user_message)
                                except Exception as e:
                                    logger.error(f"Error with direct generation: {str(e)}", exc_info=True)
                                    # Try process_request as a fallback
                                    response_text = process_request(sub_agent, user_message)

                                # Log the response for debugging
                                logger.info(f"Scout's response (first 100 chars): {response_text[:100]}...")

                                # Create a result with the response
                                result = {
                                    "response": response_text,
                                    "events": [{
                                        "type": "model_response",
                                        "category": "model_response",
                                        "text": response_text,
                                        "is_final": True,
                                        "agent_name": "SCOUT",
                                        "timestamp": datetime.now().isoformat()
                                    }]
                                }
                                break
                        else:
                            # If we get here, we didn't find Scout directly
                            logger.warning("Could not find Scout agent directly in sub_agents")
                            # Try using the standard finder
                            target = find_agent_by_name(root_agent, target_agent)
                            if target:
                                logger.info(f"Found target agent with find_agent_by_name: {target.name}")
                                response_text = process_request(target, user_message)
                                result = {
                                    "response": response_text,
                                    "events": [{
                                        "type": "model_response",
                                        "category": "model_response",
                                        "text": response_text,
                                        "is_final": True,
                                        "agent_name": target.name,
                                        "timestamp": datetime.now().isoformat()
                                    }]
                                }
                            else:
                                logger.warning(f"Target agent {target_agent} not found, using default runner")
                                result = runner.process_message(user_message)
                    else:
                        # Standard approach for other agents
                        target = find_agent_by_name(root_agent, target_agent)
                        if target:
                            logger.info(f"Found target agent: {target.name}")
                            # Process the request with the specific agent
                            response_text = process_request(target, user_message)
                            # Create a result with the response
                            result = {
                                "response": response_text,
                                "events": [{
                                    "type": "model_response",
                                    "category": "model_response",
                                    "text": response_text,
                                    "is_final": True,
                                    "agent_name": target.name,
                                    "timestamp": datetime.now().isoformat()
                                }]
                            }
                        else:
                            logger.warning(f"Target agent {target_agent} not found, using default runner")
                            result = runner.process_message(user_message)
                else:
                    # Use normal runner for processing
                    result = runner.process_message(user_message)
                
                # Extract response and events
                response = result.get("response", "")
                events = result.get("events", [])
                
                # Log event sizes for debugging
                if events:
                    for idx, event in enumerate(events):
                        if 'text' in event and isinstance(event['text'], str):
                            text_size = len(event['text'])
                            if text_size > 10000:  # Only log notably large events
                                event_type = event.get('type', 'unknown')
                                event_summary = event.get('summary', 'no summary')
                                logger.info(f"Large event[{idx}] {event_type} - {event_summary}: text size = {text_size} bytes")
                
                # Send events only (events contain the model responses)
                if events:
                    logger.info(f"Sending {len(events)} events to client")
                    await manager.send_events(session_id, events)
                
                # Update status to ready (no need to send the response separately)
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