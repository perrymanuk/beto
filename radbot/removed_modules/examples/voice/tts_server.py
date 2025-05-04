#!/usr/bin/env python
"""
Simple server for text-to-speech conversion using ElevenLabs.

This server provides a simple API endpoint for converting text to speech
using ElevenLabs. It's designed to be used with the ADK web interface.
"""

import argparse
import base64
import json
import logging
import os
import sys
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("tts_server")

# Import radbot components
from radbot.voice.simple_elevenlabs import create_elevenlabs_client, text_to_speech

# Import fastapi
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(title="RadBot TTS Server")

# Add CORS middleware to allow cross-origin requests from the ADK web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your ADK web interface URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/api/voice/text-to-speech")
async def tts_endpoint(request: Request):
    """
    Convert text to speech using ElevenLabs.
    
    Args:
        request: FastAPI request
        
    Returns:
        dict: JSON response with speech data
    """
    # Parse request body
    try:
        body = await request.json()
        text = body.get("text")
        
        if not text:
            raise HTTPException(status_code=400, detail="Missing text parameter")
            
        logger.info(f"TTS request received: {text[:50]}...")
        
        # Convert text to speech
        audio_data = text_to_speech(text)
        
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to convert text to speech")
            
        # Encode audio data as base64
        encoded_audio = base64.b64encode(audio_data).decode("utf-8")
        
        # Return response
        return {
            "success": True,
            "audio": encoded_audio
        }
        
    except Exception as e:
        logger.error(f"Error processing TTS request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Run the TTS server."""
    parser = argparse.ArgumentParser(description="Run the TTS server")
    parser.add_argument("--host", default="localhost", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind the server to")
    args = parser.parse_args()
    
    # Test the ElevenLabs connection
    logger.info("Testing ElevenLabs connection")
    client = create_elevenlabs_client()
    
    if client and client.test_connection():
        logger.info("ElevenLabs connection successful")
    else:
        logger.warning("ElevenLabs connection failed. TTS will not be available.")
    
    # Run the server
    logger.info(f"Starting TTS server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
