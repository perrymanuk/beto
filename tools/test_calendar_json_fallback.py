#!/usr/bin/env python3
"""Test Google Calendar authentication error handling for JSON fallback."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from radbot.tools.calendar.calendar_auth import get_calendar_service

def test_service_account_fallback():
    """Test that the service correctly handles empty/invalid environment variables."""
    
    print("Testing Google Calendar service account fallback logic...")
    
    # Test 1: Invalid JSON string with no file
    print("\n\nTest 1: Invalid JSON string with no file")
    os.environ['GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON'] = 'not-valid-json'
    os.environ['GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE'] = '/tmp/does-not-exist.json'
    
    try:
        get_calendar_service()
        print("ERROR: Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"SUCCESS: Properly fell back to file path and raised FileNotFoundError: {e}")
    except Exception as e:
        print(f"ERROR: Wrong exception type: {type(e).__name__}: {e}")
    
    # Test 2: Empty JSON string with no file
    print("\n\nTest 2: Empty JSON string with no file")
    os.environ['GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON'] = ''
    os.environ['GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE'] = '/tmp/does-not-exist.json'
    
    try:
        get_calendar_service()
        print("ERROR: Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"SUCCESS: Properly fell back to file path and raised FileNotFoundError: {e}")
    except Exception as e:
        print(f"ERROR: Wrong exception type: {type(e).__name__}: {e}")
    
    # Test 3: Whitespace JSON string with no file
    print("\n\nTest 3: Whitespace JSON string with no file")
    os.environ['GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON'] = '   '
    os.environ['GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE'] = '/tmp/does-not-exist.json'
    
    try:
        get_calendar_service()
        print("ERROR: Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"SUCCESS: Properly fell back to file path and raised FileNotFoundError: {e}")
    except Exception as e:
        print(f"ERROR: Wrong exception type: {type(e).__name__}: {e}")
    
    # Test 4: No environment variables - should use DEFAULT_SERVICE_ACCOUNT_PATH
    print("\n\nTest 4: No environment variables (should use default path)")
    os.environ.pop('GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON', None)
    os.environ.pop('GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE', None)
    
    # Note: This test should either succeed or fail with an API error,
    # but not with a path error since it uses the default path
    
    print("\nTests completed!")

if __name__ == "__main__":
    test_service_account_fallback()