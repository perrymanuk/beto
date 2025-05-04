# Basic Tools Implementation

This document details the implementation of basic tools for the radbot agent framework, specifically the time and weather tools.

## Tool Design Principles

Our tool implementations follow these key principles:

1. **Type Hints**: All tools use precise Python type hints for parameters and return values.
2. **Descriptive Docstrings**: Tools have comprehensive docstrings explaining their purpose, usage, parameters, and return values.
3. **Consistent Error Handling**: Tools return structured dictionaries with status information and error messages.
4. **Modularity**: Each tool is implemented as a standalone function that can be tested independently.

## Basic Tools Module (`tools/basic/basic_tools.py`)

```python
# radbot/tools/basic/basic_tools.py

"""
Basic utility tools for the radbot agent framework.

Includes tools for fetching the current time and weather information.
"""

import datetime
from typing import Dict, Optional, Any
import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

def get_current_time(city: str = "UTC", tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Gets the current time for a specified city or defaults to UTC.

    Use this tool when the user asks for the current time.

    Args:
        city (str): The city name (e.g., 'New York', 'London'). Defaults to UTC if not specified or unknown.
        tool_context (ToolContext, optional): Tool context for accessing session state.

    Returns:
        dict: A dictionary containing:
              'status' (str): 'success' or 'error'.
              'report' (str, optional): The current time string if successful.
              'error_message' (str, optional): Description of the error if failed.
    """
    # Mapping of common city names to timezone identifiers
    # This could be expanded or moved to a configuration file
    tz_map = {
        "new york": "America/New_York",
        "los angeles": "America/Los_Angeles",
        "chicago": "America/Chicago",
        "london": "Europe/London",
        "paris": "Europe/Paris",
        "berlin": "Europe/Berlin",
        "tokyo": "Asia/Tokyo",
        "sydney": "Australia/Sydney",
        "melbourne": "Australia/Melbourne",
        "auckland": "Pacific/Auckland",
        "utc": "UTC"
    }
    
    # Normalize city name and look up timezone
    normalized_city = city.lower()
    tz_identifier = tz_map.get(normalized_city)
    
    if not tz_identifier:
        logger.info(f"Timezone not found for city: {city}")
        return {"status": "error", "error_message": f"Sorry, I don't have timezone information for {city}."}
    
    try:
        # Get the timezone and current time
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        
        # Format the time report
        report = f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
        
        # Optionally store information in session state
        if tool_context:
            tool_context.state['last_time_city'] = city
            
        return {"status": "success", "report": report}
    
    except ZoneInfoNotFoundError as e:
        logger.error(f"ZoneInfo error for {tz_identifier}: {str(e)}")
        return {"status": "error", "error_message": f"An error occurred with the timezone information for {city}."}
    
    except Exception as e:
        logger.error(f"Unexpected error in get_current_time: {str(e)}")
        return {"status": "error", "error_message": f"An unexpected error occurred while fetching the time for {city}."}


def get_weather(city: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Retrieves a simulated weather report for a specified city.
    
    Note: This is a mock implementation. In a production environment, this would
    connect to a real weather API service.

    Use this tool when the user asks about the weather.

    Args:
        city (str): The name of the city for the weather report.
        tool_context (ToolContext, optional): Tool context for accessing session state.

    Returns:
        dict: A dictionary containing:
              'status' (str): 'success' or 'error'.
              'report' (str, optional): The weather report if successful.
              'error_message' (str, optional): Description of the error if failed.
    """
    # Mock weather data - in a real implementation, this would be an API call
    mock_weather = {
        "london": {"condition": "cloudy with a chance of rain", "temperature": 18},
        "new york": {"condition": "sunny and warm", "temperature": 25},
        "tokyo": {"condition": "heavy rain", "temperature": 16},
        "paris": {"condition": "partly cloudy", "temperature": 20},
        "sydney": {"condition": "clear and sunny", "temperature": 28},
        "san francisco": {"condition": "foggy", "temperature": 15},
        "berlin": {"condition": "overcast", "temperature": 17},
        "mumbai": {"condition": "hot and humid", "temperature": 32},
        "rio de janeiro": {"condition": "sunny and hot", "temperature": 30},
        "cairo": {"condition": "hot and dry", "temperature": 35}
    }
    
    try:
        # Normalize city name and get weather data
        normalized_city = city.lower()
        weather_data = mock_weather.get(normalized_city)
        
        if weather_data:
            report = f"The current weather in {city} is {weather_data['condition']}, {weather_data['temperature']}°C."
            
            # Optionally store information in session state
            if tool_context:
                tool_context.state['last_weather_city'] = city
                
            return {"status": "success", "report": report}
        else:
            logger.info(f"Weather data not available for city: {city}")
            return {"status": "error", "error_message": f"Weather information for '{city}' is not available at the moment."}
    
    except Exception as e:
        logger.error(f"Error in get_weather: {str(e)}")
        return {"status": "error", "error_message": f"An error occurred while fetching the weather for {city}."}


# Additional utility functions could be added here
def celsius_to_fahrenheit(celsius: float) -> float:
    """
    Convert temperature from Celsius to Fahrenheit.
    
    Args:
        celsius (float): Temperature in Celsius
        
    Returns:
        float: Temperature in Fahrenheit
    """
    return (celsius * 9/5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """
    Convert temperature from Fahrenheit to Celsius.
    
    Args:
        fahrenheit (float): Temperature in Fahrenheit
        
    Returns:
        float: Temperature in Celsius
    """
    return (fahrenheit - 32) * 5/9
```

