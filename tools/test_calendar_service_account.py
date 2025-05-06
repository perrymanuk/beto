#!/usr/bin/env python3
"""Test script to add a calendar event using service account auth."""

import os
import logging
import argparse
from datetime import datetime, timedelta

from radbot.tools.calendar.calendar_auth import get_calendar_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def create_test_event(calendar_id="primary", summary="Test Event", location=None, description=None, hours_from_now=1):
    """Create a test event to verify calendar write access."""
    try:
        # Get authenticated calendar service
        service = get_calendar_service(force_new=True)
        
        # Calculate event start and end times
        start_time = datetime.utcnow() + timedelta(hours=hours_from_now)
        end_time = start_time + timedelta(hours=1)
        
        # Format times for API
        start_str = start_time.isoformat() + 'Z'
        end_str = end_time.isoformat() + 'Z'
        
        # Create event body
        event = {
            'summary': summary,
            'location': location,
            'description': description or f"Test event created at {datetime.utcnow().isoformat()}",
            'start': {
                'dateTime': start_str,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_str,
                'timeZone': 'UTC',
            },
            'colorId': '7',  # A pleasant blue
            'transparency': 'transparent',  # Show as available
        }
        
        # Create the event
        logger.info(f"Creating test event '{summary}' in calendar {calendar_id}")
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='none'  # Don't send emails
        ).execute()
        
        logger.info(f"✅ Event created successfully!")
        logger.info(f"ID: {created_event['id']}")
        logger.info(f"Summary: {created_event['summary']}")
        logger.info(f"Start: {created_event['start']['dateTime']}")
        logger.info(f"HTML Link: {created_event.get('htmlLink', 'No link available')}")
        
        return created_event
        
    except Exception as e:
        logger.error(f"Error creating test event: {str(e)}")
        return None

def main():
    """Run the test script."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Test Google Calendar service account by creating an event")
    parser.add_argument(
        "--service-account-path", 
        type=str, 
        help="Path to service account JSON file (defaults to GOOGLE_CREDENTIALS_PATH env var)"
    )
    parser.add_argument(
        "--calendar-id",
        type=str,
        default="primary",
        help="Calendar ID to use (default: primary)"
    )
    parser.add_argument(
        "--summary",
        type=str,
        default="RadBot Test Event",
        help="Event summary/title"
    )
    parser.add_argument(
        "--location",
        type=str,
        help="Event location"
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Event description"
    )
    parser.add_argument(
        "--hours-from-now",
        type=int,
        default=1,
        help="Hours from now to schedule the event (default: 1)"
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
    
    # Create test event
    event = create_test_event(
        calendar_id=args.calendar_id,
        summary=args.summary,
        location=args.location,
        description=args.description,
        hours_from_now=args.hours_from_now
    )
    
    return event is not None

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)