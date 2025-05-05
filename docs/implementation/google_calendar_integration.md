# Google Calendar Integration Implementation Plan

This document outlines the implementation plan for adding Google Calendar functionality to the radbot project. The integration will allow radbot to view, create, update, and delete calendar events for both personal Google accounts and Google Workspace environments.

## Project Structure

We'll add the following components to the project:

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

## Implementation Phases

### Phase 1: Setup and Authentication (1 week)

1. Add dependencies to pyproject.toml
   - google-api-python-client
   - google-auth-httplib2 
   - google-auth-oauthlib
   - Note: gcsa (Google Calendar Simple API) was removed due to dependency conflict with ADK 0.4.0 (tzlocal version conflict)

2. Create Google Cloud project setup
   - Set up OAuth consent screen
   - Generate OAuth credentials
   - Configure service account for workspace access

3. Implement authentication methods in `calendar_auth.py`
   - Personal account authentication with OAuth flow
   - Workspace authentication with service account
   - Token management and storage

### Phase 2: Core Calendar Operations (1 week)

1. Implement basic calendar operations in `calendar_operations.py`
   - List events with filtering options
   - Create events with required and optional parameters
   - Update existing events
   - Delete events
   - Check calendar availability using free/busy API

2. Create the `CalendarManager` class in `calendar_manager.py`
   - Authentication method wrappers
   - Calendar operation method wrappers
   - Error handling and retry logic
   - Type hint all interfaces

### Phase 3: Agent Integration (1 week)

1. Create Google ADK function tools in `calendar_tools.py`
   - Wrap all calendar operations as function tools
   - Define clear schemas for each operation
   - Add comprehensive documentation

2. Create a calendar agent factory
   - Add `calendar_agent_factory.py` to radbot/agent/
   - Configure appropriate tools and instructions
   - Set up default configuration

3. Create example script
   - Add `calendar_agent_example.py` to examples/

### Phase 4: Security and Testing (1 week)

1. Implement secure credential management
   - Environment variable support
   - Keyring integration for desktop
   - Secret manager support for production

2. Add unit tests
   - Create test fixtures with mock responses
   - Test authentication flows
   - Test calendar operations
   - Test error handling

3. Create documentation
   - Add user guide for setting up credentials
   - Document all available calendar functions
   - Add example usage patterns

## API Design

### Calendar Authentication

```python
def get_calendar_service():
    """Authenticate and return a Google Calendar service object for personal accounts."""
    # OAuth flow implementation
    pass

def get_workspace_calendar_service(user_email):
    """Get calendar service using domain-wide delegation for workspace accounts."""
    # Service account implementation
    pass

def get_credentials_from_env():
    """Get credentials from environment variables."""
    # Environment variable handling
    pass
```

### Calendar Operations

```python
def list_events(service, calendar_id='primary', max_results=10, query=None, 
                time_min=None, time_max=None):
    """List calendar events with filtering options."""
    pass

def create_event(service, summary, start_time, end_time, description=None, 
                location=None, attendees=None, calendar_id='primary'):
    """Create a calendar event."""
    pass

def update_event(service, event_id, calendar_id='primary', **kwargs):
    """Update an existing calendar event with provided fields."""
    pass

def delete_event(service, event_id, calendar_id='primary'):
    """Delete a calendar event."""
    pass

def check_calendar_availability(service, calendar_ids, time_min, time_max):
    """Check availability (free/busy) for calendars."""
    pass
```

### Calendar Manager Class

```python
class CalendarManager:
    """Manages Google Calendar operations for radbot."""
    
    def __init__(self):
        self.personal_service = None
        self.workspace_service = None
        self.workspace_email = None
    
    def authenticate_personal(self):
        """Authenticate with personal Google account."""
        pass
    
    def authenticate_workspace(self, email):
        """Authenticate with Google Workspace account using service account."""
        pass
    
    def list_upcoming_events(self, calendar_id='primary', is_workspace=False):
        """List upcoming events from selected calendar."""
        pass
    
    def create_new_event(self, summary, start_time, end_time, is_workspace=False, **kwargs):
        """Create a new event in selected calendar."""
        pass
    
    def update_existing_event(self, event_id, is_workspace=False, **kwargs):
        """Update an existing event."""
        pass
    
    def delete_existing_event(self, event_id, calendar_id='primary', is_workspace=False):
        """Delete an existing event."""
        pass
    
    def get_calendar_busy_times(self, calendar_ids, time_min, time_max, is_workspace=False):
        """Get busy time slots for calendars."""
        pass
```

### Function Tools

We'll create the following Google ADK function tools:

1. `list_calendar_events` - List upcoming events 
2. `create_calendar_event` - Create a new event
3. `update_calendar_event` - Update an existing event
4. `delete_calendar_event` - Delete an event
5. `check_calendar_availability` - Check availability

Each tool will include:
- Clear parameter schemas
- Proper error handling
- Type hints
- Comprehensive docstrings

## Secret Management

For storing Google Calendar credentials securely:

1. Development environments:
   - Use environment variables loaded from .env file:
     - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` for OAuth authentication
     - `GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE` for Workspace authentication (separate from `GOOGLE_SERVICE_ACCOUNT_FILE` used for other Google services)
   - Use local token.json for OAuth refresh tokens

2. Production environments:
   - Consider cloud-based secret managers
   - Use environment variables set in deployment
   - Implement token encryption

## Testing Strategy

1. Unit Tests:
   - Test authentication workflows with mocks
   - Test calendar operations with mock responses
   - Test error handling and retry logic

2. Integration Tests:
   - Create test Google Calendar
   - Test end-to-end workflows
   - Validate event creation and retrieval

3. Security Tests:
   - Validate credential storage
   - Test access controls
   - Verify token refresh and expiration handling

## Dependencies

Required libraries:
- google-api-python-client: Primary interface to Google APIs
- google-auth-httplib2: HTTP client for authentication 
- google-auth-oauthlib: OAuth 2.0 library for Google
- gcsa (optional): Google Calendar Simple API for a more Pythonic interface

## Additional Considerations

- Calendar timezone handling
- Recurring event support
- Meeting room booking
- Conference data (Google Meet integration)
- Notification and reminder settings
- Calendar sharing permissions
- Rate limiting and quota management

## References

- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [Google Auth Library Documentation](https://googleapis.dev/python/google-auth/latest/index.html)
- [GCSA Documentation](https://github.com/kuzmoyev/Google-Calendar-Simple-API)