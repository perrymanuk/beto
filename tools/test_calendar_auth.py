#!/usr/bin/env python3
"""Test Google Calendar authentication."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from radbot.tools.calendar.calendar_auth import (
    DEFAULT_CREDENTIALS_PATH, 
    DEFAULT_TOKEN_PATH,
    get_calendar_service
)
from radbot.tools.calendar.calendar_manager import CalendarManager

def test_authentication():
    """Test Google Calendar authentication."""
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
    
    # Check for a credentials file
    print(f"\nChecking if credentials file exists at: {DEFAULT_CREDENTIALS_PATH}")
    has_credentials_file = os.path.exists(DEFAULT_CREDENTIALS_PATH)
    print(f"- Credentials file: {'FOUND' if has_credentials_file else 'NOT FOUND'}")
    
    has_auth_method = (client_id and client_secret) or has_credentials_file or calendar_service_account_file or calendar_service_account_json
    
    if not has_auth_method:
        # No authentication method available, provide instructions
        print("\n⚠️ No authentication method found!")
        
        # Check if the directory exists
        credentials_dir = os.path.dirname(DEFAULT_CREDENTIALS_PATH)
        print(f"\nChecking if credentials directory exists at: {credentials_dir}")
        if not os.path.exists(credentials_dir):
            print(f"Creating credentials directory at: {credentials_dir}")
            os.makedirs(credentials_dir, exist_ok=True)
            
        # Create an empty .gitignore file to prevent credentials from being committed
        gitignore_path = os.path.join(credentials_dir, ".gitignore")
        if not os.path.exists(gitignore_path):
            print(f"Creating .gitignore file at: {gitignore_path}")
            with open(gitignore_path, "w") as f:
                f.write("*\n!.gitignore\n")
        
        print("\nPlease follow these steps to set up Google Calendar authentication:")
        print("\nOption 1: OAuth 2.0 for Personal Accounts")
        print("1. Go to the Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Google Calendar API")
        print("4. Create OAuth 2.0 credentials (Desktop application type)")
        print("5. Download the credentials JSON file")
        print(f"6. Save it as: {DEFAULT_CREDENTIALS_PATH}")
        
        print("\nOption 2: Environment Variables for OAuth")
        print("Set the following environment variables in your .env file:")
        print("GOOGLE_CLIENT_ID=your_client_id")
        print("GOOGLE_CLIENT_SECRET=your_client_secret")
        
        print("\nOption 3: Service Account for Workspace")
        print("GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE=/path/to/service-account-key.json")
        print("OR")
        print("GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON='{ your service account JSON as a string }'")
        
        print("\nThen run this script again.")
        return
    
    # Create a calendar manager
    print("\nCreating CalendarManager instance...")
    manager = CalendarManager()
    
    # Authenticate with personal Google account
    print("\nAuthenticating with personal Google account...")
    personal_auth_success = manager.authenticate_personal()
    
    if personal_auth_success:
        print("\nAuthentication successful!")
        
        # Test listing upcoming events
        print("\nFetching upcoming events...")
        upcoming_events = manager.list_upcoming_events(max_results=5)
        
        if isinstance(upcoming_events, list):
            if upcoming_events:
                print(f"\nFound {len(upcoming_events)} upcoming events:")
                for event in upcoming_events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    print(f"- {start}: {event.get('summary', 'No title')}")
            else:
                print("\nNo upcoming events found")
        else:
            print(f"\nError fetching events: {upcoming_events.get('error')}")
    else:
        print("\nAuthentication failed. Please check your credentials.")
        
        # Try direct authentication
        try:
            print("\nTrying direct authentication with get_calendar_service()...")
            service = get_calendar_service()
            print("\nDirect authentication successful!")
            
            # Test listing upcoming events
            print("\nFetching upcoming events directly...")
            events_result = service.events().list(
                calendarId='primary',
                timeMin='2025-05-01T00:00:00Z',
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            if events:
                print(f"\nFound {len(events)} upcoming events:")
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    print(f"- {start}: {event.get('summary', 'No title')}")
            else:
                print("\nNo upcoming events found")
        except Exception as e:
            print(f"\nDirect authentication failed: {e}")
            print("\nPlease check your credentials and try again.")
    
    # Test wrapper functions with graceful error handling
    print("\n\nTesting calendar tool wrapper functions...")
    
    # Import the wrapper functions
    from radbot.tools.calendar.calendar_tools import (
        list_calendar_events_wrapper,
        create_calendar_event_wrapper,
        update_calendar_event_wrapper,
        delete_calendar_event_wrapper,
        check_calendar_availability_wrapper
    )
    
    # Test list_calendar_events_wrapper
    print("\nTesting list_calendar_events_wrapper:")
    events_result = list_calendar_events_wrapper(max_results=3)
    if isinstance(events_result, list):
        print(f"Success! Found {len(events_result)} events")
    else:
        print(f"Expected error: {events_result.get('error')}")
    
    # Test create_calendar_event_wrapper
    print("\nTesting create_calendar_event_wrapper:")
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

if __name__ == "__main__":
    test_authentication()