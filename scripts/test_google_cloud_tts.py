#!/usr/bin/env python3
"""
Test script for Google Cloud TTS adapter.

This script tests the Google Cloud TTS adapter with a simple text input
and verifies that it can properly stream audio output.
"""

import asyncio
import os
import sys
import time
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the Google Cloud TTS adapter
from radbot.voice.google_cloud_tts_adapter import (
    GoogleCloudTTSAdapter,
    create_google_cloud_tts_client
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("test_google_cloud_tts")

# Test text
TEST_TEXT = """
Hello! This is a test of the Google Cloud Text-to-Speech adapter.
We are testing if the streaming functionality works correctly with
the ADK web interface.
"""

async def save_audio_chunk(chunk, file_prefix="output"):
    """Save an audio chunk to a file."""
    # Generate a unique filename
    timestamp = int(time.time() * 1000)
    filename = f"{file_prefix}_{timestamp}.wav"
    
    # Save the chunk
    with open(filename, "wb") as f:
        f.write(chunk)
    
    logger.info(f"Saved audio chunk to {filename} ({len(chunk)} bytes)")

async def test_streaming():
    """Test streaming audio from Google Cloud TTS."""
    logger.info("Creating Google Cloud TTS adapter...")
    # Create adapter with a callback
    adapter = GoogleCloudTTSAdapter(
        send_audio_callback=save_audio_chunk
    )
    
    # Check if adapter client is available
    if not adapter.client:
        logger.error("Google Cloud TTS client not available - check GOOGLE_APPLICATION_CREDENTIALS")
        return False
    
    # Start the adapter
    adapter.start()
    logger.info("Started TTS adapter")
    
    try:
        # Stream some text
        logger.info(f"Converting text to speech: {TEST_TEXT[:50]}...")
        await adapter.process_text(TEST_TEXT)
        
        # Wait for processing to complete
        while not adapter.text_queue.empty():
            logger.info("Waiting for text queue to be processed...")
            await asyncio.sleep(1)
        
        # Give a little more time for all audio to be generated
        await asyncio.sleep(2)
        
        logger.info("Test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        return False
    finally:
        # Stop the adapter
        adapter.stop()
        logger.info("Stopped TTS adapter")

async def test_cancellation():
    """Test cancellation behavior of the TTS adapter."""
    logger.info("Testing cancellation behavior...")
    
    # Create adapter
    adapter = GoogleCloudTTSAdapter()
    
    # Check if adapter client is available
    if not adapter.client:
        logger.error("Google Cloud TTS client not available - check GOOGLE_APPLICATION_CREDENTIALS")
        return False
    
    # Start the adapter
    adapter.start()
    logger.info("Started TTS adapter")
    
    try:
        # Create a long text to ensure processing takes time
        long_text = TEST_TEXT * 20
        
        # Process the text
        logger.info(f"Adding long text to queue ({len(long_text)} characters)...")
        await adapter.process_text(long_text)
        
        # Wait a short time for processing to start
        await asyncio.sleep(0.5)
        
        # Then stop the adapter (cancel the task)
        logger.info("Stopping adapter to test cancellation...")
        adapter.stop()
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Check if everything was cleaned up properly
        if adapter.tts_task and not adapter.tts_task.done():
            logger.error("TTS task is still running!")
            return False
            
        logger.info("Cancellation test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in cancellation test: {e}")
        return False

async def main():
    """Run the tests."""
    logger.info("Starting Google Cloud TTS adapter tests...")
    
    # Check environment variables
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set!")
    
    # Test client creation
    client = create_google_cloud_tts_client()
    if not client:
        logger.error("Failed to create Google Cloud TTS client!")
        return 1
    
    logger.info("Google Cloud TTS client created successfully")
    
    # Run the streaming test
    streaming_result = await test_streaming()
    
    # Run the cancellation test
    cancellation_result = await test_cancellation()
    
    # Check results
    if streaming_result and cancellation_result:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
