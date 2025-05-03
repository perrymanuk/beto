#!/usr/bin/env python3
"""
Example script demonstrating the enhanced memory system.

This script creates an agent with the enhanced memory system and
processes example messages with different memory triggers.
"""

import os
import sys
import logging
from typing import Dict, Any

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from radbot.agent.enhanced_memory_agent_factory import create_enhanced_memory_agent
from radbot.memory.enhanced_memory import get_memory_detector, create_enhanced_memory_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Load environment variables
load_dotenv()


def print_separator():
    """Print a separator line for readability."""
    print("\n" + "=" * 80 + "\n")


def process_example_message(agent, user_id: str, message: str):
    """
    Process an example message and print the results.
    
    Args:
        agent: The agent to process the message
        user_id: User identifier
        message: Message to process
    """
    print(f"User: {message}")
    
    # Get the memory detector analysis before processing
    memory_detector = agent.memory_manager.memory_detector
    analysis = memory_detector.analyze_message(message)
    
    if analysis['memory_type']:
        print(f"\nDetected Memory Trigger:")
        print(f"  Memory Type: {analysis['memory_type']}")
        print(f"  Trigger Word: {analysis['trigger_word']}")
        if analysis.get('custom_tags'):
            print(f"  Custom Tags: {', '.join(analysis['custom_tags'])}")
        print(f"  Reference Type: {analysis['reference_type']}")
        
        # Extract the information text
        information = memory_detector.extract_information_text(
            message, analysis, agent.memory_manager.conversation_history
        )
        print(f"\nExtracted Information:")
        print(f"  {information}")
    
    # Process the message with the agent
    response = agent.process_message(user_id, message)
    
    print(f"\nAgent: {response}")
    print_separator()


def main():
    """Main example function."""
    print("Enhanced Memory System Example")
    print_separator()
    
    # Create an enhanced memory agent
    agent = create_enhanced_memory_agent(
        name="memory_example_agent",
        instruction_name="main_agent"
    )
    
    # Define a test user ID
    user_id = "example_user"
    
    # Example 1: Regular message (no memory trigger)
    regular_message = "Hello! How are you today?"
    process_example_message(agent, user_id, regular_message)
    
    # Example 2: Memory trigger with custom tag
    memory_message = "we designed a new feature for the app yesterday #beto_feature #beto_design"
    process_example_message(agent, user_id, memory_message)
    
    # Example 3: Important fact trigger
    fact_message = "important: The API key needs to be updated monthly for security reasons"
    process_example_message(agent, user_id, fact_message)
    
    # Example 4: Reference to previous message
    setup_message = "The database password is DB_PASSWORD_123"
    print(f"User: {setup_message}")
    agent.process_message(user_id, setup_message)
    print("Agent: I understand.")
    print_separator()
    
    reference_message = "remember this fact: the previous message contains sensitive information @beto_security"
    process_example_message(agent, user_id, reference_message)
    
    # Example 5: Custom memory detection
    print("Creating a new agent with custom memory triggers...")
    
    # Define custom memory triggers
    custom_memory_triggers = ["document this", "archive this", "take note of this"]
    custom_fact_triggers = ["critical info", "vital detail", "must remember"]
    
    # Create custom memory detector
    custom_agent = create_enhanced_memory_agent(
        name="custom_memory_agent",
        instruction_name="main_agent",
        memory_manager_config={
            "detector_config": {
                "memory_triggers": custom_memory_triggers,
                "fact_triggers": custom_fact_triggers
            }
        }
    )
    
    # Test with custom triggers
    custom_memory_message = "document this: The system architecture follows a microservices pattern #beto_architecture"
    process_example_message(custom_agent, user_id, custom_memory_message)
    
    custom_fact_message = "critical info: Regular backups are scheduled for 2 AM every day"
    process_example_message(custom_agent, user_id, custom_fact_message)
    
    print("Enhanced memory system example completed.")


if __name__ == "__main__":
    main()
