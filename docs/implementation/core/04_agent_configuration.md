# Agent Configuration System

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document details the configuration system for the radbot agent framework, focusing on prompt management, model selection, and configuration loading.

## Configuration System Design

The configuration system allows for:
1. Dynamic loading of agent instructions (prompts)
2. Model selection
3. Management of agent hierarchy and capabilities
4. Structured input/output using Pydantic models

## Configuration Module Implementation

### Configuration Settings (`config/settings.py`)

```python
# radbot/config/settings.py

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
        self.instruction_cache = {}
        
    def _load_model_config(self) -> Dict[str, Any]:
        """
        Load model configuration from environment variables or defaults.
        
        Returns:
            Dictionary of model configuration settings
        """
        return {
            # Primary model for main agent (default to Pro 2.5)
            "main_model": os.getenv("RADBOT_MAIN_MODEL", "gemini-2.5-pro"),
            
            # Model for simpler sub-agents (default to Flash)
            "sub_agent_model": os.getenv("RADBOT_SUB_MODEL", "gemini-2.0-flash"),
            
            # Use Vertex AI flag
            "use_vertex_ai": os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
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
        
        Returns:
            The configured main model name
        """
        return self.model_config["main_model"]
    
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
```

### Package Initialization (`config/__init__.py`)

```python
# radbot/config/__init__.py

"""
Configuration management for the radbot agent framework.
"""

from radbot.config.settings import ConfigManager

# Create a default instance for import
config_manager = ConfigManager()
```

## Default Configuration Files

### Setup Default Configuration Directory

```python
# Create necessary directories
DEFAULT_CONFIG_DIR = Path("radbot/config/default_configs")
DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
(DEFAULT_CONFIG_DIR / "instructions").mkdir(exist_ok=True)
(DEFAULT_CONFIG_DIR / "schemas").mkdir(exist_ok=True)
```

### Main Agent Instruction (`default_configs/instructions/main_agent.md`)

```markdown
# Main Coordinator Agent

You are the central coordinator for an AI assistant system. Your primary role is to understand the user's request and orchestrate the necessary actions to fulfill it.

**Capabilities:**
*   You can answer general questions directly.
*   You have access to basic tools: `get_current_time`, `get_weather`. Use them when the user asks for current time or weather information.
*   You can access long-term memory using the `search_past_conversations` tool to recall previous interactions if relevant to the current query.
*   You can interact with Home Assistant via MCP tools (e.g., `HA_turn_light_on`, `HA_get_temperature`). Use these when the user requests actions or information related to their smart home.

**Workflow:**
1.  Analyze the user's query.
2.  If the query requires past context, consider using `search_past_conversations`.
3.  Determine the best course of action: answer directly, use a basic tool, use a Home Assistant tool, or delegate.
4.  If using a tool, clearly state you are using it and present the result clearly.
5.  If a tool or sub-agent returns an error, inform the user politely and state you cannot complete the request.
6.  Provide a final, concise response to the user.

**Constraints:**
*   Be polite and helpful.
*   Do not guess information if a tool fails or doesn't provide an answer.
*   Prioritize using specific tools/agents when applicable over general knowledge.
```

## Pydantic Models for Structured Data

Pydantic models provide type-safe representations of structured data that can be automatically converted to and from JSON.

### Schema Models (`schema_models.py`)

```python
# radbot/config/schema_models.py

"""
Pydantic models for structured data interfaces in the radbot framework.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class UserInfoInput(BaseModel):
    """Schema for structured user information input."""
    
    user_id: str = Field(description="The unique ID of the user.")
    query_topic: str = Field(description="The topic the user is asking about.")

class ExtractedInfoOutput(BaseModel):
    """Schema for structured information extraction output."""
    
    summary: str = Field(description="A brief summary of the extracted information.")
    key_points: List[str] = Field(description="A list of key points.")

class MemoryQueryInput(BaseModel):
    """Schema for memory query input."""
    
    query: str = Field(description="The search query.")
    user_id: str = Field(description="The user ID to filter memory by.")
    max_results: Optional[int] = Field(default=5, description="Maximum number of results to return.")
```

## Integration with Agent Implementation

The updated agent implementation integrates with the configuration system:

```python
# radbot/agent.py (updated excerpt)

from radbot.config import config_manager
from radbot.config.schema_models import UserInfoInput, ExtractedInfoOutput

# Use the configuration manager to get instructions and model names
def create_agent(
    session_service: Optional[SessionService] = None,
    tools: Optional[List[Any]] = None,
    model: Optional[str] = None,
    instruction_name: str = "main_agent"
) -> radbotAgent:
    """
    Create a configured radbot agent.
    
    Args:
        session_service: Optional session service for conversation state
        tools: Optional list of tools for the agent
        model: Optional Gemini model to use (defaults to configured main model)
        instruction_name: Name of the instruction prompt to load (from config)
        
    Returns:
        A configured radbotAgent instance
    """
    # Get the model name (use provided or get from config)
    model_name = model or config_manager.get_main_model()
    
    # Get the instruction prompt
    try:
        instruction = config_manager.get_instruction(instruction_name)
    except FileNotFoundError:
        # Fall back to the hardcoded instruction if the file doesn't exist
        instruction = MAIN_AGENT_INSTRUCTION
    
    return radbotAgent(
        session_service=session_service,
        tools=tools,
        model=model_name,
        instruction=instruction
    )
```

## Example Structured Agent

This example shows how to create an agent with structured input:

```python
# Example agent with structured input
from radbot.agent import Agent
from radbot.config import config_manager
from radbot.config.schema_models import UserInfoInput

# Create an agent that expects structured input
data_processing_agent = Agent(
    name="data_processor",
    model=config_manager.get_sub_agent_model(),
    instruction=config_manager.get_instruction("data_processor"),
    description="Processes structured user data.",
    input_schema=UserInfoInput
)
```

## Configuration Override Strategy

The configuration system supports two levels of overrides:

1. **Environment Variables**: Users can override default settings with environment variables
2. **Custom Configuration Directory**: A different config directory with customized instruction files can be specified

```python
# Example of custom configuration directory
from radbot.config.settings import ConfigManager
from pathlib import Path

# Create a config manager with custom directory
custom_config_path = Path("/path/to/custom/configs")
custom_config = ConfigManager(config_dir=custom_config_path)

# Use the custom config to create an agent
from radbot.agent import radbotAgent

custom_agent = radbotAgent(
    model=custom_config.get_main_model(), 
    instruction=custom_config.get_instruction("custom_prompt")
)
```

## Benefits of the Configuration System

The configuration system provides several benefits:

1. **Separation of Concerns**: Agent logic is separated from configuration details
2. **Flexibility**: Easy to change model selection or instruction prompts without code changes
3. **Version Control**: Instructions stored as files can be versioned and reviewed
4. **Structured Data**: Pydantic models ensure type safety for input/output schemas
5. **Environment-Specific Settings**: Different environments (dev, staging, prod) can use different settings

## Next Steps

After implementing the configuration system:

1. Implement basic tools (time, weather)
2. Implement the Qdrant memory system
3. Design the inter-agent communication strategy