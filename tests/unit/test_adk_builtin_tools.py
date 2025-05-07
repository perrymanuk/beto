"""
Test ADK built-in tools integration.

This module tests that the ADK built-in tools are properly initialized
and used, especially with Vertex AI compatibility.
"""

import unittest
import logging
from unittest.mock import patch, MagicMock

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools import built_in_code_execution

from radbot.tools.adk_builtin.code_execution_tool import create_code_execution_agent
from radbot.tools.adk_builtin.search_tool import create_search_agent
from radbot.config.settings import ConfigManager


class TestADKBuiltinTools(unittest.TestCase):
    """Test ADK built-in tools integration."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock ConfigManager
        self.mock_config = MagicMock(spec=ConfigManager)
        self.mock_config.get_main_model.return_value = "gemini-2.0-pro"
        self.mock_config.is_using_vertex_ai.return_value = True
        self.mock_config.get_instruction.return_value = "Test instruction"

    def test_code_execution_agent_single_tool(self):
        """Test that code execution agent only uses one tool."""
        # Create a code execution agent
        code_agent = create_code_execution_agent(
            model="gemini-2.0-pro",
            config=self.mock_config,
        )
        
        # Verify the agent has only one tool
        self.assertEqual(len(code_agent.tools), 1)
        
        # Verify that tool is built_in_code_execution
        self.assertEqual(code_agent.tools[0], built_in_code_execution)
        
        # Verify transfer instructions are added
        self.assertIn("TRANSFER_BACK_TO_BETO", code_agent.instruction)

    def test_search_agent_single_tool(self):
        """Test that search agent only uses one tool."""
        # Create a search agent
        search_agent = create_search_agent(
            model="gemini-2.0-pro",
            config=self.mock_config,
        )
        
        # Verify the agent has only one tool
        self.assertEqual(len(search_agent.tools), 1)
        
        # Verify that tool is google_search
        self.assertEqual(search_agent.tools[0], google_search)
        
        # Verify transfer instructions are added
        self.assertIn("TRANSFER_BACK_TO_BETO", search_agent.instruction)

if __name__ == "__main__":
    unittest.main()