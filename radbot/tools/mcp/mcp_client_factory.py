"""
Factory for creating MCP clients based on configuration.
"""

import logging
import importlib
from typing import Dict, Any, Optional, List, Callable, Union

from radbot.config.config_loader import config_loader

logger = logging.getLogger(__name__)

class MCPClientError(Exception):
    """Exception raised for MCP client initialization errors."""
    pass

class MCPClientFactory:
    """
    Factory for creating MCP clients based on configuration.
    """
    
    _client_cache: Dict[str, Any] = {}
    
    @classmethod
    def get_client(cls, server_id: str) -> Any:
        """
        Get or create an MCP client for the given server ID.
        
        Args:
            server_id: The ID of the MCP server
            
        Returns:
            MCP client instance
            
        Raises:
            MCPClientError: If the server is not configured or client creation fails
        """
        # Check if client is already cached
        if server_id in cls._client_cache:
            return cls._client_cache[server_id]
        
        # Get server configuration
        server_config = config_loader.get_mcp_server(server_id)
        if not server_config:
            raise MCPClientError(f"MCP server '{server_id}' not found in configuration")
        
        # Check if server is enabled
        if not server_config.get("enabled", True):
            raise MCPClientError(f"MCP server '{server_id}' is disabled")
        
        # Create and cache the client
        client = cls.create_client(server_config)
        cls._client_cache[server_id] = client
        return client
    
    @classmethod
    def create_client(cls, server_config: Dict[str, Any]) -> Any:
        """
        Create an MCP client for the given server configuration.
        
        Args:
            server_config: Dictionary containing the MCP server configuration
            
        Returns:
            MCP client instance
            
        Raises:
            MCPClientError: If client creation fails
        """
        try:
            # Get required configuration values
            server_id = server_config.get("id")
            transport = server_config.get("transport", "sse")
            url = server_config.get("url")
            
            # Import the appropriate client module based on transport
            try:
                # Try to use our custom implementation first for better compatibility
                # Our client supports multiple transports
                from radbot.tools.mcp.client import MCPSSEClient
                client_class = MCPSSEClient
                logger.info(f"Using custom MCP client implementation for server: {server_id} with transport: {transport}")
            except ImportError:
                # Fall back to MCP package if available
                if transport == "sse":
                    try:
                        from mcp.client import SSEClient
                        client_class = SSEClient
                        logger.info(f"Using MCP package SSEClient for server: {server_id}")
                    except ImportError:
                        # No client implementation available
                        raise MCPClientError(f"No SSE client implementation available for server: {server_id}")
                elif transport == "websocket":
                    try:
                        # Try to import MCP WebSocket client
                        from mcp.client import WebSocketClient
                        client_class = WebSocketClient
                    except ImportError:
                        # Fall back to a custom implementation if needed
                        logger.warning(f"No WebSocket client implementation available for server: {server_id}")
                        raise MCPClientError(f"No WebSocket client implementation available for server: {server_id}")
                elif transport == "http":
                    try:
                        # Use our custom client for HTTP transport as well
                        from radbot.tools.mcp.client import MCPSSEClient
                        client_class = MCPSSEClient
                        logger.info(f"Using custom MCP client for HTTP transport: {server_id}")
                    except ImportError:
                        raise MCPClientError(f"No HTTP client implementation available for server: {server_id}")
                else:
                    raise MCPClientError(f"Unsupported transport: {transport}")
            
            # Prepare client initialization arguments
            client_args = {
                "url": url
            }
            
            # Add message_endpoint if specified (used for SSE message exchange pattern)
            if server_config.get("message_endpoint"):
                client_args["message_endpoint"] = server_config.get("message_endpoint")
            
            # Handle authentication
            auth_type = server_config.get("auth_type", "token")
            if auth_type == "token" and server_config.get("auth_token"):
                client_args["auth_token"] = server_config.get("auth_token")
            elif auth_type == "basic":
                if server_config.get("username") and server_config.get("password"):
                    client_args["username"] = server_config.get("username")
                    client_args["password"] = server_config.get("password")
                else:
                    logger.warning(f"Basic auth configured for {server_id} but username/password not provided")
            
            # Add timeout if specified
            if server_config.get("timeout"):
                client_args["timeout"] = server_config.get("timeout")
            
            # Add custom headers if specified
            if server_config.get("headers"):
                client_args["headers"] = server_config.get("headers")
            
            # Create the client
            client = client_class(**client_args)
            logger.info(f"Created MCP client for server: {server_id}")
            return client
            
        except Exception as e:
            error_msg = f"Failed to create MCP client: {str(e)}"
            logger.error(error_msg)
            raise MCPClientError(error_msg) from e
    
    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear the client cache.
        """
        cls._client_cache.clear()
    
    @classmethod
    def get_all_enabled_clients(cls) -> Dict[str, Any]:
        """
        Get all enabled MCP clients.
        
        Returns:
            Dictionary mapping server IDs to client instances
        """
        clients = {}
        for server in config_loader.get_enabled_mcp_servers():
            server_id = server.get("id")
            try:
                clients[server_id] = cls.get_client(server_id)
            except MCPClientError as e:
                logger.warning(f"Failed to initialize MCP client for {server_id}: {e}")
        return clients