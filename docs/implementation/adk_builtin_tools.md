# ADK Built-in Tools Integration

This document describes the implementation plan for integrating Google's ADK built-in tools into RadBot.

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

### Solution Architecture

To overcome these limitations, we implement a multi-agent approach:
1. The primary agent (Beto or Scout) uses a sub-agent for Google Search capabilities
2. The primary agent uses another sub-agent for Code Execution capabilities

This approach allows us to leverage both tools while respecting ADK's constraints.

### Agent Structure

```
Root Agent (Beto)
├── Search Agent (with google_search tool)
└── Code Execution Agent (with built_in_code_execution tool)
```

For the Research Agent (Scout), a similar structure is used.

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

## Testing Approach

1. Unit tests for each tool function
2. Integration tests with the main agent system
3. End-to-end tests with conversation flows

## References

- [ADK Built-in Tools Documentation](https://google.github.io/adk-docs/tools/built-in-tools/)
- [ADK Tool Limitations](https://google.github.io/adk-docs/tools/built-in-tools/#limitations)
