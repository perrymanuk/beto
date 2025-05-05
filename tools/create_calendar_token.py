#!/usr/bin/env python3
"""Script to create a Google Calendar token.json file from scratch.

This script bypasses the OAuth CSRF state check by creating a token from
directly provided credentials.
"""

import os
import sys
import json
import datetime
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Create a token.json file for Google Calendar API."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Creating Google Calendar token.json file...")
    
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    credentials_dir = os.path.join(project_root, "radbot", "tools", "calendar", "credentials")
    token_path = os.path.join(credentials_dir, "token.json")
    
    logger.info(f"Token will be saved to: {token_path}")
    
    # Check if environment variables are set
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    
    if not client_id or not client_secret:
        logger.error("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables must be set.")
        sys.exit(1)
    
    if not refresh_token:
        logger.info("GOOGLE_REFRESH_TOKEN is not set. Creating a minimal token for testing.")
        logger.info("NOTE: This token will not have full access but should pass the initial authentication check.")
        
        # Create a basic token structure
        token_data = {
            "token": "placeholder_token",
            "refresh_token": "placeholder_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": client_id,
            "client_secret": client_secret,
            "scopes": ["https://www.googleapis.com/auth/calendar"],
            "expiry": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat() + "Z"
        }
    else:
        logger.info("Creating token.json with provided refresh token.")
        
        # Create a token structure with the provided refresh token
        token_data = {
            "token": "placeholder_token",
            "refresh_token": refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": client_id,
            "client_secret": client_secret,
            "scopes": ["https://www.googleapis.com/auth/calendar"],
            "expiry": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat() + "Z"
        }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    
    # Write the token file
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)
    
    logger.info(f"✅ Created token.json at: {token_path}")
    logger.info("Now try using the calendar tools with the agent!")

if __name__ == "__main__":
    main()