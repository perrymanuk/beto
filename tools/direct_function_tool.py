#!/usr/bin/env python3
"""
Create a direct function tool for search_home_assistant_entities.

This script creates a simple agent with just the search tool to verify it works correctly.
"""

import os
import sys
import logging
import asyncio
import json
from typing import Dict, Any, Optional

# Add the parent directory to the path so we can import raderbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Create and test a direct entity search function tool."""
    print("=" * 60)
    print(" Direct Function Tool Test ".center(60, "="))
    print("=" * 60)
    
    # Import the entity search function
    from raderbot.tools.mcp_utils import find_home_assistant_entities
    
    # Create a direct wrapper function
    def search_home_assistant_entities(search_term: str, domain_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for Home Assistant entities by name.
        
        Args:
            search_term: Term to search for in entity names, like 'kitchen' or 'plant'
            domain_filter: Optional domain type to filter by (light, switch, etc.)
        """
        print(f"[SEARCH CALLED] search_term='{search_term}', domain_filter='{domain_filter}'")
        try:
            result = find_home_assistant_entities(search_term, domain_filter)
            match_count = result.get('match_count', 0)
            print(f"[SEARCH RESULT] Found {match_count} matches")
            
            if match_count > 0:
                for i, match in enumerate(result.get('matches', [])[:3]):
                    print(f"  - {i+1}: {match['entity_id']} (score: {match['score']})")
            
            return result
        except Exception as e:
            print(f"[SEARCH ERROR] {str(e)}")
            return {"success": False, "error": str(e), "matches": []}
    
    # Create the function tool directly
    search_tool_schema = {
        "name": "search_home_assistant_entities",
        "description": "Search for Home Assistant entities by name or area",
        "parameters": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "Term to search for in entity names, like 'kitchen' or 'plant'"
                },
                "domain_filter": {
                    "type": "string",
                    "description": "Optional domain type to filter by (light, switch, etc.)",
                    "enum": ["light", "switch", "sensor", "media_player", "climate", "cover", "vacuum"]
                }
            },
            "required": ["search_term"]
        }
    }
    
    # Create a test agent
    try:
        # Try with the direct function approach first
        print("\nCreating agent with direct function...")
        test_agent = Agent(
            name="entity_search_test_agent",
            model=os.getenv("MAIN_MODEL", "gemini-2.5-flash"),
            instruction="""
            You are a test agent that searches for Home Assistant entities.
            When the user mentions any location or device, use the search_home_assistant_entities function
            to find matching entities. Reply with the entity IDs you find.
            
            CRITICAL: Always follow this workflow:
            1. Use search_home_assistant_entities to find entities
            2. Report the exact entity_ids you found
            """,
            tools=[search_home_assistant_entities]
        )
        print("✅ Created agent with direct function")
    except Exception as e:
        print(f"❌ Error creating agent with direct function: {str(e)}")
        try:
            # Try with FunctionTool instead
            print("\nTrying with FunctionTool...")
            function_tool = FunctionTool(function=search_home_assistant_entities, function_schema=search_tool_schema)
            test_agent = Agent(
                name="entity_search_test_agent",
                model=os.getenv("MAIN_MODEL", "gemini-2.5-flash"),
                instruction="""
                You are a test agent that searches for Home Assistant entities.
                When the user mentions any location or device, use the search_home_assistant_entities function
                to find matching entities. Reply with the entity IDs you find.
                
                CRITICAL: Always follow this workflow:
                1. Use search_home_assistant_entities to find entities
                2. Report the exact entity_ids you found
                """,
                tools=[function_tool]
            )
            print("✅ Created agent with FunctionTool")
        except Exception as e2:
            print(f"❌ Error creating agent with FunctionTool: {str(e2)}")
            return 1
    
    # Create session service and runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=test_agent,
        app_name="entity_search_test",
        session_service=session_service
    )
    
    # Test queries
    test_queries = [
        "Find all basement lights",
        "Search for plant devices",
        "Look for switches in the living room",
        "Find kitchen devices"
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
        sys.exit(1)