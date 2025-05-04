"""
Unit tests for MCP utilities.

Tests the utility functions for working with Home Assistant MCP.
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from radbot.tools.mcp.mcp_utils import (
    test_home_assistant_connection,
    check_home_assistant_entity,
    list_home_assistant_domains
)
from radbot.tools.mcp.mcp_tools import create_home_assistant_toolset


class TestHomeAssistantConnection:
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    def test_connection_failed_initialization(self, mock_create_toolset):
        """Test handling when toolset initialization fails."""
        # Setup
        mock_create_toolset.return_value = None
        
        # Call function
        result = test_home_assistant_connection()
        
        # Assertions
        assert result["success"] is False
        assert result["status"] == "initialization_failed"
        assert "Failed to create" in result["error"]
        mock_create_toolset.assert_called_once()
    
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    def test_connection_success_with_list_tools(self, mock_create_toolset):
        """Test successful connection using list_tools method."""
        # Setup
        mock_toolset = MagicMock()
        mock_toolset.list_tools.return_value = [
            "home_assistant_mcp.light.turn_on",
            "home_assistant_mcp.sensor.get_state"
        ]
        mock_create_toolset.return_value = mock_toolset
        
        # Call function
        result = test_home_assistant_connection()
        
        # Assertions
        assert result["success"] is True
        assert result["status"] == "connected"
        assert result["tools_count"] == 2
        assert len(result["tools"]) == 2
        mock_toolset.list_tools.assert_called_once()
    
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    @pytest.mark.xfail(reason="Google ADK 0.3.0 compatibility issue")
    def test_connection_success_with_internal_tools(self, mock_create_toolset):
        """Test successful connection using _tools attribute."""
        # Setup for ADK 0.3.0+ compatibility
        mock_toolset = MagicMock()
        type(mock_toolset).list_tools = PropertyMock(side_effect=AttributeError)
        
        # Set up for the _MCPToolset__tools attribute (mangled in Python)
        mock_tools = {
            "home_assistant_mcp.light.turn_on": MagicMock(),
            "home_assistant_mcp.sensor.get_state": MagicMock()
        }
        # Set both old and new attribute patterns
        type(mock_toolset)._tools = PropertyMock(return_value=mock_tools)
        type(mock_toolset)._MCPToolset__tools = PropertyMock(return_value=mock_tools)
        mock_create_toolset.return_value = mock_toolset
        
        # Call function
        result = test_home_assistant_connection()
        
        # Assertions
        assert result["success"] is True
        assert result["status"] == "connected"
        assert result["tools_count"] == 2
        assert len(result["tools"]) == 2
    
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    def test_connection_exception(self, mock_create_toolset):
        """Test handling of exceptions during connection test."""
        # Setup
        mock_toolset = MagicMock()
        mock_toolset.list_tools.side_effect = Exception("Test exception")
        mock_create_toolset.return_value = mock_toolset
        
        # Call function
        result = test_home_assistant_connection()
        
        # Assertions
        assert result["success"] is False
        assert result["status"] == "connection_error"
        assert "Test exception" in result["error"]
        mock_toolset.list_tools.assert_called_once()


class TestCheckHomeAssistantEntity:
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    def test_entity_check_initialization_failed(self, mock_create_toolset):
        """Test handling when toolset initialization fails during entity check."""
        # Setup
        mock_create_toolset.return_value = None
        
        # Call function
        result = check_home_assistant_entity("light.living_room")
        
        # Assertions
        assert result["success"] is False
        assert result["status"] == "initialization_failed"
        mock_create_toolset.assert_called_once()
    
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    def test_entity_check_invalid_id(self, mock_create_toolset):
        """Test handling of invalid entity ID format."""
        # Setup
        mock_toolset = MagicMock()
        mock_create_toolset.return_value = mock_toolset
        
        # Call function with invalid entity ID
        result = check_home_assistant_entity("invalid_entity_id")
        
        # Assertions
        assert result["success"] is False
        assert result["status"] == "invalid_entity_id"
        assert "Invalid entity ID format" in result["error"]
    
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    @pytest.mark.xfail(reason="Google ADK 0.3.0 compatibility issue")
    def test_entity_check_unsupported_domain(self, mock_create_toolset):
        """Test handling when entity domain is not supported."""
        # Setup for ADK 0.3.0+ compatibility
        mock_toolset = MagicMock()
        # Simulate that tool is not available - in any format
        type(mock_toolset)._tools = PropertyMock(return_value={})
        type(mock_toolset)._MCPToolset__tools = PropertyMock(return_value={})
        mock_create_toolset.return_value = mock_toolset
        
        # Call function
        result = check_home_assistant_entity("nonexistent.entity")
        
        # Assertions
        assert result["success"] is False
        assert result["status"] == "unsupported_domain"
        assert "nonexistent" in result["domain"]
        assert "nonexistent.entity" in result["entity_id"]
    
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    def test_entity_check_success(self, mock_create_toolset):
        """Test successful entity check."""
        # Setup
        mock_toolset = MagicMock()
        # Simulate that the tool is available
        type(mock_toolset)._tools = PropertyMock(return_value={
            "home_assistant_mcp.light.get_state": MagicMock()
        })
        mock_create_toolset.return_value = mock_toolset
        
        # Call function
        result = check_home_assistant_entity("light.living_room")
        
        # Assertions
        assert result["success"] is True
        assert result["status"] == "entity_found"
        assert result["entity_id"] == "light.living_room"
        assert result["domain"] == "light"


class TestListHomeAssistantDomains:
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    def test_list_domains_initialization_failed(self, mock_create_toolset):
        """Test handling when toolset initialization fails during domain listing."""
        # Setup
        mock_create_toolset.return_value = None
        
        # Call function
        result = list_home_assistant_domains()
        
        # Assertions
        assert result["success"] is False
        assert result["status"] == "initialization_failed"
        mock_create_toolset.assert_called_once()
    
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    def test_list_domains_success_with_list_tools(self, mock_create_toolset):
        """Test successful domain listing using list_tools method."""
        # Setup
        mock_toolset = MagicMock()
        mock_toolset.list_tools.return_value = [
            "home_assistant_mcp.light.turn_on",
            "home_assistant_mcp.light.turn_off",
            "home_assistant_mcp.sensor.get_state",
            "home_assistant_mcp.climate.set_temperature"
        ]
        mock_create_toolset.return_value = mock_toolset
        
        # Call function
        result = list_home_assistant_domains()
        
        # Assertions
        assert result["success"] is True
        assert result["status"] == "domains_listed"
        assert sorted(result["domains"]) == ["climate", "light", "sensor"]
        assert result["domains_count"] == 3
    
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    @pytest.mark.xfail(reason="Google ADK 0.3.0 compatibility issue")
    def test_list_domains_success_with_internal_tools(self, mock_create_toolset):
        """Test successful domain listing using _tools attribute."""
        # Setup for ADK 0.3.0+ compatibility
        mock_toolset = MagicMock()
        type(mock_toolset).list_tools = PropertyMock(side_effect=AttributeError)
        
        # Set up for the _MCPToolset__tools attribute (mangled in Python)
        mock_tools = {
            "home_assistant_mcp.light.turn_on": MagicMock(),
            "home_assistant_mcp.media_player.play": MagicMock(),
            "home_assistant_mcp.cover.open_cover": MagicMock()
        }
        # Set both old and new attribute patterns
        type(mock_toolset)._tools = PropertyMock(return_value=mock_tools)
        type(mock_toolset)._MCPToolset__tools = PropertyMock(return_value=mock_tools)
        mock_create_toolset.return_value = mock_toolset
        
        # Call function
        result = list_home_assistant_domains()
        
        # Assertions
        assert result["success"] is True
        assert result["status"] == "domains_listed"
        assert sorted(result["domains"]) == ["cover", "light", "media_player"]
        assert result["domains_count"] == 3
    
    @patch('radbot.tools.mcp.mcp_tools.create_home_assistant_toolset')
    def test_list_domains_exception(self, mock_create_toolset):
        """Test handling of exceptions during domain listing."""
        # Setup
        mock_toolset = MagicMock()
        mock_toolset.list_tools.side_effect = Exception("Test exception")
        mock_create_toolset.return_value = mock_toolset
        
        # Call function
        result = list_home_assistant_domains()
        
        # Assertions
        assert result["success"] is False
        assert result["status"] == "listing_error"
        assert "Test exception" in result["error"]
        mock_toolset.list_tools.assert_called_once()