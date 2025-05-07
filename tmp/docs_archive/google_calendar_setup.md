# Google Calendar Integration Setup

This document provides step-by-step instructions for setting up Google Calendar integration with radbot.

## Prerequisites

- Google account with access to Google Cloud Console
- Basic understanding of OAuth 2.0 authentication flow
- Access to configure environment variables

## OAuth Setup for Personal Accounts

### Step 1: Create a Project in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note the Project ID as you might need it later

### Step 2: Enable the Google Calendar API

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for "Google Calendar API" and select it
3. Click "Enable" to activate the API for your project

### Step 3: Configure OAuth Consent Screen

1. Navigate to "APIs & Services" > "OAuth consent screen"
2. Select "External" or "Internal" (depending on your use case)
   - For testing, "External" is fine, but your app will be in "Testing" mode
   - For production internal use, select "Internal" if you have Google Workspace
3. Fill in the required information:
   - App name: "Radbot Calendar Integration"
   - User support email: Your email
   - Developer contact information: Your email
4. Add the scopes:
   - `https://www.googleapis.com/auth/calendar` (Full access)
   - `https://www.googleapis.com/auth/calendar.readonly` (Read-only access)
5. Add test users (if using External consent screen)
6. Complete the registration process

### Step 4: Create OAuth 2.0 Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "Radbot Calendar Client"
5. Click "Create"
6. Download the JSON file by clicking the download icon
7. Make note of the Client ID and Client Secret shown in the popup

### Step 5: Configure Authorized Redirect URIs

1. Go back to the "Credentials" page
2. Click on the OAuth 2.0 Client ID you just created
3. Add these redirect URIs:
   - `http://localhost:8000`
   - `http://localhost`
   - `http://localhost:8080`
   - `urn:ietf:wg:oauth:2.0:oob`
4. Click "Save"

### Step 6: Set Up Environment Variables

Add the following to your `.env` file:

```
# Google Calendar API Configuration
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000
GOOGLE_OAUTH_PORT=8000
```

### Step 7: Test OAuth Flow

1. Run the test script:
   ```bash
   python tools/test_calendar_oauth.py
   ```
2. Follow the browser prompts to authenticate
3. Verify that the script can access your calendars

## Service Account Setup for Google Workspace

If you want to access Google Workspace calendars with domain-wide delegation:

### Step 1: Create a Service Account

1. In the Google Cloud Console, navigate to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Name: "Radbot Calendar Service Account"
4. Grant the necessary roles (Project > Viewer is minimum)
5. Click "Create and Continue"
6. Click "Done"

### Step 2: Create and Download Service Account Key

1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" key type
5. Click "Create" to download the key file
6. Save this file securely - it grants access to your services\!

### Step 3: Enable Domain-Wide Delegation

1. Go back to the service account details
2. Click "Edit" at the top
3. Enable "Domain-wide delegation"
4. Save the changes

### Step 4: Configure Google Workspace Admin Console

1. Go to [Google Workspace Admin Console](https://admin.google.com/)
2. Navigate to "Security" > "API controls"
3. In the "Domain-wide delegation" section, click "Manage Domain-wide Delegation"
4. Click "Add new"
5. Enter the Client ID from your service account
6. Add the OAuth scope: `https://www.googleapis.com/auth/calendar`
7. Click "Authorize"

### Step 5: Set Up Environment Variables

Add the following to your `.env` file:

```
# Service account for Google Workspace
GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE=/absolute/path/to/service-account-key.json
# Alternatively, set the entire JSON content as a string:
# GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...",...}'
```

## Troubleshooting

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

## Credential Storage

By default, the radbot calendar integration stores credentials in:

- OAuth tokens: `radbot/tools/calendar/credentials/token.json`
- Service account: Environment variable or path specified in environment

For additional security:
1. Store credentials outside the repository
2. Use environment variables instead of files
3. Consider encryption for production storage
4. Use secret management systems for deployment

## Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Service Account Documentation](https://developers.google.com/identity/protocols/oauth2/service-account)
EOL < /dev/null