## Package Initialization (`tools/__init__.py`)

```python
# radbot/tools/__init__.py

"""
Tools package for the radbot agent framework.
"""

from radbot.tools.basic import get_current_time, get_weather

# Export the tools for easy import
__all__ = ['get_current_time', 'get_weather']
```

## Integration with Agent Framework

To register these tools with the agent:

```python
# radbot/tools/register_tools.py

"""
Tool registration functions for the radbot agent framework.
"""

from typing import List, Any

from radbot.tools.basic import get_current_time, get_weather
from radbot.agent import radbotAgent

def register_basic_tools(agent: radbotAgent) -> None:
    """
    Register the basic tools with the radbot agent.
    
    Args:
        agent (radbotAgent): The agent to register tools with
    """
    agent.add_tools([get_current_time, get_weather])


def get_all_basic_tools() -> List[Any]:
    """
    Get all basic tools as a list.
    
    Returns:
        List of basic tool functions
    """
    return [get_current_time, get_weather]
```

## Example Usage in Agent Creation

```python
# Example of creating an agent with basic tools

from radbot.agent import create_agent
from radbot.tools import get_current_time, get_weather

# Create an agent with basic tools
agent = create_agent(tools=[get_current_time, get_weather])

# Alternatively, use the registration function
from radbot.tools.register_tools import register_basic_tools
agent = create_agent()
register_basic_tools(agent)
```

## Real-World Weather API Integration

In a production implementation, the mock weather data would be replaced with a call to a real weather API. Here's how that might look:

```python
# Example of a real weather API implementation (not included in actual code)

import requests
import os
from dotenv import load_dotenv

# Load environment variables for API keys
load_dotenv()

def get_real_weather(city: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Retrieves actual weather data from a weather API service.

    Args:
        city (str): The name of the city for the weather report.
        tool_context (ToolContext, optional): Tool context for accessing session state.

    Returns:
        dict: Weather status and report.
    """
    try:
        # Get API key from environment variables
        api_key = os.getenv("WEATHER_API_KEY")
        
        if not api_key:
            logger.error("Weather API key not found in environment variables")
            return {"status": "error", "error_message": "Weather service is not properly configured."}
            
        # Make API request (example using OpenWeatherMap)
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": api_key,
                "units": "metric"  # Use metric for Celsius
            },
            timeout=5  # Timeout after 5 seconds
        )
        
        # Check response status
        response.raise_for_status()
        
        # Parse JSON response
        weather_data = response.json()
        
        # Extract relevant information
        temperature = weather_data["main"]["temp"]
        condition = weather_data["weather"][0]["description"]
        
        # Format the response
        report = f"The current weather in {city} is {condition}, {temperature}°C."
        
        # Optionally store in session state
        if tool_context:
            tool_context.state['last_weather_city'] = city
            tool_context.state['last_weather_data'] = {
                'temperature': temperature,
                'condition': condition,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
        return {"status": "success", "report": report}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        return {"status": "error", "error_message": f"Could not fetch weather data for {city} due to a connection error."}
        
    except KeyError as e:
        logger.error(f"Unexpected API response format: {str(e)}")
        return {"status": "error", "error_message": f"The weather service returned unexpected data format for {city}."}
        
    except Exception as e:
        logger.error(f"Unexpected error in get_real_weather: {str(e)}")
        return {"status": "error", "error_message": f"An unexpected error occurred while fetching the weather for {city}."}
```

## Testing the Tools

Unit tests should be created to verify the tool functionality:

```python
# tests/test_basic_tools.py (outline)

import unittest
from unittest.mock import MagicMock
from radbot.tools.basic import get_current_time, get_weather

class TestBasicTools(unittest.TestCase):
    def test_get_current_time_success(self):
        # Test successful time retrieval
        result = get_current_time("London")
        self.assertEqual(result["status"], "success")
        self.assertIn("London", result["report"])
    
    def test_get_current_time_unknown_city(self):
        # Test with unknown city
        result = get_current_time("UnknownCity")
        self.assertEqual(result["status"], "error")
        self.assertIn("UnknownCity", result["error_message"])
    
    def test_get_weather_success(self):
        # Test successful weather retrieval
        result = get_weather("London")
        self.assertEqual(result["status"], "success")
        self.assertIn("London", result["report"])
    
    def test_get_weather_unknown_city(self):
        # Test with unknown city
        result = get_weather("UnknownCity")
        self.assertEqual(result["status"], "error")
        self.assertIn("UnknownCity", result["error_message"])

    def test_tool_context_integration(self):
        # Test that tool context state is updated
        mock_context = MagicMock()
        mock_context.state = {}
        
        get_current_time("London", mock_context)
        self.assertEqual(mock_context.state["last_time_city"], "London")
        
        get_weather("Paris", mock_context)
        self.assertEqual(mock_context.state["last_weather_city"], "Paris")
```

## Next Steps

With the basic tools implemented, the next steps are:

1. Implement the Qdrant memory system for persistent agent memory
2. Design the inter-agent communication strategy
3. Set up MCP integration for Home Assistant