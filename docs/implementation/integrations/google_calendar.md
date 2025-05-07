# Google Calendar Integration

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document provides a comprehensive guide to the Google Calendar integration in the RadBot project, including setup, authentication methods, implementation details, and usage examples.

## Overview

Google Calendar integration allows RadBot to interact with calendars across both personal and enterprise environments, providing capabilities to:

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

RadBot supports two main authentication methods for Google Calendar:

1. **OAuth2 for Personal Accounts**: Interactive authentication for individual users
2. **Service Accounts for Google Workspace**: Non-interactive authentication for organization-wide use

### OAuth2 for Personal Accounts

For personal Google accounts, RadBot uses an OAuth2 flow:

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

For RadBot's basic viewing/creating/modifying requirements, we use `https://www.googleapis.com/auth/calendar`.

## Service Account Setup

### 1. Create a Service Account

If you haven't already created a service account:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create a project
3. Navigate to "IAM & Admin" > "Service Accounts"
4. Click "Create Service Account"
5. Give it a name and description
6. Grant it the "Calendar API" > "Calendar App Data" role
7. Create and download the JSON key file

### 2. Configure Calendar Access

For the service account to access your calendar:

1. Get the service account's email address (found in the JSON file as `client_email`)
2. Go to your Google Calendar
3. Find the calendar you want to use and click the three dots > "Settings and sharing"
4. Under "Share with specific people," add the service account's email
5. Give it "Make changes to events" permissions
6. Save

### 3. Configure RadBot

Set up RadBot to use the service account:

1. Place the service account JSON file in a secure location
2. Set the `GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE` environment variable to the full path of the JSON file:
   ```bash
   export GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE=/path/to/service-account.json
   ```
   
### 4. Validate the Setup

Use the validation tool to ensure everything is working correctly:

```bash
python tools/validate_calendar_service_account.py
```

This script will:
1. Check if the service account file exists
2. Validate that it can access the specified calendar
3. List upcoming events as a test

## Calendar ID Configuration

### Overview

RadBot supports the ability to specify which calendar ID to use when interacting with Google Calendar via a service account. This allows you to target a specific user's calendar rather than only working with the service account's primary calendar.

### Environment Variable

Set the `GOOGLE_CALENDAR_ID` environment variable to specify which calendar ID to use:

```bash
export GOOGLE_CALENDAR_ID="user@example.com"
```

By default, if this environment variable is not set, the system will use "primary" which refers to the service account's primary calendar.

### Calendar Sharing

For this to work, you must ensure that the target calendar is shared with the service account:

1. Get the service account email address (e.g., `radbot@perrymanuk-457923.iam.gserviceaccount.com`)
2. In Google Calendar, share the target calendar with this email address
3. Grant appropriate permissions (at least "Make changes to events")

### Implementation

This feature is implemented in the following way:

1. The default calendar ID is set in `calendar_auth.py`:
   ```python
   DEFAULT_CALENDAR_ID = "primary"
   CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", DEFAULT_CALENDAR_ID)
   ```

2. All calendar tool wrapper functions have been updated to:
   - Accept an optional `calendar_id` parameter
   - Default to the environment variable if no calendar ID is provided

## Token Refresh Implementation

### Problem Statement

The Google Calendar integration was experiencing issues with expired OAuth tokens. When a token expired, the system was not correctly prompting for a new authentication, leading to failed calendar operations and a poor user experience.

### Token Refresh Mechanism

The core of the solution is an improved token refresh mechanism in `radbot/tools/calendar/calendar_auth.py`. This includes:

- A dedicated `refresh_token()` function that safely handles token refreshing with better error handling
- Clear logging of token refresh attempts and errors
- Improved exception handling for different types of token errors (expired, invalid, etc.)
- Automatic re-authentication flow when token refresh fails

```python
def refresh_token(token_path: str, scopes: List[str]) -> Tuple[Optional[Credentials], Optional[str]]:
    """Attempt to refresh an expired token."""
    try:
        creds = Credentials.from_authorized_user_file(token_path, scopes)
        if creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
            
            # Save refreshed credentials
            with open(token_path, "w") as token:
                token.write(creds.to_json())
                
            logger.info("Token refreshed successfully!")
            return creds, None
        else:
            return creds, None
    except RefreshError as e:
        error_message = f"Failed to refresh token: {str(e)}. Re-authentication required."
        logger.error(error_message)
        return None, error_message
    except Exception as e:
        error_message = f"Error refreshing token: {str(e)}"
        logger.error(error_message)
        return None, error_message
```

### Manual Token Refresh Tool

A new agent tool was added to allow explicit token refresh:

- `force_refresh_token()` in `calendar_auth.py` provides a way to manually trigger token refresh
- `refresh_calendar_token_wrapper()` in `calendar_tools.py` exposes this as an agent tool
- The tool is registered in the calendar agent factory, making it available to all calendar-enabled agents

This allows users to explicitly refresh tokens when they encounter authentication issues.

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

## Calendar Manager Class

The `CalendarManager` class provides a high-level interface for calendar operations:

```python
class CalendarManager:
    """Manages Google Calendar operations for RadBot."""
    
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

## Usage Examples

### Python Code

```python
# Uses the environment variable
create_calendar_event_wrapper(
    summary="Team Meeting",
    start_time="2024-06-01T10:00:00",
    end_time="2024-06-01T11:00:00"
)

# Explicitly specify a calendar ID
create_calendar_event_wrapper(
    summary="Team Meeting",
    start_time="2024-06-01T10:00:00",
    end_time="2024-06-01T11:00:00",
    calendar_id="another-user@example.com"
)
```

### Command Line

```bash
# Set the environment variable before running
export GOOGLE_CALENDAR_ID="user@example.com"
python my_calendar_script.py

# Or set it for a single command
GOOGLE_CALENDAR_ID="user@example.com" python my_calendar_script.py
```

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

## Environment Variables

- `GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE`: Path to the service account JSON file
- `GOOGLE_CLIENT_ID`: OAuth2 client ID for personal account authentication
- `GOOGLE_CLIENT_SECRET`: OAuth2 client secret for personal account authentication
- `GOOGLE_REDIRECT_URI`: OAuth2 redirect URI
- `GOOGLE_OAUTH_PORT`: Port for OAuth2 redirect server
- `GOOGLE_IMPERSONATION_EMAIL`: (Optional) Email address to impersonate in a Google Workspace
- `GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON`: (Optional) Service account credentials as a JSON string
- `GOOGLE_CALENDAR_ID`: (Optional) ID of the calendar to use (defaults to "primary")

## Additional Considerations

When expanding RadBot's calendar functionality:

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