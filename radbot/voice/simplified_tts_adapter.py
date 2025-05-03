"""
Simplified Google Cloud Text-to-Speech adapter.

This module provides a simplified adapter for Google Cloud Text-to-Speech
without any integration with the ADK web interface.
"""

import asyncio
import logging
import os
from typing import AsyncGenerator, Callable, Awaitable, Optional, List

# Import Google Cloud TTS
from google.cloud import texttospeech

# Configure logging
logger = logging.getLogger(__name__)

class SimplifiedTTSAdapter:
    """
    Simplified adapter for Google Cloud Text-to-Speech.
    
    This adapter provides a simplified interface to Google Cloud TTS
    without any integration with ADK.
    """
    
    def __init__(self, send_audio_callback: Optional[Callable[[bytes], Awaitable[None]]] = None):
        """
        Initialize the adapter.
        
        Args:
            send_audio_callback: Callback for sending audio to a client
        """
        # Create the client
        self.client = self._create_client()
        self.send_audio_callback = send_audio_callback
        
        # Check if client was created successfully
        if self.client:
            client_type = type(self.client).__name__
            logger.info(f"Google Cloud TTS client initialized ({client_type})")
            
            # Check for streaming support
            if hasattr(self.client, 'streaming_synthesize'):
                logger.info("Streaming synthesis is supported")
                self.supports_streaming = True
            else:
                logger.info("Streaming synthesis is not supported, will use standard synthesis")
                self.supports_streaming = False
        else:
            logger.warning("Failed to create Google Cloud TTS client")
            self.supports_streaming = False
    
    def _create_client(self) -> Optional[texttospeech.TextToSpeechClient]:
        """
        Create a Google Cloud TTS client.
        
        Returns:
            Optional[texttospeech.TextToSpeechClient]: The client, or None if creation failed
        """
        try:
            # Check for credentials
            if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set, trying default credentials")
            
            # Create the client
            return texttospeech.TextToSpeechClient()
        except Exception as e:
            logger.error(f"Error creating Google Cloud TTS client: {e}")
            return None
    
    async def synthesize_text(self, text: str) -> List[bytes]:
        """
        Synthesize text to speech.
        
        Args:
            text: The text to synthesize
            
        Returns:
            List[bytes]: List of audio chunks
        """
        if not text.strip():
            return []
        
        if not self.client:
            logger.error("No Google Cloud TTS client available")
            return []
        
        logger.info(f"Synthesizing text: {text[:50]}...")
        
        audio_chunks = []
        
        # Try streaming synthesis first if supported
        if self.supports_streaming:
            try:
                # Let's see if we can access the streaming API
                import google.cloud.texttospeech_v1.types as types_v1
                
                # Create voice and audio config
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    name="en-US-Journey-F",
                )
                
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                    speaking_rate=1.0,
                    pitch=0.0,
                )
                
                # Try streaming synthesis
                logger.info("Attempting streaming synthesis...")
                
                # Create streaming config
                streaming_config = types_v1.StreamingSynthesizeConfig(
                    voice=voice,
                    audio_config=audio_config,
                )
                
                # Create initial config request
                config_request = types_v1.StreamingSynthesizeRequest(
                    streaming_config=streaming_config,
                )
                
                # Split text into chunks (or just use one chunk for simplicity)
                text_chunks = [text]
                
                # Create request generator
                def request_generator():
                    # First yield the config
                    yield config_request
                    
                    # Then yield each text chunk
                    for chunk in text_chunks:
                        if chunk.strip():
                            yield types_v1.StreamingSynthesizeRequest(
                                input=types_v1.StreamingSynthesisInput(text=chunk),
                            )
                
                # Make the streaming request
                for response in self.client.streaming_synthesize(request_generator()):
                    if response.audio_content:
                        # Collect audio chunks
                        audio_chunks.append(response.audio_content)
                        
                        # Send to callback if provided
                        if self.send_audio_callback:
                            await self.send_audio_callback(response.audio_content)
                
                # If we got audio chunks, we're done
                if audio_chunks:
                    logger.info(f"Streaming synthesis successful: {len(audio_chunks)} chunks, {sum(len(c) for c in audio_chunks)} bytes")
                    return audio_chunks
                
                # If we got here but no audio chunks, fall back to standard synthesis
                logger.warning("Streaming synthesis returned no audio chunks, falling back to standard synthesis")
            
            except Exception as e:
                logger.error(f"Error in streaming synthesis, falling back to standard synthesis: {e}")
        
        # If streaming failed or is not supported, try standard synthesis
        try:
            # Create synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Create voice selection
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Journey-F",
            )
            
            # Create audio config
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                speaking_rate=1.0,
                pitch=0.0,
            )
            
            # Make the request
            logger.info("Performing standard synthesis...")
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )
            
            # Add the audio content
            if response.audio_content:
                audio_chunks.append(response.audio_content)
                
                # Send to callback if provided
                if self.send_audio_callback:
                    await self.send_audio_callback(response.audio_content)
                
                logger.info(f"Standard synthesis successful: {len(response.audio_content)} bytes")
            else:
                logger.warning("Standard synthesis returned no audio content")
        
        except Exception as e:
            logger.error(f"Error in standard synthesis: {e}")
        
        return audio_chunks

async def test_simplified_adapter():
    """
    Test the simplified adapter.
    """
    # Create a list to collect audio chunks
    audio_chunks = []
    
    async def collect_audio(chunk: bytes):
        """Collect audio chunks."""
        audio_chunks.append(chunk)
        logger.info(f"Collected audio chunk: {len(chunk)} bytes")
    
    # Create the adapter
    adapter = SimplifiedTTSAdapter(send_audio_callback=collect_audio)
    
    # Check if adapter has a client
    if not adapter.client:
        logger.error("Failed to create adapter client")
        return
    
    # Test synthesizing some text
    test_text = "Hello! This is a test of the simplified Google Cloud Text-to-Speech adapter."
    chunks = await adapter.synthesize_text(test_text)
    
    # Check if we got any chunks
    if chunks:
        logger.info(f"Test successful! Received {len(chunks)} chunks totaling {sum(len(c) for c in chunks)} bytes")
        
        # Save to file for verification
        output_file = "simplified_adapter_test.wav"
        with open(output_file, "wb") as f:
            for chunk in chunks:
                f.write(chunk)
        logger.info(f"Saved audio to {output_file}")
    else:
        logger.warning("No audio chunks received")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run the test
    asyncio.run(test_simplified_adapter())
