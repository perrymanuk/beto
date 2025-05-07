# Google Calendar Integration

This document provides a comprehensive guide to the Google Calendar integration in the radbot project, including setup, authentication methods, implementation details, and usage examples.

## Overview

Google Calendar integration allows radbot to interact with calendars across both personal and enterprise environments, providing capabilities to:

- View upcoming calendar events
- Create, update, and delete events
- Check calendar availability
- Handle both personal accounts (via OAuth) and Google Workspace accounts (via service accounts)

The integration is designed to handle organizational constraints and security requirements while providing a seamless experience across different types of Google accounts.

## Project Structure

```
radbot/
└── tools/
    └── calendar/
        ├── __init__.py
        ├── calendar_auth.py            # Authentication handlers for Google Calendar
        ├── calendar_manager.py         # Main calendar management class
        ├── calendar_operations.py      # Core calendar operation functions
        ├── calendar_tools.py           # Google ADK function tools interfaces
        └── credentials/                # Directory for storing credential files
            └── .gitignore              # Ensure no credentials are committed
```

## Dependencies

Required libraries:
- `google-api-python-client`: Primary interface to Google APIs
- `google-auth-httplib2`: HTTP client for authentication 
- `google-auth-oauthlib`: OAuth 2.0 library for Google

Note: `gcsa` (Google Calendar Simple API) was considered but removed due to dependency conflicts with ADK 0.4.0 (specifically with `tzlocal` versions).

## Authentication Methods

### OAuth2 for Personal Accounts

For personal Google accounts, radbot uses an OAuth2 flow:

```python
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define scopes - use specific scopes for least privilege
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():
    """Authenticate and return a Google Calendar service object."""
    creds = None
    
    # Check for existing token
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future runs
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    # Build and return the service
    service = build("calendar", "v3", credentials=creds)
    return service
```

### Service Accounts for Google Workspace

For Google Workspace environments with restricted sharing:

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_workspace_calendar_service(user_email):
    """Get calendar service using domain-wide delegation."""
    # Service account credentials JSON should be secured
    SERVICE_ACCOUNT_FILE = 'service-account.json'
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # Delegate to impersonate a Workspace user
    delegated_credentials = credentials.with_subject(user_email)
    service = build('calendar', 'v3', credentials=delegated_credentials)
    
    return service
```

**Administrator setup required:** A Google Workspace administrator must configure domain-wide delegation for your service account in the Admin Console and authorize the appropriate scopes.

## Required API Scopes

Choose the most limited scope that fulfills your requirements:

| Operation | Minimum Required Scope |
|-----------|------------------------|
| Viewing events | `https://www.googleapis.com/auth/calendar.readonly` |
| Creating/modifying events | `https://www.googleapis.com/auth/calendar` |
| Free/busy info only | `https://www.googleapis.com/auth/calendar.freebusy` |

For radbot's basic viewing/creating/modifying requirements, we use `https://www.googleapis.com/auth/calendar`.

## Core Calendar Operations

### Listing Events

```python
def list_events(service, calendar_id='primary', max_results=10, query=None):
    """List calendar events with optional filtering."""
    # Get current time in ISO format
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    
    # Build request parameters
    params = {
        'calendarId': calendar_id,
        'timeMin': now,
        'maxResults': max_results,
        'singleEvents': True,
        'orderBy': 'startTime'
    }
    
    # Add query if specified (free text search)
    if query:
        params['q'] = query
    
    try:
        events_result = service.events().list(**params).execute()
        events = events_result.get('items', [])
        return events
    except HttpError as error:
        print(f"Error fetching events: {error}")
        return []
```

### Creating Events

```python
def create_event(service, summary, start_time, end_time, 
                description=None, location=None, attendees=None, 
                calendar_id='primary'):
    """Create a calendar event."""
    # Format start and end times
    start = format_time(start_time)
    end = format_time(end_time)
    
    # Build event body
    event_body = {
        'summary': summary,
        'start': start,
        'end': end,
    }
    
    # Add optional fields if provided
    if description:
        event_body['description'] = description
    if location:
        event_body['location'] = location
    if attendees:
        event_body['attendees'] = [{'email': email} for email in attendees]
    
    try:
        event = service.events().insert(
            calendarId=calendar_id, 
            body=event_body,
            sendUpdates='all'  # Notify attendees
        ).execute()
        return event
    except HttpError as error:
        print(f"Error creating event: {error}")
        return None

def format_time(time_value, timezone='UTC'):
    """Format datetime or date for Google Calendar API."""
    if isinstance(time_value, datetime.datetime):
        return {'dateTime': time_value.isoformat(), 'timeZone': timezone}
    else:  # Assume it's a date
        return {'date': time_value.isoformat()}
```

