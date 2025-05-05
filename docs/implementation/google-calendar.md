# Mastering Google Calendar in Python: Building the radbot integration

Google Calendar integration empowers your radbot project with scheduling capabilities that work across both personal and enterprise environments. The implementation involves setting up authentication flows, handling credentials securely, and writing code that works with Google's API while respecting organizational constraints. This guide provides a practical, implementation-focused approach to adding calendar functionality to your Python application.

## The essential Google Calendar integration path

Google Calendar API offers powerful functionality for Python-based bots like radbot, but requires proper setup and authentication handling. You'll need to establish a Google Cloud project, implement OAuth flows or service accounts, and write efficient calendar operation code using the appropriate scopes. 

**Security is paramount** when handling calendar credentials — especially for a project that bridges personal and workspace calendars. Google's workspace restrictions add complexity but can be addressed through service accounts with proper delegation. The most challenging aspect will be creating an authentication system that handles both scenarios gracefully.

For restricted workspace calendars, service accounts with domain-wide delegation provide the best solution, but require admin configuration in Google Workspace.

## Setting up your development environment

Start by installing the required libraries for Google Calendar integration:

```python
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

For a more Pythonic interface, consider the GCSA wrapper (Google Calendar Simple API):

```python
pip install gcsa
```

Create a Google Cloud project with the Calendar API enabled:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project for radbot
3. Navigate to "API & Services" and enable the Google Calendar API
4. Configure the OAuth consent screen (Internal for Workspace or External for public use)
5. Create OAuth 2.0 credentials (Client ID and Client Secret)
6. Download the JSON credentials file as `credentials.json`

## Implementing authentication

### OAuth2 flow for personal accounts

For personal Google Accounts, implement this OAuth2 flow:

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

### Service accounts for Google Workspace

For Google Workspace accounts with restricted sharing:

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

## Required scopes for calendar operations

Choose the most limited scope that fulfills your requirements:

| Operation | Minimum Required Scope |
|-----------|------------------------|
| Viewing events | `https://www.googleapis.com/auth/calendar.readonly` |
| Creating/modifying events | `https://www.googleapis.com/auth/calendar` |
| Free/busy info only | `https://www.googleapis.com/auth/calendar.freebusy` |

For radbot's basic viewing/creating/modifying requirements, use `https://www.googleapis.com/auth/calendar`.

## Secure credential management

**Never hardcode credentials** in your application code. The most secure approaches for storing Google API credentials are:

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
```python
# Using a secret management service (example with Google Cloud Secret Manager)
from google.cloud import secretmanager

def access_secret(project_id, secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')

client_id = access_secret("your-project-id", "oauth-client-id")
client_secret = access_secret("your-project-id", "oauth-client-secret")
```

For refresh tokens, use secure storage mechanisms appropriate to your deployment:
- System keyring for desktop applications
- Encrypted database fields for web applications
- Managed secrets for cloud deployments

## Implementing basic calendar operations

### Listing calendar events

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

### Creating events

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

### Updating events

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

### Deleting events

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

## Handling workspace calendar restrictions

When accessing Google Workspace calendars with external sharing restrictions:

### Check the access level first

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
```

### Fallback to free/busy information when detailed access is restricted

```python
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

## Error handling and reliability

Implement robust error handling for all calendar operations:

```python
import time
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

## Radbot integration architecture

For the radbot project, consider implementing a `CalendarManager` class to handle all Google Calendar operations:

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
    
    # Add similar methods for updating and deleting events
    
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

## Complete integration example

Here's a complete example showing how to use the calendar functionality in your radbot project:

```python
import datetime
from calendar_manager import CalendarManager

def init_calendar_integration():
    """Initialize calendar integration for radbot."""
    manager = CalendarManager()
    
    # Authenticate with personal account (OAuth flow)
    personal_auth = manager.authenticate_personal()
    print(f"Personal calendar authentication: {'Success' if personal_auth else 'Failed'}")
    
    # If workspace integration is needed, authenticate with workspace account
    # This requires a service account with domain-wide delegation
    workspace_email = "user@company.com"  # The user to impersonate
    workspace_auth = manager.authenticate_workspace(workspace_email)
    print(f"Workspace calendar authentication: {'Success' if workspace_auth else 'Failed'}")
    
    return manager

def demo_calendar_operations():
    """Demonstrate basic calendar operations."""
    manager = init_calendar_integration()
    
    # List upcoming events from personal calendar
    print("\nUpcoming personal events:")
    events = manager.list_upcoming_events()
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"{start} - {event['summary']}")
    
    # Create a new event in personal calendar
    print("\nCreating new event...")
    start_time = datetime.datetime.now() + datetime.timedelta(days=1)
    end_time = start_time + datetime.timedelta(hours=1)
    new_event = manager.create_new_event(
        summary="Radbot Test Event",
        start_time=start_time,
        end_time=end_time,
        description="Testing radbot calendar integration",
        location="Virtual Meeting"
    )
    
    if new_event:
        print(f"Event created: {new_event['summary']} on {new_event['start']['dateTime']}")
        
        # Update the event
        print("\nUpdating event...")
        updated_event = manager.handle_calendar_request(
            "update_event",
            {
                "event_id": new_event['id'],
                "summary": "Updated Radbot Test Event",
                "description": "This event was updated by radbot"
            }
        )
        
        if updated_event and 'error' not in updated_event:
            print(f"Event updated: {updated_event['summary']}")
        
        # Delete the event
        print("\nDeleting event...")
        delete_result = manager.handle_calendar_request(
            "delete_event",
            {"event_id": new_event['id']}
        )
        
        if delete_result and delete_result is True:
            print("Event deleted successfully")
    
    # Try to access workspace calendar if available
    if manager.workspace_service:
        print("\nWorkspace calendar availability:")
        # This will fall back to free/busy if detailed access is restricted
        workspace_events = manager.list_upcoming_events(is_workspace=True)
        if isinstance(workspace_events, list):
            for event in workspace_events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"{start} - {event['summary']}")
        else:
            print(f"Could not access detailed events: {workspace_events}")
            
            # Fall back to free/busy information
            time_min = datetime.datetime.now()
            time_max = time_min + datetime.timedelta(days=7)
            availability = manager.handle_calendar_request(
                "get_availability",
                {
                    "time_min": time_min,
                    "time_max": time_max,
                    "calendar_ids": ["primary"]
                },
                is_workspace=True
            )
            print("Workspace calendar busy times:")
            print(availability)

if __name__ == "__main__":
    demo_calendar_operations()
```

## Additional considerations

When expanding radbot's calendar functionality:

1. **Testing environments**: Create a test calendar for development to avoid modifying real calendars
2. **Token rotation**: Implement periodic refresh token rotation for enhanced security
3. **Batch requests**: Use batch requests when making multiple API calls to improve performance
4. **Pagination**: Implement proper pagination when retrieving large numbers of events
5. **Timezone handling**: Always specify and consistently handle timezones
6. **Notification subscriptions**: Consider push notifications instead of polling for event changes

By following these implementation patterns and best practices, radbot will have a robust, secure Google Calendar integration that works with both personal and workspace calendars while respecting organizational security constraints.
