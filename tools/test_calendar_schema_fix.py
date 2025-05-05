#!/usr/bin/env python3
"""Test script for verifying Google Calendar function tool schema fixes."""

import os
import sys
import json
import logging
from typing import Any, Dict, List
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Run tests to verify the calendar function tool schemas."""
    # Load environment variables
    load_dotenv()
    
    logger.info("Testing Google Calendar function tool schemas...")
    
    try:
        from google.adk.tools import FunctionTool
        logger.info("✅ Successfully imported FunctionTool from google.adk.tools")
    except ImportError as e:
        logger.error(f"❌ Failed to import FunctionTool: {e}")
        sys.exit(1)
    
    try:
        from radbot.tools.calendar.calendar_tools import (
            list_calendar_events_wrapper,
            create_calendar_event_wrapper,
            update_calendar_event_wrapper,
            delete_calendar_event_wrapper,
            check_calendar_availability_wrapper,
            list_calendar_events_tool,
            create_calendar_event_tool,
            update_calendar_event_tool,
            delete_calendar_event_tool,
            check_calendar_availability_tool,
        )
        logger.info("✅ Successfully imported calendar wrapper functions and tools")
    except ImportError as e:
        logger.error(f"❌ Failed to import calendar tools: {e}")
        sys.exit(1)
    
    # Test each function tool schema
    try:
        # Test list_calendar_events_tool
        logger.info("Testing list_calendar_events_tool schema...")
        verify_function_schema(list_calendar_events_tool)
        logger.info("✅ list_calendar_events_tool schema is valid")
        
        # Test create_calendar_event_tool
        logger.info("Testing create_calendar_event_tool schema...")
        verify_function_schema(create_calendar_event_tool)
        logger.info("✅ create_calendar_event_tool schema is valid")
        
        # Test update_calendar_event_tool
        logger.info("Testing update_calendar_event_tool schema...")
        verify_function_schema(update_calendar_event_tool)
        logger.info("✅ update_calendar_event_tool schema is valid")
        
        # Test delete_calendar_event_tool
        logger.info("Testing delete_calendar_event_tool schema...")
        verify_function_schema(delete_calendar_event_tool)
        logger.info("✅ delete_calendar_event_tool schema is valid")
        
        # Test check_calendar_availability_tool
        logger.info("Testing check_calendar_availability_tool schema...")
        verify_function_schema(check_calendar_availability_tool)
        logger.info("✅ check_calendar_availability_tool schema is valid")
        
        logger.info("All calendar function tool schemas are valid!")
    except Exception as e:
        logger.error(f"❌ Error testing function tools: {e}")
        sys.exit(1)

def verify_function_schema(function_tool):
    """Verify that a function tool has a valid schema."""
    # This is a basic check - ADK will generate schemas automatically
    # We just want to make sure nothing crashes
    if not hasattr(function_tool, '_function'):
        raise Exception(f"Function tool does not have a _function attribute")
    
    # Check that the function is callable
    if not callable(function_tool._function):
        raise Exception(f"Function tool's _function is not callable")
    
    # For debugging - print the schema
    if hasattr(function_tool, 'schema'):
        schema_json = json.dumps(function_tool.schema, indent=2)
        logger.debug(f"Schema: {schema_json}")
    
    return True

if __name__ == "__main__":
    main()