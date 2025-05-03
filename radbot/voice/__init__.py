""" 
Voice module for bidirectional voice chat through Google ADK and Google Cloud TTS.

This module provides functionality for voice input and output using Google ADK
for Speech-to-Text and Google Cloud Text-to-Speech for TTS.
"""

import logging
import os
logger = logging.getLogger(__name__)

# Log Google Cloud TTS status
if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    logger.info("Google Cloud credentials found in environment variables")
else:
    logger.warning("Google Cloud credentials not found in environment variables - voice synthesis might be unavailable")

# Import the main components
from radbot.voice.google_cloud_tts_adapter import (
    GoogleCloudTTSAdapter,
    create_google_cloud_tts_client
)
from radbot.voice.adk_voice_handler import (
    ADKVoiceHandler,
    setup_voice_handler
)
from radbot.voice.voice_agent_factory import create_voice_enabled_agent
from radbot.voice.fastapi_extension import (
    add_voice_routes,
    create_voice_app,
    run_voice_app
)

# Export components for easy import
__all__ = [
    # Google Cloud TTS
    'GoogleCloudTTSAdapter',
    'create_google_cloud_tts_client',
    
    # ADK voice handler
    'ADKVoiceHandler',
    'setup_voice_handler',
    
    # Agent factory
    'create_voice_enabled_agent',
    
    # FastAPI extension
    'add_voice_routes',
    'create_voice_app',
    'run_voice_app',
]
