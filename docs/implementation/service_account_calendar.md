# Service Account Google Calendar Integration

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document explains how to set up RadBot's Google Calendar integration using a service account.

## Overview

RadBot uses a Google service account for authenticating with the Google Calendar API. This approach is more reliable than OAuth2 for server applications as it doesn't rely on user tokens that expire.

## Requirements

1. A Google Cloud Platform project with the Google Calendar API enabled
2. A service account with appropriate permissions
3. Access to the target Google Calendar

## Setup Instructions

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

## Troubleshooting

If you encounter issues:

1. **Calendar Access Denied**: Ensure the calendar is shared with the service account email
2. **API Disabled**: Check that the Google Calendar API is enabled in your GCP project
3. **Missing File**: Verify the `GOOGLE_CREDENTIALS_PATH` points to a valid service account JSON file
4. **Permission Issues**: Make sure the service account has appropriate roles assigned

## Using with Domain-Wide Delegation (Google Workspace)

For accessing calendars across a Google Workspace domain:

1. Enable domain-wide delegation for the service account in GCP
2. In the Google Workspace Admin Console, go to Security > API Controls > Domain-wide Delegation
3. Add the service account client ID and grant it the `https://www.googleapis.com/auth/calendar` scope
4. In RadBot, set the `GOOGLE_IMPERSONATION_EMAIL` environment variable to the email of the user to impersonate:
   ```bash
   export GOOGLE_IMPERSONATION_EMAIL=user@yourdomain.com
   ```

## Environment Variables

- `GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE`: Path to the service account JSON file
- `GOOGLE_IMPERSONATION_EMAIL`: (Optional) Email address to impersonate in a Google Workspace
- `GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON`: (Optional) Service account credentials as a JSON string
- `CALENDAR_ID`: (Optional) ID of the calendar to use (defaults to "primary")

## Best Practices

1. Keep the service account key file secure
2. Use specific calendars instead of personal calendars when possible
3. Grant only the necessary permissions to the service account
4. Regularly validate that the connection is working