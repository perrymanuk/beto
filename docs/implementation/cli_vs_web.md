# CLI vs Web Interface Implementation

This document explains the differences between the CLI and web interfaces in RadBot, particularly focusing on how the Google Agent Development Kit (ADK) is used in each context.

## Overview

RadBot provides two main interfaces:
- **CLI Interface**: A command-line interface for interacting with the agent
- **Web Interface**: A web-based interface using the ADK web server

While both interfaces use the same underlying agent implementation, there are key differences in how they initialize and manage the agent.

## Key Differences

### Initialization Process

1. **CLI Interface**:
   - Custom initialization in `radbot/cli/main.py`
   - Manually creates and configures all components (Agent, Runner, SessionService, etc.)
   - Requires explicit handling of all parameters, including `app_name`
   - Runs in an async event loop managed by `asyncio.run(main())`

2. **Web Interface**:
   - Uses the ADK web server via `adk web` command
   - Agent initialization handled by ADK's web server
   - Parameters like `app_name` are automatically managed
   - Uses the root-level `agent.py` as the entry point

### Runner Initialization

The most critical difference is in how the `Runner` is initialized:

```python
# CLI Interface (explicit)
runner = Runner(
    agent=root_agent,
    app_name="radbot",  # Must be explicitly provided
    session_service=session_service,
    memory_service=memory_service
)

# Web Interface (handled by ADK)
# The ADK web server automatically creates the Runner with all required parameters
```

### Integration with External Services

1. **Home Assistant MCP**:
   - CLI: Needs careful handling of event loops, which can cause issues with the async MCP tools
   - Web: The ADK web server manages event loops properly for MCP tools

2. **Memory Service**:
   - CLI: Needs explicit initialization and attachment to the Runner
   - Web: Memory service integration handled more automatically

## Implementation Notes

### CLI-Specific Implementation

The CLI implementation in `radbot/cli/main.py` follows this pattern:

1. Creates basic tools
2. Attempts to set up Home Assistant integration
3. Falls back to a direct agent creation approach if needed
4. Manually sets up all components with explicit parameters using a direct approach:

```python
# Direct component creation in CLI
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from radbot.agent.agent import RadBotAgent

# Create components directly
session_service = InMemorySessionService()
root_agent = Agent(
    name="radbot_cli",
    model=config_manager.get_main_model(),
    instruction=instruction,
    tools=basic_tools,
    description="RadBot CLI agent"
)

# Create runner directly with explicit app_name
runner = Runner(
    agent=root_agent,
    app_name="radbot",  # Explicitly provide app_name
    session_service=session_service
)

# Create a wrapper RadBotAgent
agent = RadBotAgent(
    name="radbot_cli",
    session_service=session_service,
    tools=basic_tools,
    model=config_manager.get_main_model(),
    instruction=instruction
)

# Replace the auto-created runner with our explicit one
agent.runner = runner
agent.root_agent = root_agent
agent.app_name = "radbot"  # Ensure this is set
```

5. Uses a custom event loop for the main interaction loop

### Web-Specific Implementation

The web implementation relies on the root-level `agent.py` file:

1. Exports a `root_agent` object that ADK web can import
2. Sets up all tools, integrations, and memory services
3. Lets ADK handle Runner creation and event loop management

## Common Issues and Solutions

### Missing `app_name` Parameter

The Runner in ADK 0.3.0+ requires an `app_name` parameter:

```python
# Incorrect (missing app_name)
runner = Runner(
    agent=root_agent,
    session_service=session_service
)

# Correct
runner = Runner(
    agent=root_agent,
    app_name="radbot",  # Required parameter
    session_service=session_service
)
```

### Event Loop Conflicts

When using async MCP tools in the CLI:

```python
# Problem: Creates a new event loop inside an existing one
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
tools, exit_stack = loop.run_until_complete(_create_home_assistant_toolset_async())

# Solution: Check for existing event loop
try:
    existing_loop = asyncio.get_event_loop()
    if existing_loop.is_running():
        # Handle the case of a running loop
        return []
except RuntimeError:
    # No event loop exists, create a new one
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
```

## Best Practices

1. **CLI Development**:
   - Always explicitly provide all required parameters
   - Handle event loops carefully to avoid conflicts
   - Use try/except blocks to gracefully handle initialization failures

2. **Web Development**:
   - Follow ADK conventions for the root-level agent.py
   - Let ADK handle Runner creation and management
   - Use async/await correctly with ADK's event loop

By understanding these differences, you can avoid common issues and ensure both interfaces work correctly.
