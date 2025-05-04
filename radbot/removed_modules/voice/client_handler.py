"""
Client handler for bidirectional voice chat using ADK.

This module provides extensions to ADK's WebSocket handlers to support
bidirectional voice chat with ElevenLabs TTS.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.adk.run.live import LiveRunner, LiveRequestQueue

from radbot.voice.elevenlabs_adapter import setup_tts_for_websocket

# Set up logging
logger = logging.getLogger(__name__)

def add_voice_websocket_route(app: FastAPI, shared_context: Dict[str, Any]):
    """
    Add a voice WebSocket route to a FastAPI app.
    
    Args:
        app: FastAPI app
        shared_context: Shared context for callbacks
    """
    @app.websocket("/ws/voice/{session_id}")
    async def voice_websocket(websocket: WebSocket, session_id: str):
        """
        WebSocket endpoint for bidirectional voice chat.
        
        This endpoint handles audio input and output for voice chat.
        
        Args:
            websocket: WebSocket connection
            session_id: Session ID
        """
        await websocket.accept()
        logger.info(f"Voice WebSocket connection accepted for session: {session_id}")
        
        try:
            # Set up TTS for this WebSocket connection
            setup_tts_for_websocket(shared_context, websocket)
            
            # Main WebSocket loop
            while True:
                # Receive message from client
                message = await websocket.receive()
                
                if "bytes" in message:
                    # Audio data
                    audio_data = message["bytes"]
                    
                    # Skip empty chunks
                    if not audio_data:
                        continue
                        
                    logger.debug(f"Received {len(audio_data)} bytes of audio from client")
                    
                    # Forward to ADK
                    # In a full implementation, this would use runner.add_audio() or similar
                    # But for now, we'll just acknowledge receipt
                    await websocket.send_json({
                        "status": "audio_received",
                        "bytes": len(audio_data)
                    })
                    
                elif "text" in message:
                    # Try to parse as JSON
                    try:
                        data = json.loads(message["text"])
                        
                        if "type" in data and data["type"] == "text_input":
                            # Text input instead of audio
                            text = data.get("text", "")
                            logger.info(f"Text input received: {text}")
                            
                            # Forward to ADK
                            # In a full implementation, this would use LiveRequestQueue.add_text()
                            # But for now, we'll just acknowledge receipt
                            await websocket.send_json({
                                "status": "text_received",
                                "text": text
                            })
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Received invalid JSON from client")
                
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from voice WebSocket: {session_id}")
        except Exception as e:
            logger.error(f"Error in voice WebSocket handler: {e}")
            await websocket.close(code=1011, reason=str(e))

def setup_voice_client(app: Optional[FastAPI] = None) -> FastAPI:
    """
    Set up a FastAPI app for voice client handling.
    
    If no app is provided, a new one is created.
    
    Args:
        app: FastAPI app
        
    Returns:
        FastAPI app
    """
    # Create app if none provided
    if app is None:
        app = FastAPI()
    
    # Create shared context
    shared_context = {}
    
    # Add voice WebSocket route
    add_voice_websocket_route(app, shared_context)
    
    return app
