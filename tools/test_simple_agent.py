#!/usr/bin/env python3
"""
Create a minimal test agent with basic tools.

This script tests a barebones agent with simple tools to validate functionality.
"""

import os
import sys
import logging
import json

# Add the parent directory to the path so we can import radbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_time() -> str:
    """Get the current time."""
    import datetime
    return datetime.datetime.now().strftime("%H:%M:%S")

def search_entities(text: str) -> dict:
    """
    Search for entities matching the search text.
    
    Args:
        text: Text to search for
    
    Returns:
        Dictionary with matching entities
    """
    print(f"Search called with: {text}")
    
    # Create dummy results based on the search text
    results = []
    if "basement" in text.lower():
        results.append({"entity_id": "light.basement_main", "score": 2})
        results.append({"entity_id": "light.basement_corner", "score": 2})
    if "plant" in text.lower():
        results.append({"entity_id": "light.plant_light", "score": 2})
        results.append({"entity_id": "switch.plant_watering", "score": 1})
    if "lamp" in text.lower() or "light" in text.lower():
        results.append({"entity_id": "light.living_room", "score": 1})
        results.append({"entity_id": "light.bedroom", "score": 1})
    
    # Return formatted results
    return {
        "success": True,
        "match_count": len(results),
        "matches": results
    }

def turn_off_entity(entity_id: str) -> dict:
    """
    Turn off a Home Assistant entity.
    
    Args:
        entity_id: The entity ID to turn off
        
    Returns:
        Success status
    """
    print(f"Turn off called with entity_id: {entity_id}")
    return {"success": True, "entity_id": entity_id, "state": "off"}

def main():
    """Create and run a minimal test agent."""
    print("=" * 60)
    print(" Simple Test Agent ".center(60, "="))
    print("=" * 60)
    
    # Create a test agent with basic tools
    try:
        # Create the agent with our simple tools
        agent = Agent(
            name="simple_test_agent",
            model=os.getenv("MAIN_MODEL", "gemini-2.5-flash"),
            instruction="""
            You are a test agent that can search for entities and control them.
            
            When asked to turn on/off devices, follow this workflow:
            1. First use search_entities to find matching entities
            2. Then use turn_off_entity to turn off the entity
            
            The search_entities function takes one parameter:
            - text: Text to search for entities (e.g., "basement plant")
            
            The turn_off_entity function takes one parameter:
            - entity_id: The ID of the entity to turn off (e.g., "light.basement_main")
            """,
            tools=[get_time, search_entities, turn_off_entity]
        )
        print("✅ Created simple test agent")
        
        # Set up session and runner
        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name="simple_test",
            session_service=session_service
        )
        
        # Test messages
        test_messages = [
            "What time is it?",
            "Turn off the basement plant lamp"
        ]
        
        # Process each message
        user_id = "test_user"
        
        for message in test_messages:
            print("\n" + "=" * 60)
            print(f"Testing: \"{message}\"")
            print("=" * 60)
            
            try:
                # Run the agent
                events = list(runner.run(user_id=user_id, message=message))
                
                # Print events
                print(f"Received {len(events)} events")
                
                for i, event in enumerate(events):
                    print(f"\nEvent {i+1}: {type(event).__name__}")
                    
                    # Print error info
                    if hasattr(event, 'error_code') or hasattr(event, 'error_message'):
                        print(f"  Error: {getattr(event, 'error_code', 'Unknown')} - {getattr(event, 'error_message', 'No message')}")
                    
                    # Print tool calls
                    if hasattr(event, 'tool_calls') and event.tool_calls:
                        for j, call in enumerate(event.tool_calls):
                            print(f"  Tool call {j+1}: {call.tool_name}")
                            print(f"    Parameters: {call.parameters}")
                    
                    # Print message content
                    if hasattr(event, 'message') and event.message:
                        print(f"\n  Message: {event.message.content[:500]}")
                        
            except Exception as e:
                print(f"❌ Error running agent: {str(e)}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error creating agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    print(" Test complete! ".center(60, "="))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)