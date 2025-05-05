#!/usr/bin/env python3
"""Fix Google Calendar token.json file using a valid refresh token."""

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
    """Fix the token.json file with a valid refresh token."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Fixing Google Calendar token.json file...")
    
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    credentials_dir = os.path.join(project_root, "radbot", "tools", "calendar", "credentials")
    token_path = os.path.join(credentials_dir, "token.json")
    
    logger.info(f"Token will be saved to: {token_path}")
    
    # Check for environment variables
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    
    if not client_id or not client_secret:
        logger.error("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables must be set.")
        sys.exit(1)
    
    if not refresh_token:
        logger.info("GOOGLE_REFRESH_TOKEN environment variable is not set.")
        logger.info("Please obtain a valid refresh token manually by following these steps:")
        logger.info("1. Go to https://developers.google.com/oauthplayground/")
        logger.info("2. In the right panel, click the gear icon (OAuth 2.0 Configuration)")
        logger.info("3. Check 'Use your own OAuth credentials'")
        logger.info(f"4. Enter your Client ID: {client_id}")
        logger.info(f"5. Enter your Client Secret: {client_secret}")
        logger.info("6. Close the configuration")
        logger.info("7. In the left panel, find 'Google Calendar API v3'")
        logger.info("8. Select the scopes: https://www.googleapis.com/auth/calendar")
        logger.info("9. Click 'Authorize APIs'")
        logger.info("10. Complete the authorization")
        logger.info("11. In Step 2, click 'Exchange authorization code for tokens'")
        logger.info("12. Copy the refresh token from the response")
        logger.info("13. Set the GOOGLE_REFRESH_TOKEN environment variable and run this script again")
        sys.exit(1)
    
    # Create a token structure with the provided refresh token
    token_data = {
        "token": "ya29.placeholder", # This will be refreshed
        "refresh_token": refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": ["https://www.googleapis.com/auth/calendar"],
        "expiry": "2025-05-05T12:00:00.000000Z" # Expired, so it will be refreshed
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    
    # Write the token file
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)
    
    logger.info(f"✅ Created token.json with valid refresh token at: {token_path}")
    logger.info("Now try using the calendar tools with the agent!")
    
    # Try refreshing the token to verify it works
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        
        # Load the saved credentials
        creds = Credentials.from_authorized_user_file(token_path)
        
        # Force refresh
        if creds.expired:
            logger.info("Refreshing token...")
            creds.refresh(Request())
            
            # Save updated credentials
            with open(token_path, "w") as f:
                f.write(creds.to_json())
            
            logger.info("✅ Successfully refreshed token!")
        else:
            logger.info("Token is still valid, no need to refresh.")
        
        # Verify with API call
        from googleapiclient.discovery import build
        
        logger.info("Testing credentials with Google Calendar API...")
        service = build("calendar", "v3", credentials=creds)
        
        # Try to get primary calendar
        primary_calendar = service.calendars().get(calendarId='primary').execute()
        logger.info(f"✅ Successfully authenticated with Google Calendar as: {primary_calendar.get('summary', 'Unknown')}")
        
        logger.info("Your calendar integration should now work correctly!")
    except Exception as e:
        logger.error(f"Error testing refresh token: {e}")
        logger.error("The refresh token might not be valid. Please get a new refresh token and try again.")

if __name__ == "__main__":
    main()