#!/usr/bin/env python3
"""
Test script for weather tool with Los Angeles.

This script tests the updated get_weather function with Los Angeles
to verify that it works correctly.
"""

import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables (including OPENWEATHER_API_KEY if set)
load_dotenv()

def main():
    """Run the weather tool test."""
    logger.info("Testing weather tool with Los Angeles")
    
    # Import the get_weather function from basic_tools
    from raderbot.tools.basic_tools import get_weather
    
    # Test cities
    cities = ["Los Angeles", "New York", "Tokyo", "Paris", "NonExistentCity"]
    
    # Check if OPENWEATHER_API_KEY is set
    if os.environ.get("OPENWEATHER_API_KEY"):
        logger.info("Using real OpenWeatherMap API (OPENWEATHER_API_KEY is set)")
    else:
        logger.warning("Using mock data (OPENWEATHER_API_KEY is not set)")
    
    # Test each city
    for city in cities:
        logger.info(f"Testing weather for: {city}")
        result = get_weather(city)
        logger.info(f"Result: {result}")
        logger.info("-" * 50)
    
    # Test the direct weather connector functions
    logger.info("Testing direct weather connector functions for Los Angeles")
    
    try:
        from raderbot.tools.weather_connector import get_weather as get_real_weather
        from raderbot.tools.weather_connector import format_weather_response
        
        weather_data = get_real_weather("Los Angeles")
        
        if "error" in weather_data:
            logger.error(f"Error from weather connector: {weather_data['error']}")
        else:
            formatted = format_weather_response(weather_data)
            logger.info(f"Weather connector result: {formatted}")
        
    except Exception as e:
        logger.error(f"Error testing direct weather connector: {str(e)}")
    
    logger.info("Weather tool test completed")


if __name__ == "__main__":
    main()