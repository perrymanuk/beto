"""
Home Assistant client singleton module.

This module provides a shared Home Assistant client instance to avoid circular imports.
"""

import os
import logging
from typing import Optional

from radbot.tools.homeassistant.ha_rest_client import HomeAssistantRESTClient
from radbot.config.config_loader import config_loader

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
        
    # Get configuration from config.yaml
    ha_config = config_loader.get_home_assistant_config()
    
    # Get connection parameters from configuration or fall back to environment variables
    ha_url = ha_config.get("url")
    ha_token = ha_config.get("token")
    
    # Fall back to environment variables if not found in config
    if not ha_url:
        ha_url = os.getenv("HA_URL")
    if not ha_token:
        ha_token = os.getenv("HA_TOKEN")
    
    if not ha_url or not ha_token:
        logger.warning("Home Assistant URL or token not found in config.yaml or environment variables.")
        return None
        
    try:
        _ha_client = HomeAssistantRESTClient(ha_url, ha_token)
        
        # Test connection
        if not _ha_client.get_api_status():
            logger.error("Failed to connect to Home Assistant API.")
            _ha_client = None
        else:
            logger.info(f"Successfully connected to Home Assistant API at {ha_url}.")
        
        return _ha_client
    except Exception as e:
        logger.error(f"Error initializing Home Assistant client: {e}")
        _ha_client = None
        return None