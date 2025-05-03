"""
Simple ElevenLabs client for text-to-speech conversion.

This module provides a simple client for converting text to speech using
ElevenLabs' REST API, designed to work with the ADK web interface.
"""

import asyncio
import base64
import logging
import os
import requests
import json
from typing import Optional, Dict, List, Any, AsyncGenerator, Union

# Set up logging
logger = logging.getLogger(__name__)

class SimpleElevenLabsClient:
    """
    Simple client for ElevenLabs text-to-speech API.
    
    This client is designed to be simple and reliable, using the
    REST API rather than WebSockets for better compatibility.
    """
    
    def __init__(
        self, 
        api_key: str, 
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        model_id: str = "eleven_flash_v2_5"
    ):
        """
        Initialize the ElevenLabs client.
        
        Args:
            api_key: ElevenLabs API key
            voice_id: Voice ID to use (default: "21m00Tcm4TlvDq8ikWAM")
            model_id: Model ID to use (default: "eleven_flash_v2_5")
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def text_to_speech(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs API.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Optional[bytes]: Audio data or None if conversion failed
        """
        if not text.strip():
            return None
            
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error in ElevenLabs API request: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test the connection to ElevenLabs API.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Get list of voices as a simple API test
            response = requests.get(
                f"{self.base_url}/voices",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing ElevenLabs connection: {e}")
            return False

def create_elevenlabs_client() -> Optional[SimpleElevenLabsClient]:
    """
    Create an ElevenLabs client from environment variables.
    
    Returns:
        Optional[SimpleElevenLabsClient]: ElevenLabs client or None if API key is missing
    """
    api_key = os.environ.get("ELEVEN_LABS_API_KEY")
    if not api_key:
        logger.warning("ELEVEN_LABS_API_KEY not found in environment variables")
        return None
        
    voice_id = os.environ.get("ELEVEN_LABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    model_id = os.environ.get("ELEVEN_LABS_MODEL", "eleven_flash_v2_5")
    
    return SimpleElevenLabsClient(api_key, voice_id, model_id)

def test_elevenlabs_connection() -> bool:
    """
    Test the connection to ElevenLabs API.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    client = create_elevenlabs_client()
    if not client:
        return False
        
    return client.test_connection()

def text_to_speech(text: str) -> Optional[bytes]:
    """
    Convert text to speech using ElevenLabs API.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Optional[bytes]: Audio data or None if conversion failed
    """
    client = create_elevenlabs_client()
    if not client:
        return None
        
    return client.text_to_speech(text)
