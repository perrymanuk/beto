#!/usr/bin/env python3
"""Test script for Google Calendar OAuth flow."""

import os
import sys
import json
import logging
from typing import Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Run a test of the Google Calendar OAuth flow."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Testing Google Calendar OAuth flow...")
    
    # Check for required environment variables
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        logger.error("❌ Missing required environment variables: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
        logger.info("Please set these in your .env file or environment and try again")
        sys.exit(1)
    
    # Determine redirect URI and port from environment or use defaults
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000")
    port = int(os.environ.get("GOOGLE_OAUTH_PORT", "8000"))
    
    logger.info(f"Using redirect URI: {redirect_uri}")
    logger.info(f"Using OAuth server port: {port}")
    
    # Import necessary packages
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        logger.info("✅ Successfully imported required packages")
    except ImportError as e:
        logger.error(f"❌ Failed to import required packages: {e}")
        logger.info("Please install required packages with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        sys.exit(1)
    
    # Define scopes for Google Calendar API
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    
    # Create client config from environment variables
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [
                redirect_uri,
                "http://localhost:8000",
                "http://localhost",
                "http://localhost:8080",
                "urn:ietf:wg:oauth:2.0:oob"
            ]
        }
    }
    
    logger.info("Starting OAuth flow...")
    
    try:
        # Create flow instance
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        
        # Run the OAuth flow
        logger.info(f"Please authorize the application in your browser (port {port})...")
        creds = flow.run_local_server(port=port)
        
        # Check if we got valid credentials
        if creds and creds.valid:
            logger.info("✅ Successfully obtained valid credentials!")
            
            # Try to use the credentials to access the Calendar API
            service = build("calendar", "v3", credentials=creds)
            
            # List calendars to verify access
            logger.info("Testing API access by listing calendars...")
            calendars = service.calendarList().list().execute()
            
            logger.info(f"✅ Successfully accessed Google Calendar API! Found {len(calendars.get('items', []))} calendars:")
            
            # Print calendar names
            for calendar in calendars.get("items", []):
                logger.info(f"- {calendar.get('summary', 'Unnamed calendar')} ({calendar.get('id', 'No ID')})")
            
            # Save token to a temporary file for inspection
            token_info = json.loads(creds.to_json())
            temp_token_path = os.path.join(os.path.dirname(__file__), "temp_token.json")
            
            with open(temp_token_path, "w") as f:
                json.dump(token_info, f, indent=2)
            
            logger.info(f"Token information saved to: {temp_token_path}")
            logger.info("⚠️ This file contains sensitive information. Delete it when done!")
        else:
            logger.error("❌ Failed to obtain valid credentials")
    except Exception as e:
        logger.error(f"❌ Error during OAuth flow: {str(e)}")
        sys.exit(1)
    
    logger.info("OAuth flow test completed!")

if __name__ == "__main__":
    main()