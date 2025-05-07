# Google Calendar Token Refresh Implementation

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document describes the implementation of the improved Google Calendar token refresh mechanism in RadBot.

## Problem Statement

The Google Calendar integration was experiencing issues with expired OAuth tokens. When a token expired, the system was not correctly prompting for a new authentication, leading to failed calendar operations and a poor user experience.

## Implementation Details

### 1. Token Refresh Mechanism

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

### 2. Manual Token Refresh Tool

A new agent tool was added to allow explicit token refresh:

- `force_refresh_token()` in `calendar_auth.py` provides a way to manually trigger token refresh
- `refresh_calendar_token_wrapper()` in `calendar_tools.py` exposes this as an agent tool
- The tool is registered in the calendar agent factory, making it available to all calendar-enabled agents

This allows users to explicitly refresh tokens when they encounter authentication issues.

### 3. Improved Error Handling

The solution includes comprehensive error handling:

- Specific handling for different types of auth errors (expired token, invalid token, etc.)
- Clear error messages that explain the issue and suggest solutions
- Logging throughout the authentication process for better debuggability
- Graceful fallback to re-authentication when needed

### 4. Workspace Calendar Support

The same robust token handling is implemented for workspace calendars:

- Service account credential loading with better error handling
- Verification of authentication success with test API calls
- Clear error messages for domain-wide delegation failures

## Testing

A test script (`tools/test_calendar_token_refresh.py`) is provided to validate the token refresh mechanism. The script:

1. Tests normal calendar operations
2. Simulates an expired token by modifying the token file
3. Tests if operations trigger a successful token refresh
4. Tests the manual token refresh function
5. Restores the original token

## Usage

When users encounter a token expired message, they can now:

1. Let the system automatically handle the refresh in most cases
2. If automatic refresh fails, they can use the new token refresh tool directly:
   ```
   Please refresh my calendar token
   ```

This will trigger a browser-based OAuth flow to obtain a new valid token.

## Future Improvements

Potential future improvements include:

1. Implementing a background token refresh that pro-actively refreshes tokens before they expire
2. Adding a headless mode for server environments 
3. Supporting other OAuth flows (device flow, etc.)
4. Adding more detailed diagnostics about token status