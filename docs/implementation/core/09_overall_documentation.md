# radbot Framework Documentation

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document provides an overview of the radbot Framework, a modular AI agent system built with Google's Agent Development Kit (ADK), Qdrant vector database, and Model Context Protocol (MCP).

## System Architecture

radbot is designed as a modular, extensible framework with the following core components:

1. **Agent System**: Core agent orchestration using Google's ADK
2. **Memory System**: Persistent agent memory using Qdrant vector database
3. **Tools System**: Basic tools and MCP integration for Home Assistant
4. **Communication System**: Inter-agent communication protocols

### Architecture Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                        radbot Framework                     │
├───────────────┬───────────────────┬───────────────┬───────────┤
│  Agent System │   Memory System   │  Tools System │   MCP     │
│     (ADK)     │     (Qdrant)      │     (ADK)     │ Integration│
├───────────────┼───────────────────┼───────────────┼───────────┤
│  Main Agent   │ QdrantMemoryService│ Basic Tools  │   Home    │
│               │                   │               │ Assistant │
├───────────────┼───────────────────┼───────────────┼───────────┤
│  Sub-agents   │ Embedding Service │ Memory Tools  │           │
│ (Specialized) │                   │               │           │
└───────────────┴───────────────────┴───────────────┴───────────┘
```

## Core Components

### 1. Agent System

The agent system is built on Google's Agent Development Kit (ADK) and provides:

- **Main Coordinator Agent**: Orchestrates user interactions and delegates to specialized agents
- **Sub-agents**: Specialized agents for specific tasks (summarization, research, Home Assistant)
- **Agent Manager**: Handles agent creation, configuration, and communication

Key classes:
- `radbotAgent`: Main agent wrapper
- `AgentManager`: Manages agent hierarchies and communication

### 2. Memory System

The memory system uses Qdrant as a vector database for persistent agent memory:

- **QdrantMemoryService**: Custom implementation of ADK's memory service interface
- **Embedding Service**: Handles text vectorization using Gemini or SentenceTransformers
- **Memory Tools**: Agent tools for searching and storing memory
- **Memory Ingestion**: Pipeline for processing and storing conversation data

Key classes:
- `QdrantMemoryService`: Core memory service
- `EmbeddingModel`: Embedding model wrapper
- `MemoryIngestionService`: Background service for memory processing

### 3. Tools System

The tools system provides various capabilities to the agents:

- **Basic Tools**: Time and weather information tools
- **Memory Tools**: Tools for searching and storing memory
- **State Tools**: Tools for managing shared session state

Key classes and functions:
- `get_current_time`: Time information tool
- `get_weather`: Weather information tool
- `search_past_conversations`: Memory search tool

### 4. MCP Integration

The MCP integration connects the agent to external services using the Model Context Protocol:

- **Home Assistant MCP**: Integration with Home Assistant for smart home control
- **MCPToolset**: ADK's tool for MCP server connections
- **Home Assistant Agent**: Specialized agent for smart home control

Key classes:
- `HomeAssistantMCP`: Manager for Home Assistant MCP integration
- `create_home_assistant_toolset`: Factory function for Home Assistant MCP toolset

## Configuration System

The configuration system provides flexible configuration options:

- **Environment Variables**: Basic configuration via `.env` file
- **Instruction Files**: Agent prompts stored as Markdown files
- **Schema Models**: Pydantic models for structured data interfaces
- **Model Selection**: Configuration for LLM model selection

Key classes:
- `ConfigManager`: Core configuration manager

## Installation and Setup

### Prerequisites

- Python 3.10+
- Docker (for local Qdrant instance)
- Google API key or Vertex AI access
- Home Assistant instance with MCP Server integration (optional)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/radbot.git
   cd radbot
   ```

2. **Set up the environment**:
   ```bash
   # Create and activate virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   make setup
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configuration
   ```

5. **Start Qdrant** (if using local instance):
   ```bash
   docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant
   ```

6. **Run the CLI**:
   ```bash
   make run-cli
   ```

