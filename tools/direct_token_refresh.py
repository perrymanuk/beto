#!/usr/bin/env python3
"""Directly refresh Google Calendar token using client credentials."""

import os
import sys
import json
import logging
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Create a new token using client credentials."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Creating new Google Calendar token using client credentials...")
    
    # Check for required environment variables
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        logger.error("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables must be set.")
        sys.exit(1)
    
    # Define paths
    token_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "radbot", "tools", "calendar", "credentials", "token.json"
    )
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    
    logger.info(f"Token will be saved to: {token_path}")
    
    # Define scope for Google Calendar API
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
                "http://localhost:8000",
                "http://localhost",
                "http://localhost:8080",
                "urn:ietf:wg:oauth:2.0:oob"
            ]
        }
    }
    
    try:
        # Create flow instance with the "out of band" option
        flow = InstalledAppFlow.from_client_config(
            client_config, 
            SCOPES,
            redirect_uri="urn:ietf:wg:oauth:2.0:oob"  # This is the key - using OOB instead of local server
        )
        
        # Get the authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        logger.info(f"Please go to this URL to authorize the application:")
        logger.info(auth_url)
        
        # Get the authorization code from the user
        auth_code = input("Enter the authorization code: ")
        
        # Exchange the authorization code for tokens
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        
        # Save the credentials
        with open(token_path, "w") as token_file:
            token_json = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
                "expiry": creds.expiry.isoformat() if creds.expiry else None
            }
            json.dump(token_json, token_file, indent=2)
        
        logger.info(f"✅ Successfully created new token at {token_path}")
        
        # Test the credentials
        service = build("calendar", "v3", credentials=creds)
        calendar = service.calendars().get(calendarId='primary').execute()
        logger.info(f"✅ Successfully authenticated with Google Calendar as: {calendar.get('summary', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"Error creating token: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()