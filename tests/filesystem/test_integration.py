"""
Tests for the filesystem integration with ADK.
"""

import os
import tempfile
import shutil
import unittest
from unittest.mock import patch

from google.adk.tools import FunctionTool

from radbot.filesystem.integration import create_filesystem_tools
from radbot.filesystem.adapter import (
    get_filesystem_config,
    create_fileserver_toolset
)


class FilesystemIntegrationTest(unittest.TestCase):
    """Test the filesystem integration with ADK."""

    def setUp(self):
        """Set up the test environment with temporary directories."""
        # Create temporary test directories
        self.temp_dir = tempfile.mkdtemp(prefix="fs_integration_test_")
        
        # Create test files
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, "w") as f:
            f.write("Test file content")

    def tearDown(self):
        """Clean up the test environment."""
        # Remove the temporary directories
        shutil.rmtree(self.temp_dir)

    def test_create_filesystem_tools(self):
        """Test creating filesystem tools."""
        # Test with only read tools
        tools = create_filesystem_tools(
            allowed_directories=[self.temp_dir],
            enable_write=False,
            enable_delete=False
        )
        
        # Should have 4 tools: read_file, list_directory, get_info, search
        self.assertEqual(len(tools), 4)
        
        # Verify all tools are FunctionTool instances
        for tool in tools:
            self.assertIsInstance(tool, FunctionTool)
        
        # Test with write tools
        tools = create_filesystem_tools(
            allowed_directories=[self.temp_dir],
            enable_write=True,
            enable_delete=False
        )
        
        # Should have 7 tools: read_file, list_directory, get_info, search, 
        # write_file, edit_file, copy
        self.assertEqual(len(tools), 7)
        
        # Test with write and delete tools
        tools = create_filesystem_tools(
            allowed_directories=[self.temp_dir],
            enable_write=True,
            enable_delete=True
        )
        
        # Should have 8 tools: read_file, list_directory, get_info, search,
        # write_file, edit_file, copy, delete
        self.assertEqual(len(tools), 8)

    @patch.dict(os.environ, {
        "MCP_FS_ROOT_DIR": "/test/dir",
        "MCP_FS_ALLOW_WRITE": "true",
        "MCP_FS_ALLOW_DELETE": "false"
    })
    def test_get_filesystem_config(self):
        """Test getting filesystem configuration from environment variables."""
        root_dir, allow_write, allow_delete = get_filesystem_config()
        
        self.assertEqual(root_dir, "/test/dir")
        self.assertTrue(allow_write)
        self.assertFalse(allow_delete)

    @patch.dict(os.environ, {
        "MCP_FS_ROOT_DIR": "/test/dir",
        "MCP_FS_ALLOW_WRITE": "true",
        "MCP_FS_ALLOW_DELETE": "false"
    })
    @patch('radbot.filesystem.integration.create_filesystem_tools')
    def test_create_fileserver_toolset(self, mock_create_tools):
        """Test creating fileserver toolset with MCP-compatible environment."""
        # Mock the create_filesystem_tools function
        mock_tools = [FunctionTool(func=lambda: None) for _ in range(5)]
        mock_create_tools.return_value = mock_tools
        
        # Call the adapter function
        tools = create_fileserver_toolset()
        
        # Verify create_filesystem_tools was called with the correct arguments
        mock_create_tools.assert_called_once_with(
            allowed_directories=["/test/dir"],
            enable_write=True,
            enable_delete=False
        )
        
        # Verify the correct tools were returned
        self.assertEqual(tools, mock_tools)


if __name__ == "__main__":
    unittest.main()
