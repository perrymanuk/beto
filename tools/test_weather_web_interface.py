#!/usr/bin/env python3
"""
Test script for weather function in web interface environment.

This script simulates how the web interface would call the weather function,
running it in an event loop to test if our fix works properly.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import our weather functions
from raderbot.tools.weather_connector import get_weather, format_weather_response
from raderbot.tools.basic_tools import get_weather as basic_get_weather

async def test_weather_in_event_loop():
    """Test the weather function inside an event loop."""
    # Test cities
    cities = ["Los Angeles", "New York", "Tokyo", "Paris"]
    
    for city in cities:
        logger.info(f"Testing weather for {city} using weather_connector.get_weather")
        
        try:
            # Get weather data (this should use the mock data since we're in an event loop)
            weather_data = get_weather(city)
            
            # Format the response
            formatted = format_weather_response(weather_data)
            logger.info(f"Weather for {city}: {formatted}")
            
            # Test our basic_tools.get_weather function too
            logger.info(f"Testing weather for {city} using basic_tools.get_weather")
            
            # Add tool_context parameter as None
            basic_result = basic_get_weather(city, None)
            logger.info(f"Basic weather for {city}: {basic_result}")
        
        except Exception as e:
            logger.error(f"Error getting weather for {city}: {str(e)}")
        
        logger.info("-" * 50)

def main():
    """Run the weather test."""
    logger.info("Starting weather test in event loop")
    
    # Run the async function in an event loop
    asyncio.run(test_weather_in_event_loop())
    
    logger.info("Weather test completed")

if __name__ == "__main__":
    main()