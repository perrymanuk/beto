#!/usr/bin/env python3
"""
Test direct invocation of search_home_assistant_entities via agent.

This tests the complete flow from agent to tool invocation.
"""

import os
import sys
import logging
import asyncio
import json
from typing import Dict, Any, Optional

# Add the parent directory to the path so we can import radbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from radbot.tools.mcp_tools import create_find_ha_entities_tool
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

def test_agent_search():
    """Test search_home_assistant_entities through a minimal agent."""
    print("=" * 60)
    print(" Testing Entity Search via ADK Agent ".center(60, "="))
    print("=" * 60)
    
    # Create the search tool
    search_tool = create_find_ha_entities_tool()
    
    if not search_tool:
        print("❌ Failed to create search_home_assistant_entities tool")
        return 1
        
    # Create minimal test agent with just the search tool
    test_agent = Agent(
        name="test_agent",
        model=os.getenv("MAIN_MODEL", "gemini-2.5-flash"),
        instruction="""
        You are a test agent that only uses the search_home_assistant_entities tool.
        When I provide a search term, use the tool to search for Home Assistant entities.
        Just reply with the result information - matches found, entity IDs, etc.
        """,
        tools=[search_tool]
    )
    
    # Create a runner for the agent
    session_service = InMemorySessionService()
    runner = Runner(
        agent=test_agent,
        app_name="search_test",
        session_service=session_service
    )
    
    # Test user messages
    test_messages = [
        "Find entities with 'basement'",
        "Search for 'light' entities",
        "Look for entities in the living room",
        "Search for plant lights"
    ]
    
    # User ID for session
    user_id = "test-user-123"
    
    # Process each test message
    for message in test_messages:
        print(f"\n\nTesting: \"{message}\"")
        print("-" * 60)
        
        try:
            # Run the agent on the message
            events = list(runner.run(user_id=user_id, message=message))
            
            # Process events
            print(f"Got {len(events)} events")
            
            tool_calls_seen = False
            for i, event in enumerate(events):
                event_type = type(event).__name__
                print(f"\nEvent {i}: {event_type}")
                
                # Check for tool calls
                if hasattr(event, 'tool_calls') and event.tool_calls:
                    tool_calls_seen = True
                    for j, call in enumerate(event.tool_calls):
                        print(f"  Tool call {j}: {call.tool_name}")
                        print(f"    Params: {call.parameters}")
                        
                        if call.tool_name == "search_home_assistant_entities":
                            print("    ✅ search_home_assistant_entities was called correctly!")
                        else:
                            print("    ❓ Unexpected tool was called")
                
                # Look for text response
                if hasattr(event, 'message') and event.message:
                    print(f"  Response: {event.message.content[:100]}...")
            
            if not tool_calls_seen:
                print("\n❌ No tool calls were recorded! The agent did not use search_home_assistant_entities")
            
        except Exception as e:
            print(f"\n❌ Error running agent: {str(e)}")
    
    print("\n" + "=" * 60)
    print(" Test complete! ".center(60, "="))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(test_agent_search())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)