# Calendar ID Configuration for Service Account

This document explains how to configure the calendar ID to be used with the service account in RadBot.

## Overview

RadBot now supports the ability to specify which calendar ID to use when interacting with Google Calendar via a service account. This allows you to target a specific user's calendar rather than only working with the service account's primary calendar.

## Configuration

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

## Implementation

This feature is implemented in the following way:

1. The default calendar ID is set in `calendar_auth.py`:
   ```python
   DEFAULT_CALENDAR_ID = "primary"
   CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", DEFAULT_CALENDAR_ID)
   ```

2. All calendar tool wrapper functions have been updated to:
   - Accept an optional `calendar_id` parameter
   - Default to the environment variable if no calendar ID is provided

3. This ensures compatibility with existing code while allowing new flexibility.

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

## Troubleshooting

If events are being created successfully but not appearing in the expected calendar:

1. Verify the service account has access to the target calendar
2. Confirm the correct calendar ID is being used
3. Check for typos in email addresses
4. Ensure the sharing permissions include write access

You can validate settings with the verification tool:

```bash
GOOGLE_CALENDAR_ID="user@example.com" python tools/validate_calendar_service_account.py
```