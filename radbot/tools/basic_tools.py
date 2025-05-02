"""
Basic tools for radbot agents.

This module implements simple tools like time and weather services.
"""
import datetime
from typing import Dict, Optional
from zoneinfo import ZoneInfo

from google.adk.tools.tool_context import ToolContext

# Import the tool decorator if available (for ADK >=0.3.0)
try:
    from google.adk.tools.decorators import tool
    HAVE_TOOL_DECORATOR = True
except ImportError:
    HAVE_TOOL_DECORATOR = False
    # Create a no-op decorator for compatibility
    def tool(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


@tool(
    name="get_current_time",
    description="Get the current time for a specified city or timezone",
    parameters={
        "city": {
            "type": "string",
            "description": "The city name (e.g., 'New York', 'London'). Defaults to UTC if not specified.",
            "default": "UTC"
        }
    }
)
def get_current_time(city: str = "UTC", tool_context: Optional[ToolContext] = None) -> str:
    """
    Gets the current time for a specified city or defaults to UTC.

    Use this tool when the user asks for the current time.

    Args:
        city: The city name (e.g., 'New York', 'London'). Defaults to UTC if not specified.
        tool_context: Tool context for accessing session state.

    Returns:
        A string with the current time information or error message.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"get_current_time tool called with city: {city}")
    
    # Example mapping, expand as needed
    tz_map = {
        "new york": "America/New_York",
        "london": "Europe/London",
        "tokyo": "Asia/Tokyo",
        "paris": "Europe/Paris",
        "sydney": "Australia/Sydney",
        "los angeles": "America/Los_Angeles",
        "utc": "UTC"
    }
    tz_identifier = tz_map.get(city.lower())

    if not tz_identifier:
        result = f"Sorry, I don't have timezone information for {city}."
        logger.warning(f"No timezone found for {city}")
        return result

    try:
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        report = f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
        
        # Optionally save something to state if tool_context is provided
        if tool_context:
            tool_context.state['last_time_city'] = city
        
        logger.info(f"Returning time for {city}: {report}")
        return report
    except Exception as e:
        error_msg = f"An error occurred while fetching the time for {city}: {str(e)}"
        logger.error(f"Error in get_current_time: {error_msg}")
        return error_msg


@tool(
    name="get_weather",
    description="Get current weather information for a specified city",
    parameters={
        "city": {
            "type": "string",
            "description": "The name of the city for the weather report (e.g., 'Los Angeles', 'New York', 'Tokyo')"
        }
    },
    required=["city"]
)
def get_weather(city: str, tool_context: Optional[ToolContext] = None) -> str:
    """
    Retrieves weather information for a specified city using OpenWeatherMap API.

    Use this tool when the user asks about the weather.

    Args:
        city: The name of the city for the weather report.
        tool_context: Tool context for accessing session state.

    Returns:
        A string with the weather information or error message.
    """
    import os
    import logging
    from dotenv import load_dotenv
    from radbot.tools.weather_connector import get_weather as get_real_weather
    from radbot.tools.weather_connector import format_weather_response
    
    logger = logging.getLogger(__name__)
    logger.info(f"get_weather tool called with city: {city}")
    
    # Load environment variables to get the API key
    load_dotenv()
    
    # Check if API key is set
    if not os.environ.get("OPENWEATHER_API_KEY"):
        logger.warning("OPENWEATHER_API_KEY not set, using mock data")
        # Fall back to mock data if API key is not available
        mock_weather = {
            "london": "cloudy with a chance of rain, 18°C",
            "new york": "sunny and warm, 25°C",
            "tokyo": "heavy rain, 16°C",
            "paris": "partly cloudy, 20°C",
            "sydney": "clear skies, 22°C",
            "los angeles": "sunny and clear, 28°C"
        }
        report = mock_weather.get(city.lower())

        if report:
            # Optionally save to state if tool_context is provided
            if tool_context:
                tool_context.state['last_weather_city'] = city
            result = f"The current weather in {city} is {report}. (mock data)"
            logger.info(f"Returning mock data result: {result}")
            return result
        else:
            result = f"Weather information for '{city}' is not available at the moment. (no API key)"
            logger.info(f"Returning no data result: {result}")
            return result
    
    try:
        # Get real weather data from OpenWeatherMap API
        logger.info(f"Calling OpenWeatherMap API for {city}")
        weather_data = get_real_weather(city)
        
        # Check for errors
        if "error" in weather_data:
            result = f"Weather information for '{city}' could not be retrieved: {weather_data['error']}"
            logger.warning(f"Weather API error: {result}")
            return result
        
        # Format the weather data into a human-readable response
        response = format_weather_response(weather_data)
        
        # Optionally save to state if tool_context is provided
        if tool_context:
            tool_context.state['last_weather_city'] = city
        
        logger.info(f"Returning weather result: {response}")
        return response
    except Exception as e:
        # If anything goes wrong, return a friendly error message
        error_msg = f"Weather information for '{city}' could not be retrieved due to an error: {str(e)}"
        logger.error(f"Exception in get_weather: {error_msg}")
        return error_msg