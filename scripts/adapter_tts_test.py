#!/usr/bin/env python3
"""
Test script for our TTS adapter.

This script tests our TTS adapter implementation without using the ADK web interface.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("adapter_tts_test")

async def test_tts_adapter():
    """Test our TTS adapter implementation."""
    # Check for credentials
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    try:
        # Import our adapter
        from radbot.voice.google_cloud_tts_adapter import (
            GoogleCloudTTSAdapter, 
            create_google_cloud_tts_client
        )
        
        # First test client creation
        client = create_google_cloud_tts_client()
        if not client:
            logger.error("Failed to create Google Cloud TTS client")
            return 1
        
        logger.info(f"Successfully created Google Cloud TTS client: {type(client).__name__}")
        
        # Check for streaming_synthesize method
        has_streaming = hasattr(client, 'streaming_synthesize')
        logger.info(f"Client has streaming_synthesize method: {has_streaming}")
        
        # Create the adapter
        file_chunks = []
        
        async def save_audio_chunk(chunk):
            """Save audio chunk to our list and log."""
            file_chunks.append(chunk)
            logger.info(f"Received audio chunk: {len(chunk)} bytes")
        
        adapter = GoogleCloudTTSAdapter(send_audio_callback=save_audio_chunk)
        
        if not adapter.client:
            logger.error("Failed to initialize TTS adapter client")
            return 1
        
        logger.info("Successfully created GoogleCloudTTSAdapter")
        
        # Start the adapter
        adapter.start()
        logger.info("Started TTS adapter")
        
        try:
            # Process some text
            test_text = "Hello! This is a test of the Google Cloud Text-to-Speech adapter."
            logger.info(f"Processing text: {test_text}")
            
            # Send text to the adapter
            await adapter.process_text(test_text)
            
            # Wait for processing to complete
            timeout_seconds = 10
            start_time = asyncio.get_event_loop().time()
            
            while not adapter.text_queue.empty():
                if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                    logger.warning(f"Timed out after {timeout_seconds} seconds")
                    break
                logger.info("Waiting for text queue to be processed...")
                await asyncio.sleep(1)
            
            # Give a bit more time for audio processing
            await asyncio.sleep(2)
            
            # Check if we received any audio
            if file_chunks:
                logger.info(f"Test successful! Received {len(file_chunks)} chunks totaling {sum(len(c) for c in file_chunks)} bytes")
                
                # Save to file for verification
                output_file = "adapter_test_output.wav"
                with open(output_file, "wb") as f:
                    for chunk in file_chunks:
                        f.write(chunk)
                logger.info(f"Saved audio to {output_file}")
            else:
                logger.warning("No audio chunks received")
            
        finally:
            # Stop the adapter
            adapter.stop()
            logger.info("Stopped TTS adapter")
        
        return 0
    except Exception as e:
        logger.error(f"Error testing TTS adapter: {e}")
        import traceback
        traceback.print_exc()
        return 1

async def main():
    """Run the test."""
    try:
        return await test_tts_adapter()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
