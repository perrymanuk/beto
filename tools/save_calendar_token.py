#!/usr/bin/env python3
"""Script to authenticate with Google Calendar and save token.json to the correct location."""

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
    """Authenticate with Google Calendar and save token to the correct location."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting Google Calendar authentication process...")
    
    # Import the necessary modules
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
    
    # Check if credentials.json exists
    if not os.path.exists(credentials_path):
        logger.error(f"❌ Credentials file not found at {credentials_path}")
        # Check for environment variables
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        
        if client_id and client_secret:
            logger.info("Using environment variables for credentials...")
            # Create a credentials.json file from environment variables
            credentials_data = {
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
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(credentials_path), exist_ok=True)
            
            with open(credentials_path, "w") as f:
                json.dump(credentials_data, f)
            
            logger.info(f"Created credentials.json from environment variables")
        else:
            logger.error("No credentials found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET or provide a credentials.json file.")
            sys.exit(1)
    
    # Define scopes for Google Calendar API
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    
    # Check for existing token
    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            logger.info("Found existing token.json")
        except Exception as e:
            logger.error(f"Error loading existing token: {e}")
            creds = None
    
    # If no valid credentials, run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Refreshed expired token")
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                creds = None
        
        # If still no valid credentials, run OAuth flow
        if not creds:
            try:
                # Get the port from environment or use default
                port = int(os.environ.get("GOOGLE_OAUTH_PORT", "8000"))
                
                # Create the flow with a more direct approach
                client_id = os.environ.get("GOOGLE_CLIENT_ID")
                client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
                
                if client_id and client_secret:
                    # Use environment variables directly for flow creation
                    flow = InstalledAppFlow.from_client_config(
                        {
                            "installed": {
                                "client_id": client_id,
                                "client_secret": client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                                "redirect_uris": [f"http://localhost:{port}"]
                            }
                        },
                        SCOPES
                    )
                else:
                    # Fall back to file
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES
                    )
                
                logger.info(f"Starting OAuth flow with redirect to port {port}...")
                logger.info("Please authorize the application in your browser...")
                
                # Run with no browser open (forces a clean state)
                creds = flow.run_local_server(port=port, open_browser=False)
                
                logger.info("OAuth flow completed successfully!")
            except Exception as e:
                logger.error(f"Error during OAuth flow: {e}")
                sys.exit(1)
    
    # Save the credentials for future runs
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "w") as f:
        f.write(creds.to_json())
    
    logger.info(f"✅ Successfully saved token to: {token_path}")
    
    # Test the credentials
    try:
        from googleapiclient.discovery import build
        
        logger.info("Testing credentials by connecting to Google Calendar...")
        service = build("calendar", "v3", credentials=creds)
        
        # Try to get primary calendar to verify authentication
        primary_calendar = service.calendars().get(calendarId='primary').execute()
        logger.info(f"✅ Successfully authenticated with Google Calendar as: {primary_calendar.get('summary', 'Unknown')}")
        
        # List a few upcoming events to verify API access
        now = "2025-05-05T00:00:00Z"  # Use a fixed date for testing
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
        
    except Exception as e:
        logger.error(f"Error testing Google Calendar API: {e}")
        logger.error("Authentication succeeded but API access failed.")
        sys.exit(1)
    
    logger.info("All done! Your calendar integration should now work with the agent.")

if __name__ == "__main__":
    main()