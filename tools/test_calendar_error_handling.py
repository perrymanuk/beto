#!/usr/bin/env python3
"""Test script for verifying Google Calendar function error handling."""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Run tests to verify the calendar function error handling."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Testing Google Calendar function error handling...")
    
    try:
        # Import the wrapper functions
        from radbot.tools.calendar.calendar_tools import (
            list_calendar_events_wrapper,
            create_calendar_event_wrapper,
            update_calendar_event_wrapper,
            delete_calendar_event_wrapper,
            check_calendar_availability_wrapper,
        )
        logger.info("✅ Successfully imported calendar wrapper functions")
    except ImportError as e:
        logger.error(f"❌ Failed to import calendar wrapper functions: {e}")
        sys.exit(1)
    
    # Test functions with invalid inputs to trigger errors
    
    # Test list_calendar_events_wrapper
    logger.info("\nTesting list_calendar_events_wrapper with invalid calendar_id...")
    result = list_calendar_events_wrapper(calendar_id="nonexistent_calendar")
    logger.info(f"Result: {result}")
    
    # Test create_calendar_event_wrapper with invalid time format
    logger.info("\nTesting create_calendar_event_wrapper with invalid time format...")
    result = create_calendar_event_wrapper(
        summary="Test Event",
        start_time="invalid_time",
        end_time="invalid_time",
    )
    logger.info(f"Result: {result}")
    
    # Test update_calendar_event_wrapper with invalid event ID
    logger.info("\nTesting update_calendar_event_wrapper with invalid event ID...")
    result = update_calendar_event_wrapper(
        event_id="nonexistent_event",
        summary="Updated Event",
    )
    logger.info(f"Result: {result}")
    
    # Test delete_calendar_event_wrapper with invalid event ID
    logger.info("\nTesting delete_calendar_event_wrapper with invalid event ID...")
    result = delete_calendar_event_wrapper(
        event_id="nonexistent_event",
    )
    logger.info(f"Result: {result}")
    
    # Test check_calendar_availability_wrapper with invalid calendar IDs
    logger.info("\nTesting check_calendar_availability_wrapper with invalid calendar IDs...")
    result = check_calendar_availability_wrapper(
        calendar_ids=["nonexistent_calendar"],
    )
    logger.info(f"Result: {result}")
    
    logger.info("\nAll error handling tests completed successfully!")
    logger.info("The wrapper functions should handle errors gracefully without raising exceptions.")

if __name__ == "__main__":
    main()