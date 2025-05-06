#!/usr/bin/env python3
"""Test script for the improved Google Calendar token refresh mechanism."""

import logging
import os
import sys
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def simulate_expired_token():
    """Modify the token.json file to simulate an expired token."""
    try:
        # Find the token path
        from radbot.tools.calendar.calendar_auth import DEFAULT_TOKEN_PATH
        
        if not os.path.exists(DEFAULT_TOKEN_PATH):
            logger.error(f"Token file not found at {DEFAULT_TOKEN_PATH}")
            logger.error("Please authenticate first with Google Calendar before running this test")
            return False
        
        # Load the token
        with open(DEFAULT_TOKEN_PATH, "r") as f:
            token_data = json.load(f)
        
        # Save a backup
        backup_path = f"{DEFAULT_TOKEN_PATH}.backup"
        with open(backup_path, "w") as f:
            json.dump(token_data, f, indent=2)
        logger.info(f"Created token backup at {backup_path}")
        
        # Modify expiry to be in the past
        yesterday = datetime.utcnow() - timedelta(days=1)
        token_data["expiry"] = yesterday.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        # Save modified token
        with open(DEFAULT_TOKEN_PATH, "w") as f:
            json.dump(token_data, f, indent=2)
        
        logger.info(f"Modified token to be expired: {token_data['expiry']}")
        return True
    except Exception as e:
        logger.error(f"Error simulating expired token: {e}")
        return False

def restore_token_backup():
    """Restore the token from backup if available."""
    try:
        from radbot.tools.calendar.calendar_auth import DEFAULT_TOKEN_PATH
        backup_path = f"{DEFAULT_TOKEN_PATH}.backup"
        
        if os.path.exists(backup_path):
            with open(backup_path, "r") as f:
                token_data = json.load(f)
            
            with open(DEFAULT_TOKEN_PATH, "w") as f:
                json.dump(token_data, f, indent=2)
            
            logger.info(f"Restored token from backup")
            return True
        else:
            logger.warning(f"No backup found at {backup_path}")
            return False
    except Exception as e:
        logger.error(f"Error restoring token backup: {e}")
        return False

def test_calendar_operations():
    """Test calendar operations with an expired token."""
    try:
        from radbot.tools.calendar.calendar_manager import CalendarManager
        
        # Create a calendar manager
        logger.info("Creating calendar manager...")
        manager = CalendarManager()
        
        # Test authentication
        logger.info("Attempting to authenticate with personal Google account...")
        auth_success = manager.authenticate_personal()
        
        if auth_success:
            logger.info("✅ Authentication successful!")
            
            # Try to list events
            logger.info("Testing calendar access by listing events...")
            events = manager.list_upcoming_events(max_results=1)
            
            if isinstance(events, list):
                logger.info(f"✅ Successfully retrieved calendar events! Found {len(events)} events.")
                return True
            else:
                logger.warning(f"⚠️ Retrieved events response is not a list: {events}")
                return False
        else:
            logger.error("❌ Authentication failed")
            return False
    except Exception as e:
        logger.error(f"Error during calendar operations test: {e}")
        return False

def test_manual_token_refresh():
    """Test the manual token refresh function."""
    try:
        from radbot.tools.calendar.calendar_auth import force_refresh_token
        
        logger.info("Testing manual token refresh function...")
        result = force_refresh_token()
        
        if result["status"] == "success":
            logger.info(f"✅ Token refresh successful: {result['message']}")
            return True
        else:
            logger.error(f"❌ Token refresh failed: {result.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        logger.error(f"Error during manual token refresh test: {e}")
        return False

def main():
    """Run the token refresh test."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting Google Calendar token refresh test...")
    
    # First test normal calendar operations
    logger.info("Testing normal calendar operations...")
    initial_test = test_calendar_operations()
    
    if not initial_test:
        logger.error("Initial calendar operations test failed. Aborting test.")
        sys.exit(1)
    
    # Simulate an expired token
    logger.info("Simulating an expired token...")
    if not simulate_expired_token():
        logger.error("Failed to simulate expired token. Aborting test.")
        sys.exit(1)
    
    # Try calendar operations again - this should trigger a refresh
    logger.info("Testing calendar operations with expired token...")
    expired_test = test_calendar_operations()
    
    # Test manual token refresh
    logger.info("Testing manual token refresh function...")
    manual_refresh = test_manual_token_refresh()
    
    # Restore the original token
    logger.info("Restoring token backup...")
    restore_token_backup()
    
    # Report results
    logger.info("\n----- TEST RESULTS -----")
    logger.info(f"Initial calendar operations: {'✅ PASSED' if initial_test else '❌ FAILED'}")
    logger.info(f"Calendar operations with expired token: {'✅ PASSED' if expired_test else '❌ FAILED'}")
    logger.info(f"Manual token refresh: {'✅ PASSED' if manual_refresh else '❌ FAILED'}")
    
    if expired_test and manual_refresh:
        logger.info("✅✅✅ Token refresh mechanism is working correctly! ✅✅✅")
    else:
        logger.info("❌❌❌ Token refresh mechanism needs further investigation ❌❌❌")

if __name__ == "__main__":
    main()