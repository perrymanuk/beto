# Core Dependencies Installation and Configuration

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document covers the installation and configuration of the core dependencies required for the radbot agent framework.

## ADK Installation and Setup

### Installation

Google's Agent Development Kit (ADK) is the primary orchestration framework for our agent system. Install ADK using pip:

```bash
pip install google-adk
```

### ADK Configuration

ADK requires either a Google API key (for Google AI Studio) or Vertex AI credentials (for Google Cloud). The system will automatically detect which to use based on the `GOOGLE_GENAI_USE_VERTEXAI` environment variable.

#### Google AI Studio Setup

1. Visit [Google AI Studio](https://ai.google.dev/) and sign up
2. Generate an API key from the API Keys section
3. Set environment variables in `.env`:
   ```
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   GOOGLE_API_KEY=your_generated_api_key
   ```

#### Vertex AI Setup

1. Create a Google Cloud project
2. Enable the Vertex AI API
3. Set up Application Default Credentials:
   ```bash
   gcloud auth application-default login
   ```
4. Set environment variables in `.env`:
   ```
   GOOGLE_GENAI_USE_VERTEXAI=TRUE
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   GOOGLE_CLOUD_LOCATION=us-central1  # or your preferred region
   ```

## Qdrant Installation and Setup

Qdrant serves as our vector database for agent memory.

### Local Qdrant Setup with Docker

For development, we recommend running Qdrant locally using Docker:

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant
```

### Qdrant Cloud

For production, consider using [Qdrant Cloud](https://qdrant.tech/cloud):

1. Create an account on Qdrant Cloud
2. Create a new cluster
3. Note the URL and API key
4. Set environment variables in `.env`:
   ```
   QDRANT_URL=your_qdrant_cloud_url
   QDRANT_API_KEY=your_qdrant_api_key
   ```

### Qdrant Python Client

Install the Qdrant client:

```bash
pip install qdrant-client
```

## Model Context Protocol (MCP) Setup

For Home Assistant integration, we need the MCP SDK:

```bash
pip install modelcontextprotocol
```

### Home Assistant MCP Server Configuration

To enable the Home Assistant MCP Server:

1. Open Home Assistant
2. Go to Settings > Add-ons > Add-on Store
3. Find and install "Model Context Protocol Server"
4. Configure the integration
5. Create a Long-Lived Access Token:
   - Go to your profile page
   - Scroll to Long-Lived Access Tokens
   - Create a token with a descriptive name
6. Set the environment variables in `.env`:
   ```
   HA_MCP_SSE_URL=http://your_ha_host:8123/api/mcp_server/sse
   HA_AUTH_TOKEN=your_ha_long_lived_access_token
   ```

## Additional Dependencies

### Timezone Support

For the time tool functionality:

```bash
pip install tzdata
```

Python 3.9+ includes `zoneinfo` in the standard library.

### Environment Variable Management

For loading environment variables from the `.env` file:

```bash
pip install python-dotenv
```

## pyproject.toml Configuration

Create a `pyproject.toml` file with all dependencies:

```toml
[project]
name = "radbot"
version = "0.1.0"
description = "A modular AI agent framework using ADK, Qdrant, MCP, and A2A"
requires-python = ">=3.10"
dependencies = [
    "google-adk",
    "qdrant-client",
    "tzdata",
    "python-dotenv",
    "modelcontextprotocol",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "black",
    "isort",
    "flake8",
    "mypy",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

## Verifying the Installation

Create a simple script to verify ADK installation and configuration:

```python
# test_adk_setup.py
import os
from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Create a minimal agent
agent = Agent(
    name="test_agent",
    model="gemini-2.0-flash",
    instruction="Respond with a simple greeting.",
)

# Create a session service and runner
session_service = InMemorySessionService()
runner = Runner(
    agent=agent,
    app_name="test_app",
    session_service=session_service,
)

# Test the agent with a simple message
response = next(runner.run_async(user_id="test_user", message="Hello"))
print(f"Agent response: {response}")
```

Run the script:

```bash
python test_adk_setup.py
```

If configured correctly, this should output a friendly greeting from the test agent.

## Next Steps

After installing and configuring all dependencies:

1. Implement the base agent structure
2. Set up the Qdrant memory system
3. Create the core agent configuration system