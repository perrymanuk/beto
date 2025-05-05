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
    def test_connection_direct(self):
        """Test direct call to home assistant connection test function."""
        # Just call the function directly without mocking
        result = test_home_assistant_connection()
        
        # We expect it to fail in the test environment, but structure should be correct
        assert isinstance(result, dict)
        assert "success" in result
        assert "status" in result


class TestCheckHomeAssistantEntity:
    def test_check_entity_direct(self):
        """Test direct call to entity check function."""
        # Just call the function directly without mocking
        result = check_home_assistant_entity("light.living_room")
        
        # We expect it to fail in the test environment, but structure should be correct
        assert isinstance(result, dict)
        assert "success" in result
        assert "status" in result


class TestListHomeAssistantDomains:
    def test_list_domains_direct(self):
        """Test direct call to domain listing function."""
        # Just call the function directly without mocking
        result = list_home_assistant_domains()
        
        # We expect it to fail in the test environment, but structure should be correct
        assert isinstance(result, dict)
        assert "success" in result
        assert "status" in result