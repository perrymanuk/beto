#!/usr/bin/env python3
"""
Standalone script to authenticate with Google Calendar API and save valid token.json.

This script avoids CSRF state validation issues by using a command-line OAuth flow
instead of a local server.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Authenticate with Google Calendar and save a valid token.json file."""
    # Load environment variables
    load_dotenv()
    
    # Check for required dependencies
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        logger.info("✅ Successfully imported Google Auth modules")
    except ImportError as e:
        logger.error(f"❌ Failed to import Google Auth modules: {e}")
        sys.exit(1)
    
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    credentials_dir = os.path.join(project_root, "radbot", "tools", "calendar", "credentials")
    credentials_path = os.path.join(credentials_dir, "credentials.json")
    token_path = os.path.join(credentials_dir, "token.json")
    
    logger.info(f"Using credentials path: {credentials_path}")
    logger.info(f"Token will be saved to: {token_path}")
    
    # Get client credentials
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        if not os.path.exists(credentials_path):
            logger.error("No client credentials found. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET or provide credentials.json")
            sys.exit(1)
        credentials_source = f"file: {credentials_path}"
    else:
        credentials_source = "environment variables"
    
    logger.info(f"Using credentials from {credentials_source}")
    
    # Define scopes
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    
    try:
        # Create flow - use command-line auth instead of local server
        if client_id and client_secret:
            # Use environment variables
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
                    }
                },
                SCOPES
            )
        else:
            # Use credentials file
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES, redirect_uri="urn:ietf:wg:oauth:2.0:oob"
            )
        
        # Run the console-based authentication flow (using CLI flow)
        logger.info("Starting OAuth flow with console-based authentication...")
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        print('\nPlease go to this URL and authorize the application:')
        print(auth_url)
        print('\nAfter authorizing, you will get a code. Enter that code here:')
        code = input('Code: ').strip()
        
        # Exchange the authorization code for credentials
        flow.fetch_token(code=code)
        
        # Get the credentials from the flow
        creds = flow.credentials
        
        logger.info("Authentication successful!")
        
        # Save the credentials for future runs
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        
        logger.info(f"Token saved to {token_path}")
        
        # Test the credentials
        try:
            from googleapiclient.discovery import build
            
            logger.info("Testing credentials by connecting to Google Calendar...")
            service = build("calendar", "v3", credentials=creds)
            
            # Try to get primary calendar to verify authentication
            primary_calendar = service.calendars().get(calendarId='primary').execute()
            logger.info(f"✅ Successfully authenticated with Google Calendar as: {primary_calendar.get('summary', 'Unknown')}")
            
            # List a few upcoming events as a test
            logger.info("Listing a few upcoming events as a test...")
            now = "2025-05-05T00:00:00Z"  # Use a fixed date
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                logger.info("No upcoming events found.")
            else:
                logger.info("Upcoming events:")
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    logger.info(f"  - {start} {event['summary']}")
                    
            logger.info("\nYour Google Calendar integration should now work correctly!")
            logger.info("Make sure to restart your radbot agent to pick up the new token.")
            
        except Exception as e:
            logger.error(f"Error testing credentials: {e}")
    
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()