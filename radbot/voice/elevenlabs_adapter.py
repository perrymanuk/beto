"""
Adapter for integrating ElevenLabs Text-to-Speech with ADK.

This module provides an adapter that integrates ElevenLabs Text-to-Speech
with the ADK web interface's streaming capabilities.
"""

import asyncio
import base64
import json
import logging
import os
from typing import Dict, Any, Optional, Callable, Awaitable

from radbot.voice.elevenlabs_client import ElevenLabsClient, create_elevenlabs_client

# Set up logging
logger = logging.getLogger(__name__)

class ElevenLabsAdapter:
    """
    Adapter for integrating ElevenLabs Text-to-Speech with ADK.
    
    This adapter monitors text responses from the ADK agent and converts
    them to speech using ElevenLabs TTS.
    """
    
    def __init__(self, send_audio_callback: Optional[Callable[[bytes], Awaitable[None]]] = None):
        """
        Initialize the ElevenLabs adapter.
        
        Args:
            send_audio_callback: Callback for sending audio to the client
        """
        self.client = create_elevenlabs_client()
        self.send_audio_callback = send_audio_callback
        self.text_queue = asyncio.Queue()
        self.current_text = ""
        self.running = False
        self.tts_task = None
        
        # Check if TTS is available
        if self.client:
            logger.info("ElevenLabs TTS client initialized")
        else:
            logger.warning("ElevenLabs TTS client not available - check ELEVEN_LABS_API_KEY")
    
    def start(self):
        """Start the TTS processing loop."""
        if not self.running:
            self.running = True
            self.tts_task = asyncio.create_task(self._tts_loop())
            logger.info("ElevenLabs TTS adapter started")
    
    def stop(self):
        """Stop the TTS processing loop."""
        if self.running:
            self.running = False
            if self.tts_task:
                self.tts_task.cancel()
            logger.info("ElevenLabs TTS adapter stopped")
    
    async def process_text(self, text: str):
        """
        Process text from the agent.
        
        Args:
            text: Text to process
        """
        if not self.client:
            # No TTS client available
            return
            
        # For streaming, we need to determine what's new
        if not text.startswith(self.current_text):
            # Text doesn't start with current text, just process the whole thing
            await self.text_queue.put(text)
            self.current_text = text
        else:
            # Text starts with current text, so get just the new part
            new_text = text[len(self.current_text):]
            if new_text:
                await self.text_queue.put(new_text)
                self.current_text = text
    
    async def _tts_loop(self):
        """Process text in the queue and convert to speech."""
        if not self.client:
            return
            
        try:
            while self.running:
                # Get next text from queue
                try:
                    text = await asyncio.wait_for(self.text_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    # No text available, continue
                    continue
                
                if not text.strip():
                    self.text_queue.task_done()
                    continue
                
                try:
                    # Convert text to speech
                    logger.debug(f"Converting to speech: {text[:50]}...")
                    
                    # Stream audio from ElevenLabs
                    async for audio_chunk in self.client.stream_speech(text):
                        if self.send_audio_callback:
                            # Send audio chunk to client
                            await self.send_audio_callback(audio_chunk)
                        else:
                            # No callback, just log
                            logger.debug(f"Generated {len(audio_chunk)} bytes of audio")
                except Exception as e:
                    logger.error(f"Error converting text to speech: {e}")
                
                # Mark as done
                self.text_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info("TTS loop cancelled")
        except Exception as e:
            logger.error(f"Error in TTS loop: {e}")

def before_agent_callback(shared_context: Dict[str, Any], inputs: Any, outputs: Any) -> Any:
    """
    Callback that runs before the agent processes input.
    
    This is used to prepare for TTS.
    
    Args:
        shared_context: Shared context between callbacks
        inputs: Agent inputs
        outputs: Agent outputs
        
    Returns:
        Agent outputs
    """
    # Initialize TTS adapter if needed
    if "tts_adapter" not in shared_context:
        # Create adapter with callback for sending audio
        # The actual callback will be set when we have a WebSocket connection
        shared_context["tts_adapter"] = ElevenLabsAdapter()
        shared_context["tts_adapter"].start()
        logger.info("Initialized TTS adapter in shared context")
    
    return outputs

def after_agent_callback(shared_context: Dict[str, Any], inputs: Any, outputs: Any) -> Any:
    """
    Callback that runs after the agent processes input.
    
    This is used to send the agent's response to the TTS adapter.
    
    Args:
        shared_context: Shared context between callbacks
        inputs: Agent inputs
        outputs: Agent outputs
        
    Returns:
        Agent outputs
    """
    # Get TTS adapter
    tts_adapter = shared_context.get("tts_adapter")
    if not tts_adapter:
        return outputs
    
    # Process agent response
    if hasattr(outputs, "response"):
        # Process response text
        response_text = str(outputs.response)
        if response_text:
            # Create task to process text
            asyncio.create_task(tts_adapter.process_text(response_text))
    
    return outputs

async def send_audio_to_client(websocket, audio_data: bytes):
    """
    Send audio data to a client via WebSocket.
    
    Args:
        websocket: WebSocket connection
        audio_data: Audio data to send
    """
    try:
        # Encode audio as base64
        encoded_audio = base64.b64encode(audio_data).decode("utf-8")
        
        # Create message
        message = {
            "audio_chunk": encoded_audio
        }
        
        # Send to client
        await websocket.send_text(json.dumps(message))
    except Exception as e:
        logger.error(f"Error sending audio to client: {e}")

def setup_tts_for_websocket(shared_context: Dict[str, Any], websocket):
    """
    Set up TTS for a WebSocket connection.
    
    Args:
        shared_context: Shared context between callbacks
        websocket: WebSocket connection
    """
    # Get TTS adapter
    tts_adapter = shared_context.get("tts_adapter")
    if not tts_adapter:
        logger.warning("No TTS adapter available in shared context")
        return
    
    # Set callback for sending audio to client
    tts_adapter.send_audio_callback = lambda audio: send_audio_to_client(websocket, audio)
    logger.info("Set up TTS for WebSocket connection")
