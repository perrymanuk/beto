"""
Unit tests for basic tools.
"""
import pytest
from unittest.mock import MagicMock

from radbot.tools.basic_tools import get_current_time, get_weather


class TestGetCurrentTime:
    def test_get_current_time_success(self):
        """Test successful time retrieval for a known city."""
        result = get_current_time("London")
        assert "The current time in London is" in result
    
    def test_get_current_time_unknown_city(self):
        """Test error handling for an unknown city."""
        result = get_current_time("UnknownCity")
        assert "don't have timezone information" in result
    
    def test_get_current_time_with_context(self):
        """Test that tool_context is used to store last city."""
        mock_context = MagicMock()
        mock_context.state = {}
        
        result = get_current_time("Tokyo", tool_context=mock_context)
        
        assert "The current time in Tokyo is" in result
        assert mock_context.state["last_time_city"] == "Tokyo"


class TestGetWeather:
    def test_get_weather_success(self):
        """Test successful weather retrieval for a known city."""
        result = get_weather("London")
        assert "The current weather in London is" in result
    
    def test_get_weather_unknown_city(self):
        """Test error handling for an unknown city."""
        result = get_weather("UnknownCity")
        assert "not available at the moment" in result
    
    def test_get_weather_with_context(self):
        """Test that tool_context is used to store last city."""
        mock_context = MagicMock()
        mock_context.state = {}
        
        result = get_weather("Paris", tool_context=mock_context)
        
        assert "The current weather in Paris is" in result
        assert mock_context.state["last_weather_city"] == "Paris"