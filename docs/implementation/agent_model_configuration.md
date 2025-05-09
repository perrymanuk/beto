# Agent-Specific Model Configuration

## Overview

This document describes how to configure different LLM models for each agent type in the RadBot system. This feature allows you to customize the model used for each specialized agent based on your requirements.

## Configuration Methods

You can configure agent-specific models using either:

1. YAML configuration file (recommended)
2. Environment variables

### YAML Configuration

In your `config.yaml` file, add the `agent_models` section under the `agent` configuration:

```yaml
agent:
  main_model: gemini-2.5-pro
  sub_agent_model: gemini-2.0-flash
  agent_models:
    code_execution_agent: gemini-2.5-pro
    search_agent: gemini-2.5-pro
    scout_agent: gemini-2.5-pro
    todo_agent: gemini-2.0-flash
  use_vertex_ai: true
  vertex_project: your-gcp-project
  vertex_location: us-central1
```

### Environment Variables

You can also use environment variables to configure agent-specific models:

```bash
# Main and default models
export RADBOT_MAIN_MODEL="gemini-2.5-pro"
export RADBOT_SUB_MODEL="gemini-2.0-flash"

# Agent-specific models
export RADBOT_CODE_AGENT_MODEL="gemini-2.5-pro"
export RADBOT_SEARCH_AGENT_MODEL="gemini-2.5-pro"
export RADBOT_SCOUT_AGENT_MODEL="gemini-2.5-pro"
export RADBOT_TODO_AGENT_MODEL="gemini-2.0-flash"
```

Environment variables override YAML configuration settings.

## Default Model Fallbacks

If an agent-specific model is not configured, the system will use the following fallback logic:

1. For code_execution_agent: Use the main_model
2. For search_agent: Use the main_model
3. For scout_agent: Use the main_model  
4. For other agents: Use the sub_agent_model

This is because the search, code execution, and scout agents typically require more advanced capabilities, while other sub-agents can often use a faster, more efficient model.

## Model Requirements

Note that some agent types have specific model requirements:

1. **code_execution_agent**: Requires a Gemini 2.x model with code execution capability
2. **search_agent**: Requires a Gemini 2.x model with Google Search capability
3. **scout_agent**: Works best with a more capable model

## Implementation Details

The agent-specific model configuration is implemented in the following components:

1. **ConfigManager**: Defines and loads the agent-specific model settings
   - `get_agent_model(agent_name)` method to retrieve the model for a specific agent

2. **Specialized Agent Factories**: Each specialized agent factory uses the agent-specific model
   - `code_execution_tool.py`: Creates the code execution agent with its specific model
   - `search_tool.py`: Creates the search agent with its specific model
   - `research_agent/factory.py`: Creates the scout agent with its specific model

## Example: Using Different Models for Specific Tasks

You might want to use different models based on the agent's purpose:

```yaml
agent:
  main_model: gemini-2.5-pro
  sub_agent_model: gemini-2.0-flash
  agent_models:
    # Complex coding tasks need the most capable model
    code_execution_agent: gemini-2.5-pro-latest
    # Web search can use a slightly faster model
    search_agent: gemini-2.5-pro
    # Research tasks need a very capable model
    scout_agent: gemini-2.5-pro-latest
    # Todo management can use a simpler model
    todo_agent: gemini-2.0-flash
```

This configuration allows you to balance capability and performance for each agent type.

## Recommendations

1. For production environments, use the YAML configuration approach for better maintainability
2. Test different models for each agent type to find the optimal balance of performance and capability
3. Consider using faster models for simple agents and more capable models for complex tasks
4. Remember that all models must be compatible with Vertex AI when using Vertex AI integration