### Updating Events

```python
def update_event(service, event_id, calendar_id='primary', **kwargs):
    """Update an existing calendar event with provided fields."""
    try:
        # First retrieve the event
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        
        # Update fields that were provided
        for key, value in kwargs.items():
            if key in ['start', 'end']:
                event[key] = format_time(value)
            else:
                event[key] = value
        
        # Update the event
        updated_event = service.events().update(
            calendarId=calendar_id, 
            eventId=event_id, 
            body=event
        ).execute()
        
        return updated_event
    except HttpError as error:
        print(f"Error updating event: {error}")
        return None
```

### Deleting Events

```python
def delete_event(service, event_id, calendar_id='primary'):
    """Delete a calendar event."""
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return True
    except HttpError as error:
        print(f"Error deleting event: {error}")
        return False
```

### Handling Workspace Restrictions

```python
def check_calendar_access(service, calendar_id):
    """Check what level of access we have to a calendar."""
    try:
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        # accessRole can be 'owner', 'writer', 'reader', or 'freeBusyReader'
        return calendar.get('accessRole')
    except HttpError as error:
        if error.resp.status == 404:
            return "No access"
        return f"Error: {error}"

def get_calendar_availability(service, calendar_ids, time_min, time_max):
    """Get free/busy information for calendars."""
    body = {
        "timeMin": time_min.isoformat() + 'Z',
        "timeMax": time_max.isoformat() + 'Z',
        "items": [{"id": calendar_id} for calendar_id in calendar_ids]
    }
    
    try:
        freebusy = service.freebusy().query(body=body).execute()
        return freebusy
    except HttpError as error:
        print(f"Error fetching free/busy info: {error}")
        return None
```

## Calendar Manager Class

The `CalendarManager` class provides a high-level interface for calendar operations:

```python
class CalendarManager:
    """Manages Google Calendar operations for radbot."""
    
    def __init__(self, credentials_path='credentials.json'):
        self.credentials_path = credentials_path
        self.personal_service = None
        self.workspace_service = None
        self.workspace_email = None
    
    def authenticate_personal(self):
        """Authenticate with personal Google account."""
        self.personal_service = get_calendar_service()
        return self.personal_service is not None
    
    def authenticate_workspace(self, email):
        """Authenticate with Google Workspace account using service account."""
        self.workspace_email = email
        self.workspace_service = get_workspace_calendar_service(email)
        return self.workspace_service is not None
    
    def list_upcoming_events(self, calendar_id='primary', is_workspace=False):
        """List upcoming events from selected calendar."""
        service = self.workspace_service if is_workspace else self.personal_service
        if not service:
            return {"error": "Not authenticated"}
        
        return list_events(service, calendar_id=calendar_id)
    
    def create_new_event(self, summary, start_time, end_time, is_workspace=False, **kwargs):
        """Create a new event in selected calendar."""
        service = self.workspace_service if is_workspace else self.personal_service
        if not service:
            return {"error": "Not authenticated"}
        
        calendar_id = kwargs.pop('calendar_id', 'primary')
        return create_event(service, summary, start_time, end_time, 
                           calendar_id=calendar_id, **kwargs)
    
    def handle_calendar_request(self, action, params=None, is_workspace=False):
        """Process calendar requests with appropriate error handling."""
        if params is None:
            params = {}
            
        try:
            if action == "list_events":
                return self.list_upcoming_events(is_workspace=is_workspace, **params)
            elif action == "create_event":
                required = ["summary", "start_time", "end_time"]
                if not all(k in params for k in required):
                    return {"error": "Missing required parameters"}
                return self.create_new_event(is_workspace=is_workspace, **params)
            # Add more actions as needed
            else:
                return {"error": "Unknown action"}
        except Exception as e:
            return {"error": str(e)}
```

## Error Handling and Reliability

Implement robust error handling for all calendar operations:

```python
import time
import random
from googleapiclient.errors import HttpError

def execute_with_retry(request_func, max_retries=5):
    """Execute a request with exponential backoff for rate limiting."""
    for retry in range(max_retries):
        try:
            return request_func()
        except HttpError as error:
            if error.resp.status in [403, 429] and 'rate limit exceeded' in str(error).lower():
                # Calculate exponential backoff with jitter
                wait_time = (2 ** retry) + (random.random() * 0.5)
                print(f"Rate limit exceeded. Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                continue
            else:
                # If it's not a rate limit error, re-raise it
                raise
    
    # If we've exhausted retries
    raise Exception(f"Failed after {max_retries} retries due to rate limiting")
```

