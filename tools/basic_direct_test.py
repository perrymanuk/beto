#!/usr/bin/env python3
"""
Create a simple direct function with just the name and required parameters.

This script creates a simplified version of the search tool to test the basic issue.
"""

import os
import sys
import logging

# Add the parent directory to the path so we can import raderbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Create and test a simplified direct function."""
    print("=" * 60)
    print(" Simplified Function Test ".center(60, "="))
    print("=" * 60)
    
    # Create a very simple function 
    def search_home_assistant_entities(search_term: str, domain_filter: str = None):
        """Search for entities matching the search term."""
        print(f"[SEARCH CALLED] search_term='{search_term}', domain_filter='{domain_filter}'")
        if domain_filter:
            result = f"Entities matching '{search_term}' in domain '{domain_filter}'"
        else:
            result = f"Entities matching '{search_term}' in all domains"
        print(f"[SEARCH RESULT] {result}")
        
        # Return dummy results
        return {
            "success": True,
            "match_count": 3,
            "matches": [
                {"entity_id": f"light.{search_term}_1", "score": 2},
                {"entity_id": f"switch.{search_term}_2", "score": 1},
                {"entity_id": f"light.{search_term}_3", "score": 1}
            ]
        }
    
    # Mark the function explicitly for clarity
    search_home_assistant_entities.__name__ = "search_home_assistant_entities"
    
    # Create a test agent
    try:
        print("\nCreating agent with direct function...")
        test_agent = Agent(
            name="simple_test_agent",
            model=os.getenv("MAIN_MODEL", "gemini-2.5-flash"),
            instruction="""
            You are a test agent that searches for Home Assistant entities.
            When the user mentions any location or device, use the search_home_assistant_entities function 
            to find matching entities.
            
            Always follow this process:
            1. Call search_home_assistant_entities with the search term from the user
            2. Report the entity_ids from the results
            
            Very important: The search_home_assistant_entities function has these parameters:
            - search_term: Required. Term to search for (e.g., "basement", "light")
            - domain_filter: Optional. Type of entity (e.g., "light", "switch")
            """,
            tools=[search_home_assistant_entities]
        )
        print("✅ Created test agent")
        
        # Create runner
        session_service = InMemorySessionService()
        runner = Runner(
            agent=test_agent,
            app_name="simple_test",
            session_service=session_service
        )
        
        # Test queries
        test_queries = [
            "Find all basement lights",
            "Search for plant devices"
        ]
        
        # Test the agent
        user_id = "test_user"
        for query in test_queries:
            print("\n" + "-" * 60)
            print(f"Testing query: \"{query}\"")
            print("-" * 60)
            
            try:
                # Run the agent
                events = list(runner.run(user_id=user_id, message=query))
                
                # Process events
                print(f"Got {len(events)} events")
                
                for i, event in enumerate(events):
                    event_type = type(event).__name__
                    print(f"\nEvent {i+1}: {event_type}")
                    
                    # Log details about the event for debugging
                    if hasattr(event, "error_code") or hasattr(event, "error_message"):
                        print(f"  ERROR: {getattr(event, 'error_code', 'Unknown')} - {getattr(event, 'error_message', 'No message')}")
                    
                    # Print tool calls
                    if hasattr(event, 'tool_calls') and event.tool_calls:
                        for j, call in enumerate(event.tool_calls):
                            print(f"  Tool call {j+1}: {call.tool_name}")
                            print(f"    Parameters: {call.parameters}")
                    
                    # Print agent response
                    if hasattr(event, 'message') and event.message:
                        print(f"\nAgent response:")
                        print(f"  {event.message.content[:500]}")
                        
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