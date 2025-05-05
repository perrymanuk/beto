"""Authentication module for Google Calendar API."""

import os.path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define scope constants
READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
FULL_ACCESS_SCOPE = "https://www.googleapis.com/auth/calendar"
FREEBUSY_SCOPE = "https://www.googleapis.com/auth/calendar.freebusy"

# Default locations for credentials
DEFAULT_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "credentials", "credentials.json")
DEFAULT_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "credentials", "token.json")
DEFAULT_SERVICE_ACCOUNT_PATH = os.path.join(os.path.dirname(__file__), "credentials", "service-account.json")

# Try to get service account path from environment variable first
CALENDAR_SERVICE_ACCOUNT_PATH = os.environ.get("GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE", DEFAULT_SERVICE_ACCOUNT_PATH)


def get_calendar_service(
    credentials_path: str = DEFAULT_CREDENTIALS_PATH,
    token_path: str = DEFAULT_TOKEN_PATH,
    scopes: Optional[List[str]] = None,
    use_env_vars: bool = True,
) -> Any:
    """Authenticate and return a Google Calendar service object for personal accounts.
    
    Args:
        credentials_path: Path to the credentials.json file.
        token_path: Path where the token will be saved.
        scopes: List of authorization scopes to request.
        
    Returns:
        A Google Calendar service object.
        
    Raises:
        FileNotFoundError: If credentials.json is not found.
        Exception: If authentication fails.
    """
    if scopes is None:
        scopes = [FULL_ACCESS_SCOPE]
    
    creds = None
    
    # Check for existing token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Try environment variables first if enabled
            client_id = os.environ.get("GOOGLE_CLIENT_ID")
            client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
            
            if use_env_vars and client_id and client_secret:
                # Use environment variables for authentication
                print(f"Using environment variables for Google Calendar authentication")
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "redirect_uris": [
                                "http://localhost:8000",
                                "http://localhost",
                                "http://localhost:8080",
                                "urn:ietf:wg:oauth:2.0:oob"
                            ]
                        }
                    },
                    scopes
                )
                # Get the port from environment or use default
                port = int(os.environ.get("GOOGLE_OAUTH_PORT", "8000"))
                creds = flow.run_local_server(port=port)
            else:
                # Fall back to credentials file
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(f"Credentials file not found at {credentials_path} and no environment variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) set")
                
                # Get the redirect URI from environment or use default
                redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, scopes, redirect_uri=redirect_uri
                )
                # Get the port from environment or use default
                port = int(os.environ.get("GOOGLE_OAUTH_PORT", "8000"))
                creds = flow.run_local_server(port=port)
        
        # Save credentials for future runs
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    
    # Build and return the service
    service = build("calendar", "v3", credentials=creds)
    return service


def get_workspace_calendar_service(
    user_email: str,
    service_account_file: str = CALENDAR_SERVICE_ACCOUNT_PATH,
    scopes: Optional[List[str]] = None,
    use_env_vars: bool = True,
) -> Any:
    """Get calendar service using domain-wide delegation for Google Workspace.
    
    Args:
        user_email: The user email to impersonate.
        service_account_file: Path to the service account credentials JSON file.
        scopes: List of authorization scopes to request.
        
    Returns:
        A Google Calendar service object.
        
    Raises:
        FileNotFoundError: If service account file is not found.
        Exception: If authentication fails.
    """
    if scopes is None:
        scopes = [FULL_ACCESS_SCOPE]
    
    # Get service account information from environment or file
    service_account_info = None
    service_account_json = os.environ.get("GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON")
    
    if use_env_vars and service_account_json:
        try:
            # Try to parse the JSON string from environment variable
            import json
            service_account_info = json.loads(service_account_json)
            print("Using GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON environment variable for authentication")
        except json.JSONDecodeError as e:
            print(f"Error parsing GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON: {e}")
            service_account_info = None
    
    if service_account_info:
        # Use the parsed service account info from environment
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=scopes)
    else:
        # Fall back to file
        if not os.path.exists(service_account_file):
            raise FileNotFoundError(f"Service account file not found at {service_account_file} and GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON environment variable not set or invalid")
        
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=scopes)
    
    # Delegate to impersonate a Workspace user
    delegated_credentials = credentials.with_subject(user_email)
    service = build('calendar', 'v3', credentials=delegated_credentials)
    
    return service


def get_credentials_from_env() -> Dict[str, str]:
    """Get credentials from environment variables.
    
    Returns:
        Dictionary containing credential information.
    """
    credentials = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "service_account_file": os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE", DEFAULT_SERVICE_ACCOUNT_PATH),
        "service_account_json": os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON", ""),
    }
    
    # Add some debug logging
    if credentials["client_id"] and credentials["client_secret"]:
        print("Found Google Calendar OAuth credentials in environment variables")
    
    if credentials["service_account_file"] != DEFAULT_SERVICE_ACCOUNT_PATH:
        print(f"Found Google Calendar service account file path in environment: {credentials['service_account_file']}")
    
    if credentials["service_account_json"]:
        print("Found Google Calendar service account JSON in environment variables")
    
    return credentials