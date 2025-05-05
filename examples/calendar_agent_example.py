#!/usr/bin/env python3
"""Example demonstrating Google Calendar integration with radbot."""

import asyncio
import datetime
import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv

from radbot.agent.calendar_agent_factory import create_calendar_agent
from radbot.tools.calendar.calendar_manager import CalendarManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_calendar_demo():
    """Run the calendar integration demo."""
    # Load environment variables
    load_dotenv()
    
    # Create a calendar manager
    calendar_manager = CalendarManager()
    
    # Authenticate with personal Google account
    logger.info("Authenticating with personal Google account...")
    personal_auth_success = calendar_manager.authenticate_personal()
    
    if not personal_auth_success:
        logger.error("Failed to authenticate with personal Google account")
        logger.info("Make sure you have set up credentials.json in the credentials directory")
        return
    
    logger.info("Authentication successful!")
    
    # List upcoming events
    logger.info("Fetching upcoming events...")
    upcoming_events = calendar_manager.list_upcoming_events(max_results=5)
    
    if isinstance(upcoming_events, list):
        if upcoming_events:
            logger.info(f"Found {len(upcoming_events)} upcoming events:")
            for event in upcoming_events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                logger.info(f"- {start}: {event.get('summary', 'No title')}")
        else:
            logger.info("No upcoming events found")
    else:
        logger.error(f"Error fetching events: {upcoming_events.get('error')}")
    
    # Create a new test event
    logger.info("Creating a test event...")
    
    # Event starts tomorrow at 10:00 AM
    start_time = datetime.datetime.now() + datetime.timedelta(days=1)
    start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # Event ends 1 hour later
    end_time = start_time + datetime.timedelta(hours=1)
    
    new_event = calendar_manager.create_new_event(
        summary="Radbot Calendar Test Event",
        start_time=start_time,
        end_time=end_time,
        description="This is a test event created by the radbot calendar integration example",
        location="Virtual",
    )
    
    if "error" not in new_event:
        event_id = new_event["id"]
        logger.info(f"Event created successfully! ID: {event_id}")
        
        # Update the event
        logger.info("Updating the event...")
        updated_event = calendar_manager.update_existing_event(
            event_id,
            summary="Updated Radbot Calendar Test Event",
            description="This event was updated by the radbot calendar integration example",
        )
        
        if "error" not in updated_event:
            logger.info("Event updated successfully!")
            
            # Delete the event
            logger.info("Deleting the event...")
            delete_result = calendar_manager.delete_existing_event(event_id)
            
            if delete_result.get("success"):
                logger.info("Event deleted successfully!")
            else:
                logger.error(f"Failed to delete event: {delete_result.get('error')}")
        else:
            logger.error(f"Failed to update event: {updated_event.get('error')}")
    else:
        logger.error(f"Failed to create event: {new_event.get('error')}")
    
    # Check calendar availability
    logger.info("Checking calendar availability for the next 7 days...")
    time_min = datetime.datetime.utcnow()
    time_max = time_min + datetime.timedelta(days=7)
    
    availability = calendar_manager.get_calendar_busy_times(
        calendar_ids=["primary"],
        time_min=time_min,
        time_max=time_max,
    )
    
    if "error" not in availability:
        calendars = availability.get("calendars", {})
        for calendar_id, calendar_info in calendars.items():
            busy_times = calendar_info.get("busy", [])
            if busy_times:
                logger.info(f"Found {len(busy_times)} busy time slots for calendar {calendar_id}:")
                for busy in busy_times:
                    start = busy.get("start")
                    end = busy.get("end")
                    logger.info(f"- Busy from {start} to {end}")
            else:
                logger.info(f"No busy time slots found for calendar {calendar_id}")
    else:
        logger.error(f"Failed to get availability: {availability.get('error')}")
    
    # Create and run a radbot agent with calendar tools
    logger.info("Creating a radbot agent with calendar tools...")
    agent = create_calendar_agent(calendar_manager=calendar_manager)
    
    # Run a simple conversation with the agent
    logger.info("Running a conversation with the agent...")
    
    # Create a simple prompt about calendars
    prompt = "What can you tell me about my calendar? What events do I have coming up?"
    
    logger.info(f"User: {prompt}")
    
    # The process_message method returns a Message object with a text attribute
    response = await agent.process_message(prompt)
    
    # Get the text from the response
    response_text = getattr(response, 'text', str(response))
    logger.info(f"Agent: {response_text}")


if __name__ == "__main__":
    asyncio.run(run_calendar_demo())