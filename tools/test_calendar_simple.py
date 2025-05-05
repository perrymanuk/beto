#!/usr/bin/env python3
"""Simplified test for Google Calendar functionality."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from radbot.tools.calendar.calendar_tools import (
    list_calendar_events_wrapper,
    create_calendar_event_wrapper,
    update_calendar_event_wrapper,
    delete_calendar_event_wrapper,
    check_calendar_availability_wrapper,
    get_calendar_manager,
)

def test_calendar_simple():
    """Test calendar functionality directly."""
    # Check environment variables first
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    calendar_service_account_file = os.environ.get("GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE")
    calendar_service_account_json = os.environ.get("GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON")
    
    # Print found environment variables
    print("Checking for Google Calendar environment variables:")
    print(f"- GOOGLE_CLIENT_ID: {'FOUND' if client_id else 'NOT FOUND'}")
    print(f"- GOOGLE_CLIENT_SECRET: {'FOUND' if client_secret else 'NOT FOUND'}")
    print(f"- GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE: {'FOUND' if calendar_service_account_file else 'NOT FOUND'}")
    print(f"- GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON: {'FOUND' if calendar_service_account_json else 'NOT FOUND'}")
    
    # Get calendar manager and check authentication status
    print("\nGetting calendar manager...")
    manager = get_calendar_manager()
    
    # Test wrapper functions with graceful error handling
    print("\nTesting calendar tool wrapper functions...")
    
    # Test list_calendar_events_wrapper
    print("\nTesting list_calendar_events_wrapper:")
    events_result = list_calendar_events_wrapper(max_results=3)
    if isinstance(events_result, list):
        print(f"Success! Found {len(events_result)} events")
        for event in events_result:
            start = event['start'].get('dateTime', event['start'].get('date', 'Unknown'))
            print(f"- {start}: {event.get('summary', 'No title')}")
    else:
        print(f"Expected error: {events_result.get('error')}")
    
    # Test create_calendar_event_wrapper with invalid time format (should be caught by error handling)
    print("\nTesting create_calendar_event_wrapper with invalid date format:")
    invalid_create_result = create_calendar_event_wrapper(
        summary="Test Event", 
        start_time="invalid-date", 
        end_time="also-invalid", 
        description="Test event with invalid dates"
    )
    if "error" in invalid_create_result:
        print(f"Expected error: {invalid_create_result.get('error')}")
    else:
        print(f"Unexpected success with invalid dates: {invalid_create_result}")
    
    # Test create_calendar_event_wrapper with valid data
    print("\nTesting create_calendar_event_wrapper with valid data:")
    create_result = create_calendar_event_wrapper(
        summary="Test Event", 
        start_time="2025-06-01T10:00:00", 
        end_time="2025-06-01T11:00:00",
        description="Test event from radbot"
    )
    if "error" in create_result:
        print(f"Expected error: {create_result.get('error')}")
    else:
        print(f"Success! Created event: {create_result.get('id')}")
        
        # Test update_calendar_event_wrapper if we have an event ID
        event_id = create_result.get('id')
        if event_id:
            print("\nTesting update_calendar_event_wrapper:")
            update_result = update_calendar_event_wrapper(
                event_id=event_id,
                summary="Updated Test Event",
                description="Updated test event from radbot"
            )
            if "error" in update_result:
                print(f"Expected error: {update_result.get('error')}")
            else:
                print(f"Success! Updated event: {update_result.get('id')}")
            
            # Test delete_calendar_event_wrapper
            print("\nTesting delete_calendar_event_wrapper:")
            delete_result = delete_calendar_event_wrapper(event_id=event_id)
            if "error" in delete_result:
                print(f"Expected error: {delete_result.get('error')}")
            else:
                print(f"Success! {delete_result.get('message', 'Event deleted')}")
    
    # Test check_calendar_availability_wrapper
    print("\nTesting check_calendar_availability_wrapper:")
    availability_result = check_calendar_availability_wrapper(calendar_ids=["primary"])
    if "error" in availability_result:
        print(f"Expected error: {availability_result.get('error')}")
    else:
        print(f"Success! Retrieved availability for {len(availability_result.get('calendars', {}))} calendars")
        
    # Test with non-existent event ID
    print("\nTesting delete_calendar_event_wrapper with non-existent event:")
    bad_delete_result = delete_calendar_event_wrapper(event_id="nonexistentID12345")
    if "error" in bad_delete_result:
        print(f"Expected error: {bad_delete_result.get('error')}")
    else:
        print(f"Unexpected success: {bad_delete_result}")

if __name__ == "__main__":
    test_calendar_simple()