## ADK Function Tools

Calendar functionality is exposed through ADK function tools in `calendar_tools.py`:

```python
from radbot.tools.calendar.calendar_manager import CalendarManager

def list_calendar_events_tool(calendar_id='primary', max_results=10, 
                             query=None, is_workspace=False):
    """List upcoming calendar events."""
    manager = CalendarManager()
    
    # Authentication based on account type
    if is_workspace:
        if not manager.authenticate_workspace(get_workspace_email()):
            return {"error": "Failed to authenticate with Workspace account"}
    else:
        if not manager.authenticate_personal():
            return {"error": "Failed to authenticate with personal account"}
    
    # List events
    events = manager.list_upcoming_events(
        calendar_id=calendar_id,
        is_workspace=is_workspace
    )
    
    # Format event data for display
    formatted_events = []
    for event in events:
        formatted_events.append({
            "id": event.get("id"),
            "summary": event.get("summary"),
            "start": event.get("start"),
            "end": event.get("end"),
            "location": event.get("location", ""),
            "description": event.get("description", "")
        })
    
    return {"events": formatted_events}
```

## Setup Instructions

### OAuth Setup for Personal Accounts

1. Create a project in Google Cloud Console
2. Enable the Google Calendar API
3. Configure the OAuth consent screen
4. Create OAuth 2.0 credentials
5. Configure authorized redirect URIs
6. Set up environment variables

```
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000
GOOGLE_OAUTH_PORT=8000
```

### Service Account Setup for Google Workspace

1. Create a service account
2. Create and download service account key
3. Enable domain-wide delegation
4. Configure Google Workspace Admin Console
5. Set up environment variables

```
# Service account for Google Workspace
GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE=/absolute/path/to/service-account-key.json
```

## Secure Credential Management

**Never hardcode credentials** in application code. Instead, use:

### For development environments:
```python
# Using environment variables with python-dotenv
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env file
client_id = os.getenv('GOOGLE_CLIENT_ID')
client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
```

### For production environments:
Consider using a secret management service.

For refresh tokens, use secure storage mechanisms appropriate to your deployment:
- System keyring for desktop applications
- Encrypted database fields for web applications
- Managed secrets for cloud deployments

## Common Issues and Troubleshooting

### Error 400: redirect_uri_mismatch

This error indicates that the redirect URI in your OAuth flow doesn't match what's configured in the Google Cloud Console.

**Solution:**
1. Check the redirect URIs in your Google Cloud Console credentials
2. Make sure they include: `http://localhost:8000`
3. Set the `GOOGLE_REDIRECT_URI` environment variable to match exactly
4. Set the `GOOGLE_OAUTH_PORT` to match the port in your redirect URI

### Invalid Client

This error can occur if your client ID or client secret is incorrect.

**Solution:**
1. Double-check the values in your `.env` file
2. Ensure there are no extra spaces or quotes in the values
3. Regenerate client ID and secret if necessary

### Access Denied

This can happen if you haven't granted the necessary permissions to your application.

**Solution:**
1. Check the OAuth consent screen configuration
2. Verify that the correct scopes are enabled
3. Make sure you're using a test user account if in testing mode
4. Check domain-wide delegation settings for service accounts

### Credential Expired

OAuth tokens expire after some time, and need to be refreshed.

**Solution:**
1. Delete the stored token.json file to force a new authentication
2. Ensure your code properly handles token refreshing
3. Check that your refresh token hasn't been revoked

## Additional Considerations

When expanding radbot's calendar functionality:

1. **Testing environments**: Create a test calendar for development to avoid modifying real calendars
2. **Token rotation**: Implement periodic refresh token rotation for enhanced security
3. **Batch requests**: Use batch requests when making multiple API calls to improve performance
4. **Pagination**: Implement proper pagination when retrieving large numbers of events
5. **Timezone handling**: Always specify and consistently handle timezones
6. **Notification subscriptions**: Consider push notifications instead of polling for event changes
7. **Calendar timezone handling**: Properly handle different calendar timezone settings
8. **Recurring event support**: Implement support for creating and managing recurring events
9. **Meeting room booking**: Add functionality for booking meeting rooms
10. **Conference data**: Integrate with Google Meet for video conferences
11. **Notification and reminder settings**: Allow customization of event notifications
12. **Calendar sharing permissions**: Manage shared calendars and permissions
13. **Rate limiting and quota management**: Handle API quota limits gracefully

## References

- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [Google Auth Library Documentation](https://googleapis.dev/python/google-auth/latest/index.html)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Service Account Documentation](https://developers.google.com/identity/protocols/oauth2/service-account)