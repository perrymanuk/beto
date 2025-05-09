"""
ConfigLoader for YAML-based configuration with environment variable interpolation.
"""

import os
import re
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, TypeVar, Type, cast

# Try to import jsonschema for validation, but make it optional
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

# Define logger
logger = logging.getLogger(__name__)

# Type variable for Python classes
T = TypeVar('T')

class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass

class ConfigLoader:
    """
    Loads and manages YAML configuration with environment variable interpolation.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Optional explicit path to config.yaml
        """
        self.config_path = self._find_config_path(config_path)
        self.schema_path = Path(__file__).parent / "schema" / "config_schema.json"
        self.config = self._load_config()
        
    def _find_config_path(self, config_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Find the configuration file path.
        
        Looks in the following locations (in order):
        1. Explicit path provided to constructor
        2. Path specified by RADBOT_CONFIG environment variable
        3. Current working directory
        4. User's config directory (~/.config/radbot/)
        5. Project root directory
        
        Args:
            config_path: Optional explicit path to config.yaml
            
        Returns:
            Path to the configuration file
            
        Raises:
            ConfigError: If config.yaml cannot be found
        """
        # Check explicit path
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            else:
                logger.warning(f"Specified config path does not exist: {path}")
        
        # Check environment variable
        env_path = os.getenv("RADBOT_CONFIG")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
            else:
                logger.warning(f"Config path from environment variable does not exist: {path}")
        
        # Check current working directory
        cwd_path = Path.cwd() / "config.yaml"
        if cwd_path.exists():
            return cwd_path
        
        # Check user's config directory
        user_config_dir = Path.home() / ".config" / "radbot"
        user_config_path = user_config_dir / "config.yaml"
        if user_config_path.exists():
            return user_config_path
        
        # Check project root directory
        project_root = Path(__file__).parent.parent.parent
        project_config_path = project_root / "config.yaml"
        if project_config_path.exists():
            return project_config_path
        
        # Check for example file to copy
        example_path = project_root / "examples" / "config.yaml.example"
        if example_path.exists():
            logger.warning(
                f"No config.yaml found. You can copy the example from {example_path} "
                f"to {project_config_path} and customize it."
            )
        
        # If we reach here, we couldn't find config.yaml
        # Instead of raising an error, return a default path for potential creation
        logger.warning(f"No config.yaml found. Using default configuration with environment variables.")
        return project_config_path

    def _load_schema(self) -> Dict[str, Any]:
        """
        Load the JSON schema for validation.
        
        Returns:
            Dictionary containing the JSON schema
        """
        if not self.schema_path.exists():
            logger.warning(f"Schema file not found: {self.schema_path}")
            return {}
        
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading schema: {e}")
            return {}

    def _interpolate_env_vars(self, value: Any) -> Any:
        """
        Recursively interpolate environment variables in configuration values.
        
        Replaces "${ENV_VAR}" or "$ENV_VAR" with the value of the environment variable.
        
        Args:
            value: The value to interpolate, can be a string, list, or dictionary
            
        Returns:
            The value with environment variables interpolated
        """
        if isinstance(value, str):
            # Match ${ENV_VAR} or $ENV_VAR
            pattern = r'\${([^}]+)}|\$([a-zA-Z0-9_]+)'
            
            def replace_env_var(match):
                env_var = match.group(1) or match.group(2)
                return os.environ.get(env_var, f"${{{env_var}}}")
            
            return re.sub(pattern, replace_env_var, value)
        elif isinstance(value, list):
            return [self._interpolate_env_vars(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._interpolate_env_vars(v) for k, v in value.items()}
        else:
            return value

    def _validate_config(self, config: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """
        Validate the configuration against the schema.
        
        Args:
            config: The configuration to validate
            schema: The JSON schema to validate against
            
        Raises:
            ConfigError: If validation fails
        """
        if not JSONSCHEMA_AVAILABLE:
            logger.warning("jsonschema package not available. Skipping configuration validation.")
            return
        
        if not schema:
            logger.warning("No schema available. Skipping configuration validation.")
            return
        
        try:
            jsonschema.validate(instance=config, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            # Provide a more user-friendly error message
            path = ' -> '.join([str(p) for p in e.path])
            message = f"Configuration validation error: {e.message}"
            if path:
                message = f"{message} (at {path})"
            raise ConfigError(message) from e

    def _load_config(self) -> Dict[str, Any]:
        """
        Load and validate the configuration file.
        
        Returns:
            Dictionary containing the configuration
            
        Raises:
            ConfigError: If the configuration file cannot be loaded or is invalid
        """
        # If the config file doesn't exist, return empty dict for fallback to env vars
        if not self.config_path.exists():
            logger.info(f"Configuration file not found: {self.config_path}. Using default configuration.")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Interpolate environment variables
            config = self._interpolate_env_vars(config)
            
            # Validate against schema
            schema = self._load_schema()
            self._validate_config(config, schema)
            
            return config
        except yaml.YAMLError as e:
            error_msg = f"Error parsing config.yaml: {e}"
            logger.error(error_msg)
            raise ConfigError(error_msg) from e
        except Exception as e:
            error_msg = f"Error loading configuration: {e}"
            logger.error(error_msg)
            raise ConfigError(error_msg) from e

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get a default configuration based on environment variables.
        
        Returns:
            Dictionary containing the default configuration
        """
        # Load from environment variables similar to settings.py
        return {
            "agent": {
                "main_model": os.getenv("RADBOT_MAIN_MODEL", "gemini-2.5-pro"),
                "sub_agent_model": os.getenv("RADBOT_SUB_MODEL", "gemini-2.0-flash"),
                "agent_models": {
                    "code_execution_agent": os.getenv("RADBOT_CODE_AGENT_MODEL", ""),
                    "search_agent": os.getenv("RADBOT_SEARCH_AGENT_MODEL", ""),
                    "scout_agent": os.getenv("RADBOT_SCOUT_AGENT_MODEL", ""),
                    "todo_agent": os.getenv("RADBOT_TODO_AGENT_MODEL", ""),
                },
                "use_vertex_ai": os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE",
                "vertex_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
                "vertex_location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            },
            "cache": {
                "enabled": os.getenv("RADBOT_CACHE_ENABLED", "TRUE").upper() in ('TRUE', 'YES', '1'),
                "ttl": int(os.getenv("RADBOT_CACHE_TTL", "3600")),
                "max_size": int(os.getenv("RADBOT_CACHE_MAX_SIZE", "1000")),
                "selective": os.getenv("RADBOT_CACHE_SELECTIVE", "TRUE").upper() in ('TRUE', 'YES', '1'),
                "min_tokens": int(os.getenv("RADBOT_CACHE_MIN_TOKENS", "50")),
                "redis_url": os.getenv("REDIS_URL"),
            },
            "integrations": {
                "home_assistant": {
                    "enabled": bool(os.getenv("HA_URL") and os.getenv("HA_TOKEN")),
                    "url": os.getenv("HA_URL"),
                    "token": os.getenv("HA_TOKEN"),
                },
                "mcp": {
                    "servers": []
                }
            }
        }

    def get_config(self) -> Dict[str, Any]:
        """
        Get the full configuration.
        
        Returns:
            Dictionary containing the full configuration
        """
        return self.config

    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get the agent configuration section.
        
        Returns:
            Dictionary containing the agent configuration
        """
        return self.config.get("agent", {})

    def get_cache_config(self) -> Dict[str, Any]:
        """
        Get the cache configuration section.
        
        Returns:
            Dictionary containing the cache configuration
        """
        return self.config.get("cache", {})

    def get_integrations_config(self) -> Dict[str, Any]:
        """
        Get the integrations configuration section.
        
        Returns:
            Dictionary containing the integrations configuration
        """
        return self.config.get("integrations", {})

    def get_home_assistant_config(self) -> Dict[str, Any]:
        """
        Get the Home Assistant configuration.
        
        Returns:
            Dictionary containing the Home Assistant configuration
        """
        integrations = self.get_integrations_config()
        return integrations.get("home_assistant", {})

    def get_mcp_config(self) -> Dict[str, Any]:
        """
        Get the MCP configuration.
        
        Returns:
            Dictionary containing the MCP configuration
        """
        integrations = self.get_integrations_config()
        return integrations.get("mcp", {})

    def get_mcp_servers(self) -> List[Dict[str, Any]]:
        """
        Get all configured MCP servers.
        
        Returns:
            List of MCP server configurations
        """
        mcp_config = self.get_mcp_config()
        return mcp_config.get("servers", [])

    def get_enabled_mcp_servers(self) -> List[Dict[str, Any]]:
        """
        Get only enabled MCP servers.
        
        Returns:
            List of enabled MCP server configurations
        """
        servers = self.get_mcp_servers()
        return [s for s in servers if s.get("enabled", True)]

    def get_mcp_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific MCP server by ID.
        
        Args:
            server_id: The ID of the MCP server
            
        Returns:
            Dictionary containing the MCP server configuration, or None if not found
        """
        servers = self.get_mcp_servers()
        for server in servers:
            if server.get("id") == server_id:
                return server
        return None

    def is_mcp_server_enabled(self, server_id: str) -> bool:
        """
        Check if a specific MCP server is enabled.
        
        Args:
            server_id: The ID of the MCP server
            
        Returns:
            Boolean indicating if the server is enabled
        """
        server = self.get_mcp_server(server_id)
        if server is None:
            return False
        return server.get("enabled", True)

    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get the logging configuration.
        
        Returns:
            Dictionary containing the logging configuration
        """
        return self.config.get("logging", {})

# Create a singleton instance
config_loader = ConfigLoader()