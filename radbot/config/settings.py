"""
Configuration settings and management for the radbot agent framework.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the new YAML config loader
from radbot.config.config_loader import config_loader

# Default paths
DEFAULT_CONFIG_DIR = Path(__file__).parent / "default_configs"

class ConfigManager:
    """
    Manager for agent configuration settings.
    
    Handles loading instruction prompts, model selection, and other configuration settings.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Optional directory path for configuration files
        """
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.model_config = self._load_model_config()
        self.ha_config = self._load_home_assistant_config()
        self.instruction_cache = {}
        
    def _load_model_config(self) -> Dict[str, Any]:
        """
        Load model configuration from YAML config or environment variables as fallback.
        
        Returns:
            Dictionary of model configuration settings
        """
        # First try to get from YAML config
        agent_config = config_loader.get_agent_config()
        
        return {
            # Primary model for main agent
            "main_model": agent_config.get("main_model") or os.getenv("RADBOT_MAIN_MODEL", "gemini-2.5-pro"),
            
            # Also check GEMINI_MODEL env var for compatibility 
            "gemini_model": os.getenv("GEMINI_MODEL"),
            
            # Model for simpler sub-agents
            "sub_agent_model": agent_config.get("sub_agent_model") or os.getenv("RADBOT_SUB_MODEL", "gemini-2.0-flash"),
            
            # Use Vertex AI flag
            "use_vertex_ai": agent_config.get("use_vertex_ai", False) if "use_vertex_ai" in agent_config else os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE",
            
            # Vertex AI project ID
            "vertex_project": agent_config.get("vertex_project") or os.getenv("GOOGLE_CLOUD_PROJECT"),
            
            # Vertex AI location
            "vertex_location": agent_config.get("vertex_location") or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            
            # Vertex AI service account file
            "service_account_file": agent_config.get("service_account_file") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            
            # ADK Built-in Tools Configuration
            "enable_adk_search": agent_config.get("enable_adk_search", False) if "enable_adk_search" in agent_config else os.getenv("RADBOT_ENABLE_ADK_SEARCH", "FALSE").upper() == "TRUE",
            
            # Enable ADK Code Execution Tool
            "enable_adk_code_execution": agent_config.get("enable_adk_code_execution", False) if "enable_adk_code_execution" in agent_config else os.getenv("RADBOT_ENABLE_ADK_CODE_EXEC", "FALSE").upper() == "TRUE"
        }

    def _load_home_assistant_config(self) -> Dict[str, Any]:
        """
        Load Home Assistant configuration from YAML config or environment variables.
        
        Returns:
            Dictionary of Home Assistant configuration settings
        """
        # First try to get from YAML config
        ha_yaml_config = config_loader.get_home_assistant_config()
        
        # Get REST API configuration, first from YAML then from env vars
        ha_url = ha_yaml_config.get("url") or os.getenv("HA_URL")
        ha_token = ha_yaml_config.get("token") or os.getenv("HA_TOKEN")
        ha_mcp_sse_url = ha_yaml_config.get("mcp_sse_url") or os.getenv("HA_MCP_SSE_URL")
        ha_enabled = ha_yaml_config.get("enabled", bool(ha_url and ha_token))
            
        return {
            # Overall configuration
            "use_rest_api": True,  # Always use REST API approach
            "enabled": ha_enabled,
            
            # REST API configuration
            "url": ha_url,
            "token": ha_token,
            "mcp_sse_url": ha_mcp_sse_url,
        }
    
    def get_instruction(self, name: str) -> str:
        """
        Get an instruction prompt by name.
        
        Args:
            name: Name of the instruction prompt to load
            
        Returns:
            The instruction prompt text
            
        Raises:
            FileNotFoundError: If the instruction file doesn't exist
        """
        # Return from cache if already loaded
        if name in self.instruction_cache:
            return self.instruction_cache[name]
        
        # Load the instruction from file
        instruction_path = self.config_dir / "instructions" / f"{name}.md"
        if not instruction_path.exists():
            raise FileNotFoundError(f"Instruction prompt '{name}' not found at {instruction_path}")
        
        # Read, cache, and return the instruction
        instruction = instruction_path.read_text(encoding="utf-8")
        self.instruction_cache[name] = instruction
        return instruction
    
    def get_schema_config(self, schema_name: str) -> Dict[str, Any]:
        """
        Get JSON schema configuration for structured data interfaces.
        
        Args:
            schema_name: Name of the schema to load
            
        Returns:
            Dictionary representation of the JSON schema
            
        Raises:
            FileNotFoundError: If the schema file doesn't exist
        """
        schema_path = self.config_dir / "schemas" / f"{schema_name}.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema '{schema_name}' not found at {schema_path}")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_main_model(self) -> str:
        """
        Get the main agent model name.
        
        Order of precedence:
        1. RADBOT_MAIN_MODEL env var 
        2. GEMINI_MODEL env var
        3. Default model (gemini-2.5-pro)
        
        Returns:
            The configured main model name
        """
        # First try RADBOT_MAIN_MODEL, then GEMINI_MODEL, then default
        return (self.model_config["main_model"] or 
                self.model_config.get("gemini_model") or 
                "gemini-2.5-pro")
    
    def get_sub_agent_model(self) -> str:
        """
        Get the sub-agent model name.
        
        Returns:
            The configured sub-agent model name
        """
        return self.model_config["sub_agent_model"]
    
    def is_using_vertex_ai(self) -> bool:
        """
        Check if the agent is configured to use Vertex AI.
        
        Returns:
            True if using Vertex AI, False otherwise
        """
        return self.model_config["use_vertex_ai"]
        
    def get_vertex_project(self) -> Optional[str]:
        """
        Get the Google Cloud project ID for Vertex AI.
        
        Returns:
            The project ID or None if not configured
        """
        return self.model_config.get("vertex_project")
        
    def get_vertex_location(self) -> str:
        """
        Get the Google Cloud location for Vertex AI.
        
        Returns:
            The location (defaults to "us-central1" if not configured)
        """
        return self.model_config.get("vertex_location", "us-central1")
        
    def get_service_account_file(self) -> Optional[str]:
        """
        Get the Google Cloud service account file path for Vertex AI.
        
        Returns:
            The service account file path or None if not configured
        """
        return self.model_config.get("service_account_file")
        
    def is_adk_search_enabled(self) -> bool:
        """
        Check if the ADK Google Search built-in tool is enabled.
        
        Returns:
            True if ADK Google Search is enabled, False otherwise
        """
        return self.model_config.get("enable_adk_search", False)
        
    def is_adk_code_execution_enabled(self) -> bool:
        """
        Check if the ADK Code Execution built-in tool is enabled.
        
        Returns:
            True if ADK Code Execution is enabled, False otherwise
        """
        return self.model_config.get("enable_adk_code_execution", False)
    
    def get_home_assistant_config(self) -> Dict[str, Any]:
        """
        Get the Home Assistant configuration settings.
        
        Returns:
            Dictionary with Home Assistant configuration
        """
        return self.ha_config
    
    def is_home_assistant_enabled(self) -> bool:
        """
        Check if Home Assistant integration is enabled and properly configured.
        
        Returns:
            True if Home Assistant integration is enabled, False otherwise
        """
        return self.ha_config.get("enabled", False)
    
    def get_home_assistant_url(self) -> Optional[str]:
        """
        Get the Home Assistant URL.
        
        Returns:
            The Home Assistant URL or None if not configured
        """
        return self.ha_config.get("url")
    
    def get_home_assistant_token(self) -> Optional[str]:
        """
        Get the Home Assistant authentication token.
        
        Returns:
            The Home Assistant token or None if not configured
        """
        return self.ha_config.get("token")