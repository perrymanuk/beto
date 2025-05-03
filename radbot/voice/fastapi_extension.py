"""
FastAPI extension for adding voice capabilities to ADK web interface.

This module provides a FastAPI extension that adds voice capabilities to the
ADK web interface by intercepting text responses and converting them to speech.
"""

import asyncio
import base64
import json
import logging
from typing import Dict, Any, Optional, Callable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.adk.agents import BaseAgent

from radbot.voice.elevenlabs_client import create_elevenlabs_client
from radbot.voice.adk_voice_handler import setup_voice_handler

# Set up logging
logger = logging.getLogger(__name__)

def add_voice_routes(app: FastAPI, agent: BaseAgent) -> FastAPI:
    """
    Add voice-related routes to a FastAPI app.
    
    Args:
        app: FastAPI app
        agent: ADK agent
        
    Returns:
        FastAPI: Updated FastAPI app
    """
    # Set up voice handler
    voice_handler = setup_voice_handler()
    
    # Add WebSocket endpoint for voice
    @app.websocket("/voice/{session_id}")
    async def voice_endpoint(websocket: WebSocket, session_id: str):
        """
        WebSocket endpoint for voice communication.
        
        Args:
            websocket: WebSocket connection
            session_id: Session ID
        """
        await websocket.accept()
        logger.info(f"Voice WebSocket connection established: {session_id}")
        
        try:
            # Handle stream
            await voice_handler.handle_adk_stream(websocket, session_id, agent)
        
        except WebSocketDisconnect:
            logger.info(f"Voice WebSocket connection closed: {session_id}")
        
        except Exception as e:
            logger.error(f"Error in voice WebSocket endpoint: {e}")
            await websocket.close(code=1011, reason=str(e))
    
    # Return the app
    return app

def create_voice_app(agent: BaseAgent) -> FastAPI:
    """
    Create a FastAPI app with voice capabilities.
    
    Args:
        agent: ADK agent
        
    Returns:
        FastAPI: FastAPI app with voice capabilities
    """
    # Create FastAPI app
    app = FastAPI(title="RadBot Voice Server")
    
    # Add voice routes
    app = add_voice_routes(app, agent)
    
    return app

def run_voice_app(agent: BaseAgent, host: str = "0.0.0.0", port: int = 8000):
    """
    Run a FastAPI app with voice capabilities.
    
    Args:
        agent: ADK agent
        host: Host to bind to
        port: Port to bind to
    """
    # Import uvicorn here to avoid circular import
    import uvicorn
    
    # Create app
    app = create_voice_app(agent)
    
    # Run app
    uvicorn.run(app, host=host, port=port)
