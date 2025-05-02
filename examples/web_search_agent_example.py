#!/usr/bin/env python
"""
Example script demonstrating the web search capabilities of radbot.

This example shows how to create and use an agent with Tavily web search integration.
"""

import logging
import os

from dotenv import load_dotenv

from radbot.agent import create_websearch_agent
from radbot.tools.basic_tools import get_current_time, get_weather

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def main():
    """Run the web search agent example."""
    # Check if Tavily API key is set
    if not os.environ.get("TAVILY_API_KEY"):
        logger.warning("TAVILY_API_KEY environment variable not set. Web search will not work properly.")
        logger.warning("Please add your Tavily API key to your .env file or environment variables.")
        logger.warning("You can get a key at https://tavily.com/")

    # Create a radbot agent with web search capabilities and basic tools
    logger.info("Creating web search enabled agent...")
    agent = create_websearch_agent(
        max_results=3,  # Return top 3 search results
        search_depth="advanced",  # Use advanced search depth
        base_tools=[get_current_time, get_weather],  # Add basic tools
    )
    
    logger.info("Agent created successfully.")
    
    # Example queries to demonstrate capabilities
    queries = [
        "What is the capital of France?",
        "What's the weather like in Paris?",
        "What time is it in Tokyo?",
        "Tell me about the latest advancements in AI.",
        "Who won the last World Cup?",
        "What are the top news stories today?",
    ]
    
    # Process each query
    for i, query in enumerate(queries):
        logger.info(f"Processing query {i+1}/{len(queries)}: '{query}'")
        
        # Process the query with the agent
        response = agent.process_message(
            user_id="example_user",  # User ID for session management
            message=query
        )
        
        # Print the response
        print(f"\nQuery: {query}")
        print(f"Response:\n{response}\n")
        print("-" * 80)


if __name__ == "__main__":
    main()