## Usage Examples

### Basic Interaction

```python
from radbot.agent import create_agent

# Create an agent with default configuration
agent = create_agent()

# Process a user message
response = agent.process_message(user_id="user123", message="What's the time in New York?")
print(response)
```

### Memory-Enabled Agent

```python
from radbot.agent_factory import create_memory_enabled_agent

# Create an agent with memory capabilities
agent = create_memory_enabled_agent()

# Process a message with memory context
response = agent.process_message(user_id="user123", message="What did we talk about yesterday?")
print(response)
```

### Home Assistant Integration

```python
from radbot.agent import create_agent
from radbot.tools.mcp_tools import home_assistant_mcp

# Create an agent
agent = create_agent()

# Initialize Home Assistant MCP
if home_assistant_mcp.initialize():
    # Add Home Assistant tools to the agent
    home_assistant_mcp.add_to_agent(agent)

# Process a Home Assistant command
response = agent.process_message(user_id="user123", message="Turn on the living room lights")
print(response)
```

## Customization

### Adding Custom Tools

```python
from radbot.agent import create_agent

# Define a custom tool
def my_custom_tool(parameter: str) -> dict:
    """
    A custom tool for the agent.
    
    Use this tool when the user asks about custom functionality.
    
    Args:
        parameter: The input parameter
        
    Returns:
        dict: The result
    """
    # Tool implementation
    return {"status": "success", "result": f"Processed: {parameter}"}

# Create an agent with the custom tool
agent = create_agent(tools=[my_custom_tool])
```

### Custom Agent Instructions

Create a custom instruction file in `radbot/config/default_configs/instructions/my_custom_agent.md` and use it:

```python
from radbot.agent import create_agent

# Create an agent with custom instruction
agent = create_agent(instruction_name="my_custom_agent")
```

## Error Handling

The framework includes comprehensive error handling:

1. **Tool Errors**: All tools return structured status information
2. **MCP Connection Errors**: Robust error handling for MCP connections
3. **Memory Errors**: Fallbacks for memory service failures
4. **Agent Errors**: Graceful handling of agent execution failures

Example error handling:

```python
from radbot.tools.mcp_tools import home_assistant_mcp
from radbot.tools.mcp_utils import test_home_assistant_connection

# Test the Home Assistant connection
result = test_home_assistant_connection()

if result["success"]:
    print("Connected to Home Assistant MCP")
else:
    print(f"Connection failed: {result['error']}")
```

## Testing

The framework includes tests for all components:

- **Unit Tests**: Tests for individual functions and classes
- **Integration Tests**: Tests for component interactions
- **Agent Tests**: Tests for agent behavior
- **Memory Tests**: Tests for memory storage and retrieval

Run the tests with:

```bash
make test
```

## Security Considerations

The framework includes several security considerations:

1. **API Key Management**: Secure storage of API keys in environment variables
2. **Authorization**: Token-based authentication for Home Assistant MCP
3. **Input Validation**: Validation of user inputs and tool parameters
4. **Error Handling**: Graceful handling of security-related errors

## Performance Optimization

Several optimizations are included:

1. **Efficient Embedding**: Smart caching and batching of embeddings
2. **Selective Memory Storage**: Only storing relevant conversation parts
3. **Model Selection**: Using appropriate models for different tasks
4. **Session State**: Efficient use of session state for context passing

## Next Steps and Future Enhancements

Potential enhancements for future development:

1. **Enhanced Memory Strategies**: More sophisticated memory retrieval strategies
2. **Additional MCP Integrations**: Integration with other MCP servers
3. **Web Interface**: Building a web interface for easier interaction
4. **Voice Integration**: Adding speech-to-text and text-to-speech for voice interaction

## Support Resources

- **Documentation**: Comprehensive documentation in the `/docs` directory
- **Examples**: Code examples in the `/examples` directory
- **Issue Tracker**: GitHub issue tracker for reporting bugs and requesting features
- **Wiki**: Wiki for community contributions and additional documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.