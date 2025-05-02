"""
Unit tests for MCP tools.

Tests the functionality of the Home Assistant MCP integration tools.
"""
import pytest
from unittest.mock import patch, MagicMock, ANY

from raderbot.tools.mcp_tools import create_home_assistant_toolset, create_ha_mcp_enabled_agent


class TestCreateHomeAssistantToolset:
    @patch('raderbot.tools.mcp_tools.os.getenv')
    @patch('raderbot.tools.mcp_tools.MCPToolset')
    def test_create_home_assistant_toolset_success(self, mock_mcp_toolset, mock_getenv):
        """Test successful creation of Home Assistant MCPToolset."""
        # Setup environment variables
        mock_getenv.side_effect = lambda key: {
            "HA_MCP_SSE_URL": "http://homeassistant:8123/api/mcp/stream",
            "HA_AUTH_TOKEN": "fake_token_123"
        }.get(key)
        
        # Setup mock MCPToolset
        mock_mcp_instance = MagicMock()
        mock_mcp_toolset.return_value = mock_mcp_instance
        
        # Call function
        result = create_home_assistant_toolset()
        
        # Assertions
        assert result is mock_mcp_instance
        mock_mcp_toolset.assert_called_once()
        mock_getenv.assert_any_call("HA_MCP_SSE_URL")
        mock_getenv.assert_any_call("HA_AUTH_TOKEN")
    
    @patch('raderbot.tools.mcp_tools.os.getenv')
    def test_missing_url_environment_variable(self, mock_getenv):
        """Test handling of missing Home Assistant MCP URL environment variable."""
        # Setup missing HA_MCP_SSE_URL
        mock_getenv.side_effect = lambda key: {
            "HA_MCP_SSE_URL": None,
            "HA_AUTH_TOKEN": "fake_token_123"
        }.get(key)
        
        # Call function
        result = create_home_assistant_toolset()
        
        # Assertions
        assert result is None
        mock_getenv.assert_any_call("HA_MCP_SSE_URL")
    
    @patch('raderbot.tools.mcp_tools.os.getenv')
    def test_missing_token_environment_variable(self, mock_getenv):
        """Test handling of missing Home Assistant auth token environment variable."""
        # Setup missing HA_AUTH_TOKEN
        mock_getenv.side_effect = lambda key: {
            "HA_MCP_SSE_URL": "http://homeassistant:8123/api/mcp/stream",
            "HA_AUTH_TOKEN": None
        }.get(key)
        
        # Call function
        result = create_home_assistant_toolset()
        
        # Assertions
        assert result is None
        mock_getenv.assert_any_call("HA_MCP_SSE_URL")
        mock_getenv.assert_any_call("HA_AUTH_TOKEN")
    
    @patch('raderbot.tools.mcp_tools.os.getenv')
    @patch('raderbot.tools.mcp_tools.MCPToolset')
    def test_exception_handling(self, mock_mcp_toolset, mock_getenv):
        """Test exception handling during toolset creation."""
        # Setup environment variables
        mock_getenv.side_effect = lambda key: {
            "HA_MCP_SSE_URL": "http://homeassistant:8123/api/mcp/stream",
            "HA_AUTH_TOKEN": "fake_token_123"
        }.get(key)
        
        # Setup exception in MCPToolset creation
        mock_mcp_toolset.side_effect = Exception("Test exception")
        
        # Call function
        result = create_home_assistant_toolset()
        
        # Assertions
        assert result is None
        mock_getenv.assert_any_call("HA_MCP_SSE_URL")
        mock_getenv.assert_any_call("HA_AUTH_TOKEN")


class TestCreateHaMcpEnabledAgent:
    @patch('raderbot.tools.mcp_tools.create_home_assistant_toolset')
    def test_create_agent_with_ha_toolset(self, mock_create_ha_toolset):
        """Test creating an agent with Home Assistant toolset."""
        # Setup
        mock_toolset = MagicMock()
        mock_create_ha_toolset.return_value = mock_toolset
        mock_agent = MagicMock()
        mock_factory = MagicMock(return_value=mock_agent)
        base_tools = [MagicMock(), MagicMock()]
        
        # Call function
        agent = create_ha_mcp_enabled_agent(mock_factory, base_tools)
        
        # Assertions
        assert agent is mock_agent
        mock_create_ha_toolset.assert_called_once()
        mock_factory.assert_called_once_with(tools=[*base_tools, mock_toolset])
    
    @patch('raderbot.tools.mcp_tools.create_home_assistant_toolset')
    def test_create_agent_without_ha_toolset(self, mock_create_ha_toolset):
        """Test creating an agent when Home Assistant toolset is not available."""
        # Setup
        mock_create_ha_toolset.return_value = None
        mock_agent = MagicMock()
        mock_factory = MagicMock(return_value=mock_agent)
        base_tools = [MagicMock(), MagicMock()]
        
        # Call function
        agent = create_ha_mcp_enabled_agent(mock_factory, base_tools)
        
        # Assertions
        assert agent is mock_agent
        mock_create_ha_toolset.assert_called_once()
        mock_factory.assert_called_once_with(tools=base_tools)
    
    @patch('raderbot.tools.mcp_tools.create_home_assistant_toolset')
    def test_create_agent_with_no_base_tools(self, mock_create_ha_toolset):
        """Test creating an agent with no base tools."""
        # Setup
        mock_toolset = MagicMock()
        mock_create_ha_toolset.return_value = mock_toolset
        mock_agent = MagicMock()
        mock_factory = MagicMock(return_value=mock_agent)
        
        # Call function
        agent = create_ha_mcp_enabled_agent(mock_factory)
        
        # Assertions
        assert agent is mock_agent
        mock_create_ha_toolset.assert_called_once()
        mock_factory.assert_called_once_with(tools=[mock_toolset])
    
    @patch('raderbot.tools.mcp_tools.create_home_assistant_toolset')
    def test_exception_handling(self, mock_create_ha_toolset):
        """Test exception handling during agent creation."""
        # Setup
        mock_toolset = MagicMock()
        mock_create_ha_toolset.return_value = mock_toolset
        mock_factory = MagicMock(side_effect=Exception("Test exception"))
        
        # Call function
        agent = create_ha_mcp_enabled_agent(mock_factory)
        
        # Assertions
        assert agent is None
        mock_create_ha_toolset.assert_called_once()