# ADK Built-in Tools Integration

This document describes the implementation for integrating Google's ADK built-in tools into RadBot.

## Overview

Google ADK provides several built-in tools that offer advanced capabilities like web search and code execution. This implementation integrates two of these tools:

1. `google_search` - Allows the agent to search the web with Google Search
2. `built_in_code_execution` - Allows the agent to execute Python code

## Implementation Details

### Limitations

The ADK built-in tools have specific limitations:
- Only one built-in tool can be used per agent instance
- Built-in tools cannot be used in sub-agents
- Both tools require Gemini 2 models
- For ADK 0.4.0+, agent transfers require specific sub-agent relationships

### Agent Transfer Requirements

With ADK 0.4.0+, agent transfers have additional requirements:
1. For agent A to transfer to agent B, agent B must be in agent A's sub_agents list
2. For bidirectional transfers, agents must be in each other's sub_agents lists
3. All agents involved in transfers must have the transfer_to_agent tool

### Solution Architecture

To overcome these limitations, we implement a multi-agent approach:
1. The primary agent (Beto or Scout) uses a sub-agent for Google Search capabilities
2. The primary agent uses another sub-agent for Code Execution capabilities
3. Each agent has other agents in its sub_agents list to enable bidirectional transfers

This approach allows us to leverage both tools while respecting ADK's constraints.

### Agent Structure

```
Root Agent (Beto)
├── Search Agent (with google_search tool)
│   └── Sub-agents: [Beto, Scout, Code Execution Agent]
├── Code Execution Agent (with built_in_code_execution tool)
│   └── Sub-agents: [Beto, Scout, Search Agent]
└── Scout Agent (Research Agent)
    └── Sub-agents: [Beto, Search Agent, Code Execution Agent]
```

This structure ensures that any agent can transfer to any other agent through their sub_agents relationships.

## Implementation Plan

### 1. Create Directory Structure

Create the following directory and files:

```
/Users/perry.manuk/git/perrymanuk/radbot/radbot/tools/adk_builtin/
├── __init__.py
├── search_tool.py
└── code_execution_tool.py
```

### 2. Implementation Components

#### 2.1. Module Structure

- `__init__.py`: Export the factory and registration functions
- `search_tool.py`: Implement Google Search agent creation and registration
- `code_execution_tool.py`: Implement Code Execution agent creation and registration

#### 2.2. Core Functions

For each tool, implement:
1. A factory function that creates an agent with the specific tool
2. A registration function that registers the agent as a sub-agent to a parent agent

#### 2.3. Agent Modification

Modify the agent creation functions to support:
- Creating agents with built-in tools enabled via parameters
- Handling the sub-agent registration process

### 3. Implementation Steps

1. Create the directory structure and files
2. Implement the core functions for both tools
3. Modify the existing agent creation process to support the new tools
4. Add unit tests for the new functionality
5. Update documentation to explain the usage of the tools

### 4. Agent Interfaces

#### 4.1. Root Agent (Beto)

Update the `create_agent` function to support built-in tools:

```python
def create_agent(
    # Existing parameters...
    include_google_search: bool = False,
    include_code_execution: bool = False,
    # Other parameters...
) -> Union[RadBotAgent, Agent]:
    # Implementation...
```

#### 4.2. Research Agent (Scout)

Update the `ResearchAgent` class to support built-in tools:

```python
def __init__(
    self,
    # Existing parameters...
    enable_google_search: bool = False,
    enable_code_execution: bool = False,
    # Other parameters...
):
    # Implementation...
```

## Usage Examples

### Root Agent (Beto)

```python
from radbot.agent import create_agent

agent = create_agent(
    include_google_search=True,
    include_code_execution=True
)
```

### Research Agent (Scout)

```python
from radbot.agent.research_agent import ResearchAgent

research_agent = ResearchAgent(
    enable_google_search=True,
    enable_code_execution=True
)
```

### Standalone Agents

For standalone use (not requiring transfers), create agents without the transfer_to_agent tool:

```python
from radbot.tools.adk_builtin.search_tool import create_search_agent
from radbot.tools.adk_builtin.code_execution_tool import create_code_execution_agent

# Create a search agent without transfer_to_agent (for standalone use)
search_agent = create_search_agent(
    name="search_agent",
    include_transfer_tool=False  # Important for standalone tests with Vertex AI
)

# Create a code execution agent without transfer_to_agent (for standalone use)
code_agent = create_code_execution_agent(
    name="code_execution_agent",
    include_transfer_tool=False  # Important for standalone tests with Vertex AI
)
```

**Note**: When using Vertex AI with standalone agents, `include_transfer_tool=False` is required due to Vertex AI's limitation of supporting only one tool per agent.

## Testing Approach

