"""
Example usage of the ConfigManager and updated agent implementation.
This is for demonstration purposes only.
"""

from pathlib import Path
from radbot.agent.agent import create_agent, radbotAgent
from radbot.config import config_manager
from radbot.config.settings import ConfigManager
from radbot.config.schema_models import UserInfoInput, MemoryQueryInput

# Example 1: Using the default config_manager instance
agent = create_agent()
response = agent.process_message("user123", "Hello, what can you help me with?")
print(response)

# Example 2: Using a custom configuration directory
custom_config_path = Path("/path/to/custom/configs")
custom_config = ConfigManager(config_dir=custom_config_path)

# Creating an agent with custom configuration
custom_agent = radbotAgent(
    model=custom_config.get_main_model(), 
    instruction_name="custom_prompt"
)

# Example 3: Using the structured schema models
memory_query = MemoryQueryInput(
    query="What did we discuss about machine learning?",
    user_id="user123",
    max_results=10
)

# Example 4: Getting configuration values
main_model = config_manager.get_main_model()
print(f"Using main model: {main_model}")

sub_model = config_manager.get_sub_agent_model()
print(f"Using sub-agent model: {sub_model}")

is_vertex = config_manager.is_using_vertex_ai()
print(f"Using Vertex AI: {is_vertex}")

# Example 5: Getting a schema configuration
try:
    memory_schema = config_manager.get_schema_config("memory_query")
    print(f"Loaded memory query schema: {memory_schema['title']}")
except FileNotFoundError as e:
    print(f"Schema not found: {e}")