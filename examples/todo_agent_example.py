#!/usr/bin/env python3
"""
Example script demonstrating the use of the Todo Tool with PostgreSQL persistence.

This script creates a Todo Agent and uses the ADK Runner for interaction.
Make sure to set up the PostgreSQL database and required environment variables
before running this example.
"""

import os
import sys
import uuid
import logging
from dotenv import load_dotenv

# Add the project root to the Python path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from radbot.agent.todo_agent_factory import create_todo_agent
from radbot.agent import create_runner

def main():
    """Run the Todo Agent example."""
    logger.info("Creating Todo Agent...")
    
    # Create the Todo Agent
    agent = create_todo_agent(name="todo_example_agent")
    
    # Create a runner for the agent
    runner = create_runner(agent)
    
    # Example project name for demonstration
    example_project = "home"
    logger.info(f"Example project: {example_project}")
    
    print("\n" + "="*80)
    print("Todo Agent Example")
    print("="*80)
    print("\nThis example demonstrates using the todo agent with PostgreSQL persistence.")
    print("You can try commands like:")
    print(f"  - Add a task to project {example_project}")
    print("  - List all my tasks")
    print("  - Show me all my projects")
    print("  - Mark task XYZ as complete")
    print("  - Remove task XYZ")
    print("\nType 'exit' or 'quit' to end the session.\n")
    
    # Interactive session with the agent
    try:
        while True:
            user_input = input("You: ")
            
            if user_input.lower() in ['exit', 'quit']:
                print("Exiting todo agent example.")
                break
                
            response = runner.run(user_input)
            print(f"Agent: {response.response}")
            
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt.")
    except Exception as e:
        logger.error(f"Error during agent interaction: {str(e)}")
        
    print("\nTodo Agent example completed.")

if __name__ == "__main__":
    main()
