"""
Example of using a memory-enabled agent.

This example demonstrates how to create and use an agent with memory capabilities.
"""

import os
import uuid
from dotenv import load_dotenv

from raderbot.tools.basic_tools import get_current_time, get_weather
from raderbot.agent.memory_agent_factory import create_memory_enabled_agent

# Load environment variables
load_dotenv()

def main():
    """Run the memory agent example."""
    print("Initializing memory-enabled agent...")
    
    # Create a memory-enabled agent with basic tools
    agent = create_memory_enabled_agent(
        tools=[get_current_time, get_weather],
        name="memory_agent",
        instruction_name="main_agent"
    )
    
    print("Agent initialized.")
    print("Type 'exit' to quit.")
    print("=" * 50)
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    # Start interactive loop
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == "exit":
            print("Exiting...")
            break
        
        # Process the message and get response
        response = agent.process_message(session_id, user_input)
        
        # Display the response
        print(f"\nAgent: {response}")
    
if __name__ == "__main__":
    main()