"""
Adapter for integrating Google Cloud Text-to-Speech with ADK.

This module provides an adapter that integrates Google Cloud Text-to-Speech
with the ADK web interface's streaming capabilities.
"""

import asyncio
import base64
import json
import logging
import os
from typing import Dict, Any, Optional, Callable, Awaitable, List, AsyncGenerator

import websockets
from google.cloud import texttospeech
from google.cloud import texttospeech_v1

# Set up logging
logger = logging.getLogger(__name__)

class GoogleCloudTTSAdapter:
    """
    Adapter for integrating Google Cloud Text-to-Speech with ADK.
    
    This adapter monitors text responses from the ADK agent and converts
    them to speech using Google Cloud TTS streaming.
    """
    
    def __init__(self, send_audio_callback: Optional[Callable[[bytes], Awaitable[None]]] = None):
        """
        Initialize the Google Cloud TTS adapter.
        
        Args:
            send_audio_callback: Callback for sending audio to the client
        """
        # Try to create the client
        self.client = create_google_cloud_tts_client()
        self.send_audio_callback = send_audio_callback
        self.text_queue = asyncio.Queue()
        self.current_text = ""
        self.running = False
        self.tts_task = None
        
        # Check if TTS is available
        if self.client:
            client_type = type(self.client).__name__
            logger.info(f"Google Cloud TTS client initialized ({client_type})")
            
            # Check if streaming is available
            try:
                # Check if streaming_synthesize is available
                if hasattr(self.client, 'streaming_synthesize'):
                    logger.info("Streaming synthesis API is available")
                else:
                    logger.warning("Streaming synthesis API not available - falling back to standard synthesis")
            except Exception as e:
                logger.warning(f"Error checking streaming API: {e}")
        else:
            logger.warning("Google Cloud TTS client not available - check GOOGLE_APPLICATION_CREDENTIALS")
    
    def start(self):
        """Start the TTS processing loop."""
        if not self.running:
            self.running = True
            self.tts_task = asyncio.create_task(self._tts_loop())
            logger.info("Google Cloud TTS adapter started")
    
    def stop(self):
        """Stop the TTS processing loop."""
        if self.running:
            self.running = False
            if self.tts_task:
                self.tts_task.cancel()
            logger.info("Google Cloud TTS adapter stopped")
    
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
                # Use a shorter timeout to respond more quickly to cancellation
                try:
                    text = await asyncio.wait_for(self.text_queue.get(), timeout=0.05)
                except asyncio.TimeoutError:
                    # No text available, just yield control
                    await asyncio.sleep(0)
                    continue
                
                if not text.strip():
                    self.text_queue.task_done()
                    continue
                
                try:
                    # Convert text to speech
                    logger.debug(f"Converting to speech: {text[:50]}...")
                    
                    # Use a shield to protect from cancellation during streaming
                    streaming_task = asyncio.create_task(self._process_speech_text(text))
                    
                    # Wait for the streaming to complete, but allow cancellation
                    try:
                        await streaming_task
                    except asyncio.CancelledError:
                        # Cancel the streaming task if we're cancelled
                        if not streaming_task.done():
                            streaming_task.cancel()
                        raise
                        
                except Exception as e:
                    logger.error(f"Error converting text to speech: {e}")
                    
                # Mark as done
                self.text_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info("TTS loop cancelled")
            # Don't re-raise
        except Exception as e:
            logger.error(f"Error in TTS loop: {e}")
            
    async def _process_speech_text(self, text: str):
        """Process a single text chunk for speech synthesis."""
        try:
            logger.info(f"Processing speech text: {text[:30]}...")
            # Stream audio from Google Cloud TTS
            async for audio_chunk in self.stream_speech(text):
                if not self.running:
                    # Stop if we're no longer running
                    break
                    
                logger.debug(f"Received audio chunk of {len(audio_chunk)} bytes")
                if self.send_audio_callback:
                    # Send audio chunk to client
                    await self.send_audio_callback(audio_chunk)
                else:
                    # No callback, just log
                    logger.debug(f"Generated {len(audio_chunk)} bytes of audio")
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            logger.info("Speech processing cancelled")
            # Don't re-raise
        except Exception as e:
            logger.error(f"Error processing speech text: {e}")

    async def stream_speech(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Stream text to speech using Google Cloud TTS.
        
        Args:
            text: Text to convert to speech
            
        Yields:
            bytes: Audio chunks as they are received
        """
        if not text.strip():
            return
        
        # Set up streaming configuration
        voice_params = get_voice_selection_params()
        audio_config = get_audio_config()
        
        # Create streaming config request - handle both API versions
        try:
            # Try the v1 module first
            streaming_config = texttospeech_v1.StreamingSynthesizeRequest(
                streaming_config=texttospeech_v1.StreamingSynthesizeConfig(
                    voice=voice_params,
                    audio_config=audio_config
                )
            )
            
            # Create text iterator for streaming
            # Use a single chunk to avoid generator issues
            text_chunks = [text]
            
            # Create request generator
            request_iterator = []
            # First add the config request
            request_iterator.append(streaming_config)
            
            # Then add each text chunk
            for chunk in text_chunks:
                if chunk.strip():
                    request_iterator.append(texttospeech_v1.StreamingSynthesizeRequest(
                        input=texttospeech_v1.StreamingSynthesisInput(text=chunk)
                    ))
            
            # Stream responses using the new API
            logger.info("Using texttospeech_v1 for streaming synthesis")
            streaming_responses = self.client.streaming_synthesize(iter(request_iterator))
        except (AttributeError, ImportError) as e:
            logger.warning(f"Failed to use texttospeech_v1 for streaming: {e}")
            # Try to use the top-level module as fallback
            try:
                # Fallback to the top-level module if possible
                input_text = texttospeech.SynthesisInput(text=text)
                voice = texttospeech.VoiceSelectionParams(
                    language_code=voice_params.language_code,
                    name=voice_params.name
                )
                audio_config_fallback = texttospeech.AudioConfig(
                    audio_encoding=audio_config.audio_encoding,
                    speaking_rate=audio_config.speaking_rate,
                    pitch=audio_config.pitch,
                    volume_gain_db=audio_config.volume_gain_db
                )
                
                # Use regular synthesize_speech instead
                logger.info("Falling back to standard synthesis (non-streaming)")
                response = self.client.synthesize_speech(
                    input=input_text,
                    voice=voice,
                    audio_config=audio_config_fallback
                )
                
                # Return single chunk of audio
                if response.audio_content:
                    yield response.audio_content
                
                # Exit generator after yielding non-streaming response
                return
            except Exception as inner_e:
                # Both approaches failed
                logger.error(f"Both streaming and standard synthesis failed: {inner_e}")
                return
        
        try:
            # Process streaming responses
            for response in streaming_responses:
                # Check if we should stop
                if not self.running:
                    break
                    
                # Yield audio content
                if response.audio_content:
                    yield response.audio_content
                    
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            logger.info("TTS streaming cancelled")
        except Exception as e:
            logger.error(f"Error in Google Cloud TTS streaming: {e}")
            # Don't re-raise to avoid unhandled exceptions in async generators

def create_google_cloud_tts_client() -> Optional[texttospeech.TextToSpeechClient]:
    """
    Create a Google Cloud TTS client.
    
    Returns:
        Optional[texttospeech.TextToSpeechClient]: TTS client or None if configuration is missing
    """
    try:
        # Check for Google Cloud credentials
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            # Try to use default credentials
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set, attempting to use default credentials")
        
        # Create the client using the standard module
        client = texttospeech.TextToSpeechClient()
        return client
    except Exception as e:
        logger.error(f"Failed to create Google Cloud TTS client: {e}")
        return None

def get_voice_selection_params() -> texttospeech_v1.VoiceSelectionParams:
    """
    Get voice selection parameters from environment variables.
    
    Returns:
        texttospeech_v1.VoiceSelectionParams: Voice selection parameters
    """
    language_code = os.environ.get("GOOGLE_TTS_LANGUAGE_CODE", "en-US")
    voice_name = os.environ.get("GOOGLE_TTS_VOICE_NAME", "en-US-Journey-F")
    
    # Create voice selection parameters using version-specific module
    # This is for the streaming implementation
    return texttospeech_v1.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name
    )

def get_audio_config() -> texttospeech_v1.AudioConfig:
    """
    Get audio configuration from environment variables.
    
    Returns:
        texttospeech_v1.AudioConfig: Audio configuration
    """
    # Get audio parameters from environment variables
    audio_encoding_str = os.environ.get("GOOGLE_TTS_AUDIO_ENCODING", "LINEAR16")
    speaking_rate = float(os.environ.get("GOOGLE_TTS_SPEAKING_RATE", "1.0"))
    pitch = float(os.environ.get("GOOGLE_TTS_PITCH", "0.0"))
    volume_gain_db = float(os.environ.get("GOOGLE_TTS_VOLUME_GAIN_DB", "0.0"))
    
    # Map audio encoding string to enum
    audio_encoding_map = {
        "LINEAR16": texttospeech_v1.AudioEncoding.LINEAR16,
        "MP3": texttospeech_v1.AudioEncoding.MP3,
        "OGG_OPUS": texttospeech_v1.AudioEncoding.OGG_OPUS
    }
    
    audio_encoding = audio_encoding_map.get(
        audio_encoding_str, texttospeech_v1.AudioEncoding.LINEAR16
    )
    
    # Create audio configuration for streaming implementation
    return texttospeech_v1.AudioConfig(
        audio_encoding=audio_encoding,
        speaking_rate=speaking_rate,
        pitch=pitch,
        volume_gain_db=volume_gain_db
    )

def split_text_into_chunks(text: str, max_chunk_size: int = 100) -> List[str]:
    """
    Split text into chunks for streaming.
    
    Args:
        text: Text to split
        max_chunk_size: Maximum chunk size in characters
        
    Returns:
        List[str]: List of text chunks
    """
    # Split at sensible boundaries
    chunks = []
    
    # Handle empty text
    if not text:
        return chunks
    
    # Try to split at sentence boundaries
    sentences = text.replace("\n", " ").split(". ")
    current_chunk = ""
    
    for sentence in sentences:
        # Add period back if it was removed (except for the last sentence)
        if sentence != sentences[-1] and not sentence.endswith("."):
            sentence = sentence + "."
        
        # If adding this sentence would exceed max chunk size,
        # add current chunk to list and start a new chunk
        if len(current_chunk) + len(sentence) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If sentence is longer than max_chunk_size, split it
            if len(sentence) > max_chunk_size:
                # Split long sentences at word boundaries
                words = sentence.split()
                current_chunk = ""
                
                for word in words:
                    if len(current_chunk) + len(word) + 1 > max_chunk_size:
                        chunks.append(current_chunk)
                        current_chunk = word
                    else:
                        if current_chunk:
                            current_chunk += " " + word
                        else:
                            current_chunk = word
            else:
                current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

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
        shared_context["tts_adapter"] = GoogleCloudTTSAdapter()
        shared_context["tts_adapter"].start()
        logger.info("Initialized Google Cloud TTS adapter in shared context")
    
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
        
        # We need to handle cases where the WebSocket is disconnected while we're sending
        try:
            # Use a timeout for the send operation
            await asyncio.wait_for(
                websocket.send_text(json.dumps(message)),
                timeout=1.0  # 1 second timeout
            )
        except (asyncio.TimeoutError, websockets.exceptions.WebSocketException):
            logger.warning("WebSocket message timed out or connection closed")
            # Return to signal a problem
            return False
    except asyncio.CancelledError:
        # Handle cancellation explicitly
        logger.info("Audio sending cancelled")
        # Re-raise to properly propagate cancellation
        raise
    except Exception as e:
        logger.error(f"Error sending audio to client: {e}")
        return False
        
    # Successful send
    return True

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
    
    # Define a wrapper for the send_audio_to_client function
    async def safe_send_audio(audio: bytes):
        # Use send_audio_to_client but handle errors
        success = await send_audio_to_client(websocket, audio)
        # If send failed, stop the TTS adapter to prevent more failed sends
        if not success and tts_adapter and tts_adapter.running:
            logger.warning("WebSocket send failed, stopping TTS adapter")
            tts_adapter.stop()
            
    # Set callback for sending audio to client
    tts_adapter.send_audio_callback = safe_send_audio
    logger.info("Set up TTS for WebSocket connection")
