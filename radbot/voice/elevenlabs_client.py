"""
ElevenLabs client for text-to-speech conversion via WebSocket API.

This module provides a client for converting text to speech using ElevenLabs'
WebSocket API, which offers low-latency streaming capabilities.
"""

import asyncio
import base64
import json
import logging
import os
from typing import Optional, Dict, List, Any, AsyncGenerator, Callable

import websockets
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger(__name__)

class ElevenLabsConfig(BaseModel):
    """Configuration for ElevenLabs client."""
    api_key: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default voice
    model_id: str = "eleven_flash_v2_5"      # Lowest latency model
    output_format: str = "pcm_24000"         # Default output format
    stability: float = 0.5                   # Voice stability (0.0-1.0)
    similarity_boost: float = 0.8            # Voice similarity boost (0.0-1.0)

class ElevenLabsClient:
    """
    Client for ElevenLabs WebSocket API for streaming TTS.
    
    This client connects to the ElevenLabs WebSocket API and streams text
    to be synthesized into speech, receiving audio chunks in real-time.
    """
    
    def __init__(self, config: ElevenLabsConfig):
        """
        Initialize the ElevenLabs WebSocket client.
        
        Args:
            config: Configuration for the ElevenLabs client
        """
        self.config = config
        self._ws_url = (
            f"wss://api.elevenlabs.io/v1/text-to-speech/{config.voice_id}/stream-input"
            f"?model_id={config.model_id}&output_format={config.output_format}"
        )
        self._voice_settings = {
            "stability": config.stability,
            "similarity_boost": config.similarity_boost
        }
        
    async def test_connection(self) -> bool:
        """
        Test the connection to ElevenLabs API.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Use a simple voice generation to test the connection
            test_text = "Connection test."
            async for _ in self.stream_speech(test_text):
                # Just getting one chunk is enough to verify connection
                return True
        except Exception as e:
            logger.error(f"ElevenLabs connection test failed: {e}")
            return False
            
    async def stream_speech(
        self, 
        text: str,
        chunk_callback: Optional[Callable[[bytes], None]] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream text to speech using ElevenLabs WebSocket API.
        
        Args:
            text: Text to convert to speech
            chunk_callback: Optional callback for each audio chunk
            
        Yields:
            bytes: Audio chunks as they are received
        """
        if not text.strip():
            return
            
        try:
            async with websockets.connect(self._ws_url) as ws:
                # Initial configuration message
                await ws.send(json.dumps({
                    "text": " ",  # Single space required to initialize
                    "voice_settings": self._voice_settings,
                    "xi_api_key": self.config.api_key
                }))
                
                # Send the text as one chunk with flush=True to ensure immediate generation
                await ws.send(json.dumps({
                    "text": text + " ",  # Add space for better flow
                    "flush": True  # Force immediate generation
                }))
                
                # Signal end of text
                await ws.send(json.dumps({"text": ""}))
                
                # Receive and yield audio chunks
                async for message in ws:
                    # Audio data is binary, status messages are JSON strings
                    if isinstance(message, bytes):
                        if chunk_callback:
                            chunk_callback(message)
                        yield message
                    else:
                        # Handle JSON status message
                        try:
                            status = json.loads(message)
                            if status.get("isFinal"):
                                logger.debug("Received final message from ElevenLabs")
                                break
                            if status.get("error"):
                                logger.error(f"ElevenLabs error: {status.get('error')}")
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"Received invalid JSON status: {message}")
                
        except Exception as e:
            logger.error(f"Error in ElevenLabs WebSocket connection: {e}")
            raise

def create_elevenlabs_client() -> Optional[ElevenLabsClient]:
    """
    Create an ElevenLabs client from environment variables.
    
    Returns:
        Optional[ElevenLabsClient]: ElevenLabs client or None if configuration is missing
    """
    api_key = os.environ.get("ELEVEN_LABS_API_KEY")
    if not api_key:
        logger.warning("ELEVEN_LABS_API_KEY not found in environment variables")
        return None
        
    config = ElevenLabsConfig(
        api_key=api_key,
        voice_id=os.environ.get("ELEVEN_LABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
        model_id=os.environ.get("ELEVEN_LABS_MODEL", "eleven_flash_v2_5"),
        output_format=os.environ.get("ELEVEN_LABS_OUTPUT_FORMAT", "pcm_24000"),
        stability=float(os.environ.get("ELEVEN_LABS_STABILITY", "0.5")),
        similarity_boost=float(os.environ.get("ELEVEN_LABS_SIMILARITY_BOOST", "0.8"))
    )
    
    return ElevenLabsClient(config)
    
async def test_elevenlabs_connection() -> bool:
    """
    Test the connection to ElevenLabs API.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    client = create_elevenlabs_client()
    if not client:
        return False
        
    return await client.test_connection()
