# CLI Interface Implementation

This document details the implementation of the command-line interface (CLI) for the RaderBot agent framework, as well as the ADK web interface.

## Overview

The CLI interface provides a simple, interactive way to test and use the RaderBot agent. It serves both as a development tool for testing new features and as a basic user interface for interacting with the agent.

## Key Components

### 1. Agent Setup

The CLI initializes and configures the RaderBot agent with appropriate tools:

```python
def setup_agent() -> Optional[RaderBotAgent]:
    """Set up and configure the agent with tools and memory."""
    try:
        # Configure basic tools
        tools = [get_current_time, get_weather]
        
        # Create the agent with tools
        agent = create_agent(tools=tools)
        logger.info("Agent setup complete")
        return agent
    except Exception as e:
        logger.error(f"Error setting up agent: {str(e)}")
        return None
```

This function:
- Loads and configures the basic tools (time and weather)
- Creates an instance of RaderBotAgent using the factory function
- Handles any exceptions that might occur during setup
- Returns the configured agent or None if setup fails

### 2. User Interface

The CLI provides a simple text-based interface with commands:

```python
def display_welcome_message() -> None:
    """Display welcome message and instructions."""
    print("\n" + "=" * 60)
    print("RaderBot CLI Interface".center(60))
    print("=" * 60)
    print("Type your messages and press Enter to interact with the agent")
    print("Commands:")
    print("  /exit, /quit - Exit the application")
    print("  /reset       - Reset the conversation history")
    print("  /help        - Show this help message")
    print("=" * 60)
```

### 3. Command Processing

The CLI supports special commands prefixed with a slash (/):

```python
def process_commands(command: str, agent: RaderBotAgent, user_id: str) -> bool:
    """Process special commands."""
    if command in ["exit", "quit"]:
        print("\nExiting RaderBot CLI. Goodbye!")
        return True
    elif command == "reset":
        try:
            agent.reset_session(user_id)
            print("\nConversation history has been reset.")
        except Exception as e:
            print(f"\nError resetting conversation: {str(e)}")
        return False
    elif command == "help":
        display_welcome_message()
        return False
    else:
        print(f"\nUnknown command: /{command}")
        print("Type /help for available commands")
        return False
```

This function:
- Processes exit/quit commands by returning True
- Handles reset commands by calling the agent's reset_session method
- Shows help information when requested
- Provides feedback for unknown commands

### 4. Main Loop

The main interaction loop handles user input and agent responses:

```python
def main():
    """Main CLI entry point."""
    display_welcome_message()
    
    # Set up agent
    agent = setup_agent()
    
    if not agent:
        print("Failed to set up agent. Exiting.")
        sys.exit(1)
    
    # Generate a random user ID for this session
    user_id = str(uuid.uuid4())
    logger.info(f"Starting session with user_id: {user_id}")
    
    # Main interaction loop
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ")
            
            # Check for commands
            if user_input.startswith('/'):
                command = user_input[1:].strip().lower()
                should_exit = process_commands(command, agent, user_id)
                if should_exit:
                    sys.exit(0)
                continue
            
            # Process regular message
            response = agent.process_message(user_id, user_input)
            print(f"\nRaderBot: {response}")
            
        except KeyboardInterrupt:
            print("\n\nSession interrupted. Exiting.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            print(f"\nAn error occurred: {str(e)}")
            print("Continuing with new message...")
```

This function:
- Sets up the agent and generates a unique user ID for the session
- Enters a continuous input/response loop
- Checks for command prefixes and processes them accordingly
- Sends regular messages to the agent and displays responses
- Handles interruptions and errors gracefully

## Error Handling

The CLI implements multi-level error handling:

1. **Setup Errors**: If agent setup fails, the application exits with an error message
2. **Command Errors**: Errors during command processing are caught and reported without exiting
3. **Processing Errors**: Errors during message processing are caught, logged, and allow continuation
4. **Application-Level Errors**: Critical errors at the application level are caught, logged, and cause a graceful exit

## Session Management

Each CLI session uses a unique user ID (UUID) to maintain conversation context:

```python
user_id = str(uuid.uuid4())
```

This ensures that:
- Each CLI session has its own conversation history
- The `/reset` command can clear the history for the current session only
- Multiple CLI instances can run independently without affecting each other's state

## Usage

The CLI can be run using:

```bash
make run-cli
```

Or directly with:

```bash
python -m raderbot.cli.main
```

## ADK Web Interface

Google ADK provides a web interface that can be used to interact with RaderBot through a browser. The web interface can be launched using:

```bash
make run-web        # Using the provided Makefile target
# or
adk web -a raderbot  # Directly using the ADK command
```

### ADK Web Requirements

For the ADK web interface to work properly, the agent module must expose a `root_agent` attribute. RaderBot implements this in `raderbot/agent/__init__.py` by creating and exporting a default agent:

```python
# Setup a default root_agent for ADK web command
root_agent = AgentFactory.create_root_agent(
    name="raderbot_web",
    tools=[get_current_time, get_weather]
)

# Export it in __all__
__all__ = [
    # ...other exports
    'root_agent'
]
```

When `adk web -a raderbot` is run, the ADK web server:

1. Imports the `raderbot` module
2. Looks for `raderbot.agent.root_agent`
3. Uses this agent to handle web UI interactions

### Customizing the Web Agent

To customize the web agent with additional tools or different configurations:

1. Modify the `root_agent` initialization in `raderbot/agent/__init__.py`
2. Add any necessary imports for tools or sub-agents
3. Restart the web server to apply changes

## Future Enhancements

Potential future enhancements for the CLI interface:

1. **Configuration Options**: Command-line arguments to configure the agent (model, tools, etc.)
2. **Scripted Mode**: Support for reading commands from a file or pipe
3. **Rich Text Formatting**: Improved output formatting with colors and styles
4. **Debug Commands**: Special commands for developers to inspect agent state
5. **Memory Commands**: Commands to view and manage the agent's memory
6. **Additional Tools**: Dynamic loading of additional tools based on configuration

## Integration with Overall System

The CLI and ADK web interfaces serve as multiple possible interfaces to the RaderBot agent system. They demonstrate how the RaderBotAgent class can be integrated into different environments while maintaining consistent behavior.

Other potential interfaces that could be implemented in the future include:
- Voice interface
- Chat application integration
- API endpoints

All of these would use the same underlying RaderBotAgent class and tools, just with different input/output mechanisms.