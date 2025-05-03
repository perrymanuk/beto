#!/usr/bin/env python3
"""
Simple test script for Google Cloud TTS.

This script tests the Google Cloud TTS functionality without any ADK dependencies.
"""

import os
import asyncio
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simple_tts_test")

# Import necessary modules
try:
    from google.cloud import texttospeech
    logger.info("Successfully imported texttospeech module")
except ImportError as e:
    logger.error(f"Failed to import texttospeech module: {e}")
    raise

async def test_google_cloud_tts():
    """Test Google Cloud TTS functionality."""
    # Check for credentials
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    try:
        # Create a client instance
        client = texttospeech.TextToSpeechClient()
        logger.info(f"Created TextToSpeechClient successfully (type: {type(client).__name__})")
        
        # Test standard synthesis
        await test_standard_synthesis(client)
        
        # Test streaming synthesis if available
        await test_streaming_synthesis(client)
        
        logger.info("All tests completed successfully")
    except Exception as e:
        logger.error(f"Error during TTS test: {e}")
        raise

async def test_standard_synthesis(client):
    """Test standard synthesis API."""
    logger.info("Testing standard synthesis...")
    
    try:
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text="Hello, this is a test of the Google Cloud Text-to-Speech API")

        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-F",  # Journey voice is recommended for best quality
        )

        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=1.0,
            pitch=0.0
        )

        # Perform the synthesis request
        logger.info("Calling synthesize_speech...")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # The response's audio_content is binary
        logger.info(f"Synthesis successful! Received {len(response.audio_content)} bytes of audio")
        
        # Write the response to a file
        output_file = "test_output.wav"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        logger.info(f"Audio content written to '{output_file}'")
        
        return True
    except Exception as e:
        logger.error(f"Error in standard synthesis: {e}")
        return False

async def test_streaming_synthesis(client):
    """Test streaming synthesis API if available."""
    # Check if streaming_synthesize method is available
    if not hasattr(client, 'streaming_synthesize'):
        logger.warning("streaming_synthesize method not available on the client. Skipping streaming test.")
        return False
    
    logger.info("Testing streaming synthesis...")
    
    try:
        # Try to import necessary classes for streaming
        try:
            from google.cloud.texttospeech_v1.types import (
                StreamingSynthesizeConfig, 
                StreamingSynthesizeRequest,
                StreamingSynthesisInput,
            )
            logger.info("Successfully imported streaming synthesis types from google.cloud.texttospeech_v1.types")
        except ImportError as e:
            logger.error(f"Failed to import streaming types: {e}")
            return False
        
        # Create streaming config
        streaming_config = StreamingSynthesizeConfig(
            voice=texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Journey-F",
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                speaking_rate=1.0,
                pitch=0.0
            )
        )
        
        # Create streaming request
        config_request = StreamingSynthesizeRequest(
            streaming_config=streaming_config
        )
        
        # Create text chunks
        text_chunks = [
            "Hello there. ",
            "How are you ",
            "today? It's ",
            "such nice weather outside."
        ]
        
        # Create request generator
        def request_generator():
            yield config_request
            for text in text_chunks:
                yield StreamingSynthesizeRequest(
                    input=StreamingSynthesisInput(text=text)
                )
        
        # Call streaming synthesis
        logger.info("Calling streaming_synthesize...")
        streaming_responses = client.streaming_synthesize(request_generator())
        
        # Process responses
        total_bytes = 0
        output_file = "test_streaming_output.wav"
        with open(output_file, "wb") as out:
            for response in streaming_responses:
                if response.audio_content:
                    out.write(response.audio_content)
                    total_bytes += len(response.audio_content)
                    logger.info(f"Received chunk of {len(response.audio_content)} bytes")
        
        logger.info(f"Streaming synthesis successful! Received {total_bytes} bytes of audio")
        logger.info(f"Audio content written to '{output_file}'")
        
        return True
    except Exception as e:
        logger.error(f"Error in streaming synthesis: {e}")
        return False

async def main():
    """Run the test."""
    try:
        await test_google_cloud_tts()
        return 0
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
