"""
ADK voice handler for integrating Google Cloud TTS with ADK streaming.

This module provides functions to intercept ADK text streams and convert them
to speech using Google Cloud Text-to-Speech.
"""

import asyncio
import base64
import json
import logging
import os
from typing import Dict, Any, Optional, List, Set, AsyncGenerator, Callable

import websockets
from fastapi import WebSocket, WebSocketDisconnect
from google.adk.agents import BaseAgent
from google.adk.runners import Runner

from radbot.voice.google_cloud_tts_adapter import GoogleCloudTTSAdapter, create_google_cloud_tts_client

# Set up logging
logger = logging.getLogger(__name__)

class ADKVoiceHandler:
    """
    Handler for integrating Google Cloud TTS with ADK streaming.
    
    This class provides methods to intercept ADK text streams and convert them
    to speech using Google Cloud Text-to-Speech.
    """
    
    def __init__(self, tts_adapter: Optional[GoogleCloudTTSAdapter] = None):
        """
        Initialize the ADK voice handler.
        
        Args:
            tts_adapter: Google Cloud TTS adapter for text-to-speech
        """
        self.tts_adapter = tts_adapter or GoogleCloudTTSAdapter()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
    async def handle_websocket(self, websocket: WebSocket, session_id: str, text_msg: str):
        """
        Handle a WebSocket message containing text to be converted to speech.
        
        Args:
            websocket: WebSocket connection to client
            session_id: Session ID
            text_msg: Text message from ADK agent
        """
        if not self.tts_adapter or not self.tts_adapter.client:
            # No TTS adapter or client, just echo the text back
            await websocket.send_json({"message": text_msg})
            return
            
        # Convert text to speech
        try:
            # Stream text to Google Cloud TTS and get audio chunks
            audio_chunks = []
            async for audio_chunk in self.tts_adapter.stream_speech(text_msg):
                # Encode audio as base64
                encoded_audio = base64.b64encode(audio_chunk).decode("utf-8")
                
                # Send to client
                await websocket.send_json({"audio_chunk": encoded_audio})
                
                # Store for potential replay
                audio_chunks.append(audio_chunk)
                
            # Store in session for potential replay
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["last_audio"] = audio_chunks
                
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            # Fall back to text
            await websocket.send_json({"message": text_msg})
            
    async def handle_adk_stream(
        self, 
        websocket: WebSocket, 
        session_id: str, 
        agent: BaseAgent
    ):
        """
        Handle an ADK event stream.
        
        Args:
            websocket: WebSocket connection to client
            session_id: Session ID
            agent: ADK agent
        """
        # Set up session
        self.active_sessions[session_id] = {
            "websocket": websocket,
            "last_text": "",
            "last_audio": []
        }
        
        # Create a runner for the agent
        runner = Runner(agent=agent)
        
        # Start listening for WebSocket messages
        asyncio.create_task(self._receive_client_messages(websocket, session_id, runner))
        
        try:
            # Main WebSocket loop
            while True:
                # Wait for client message
                await asyncio.sleep(0.1)
                
        except WebSocketDisconnect:
            # Client disconnected
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
        except Exception as e:
            logger.error(f"Error in ADK stream handler: {e}")
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                
    async def _receive_client_messages(self, websocket: WebSocket, session_id: str, runner: Runner):
        """
        Receive messages from client and forward to ADK.
        
        Args:
            websocket: WebSocket connection to client
            session_id: Session ID
            runner: ADK runner
        """
        try:
            while True:
                # Receive message from client
                message = await websocket.receive()
                
                if "text" in message:
                    # Process text message
                    try:
                        data = json.loads(message["text"])
                        
                        if "type" in data and data["type"] == "text_input":
                            # Text input
                            text = data.get("text", "")
                            if text:
                                # Run agent with text
                                response = await runner.run_text(text)
                                
                                # Process response text
                                response_text = str(response.response) if hasattr(response, "response") else ""
                                if response_text:
                                    await self.handle_websocket(websocket, session_id, response_text)
                    
                    except json.JSONDecodeError:
                        logger.warning(f"Received invalid JSON from client: {message}")
                
                # Later: Implement audio handling for speech-to-text
                
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from session {session_id}")
        
        except Exception as e:
            logger.error(f"Error receiving client messages: {e}")

def setup_voice_handler() -> ADKVoiceHandler:
    """
    Set up an ADK voice handler.
    
    Returns:
        ADKVoiceHandler: ADK voice handler
    """
    # Create a Google Cloud TTS adapter
    tts_adapter = GoogleCloudTTSAdapter()
    if tts_adapter.client:
        logger.info("Created Google Cloud TTS adapter for TTS")
    else:
        logger.warning("Could not create Google Cloud TTS adapter - check GOOGLE_APPLICATION_CREDENTIALS in environment")
    
    # Create and return handler
    return ADKVoiceHandler(tts_adapter)
