#!/usr/bin/env python3
"""Validate Google Calendar service account access."""

import os
import logging
import argparse
from datetime import datetime

from radbot.tools.calendar.calendar_auth import validate_calendar_access, get_calendar_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Validate the Google Calendar service account configuration."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Validate Google Calendar service account")
    parser.add_argument(
        "--service-account-path", 
        type=str, 
        help="Path to service account JSON file (defaults to GOOGLE_CREDENTIALS_PATH env var)"
    )
    parser.add_argument(
        "--calendar-id",
        type=str,
        default="primary",
        help="Calendar ID to validate access to (default: primary)"
    )
    args = parser.parse_args()

    # Get service account path from args or environment
    service_account_path = args.service_account_path or os.environ.get('GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE')
    
    if not service_account_path:
        logger.error("No service account path provided. Please set GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE environment variable or use --service-account-path")
        return False
    
    if not os.path.exists(service_account_path):
        logger.error(f"Service account file not found at: {service_account_path}")
        return False
    
    logger.info(f"Using service account file: {service_account_path}")
    
    # Set the environment variable for the auth module
    os.environ['GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE'] = service_account_path
    
    # Validate calendar access
    logger.info(f"Validating access to calendar: {args.calendar_id}")
    access_valid = validate_calendar_access(args.calendar_id)
    
    if access_valid:
        logger.info("✅ Calendar access validation successful!")
        
        # Try to list events as an additional test
        try:
            service = get_calendar_service()
            now = datetime.utcnow().isoformat() + 'Z'
            
            logger.info("Testing event listing...")
            events_result = service.events().list(
                calendarId=args.calendar_id,
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                logger.info("No upcoming events found.")
            else:
                logger.info(f"Upcoming events ({len(events)}):")
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    logger.info(f"  {start} - {event['summary']}")
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            return False
        
        return True
    else:
        logger.error("❌ Calendar access validation failed!")
        logger.error("Please check permissions and service account configuration")
        
        logger.info("\n=== TROUBLESHOOTING TIPS ===")
        logger.info("1. Ensure the service account file is valid and contains the correct credentials")
        logger.info("2. Make sure the calendar has been shared with the service account email")
        logger.info("3. Verify the calendar ID is correct")
        logger.info("4. If using domain-wide delegation, ensure proper setup in Google Workspace Admin Console")
        logger.info("5. Check scopes in the service account configuration")
        
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)