1. Unit tests for each tool function
2. Integration tests with the main agent system
3. End-to-end tests with conversation flows
4. Dedicated agent transfer tests with both web interface and automated validation

### Agent Transfer Testing

We've implemented a dedicated testing script `tools/test_adk_builtin_transfers.py` that provides:

1. **Validation Testing**: Programmatically verifies that all required agent transfers work
   ```bash
   python -m tools.test_adk_builtin_transfers --validate
   ```
   
2. **Web Testing**: Starts the web application for manual testing of agent transfers
   ```bash
   python -m tools.test_adk_builtin_transfers --web
   ```

3. **Test Examples**: Sample prompts to test specific agent transfers
   - Google Search: "Please search for the latest news on quantum computing"
   - Code Execution: "Calculate the factorial of 5 using Python"
   - Research Agent: "I need research on the environmental impact of electric vehicles"

The test validates that:
- All agents have the transfer_to_agent tool
- Target agents are in the source agent's sub_agents list
- Agent names are consistent for reliable transfers
- Agents can transfer back to their parent agents

## Authentication Setup

### Google Search Tool Authentication

The `google_search` built-in tool requires Google Cloud authentication. Follow these steps to set it up:

1. Authenticate with Google Cloud:
   ```bash
   gcloud auth login
   ```

2. Set up application default credentials:
   ```bash
   gcloud auth application-default login
   ```

3. Enable the Vertex AI API in your Google Cloud project.

4. Add the following environment variables:
   ```
   # Google Cloud settings for ADK built-in tools
   GOOGLE_CLOUD_PROJECT="your-project-id"
   GOOGLE_CLOUD_LOCATION="your-location"  # e.g., us-central1
   GOOGLE_GENAI_USE_VERTEXAI="True"
   ```

5. Policy Compliance: When the Google Search tool returns search suggestions, you must display these suggestions in your application. The search suggestions are returned as HTML in the Gemini response's `renderedContent` field.

### Code Execution Tool Authentication

The `built_in_code_execution` tool doesn't require additional authentication beyond what's needed for the Gemini model itself, which is handled by the same Google Cloud authentication as above.

## Key Fixes for Agent Transfers

### 1. LlmAgent Configuration Handling

To fix the "LlmAgent object has no field 'config'" error, we implemented robust configuration handling:

```python
# Check if the agent has a config attribute already
if not hasattr(code_agent, "config"):
    # For LlmAgent type in ADK 0.4.0+
    if hasattr(code_agent, "set_config"):
        # Use set_config method if available
        config = types.GenerateContentConfig()
        config.tools = [types.Tool(code_execution=types.ToolCodeExecution())]
        code_agent.set_config(config)
    else:
        # Try to add config attribute directly
        code_agent.config = types.GenerateContentConfig()
        code_agent.config.tools = [types.Tool(code_execution=types.ToolCodeExecution())]
```

### 2. Bidirectional Agent Registration

For agent transfers to work in both directions:

```python
# Add parent to search agent's sub_agents if not already there
if not parent_exists:
    # Create a proxy for the parent agent
    parent_proxy = Agent(
        name=parent_agent.name,
        model=parent_agent.model,
        instruction="Main coordinating agent",
        description="Main agent for coordinating tasks",
        tools=[transfer_to_agent]  # Critical for transfers
    )
    
    search_sub_agents.append(parent_proxy)
    agent_to_register.sub_agents = search_sub_agents
```

### 3. Consistent Agent Naming

Agent names must be consistent for transfers to work:

```python
# Ensure agent name is always "search_agent" for consistent transfers
if name != "search_agent":
    logger.warning(f"Agent name '{name}' changed to 'search_agent' for consistent transfers")
    name = "search_agent"
```

### 4. Backward Compatibility

For older code expecting AgentTransferTool:

```python
class AgentTransferTool:
    """
    Wrapper around transfer_to_agent for backward compatibility.
    """
    
    def __init__(self):
        self.name = "transfer_to_agent"
        self.description = "Transfers control to another agent"
        self._transfer_fn = transfer_to_agent
    
    def __call__(self, agent_name: str, **kwargs) -> Any:
        """Call the transfer_to_agent function with the given agent name."""
        return self._transfer_fn(agent_name=agent_name, **kwargs)
```

## References

- [ADK Built-in Tools Documentation](https://google.github.io/adk-docs/tools/built-in-tools/)
- [ADK Tool Limitations](https://google.github.io/adk-docs/tools/built-in-tools/#limitations)
- [Google Cloud Authentication](https://cloud.google.com/docs/authentication/provide-credentials-adc)
- [ADK Agent Transfer Documentation](https://google.github.io/adk-docs/agents/transfer-to-agent/)
- [ADK 0.4.0 Updates](https://github.com/google/adk-python/releases/tag/v0.4.0)
