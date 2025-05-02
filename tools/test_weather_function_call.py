#!/usr/bin/env python3
"""
Test script for weather function calling.

This script tests the agent's ability to properly make function calls
to the weather tool.
"""

import os
import logging
import uuid
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def setup_test_agent():
    """Set up a test agent with the weather tool."""
    # Import the weather tool
    from raderbot.tools.basic_tools import get_weather, get_current_time
    
    # Create an agent with just the weather tool
    agent = Agent(
        name="weather_test_agent",
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"),
        instruction="""You are a helpful assistant that specializes in providing weather information.
When the user asks about the weather in a particular city, use the get_weather tool to get that information.
Do not describe your process, just get the weather information and respond with it.
Use the tools provided to you to answer the user's questions.""",
        tools=[get_weather, get_current_time]
    )
    
    # Create a runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="weather_test",
        session_service=session_service
    )
    
    return agent, runner

def test_weather_query(runner, query):
    """Test a weather query with the agent."""
    logger.info(f"Testing query: '{query}'")
    
    # Generate a random user ID
    user_id = str(uuid.uuid4())
    
    # Run the agent
    events = list(runner.run(user_id=user_id, message=query))
    
    # Log each event
    for i, event in enumerate(events):
        logger.info(f"Event {i}: {type(event).__name__}")
        
        # Log tool calls
        if hasattr(event, 'tool_calls') and event.tool_calls:
            for call in event.tool_calls:
                logger.info(f"Tool call: {call.tool_name} with params: {call.parameters}")
        
        # Log message content
        if hasattr(event, 'message') and event.message:
            logger.info(f"Message content: {event.message.content}")
            return event.message.content
    
    # Fallback if no response
    return "No response generated"

def main():
    """Run the weather function call test."""
    logger.info("Setting up test agent")
    agent, runner = setup_test_agent()
    
    # Define test queries
    test_queries = [
        "What's the weather in Los Angeles?",
        "Tell me the weather in New York",
        "How's the weather in Tokyo today?",
        "I want to know the weather in Paris",
        "Weather in NonExistentCity please"
    ]
    
    # Run each test query
    for query in test_queries:
        response = test_weather_query(runner, query)
        print(f"\nQuery: {query}")
        print(f"Response: {response}")
        print("-" * 60)
    
    logger.info("Weather function call test completed")

if __name__ == "__main__":
    main()