# Project Setup and Environment Configuration

This document details the initial setup of the RaderBot project, an AI agent framework built with Google's Agent Development Kit (ADK).

## Directory Structure

The project follows a modular structure to organize code effectively:

```
raderbot/
├── raderbot/
│   ├── __init__.py           # Package initialization
│   ├── agent.py              # Core agent definitions
│   ├── tools/
│   │   ├── __init__.py       # Tools package initialization 
│   │   ├── basic_tools.py    # Time, weather implementations
│   │   └── mcp_tools.py      # MCP integration tools
│   ├── memory/
│   │   ├── __init__.py       # Memory package initialization
│   │   └── qdrant.py         # Qdrant memory service
│   └── config/
│       ├── __init__.py       # Config package initialization
│       └── settings.py       # Configuration loading utilities
├── tests/                    # Test suite
├── docs/
│   └── implementation/       # Implementation docs
├── .env.example              # Example environment variables
├── pyproject.toml            # Project metadata and dependencies
├── Makefile                  # Build commands
└── README.md                 # Project overview
```

## Environment Setup

### Python Environment

The project requires Python 3.10+ as specified in the CLAUDE.md guidelines. We'll use uv for Python tooling as mentioned in the guidelines.

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - macOS/Linux: `source .venv/bin/activate`
   - Windows CMD: `.venv\Scripts\activate.bat`
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`

### Environment Variables

The following environment variables are required for the project:

```
# ADK Authentication (Choose one approach)
# For Google AI Studio API:
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_gemini_api_key

# OR For Vertex AI:
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=your-vertex-ai-region

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
# If using Qdrant Cloud:
# QDRANT_URL=your_qdrant_cloud_url
# QDRANT_API_KEY=your_qdrant_api_key

# Home Assistant MCP Configuration
HA_MCP_SSE_URL=http://your_ha_host:8123/api/mcp_server/sse
HA_AUTH_TOKEN=your_ha_long_lived_access_token
```

Copy the example `.env.example` file and customize for your environment:

```bash
cp .env.example .env
# Edit .env with your specific values
```

### Core Dependencies

The project has the following core dependencies:

- `google-adk`: Agent Development Kit for orchestrating agent behavior
- `qdrant-client`: Client for Qdrant vector database
- `zoneinfo` and `tzdata`: For timezone handling in the time tool
- `python-dotenv`: For loading environment variables from .env file
- `modelcontextprotocol`: MCP client for Home Assistant integration

These dependencies are defined in `pyproject.toml` and installed via the Makefile setup command.

## Makefile Commands

The project includes several essential commands in the Makefile:

- `make setup`: Install all dependencies
- `make test`: Run all tests
- `make test-unit`: Run unit tests
- `make lint`: Check code quality with flake8
- `make format`: Format code with Black and isort
- `make run-cli`: Launch the CLI interface
- `make run-scheduler`: Run the agent scheduler with optional arguments

## Next Steps

After setting up the project structure and environment:

1. Install core dependencies (ADK, Qdrant)
2. Begin implementing the base agent structure
3. Create the agent configuration system

See the other implementation documents for details on these next steps.