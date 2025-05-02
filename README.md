# Radbot: Modular AI Agent Framework

A sophisticated, modular AI agent framework leveraging Google's Agent Development Kit (ADK), Qdrant vector database, Model Context Protocol (MCP), and Agent2Agent (A2A) protocols.

## Features

- **ADK-based Orchestration**: Uses Google's Agent Development Kit as the core orchestration layer
- **Multiple LLM Support**: Configurable to use various Google Gemini models (Flash, Pro 2.5)
- **Persistent Memory**: Integrated Qdrant vector database for agent memory
- **External Integration**: MCP protocol support for connecting to services like Home Assistant
- **Agent Communication**: Internal sub-agent communication and optional A2A protocol support
- **Modular Design**: Clear separation of concerns for easy extension and maintenance

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/perrymanuk/radbot.git
   cd radbot
   ```

2. Set up your environment:
   ```
   make setup
   ```

3. Create your `.env` file from the example:
   ```
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

## Usage

Run the CLI:
```
make run-cli
```

Run the scheduler with additional arguments:
```
make run-scheduler ARGS="--additional-args"
```

## Development

- Run tests: `make test`
- Run unit tests only: `make test-unit`
- Run integration tests only: `make test-integration`
- Run a specific test: `pytest tests/path/to/test_file.py::TestClass::test_method`
- Format code: `make format`
- Lint code: `make lint`

## Project Structure

- `/radbot/agent`: Core agent logic and definitions
- `/radbot/tools`: Tool implementations (time, weather, etc.)
- `/radbot/memory`: Memory system with Qdrant integration
- `/radbot/cli`: Command-line interfaces and runners
- `/docs/implementation`: Implementation documentation
- `/tests`: Unit and integration tests

## Documentation

See the `docs/implementation` directory for detailed documentation on each feature.

## License

MIT