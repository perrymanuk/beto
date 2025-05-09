#!/usr/bin/env python3
"""
Example of using the Axel specialized agent directly.

This example demonstrates how to create and use the Axel agent
for implementation and execution tasks.
"""

import logging
import os
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import radbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Axel agent implementation
from radbot.agent.specialized.axel import AxelAgent

def main():
    """Run the Axel agent example."""
    logger.info("Creating Axel agent...")
    
    # Create the Axel agent
    axel = AxelAgent.create_axel_agent(
        name="axel_agent",
        register_with_transfer_controller=True
    )
    
    # Use the agent directly
    task = "Create a Python function that generates Fibonacci numbers up to a given limit."
    logger.info(f"Asking Axel to implement: {task}")
    
    # Run the agent
    response = axel(task)
    
    # Display the response
    logger.info("Axel's response:")
    print("=" * 80)
    print(response)
    print("=" * 80)
    
    # Create a worker agent
    logger.info("Creating worker agent...")
    worker = AxelAgent.create_worker_agent(
        index=0,
        parent_agent=axel,
        task_description="Worker agent for implementing a specific component"
    )
    
    # Use the worker agent
    worker_task = "Create a Python function to check if a number is prime."
    logger.info(f"Asking worker to implement: {worker_task}")
    
    # Run the worker agent
    worker_response = worker(worker_task)
    
    # Display the worker response
    logger.info("Worker's response:")
    print("=" * 80)
    print(worker_response)
    print("=" * 80)
    
    logger.info("Axel agent example completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())