#!/usr/bin/env python3
"""
Example of using the WeatherConnector to fetch weather data.

This script shows how to use the WeatherConnector to get current weather
and forecasts for different cities.

Usage:
    python weather_connector_example.py

Prerequisites:
    - Set OPENWEATHER_API_KEY in your environment variables or .env file
"""

import os
import asyncio
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

# Import the WeatherConnector
from raderbot.tools.weather_connector import WeatherConnector, get_weather, get_forecast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables (make sure OPENWEATHER_API_KEY is set)
load_dotenv()

# List of cities for the example
CITIES = ["London", "New York", "Tokyo", "Sydney", "Paris"]


async def main():
    """Run the weather connector example."""
    logger.info("Starting weather connector example")
    
    # Check if API key is set
    if not os.environ.get("OPENWEATHER_API_KEY"):
        logger.error("OPENWEATHER_API_KEY environment variable is not set.")
        logger.error("Please set it in your .env file or environment.")
        return
    
    # Create weather connector instance
    weather_connector = WeatherConnector()
    
    # Example 1: Get current weather for each city
    logger.info("Example 1: Getting current weather for multiple cities")
    for city in CITIES:
        logger.info(f"Fetching weather for {city}")
        weather_data = await weather_connector.get_weather(city)
        
        if "error" in weather_data:
            logger.error(f"Error fetching weather for {city}: {weather_data['error']}")
        else:
            formatted = weather_connector.format_weather_response(weather_data)
            logger.info(f"Weather for {city}: {formatted}")
        
        # Add a small delay between requests to avoid rate limiting
        await asyncio.sleep(1)
    
    # Example 2: Get forecast for a specific city
    selected_city = "London"
    logger.info(f"Example 2: Getting 3-day forecast for {selected_city}")
    forecast_data = await weather_connector.get_forecast(selected_city, days=3)
    
    if "error" in forecast_data:
        logger.error(f"Error fetching forecast for {selected_city}: {forecast_data['error']}")
    else:
        # Get both summary and detailed forecast
        summary_forecast = weather_connector.format_forecast_response(forecast_data)
        detailed_forecast = weather_connector.format_forecast_response(forecast_data, detailed=True)
        
        logger.info(f"Forecast summary for {selected_city}:")
        logger.info(summary_forecast)
        
        logger.info(f"Detailed forecast for {selected_city}:")
        logger.info(detailed_forecast)
    
    # Example 3: Using the synchronous wrapper functions
    logger.info("Example 3: Using synchronous wrapper functions")
    
    # Get weather for Paris
    sync_city = "Paris"
    logger.info(f"Getting weather for {sync_city} using synchronous function")
    
    weather_result = get_weather(sync_city)
    if "error" in weather_result:
        logger.error(f"Error: {weather_result['error']}")
    else:
        from raderbot.tools.weather_connector import format_weather_response
        formatted = format_weather_response(weather_result)
        logger.info(formatted)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())