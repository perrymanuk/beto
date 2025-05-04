"""
Home Assistant client singleton module.

This module provides a shared Home Assistant client instance to avoid circular imports.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

from radbot.tools.homeassistant.ha_rest_client import HomeAssistantRESTClient

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Singleton client instance
_ha_client = None

def get_ha_client() -> Optional[HomeAssistantRESTClient]:
    """
    Get or initialize the Home Assistant client.
    
    Returns:
        The Home Assistant client instance, or None if configuration is invalid.
    """
    global _ha_client
    
    if _ha_client is not None:
        return _ha_client
        
    # Get configuration from environment variables
    ha_url = os.getenv("HA_URL")
    ha_token = os.getenv("HA_TOKEN")
    
    if not ha_url or not ha_token:
        logger.warning("HA_URL or HA_TOKEN environment variables not set.")
        return None
        
    try:
        _ha_client = HomeAssistantRESTClient(ha_url, ha_token)
        
        # Test connection
        if not _ha_client.get_api_status():
            logger.error("Failed to connect to Home Assistant API.")
            _ha_client = None
        else:
            logger.info("Successfully connected to Home Assistant API.")
        
        return _ha_client
    except Exception as e:
        logger.error(f"Error initializing Home Assistant client: {e}")
        _ha_client = None
        return None