#!/usr/bin/env python3
"""Test script for verifying the Google Calendar integration fix."""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Run tests to verify the calendar integration is working."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Testing Google Calendar authentication fix")
    
    # Import the calendar manager
    try:
        from radbot.tools.calendar.calendar_manager import CalendarManager
        logger.info("✅ Successfully imported CalendarManager")
    except ImportError as e:
        logger.error(f"❌ Failed to import CalendarManager: {e}")
        sys.exit(1)
    
    # Test get_credentials_from_env import
    try:
        from radbot.tools.calendar.calendar_auth import get_credentials_from_env
        logger.info("✅ Successfully imported get_credentials_from_env")
        
        # Test the function
        creds = get_credentials_from_env()
        logger.info(f"Credentials retrieved from environment: {list(creds.keys())}")
    except ImportError as e:
        logger.error(f"❌ Failed to import get_credentials_from_env: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error retrieving credentials: {e}")
        sys.exit(1)
    
    # Test calendar manager authentication
    try:
        # Create a calendar manager
        manager = CalendarManager()
        logger.info("✅ Successfully created CalendarManager instance")
        
        # Test authentication
        logger.info("Attempting to authenticate with personal Google account...")
        auth_success = manager.authenticate_personal()
        
        if auth_success:
            logger.info("✅ Authentication successful!")
            
            # Try to retrieve calendar information
            logger.info("Testing calendar access by retrieving events...")
            events = manager.list_upcoming_events(max_results=1)
            
            if isinstance(events, list):
                logger.info(f"✅ Successfully retrieved calendar events! Found {len(events)} events.")
                
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    logger.info(f"Sample event: {start}: {event.get('summary', 'No title')}")
            else:
                logger.warning(f"⚠️ Retrieved events but got non-list response: {events}")
        else:
            logger.warning("⚠️ Authentication not successful, but no exception was raised.")
            logger.info("This might be expected if credentials are not set up.")
    except Exception as e:
        logger.error(f"❌ Error testing calendar manager: {e}")
        sys.exit(1)
    
    logger.info("Calendar integration tests completed!")

if __name__ == "__main__":
    main()