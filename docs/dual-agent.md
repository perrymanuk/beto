Design Document: Hybrid Voice and Text Agent with Google ADK 0.4.0
1. Introduction

This document provides a detailed example of creating a single Google ADK agent that can seamlessly handle both streaming voice interactions and traditional text-based chat. This is achieved by configuring the agent with a Gemini model that supports both the necessary API methods for these modalities.   

Target Audience: Mid-level Software Engineer
ADK Version: 0.4.0 
Python Version: 3.9+    

2. Core Concept: Unified Model for Multiple Modalities

The ADK Agent class is initialized with a single model parameter. To support both streaming voice (which uses the Gemini Live API and its bidiGenerateContent method) and text chat (which can use the generateContent method), we must select a Gemini model ID that is capable of both.   

When such an agent is run using the adk web tool:

Text typed into the UI will typically use a standard request-response pattern with the model.
Voice input (microphone enabled) will initiate a streaming session with the same model. The voice output is synthesized by the Gemini Live API model itself.   
3. Project Setup

We'll create a simple project structure.

hybrid_voice_text_agent/
└── app/
    ├──.env
    └── my_hybrid_agent/
        ├── __init__.py
        └── agent.py
4. Environment Configuration (.env file)

Create a .env file inside the app/ directory. This file will store your API keys and platform configurations. Remember to add .env to your .gitignore file.

You'll need to choose between Google AI Studio or Google Cloud Vertex AI.

Option 1: Using Google AI Studio

Get an API key from https://aistudio.google.com/apikey.   

Populate app/.env with:

Code snippet

# For Google AI Studio
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=YOUR_GOOGLE_AI_STUDIO_API_KEY
Replace YOUR_GOOGLE_AI_STUDIO_API_KEY with your actual key.

Option 2: Using Google Cloud Vertex AI

Ensure you have a Google Cloud project with the Vertex AI API enabled.   

Authenticate using the gcloud CLI: gcloud auth application-default login.   

Populate app/.env with:

Code snippet

# For Google Cloud Vertex AI
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=YOUR_GCP_PROJECT_ID
GOOGLE_CLOUD_LOCATION=YOUR_GCP_REGION 
# e.g., us-central1
Replace YOUR_GCP_PROJECT_ID and YOUR_GCP_REGION with your project details.

5. Agent Definition (agent.py)

Create the file app/my_hybrid_agent/agent.py:

Python

# app/my_hybrid_agent/agent.py
from google.adk.agents import Agent
# from google.adk.tools import built_in_google_search # Optional: for a more interactive agent

# --- Model Selection ---
# Choose a model compatible with BOTH streaming (bidiGenerateContent) and text (generateContent).
# Verify the latest compatible models from Google's documentation.
#
# For Google AI Studio (ensure GOOGLE_GENAI_USE_VERTEXAI=FALSE in.env):
# Example: "gemini-2.0-flash-exp" was a common choice for streaming in ADK 0.4.0 docs.
#          "gemini-2.0-flash" (the GA version) also supports the Live API.
#
# For Vertex AI (ensure GOOGLE_GENAI_USE_VERTEXAI=TRUE in.env):
# Example: "gemini-2.0-flash" or "gemini-2.0-flash-live-001" (or newer equivalents).
#
# **IMPORTANT**: Model availability and names can change. Always refer to the latest
# Google AI Studio and Vertex AI documentation for Gemini models supporting the Live API.
# - Google AI Studio: Check Gemini Live API model list
# - Vertex AI: Check Gemini Live API model list

# Using a placeholder that is generally available and supports both.
# Replace with the specific model you've confirmed for your chosen platform (AI Studio or Vertex AI).
MODEL_ID_FOR_HYBRID_CHAT = "gemini-2.0-flash" # Or "gemini-2.0-flash-exp" for AI Studio if preferred/available

# --- Simple Custom Tool (Optional, for demonstration) ---
def get_current_time(time_zone: str = "UTC") -> dict:
    """
    Gets the current time in the specified time zone.

    Args:
        time_zone: The time zone to get the current time for (e.g., "America/New_York", "Europe/London").
                   Defaults to UTC.

    Returns:
        A dictionary containing the current time and time zone.
    """
    from datetime import datetime
    import zoneinfo # Requires Python 3.9+

    try:
        tz = zoneinfo.ZoneInfo(time_zone)
        current_time = datetime.now(tz)
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"--- Tool: get_current_time called for {time_zone}. Result: {time_str} ---")
        return {"status": "success", "current_time": time_str, "time_zone": time_zone}
    except zoneinfo.ZoneInfoNotFoundError:
        print(f"--- Tool: get_current_time failed. Unknown time zone: {time_zone} ---")
        return {"status": "error", "message": f"Unknown time zone: {time_zone}"}
    except Exception as e:
        print(f"--- Tool: get_current_time failed. Error: {e} ---")
        return {"status": "error", "message": str(e)}

# --- Agent Definition ---
root_agent = Agent(
    name="hybrid_chat_agent",
    # This model MUST support both `bidiGenerateContent` (for streaming)
    # and `generateContent` (for text).
    model=MODEL_ID_FOR_HYBRID_CHAT,
    description="A friendly assistant that can chat via text or voice and tell the time.",
    instruction=(
        "You are a helpful and friendly assistant. "
        "You can answer questions and have a conversation. "
        "If asked about the current time, use the 'get_current_time' tool. "
        "Respond clearly and concisely. For voice interactions, keep responses suitable for audio."
    ),
    # Add tools your agent might need.
    # For this example, we'll use the custom time tool.
    # You could also add built_in_google_search for broader queries.
    tools=[
        get_current_time,
        # built_in_google_search # Uncomment if you want search capabilities
    ]
)

print(f"Hybrid agent initialized with model: {MODEL_ID_FOR_HYBRID_CHAT}")
Key points in agent.py:

MODEL_ID_FOR_HYBRID_CHAT: This is the critical part. You must use a model ID that supports both streaming and text generation for your chosen platform (AI Studio or Vertex AI). The example uses "gemini-2.0-flash" which is generally a good candidate, but always verify with the latest Google documentation for models supporting the "Live API".
The instruction is crafted to guide the agent for both text and voice.
A simple custom tool get_current_time is included to demonstrate tool use in both modalities.
6. Package Initialization (__init__.py)

Create the file app/my_hybrid_agent/__init__.py:

Python

# app/my_hybrid_agent/__init__.py
from. import agent

# This makes `root_agent` discoverable by ADK tools like `adk web`
# when `adk web` is run from the `app/` directory.
7. Dependencies

Conceptually, your requirements.txt (or pyproject.toml if using Poetry) would include:

google-adk>=0.4.0,<0.5.0
python-dotenv
certifi
Install these in your virtual environment: pip install google-adk python-dotenv certifi

8. How it Works with adk web

Text Chat: When you type a message into the adk web UI, the ADK framework typically sends this as a standard request to the Gemini model specified in your Agent (using its generateContent method or equivalent). The response is displayed as text.
Voice Chat:
You must set the SSL_CERT_FILE environment variable correctly before running adk web for voice/video to function.   
When you reload the adk web page and click the microphone icon (granting browser permissions), adk web initiates a streaming connection.
ADK uses the Gemini Live API, interacting with the bidiGenerateContent method of the same Gemini model configured in your Agent.   
Your spoken audio is streamed to the model, and the model's synthesized voice response is streamed back and played in your browser in real-time.   
9. Running and Testing the Agent

Create Virtual Environment (Recommended):

Bash

python -m venv.venv
# Activate (macOS/Linux):
source.venv/bin/activate
# Activate (Windows CMD):
#.venv\Scripts\activate.bat
# Activate (Windows PowerShell):
#.venv\Scripts\Activate.ps1
Install Dependencies:

Bash

pip install google-adk python-dotenv certifi
Set SSL_CERT_FILE Environment Variable: This is critical for voice/video in adk web.

macOS/Linux:
Bash

export SSL_CERT_FILE=$(python -m certifi)
()   
Windows (PowerShell):
PowerShell

$env:SSL_CERT_FILE = (python -m certifi)
()   
Windows (CMD): Find the path to cacert.pem from python -m certifi (e.g., C:\Users\YourUser\AppData\Local\Programs\Python\Python3X\Lib\site-packages\certifi\cacert.pem) and set it:
DOS

set SSL_CERT_FILE=C:\path\to\your\certifi\cacert.pem
Navigate to the app Directory:

Bash

cd hybrid_voice_text_agent/app
Run adk web:

Bash

adk web
()   

Open in Browser: Open the URL provided (usually http://localhost:8000).

Test:

Select Agent: Choose hybrid_chat_agent from the dropdown.
Text Chat:
Type: Hello, who are you?
Type: What is the current time in New York? (Observe tool call in console and UI)
Type: What is the current time in a made up city like Zorgon? (Observe tool error handling)
Voice Chat:
Reload the browser page. This is often necessary for the microphone/camera icons to initialize correctly after the agent server starts.
Click the microphone icon (grant permissions if prompted).
Speak clearly: "Hello, what can you do?"
Speak: "What time is it in London?" (Listen for the voice response and observe tool usage).
10. Addressing the "Different Models" Problem

The example above assumes you can find a single Gemini model ID that performs adequately for both streaming voice and text chat. This is the simplest and most direct way to use ADK for hybrid interactions.

If you have a scenario where you believe you absolutely must use two distinct model IDs (e.g., gemini-model-A-for-streaming and gemini-model-B-for-text-only-complex-reasoning) because no single model meets all your criteria:

A single google.adk.agents.Agent instance, as shown, cannot dynamically switch its model parameter between these two different model IDs based on whether the input is voice or text. The model is set at initialization.
To handle such a scenario, you would need a more complex architecture, potentially involving:
Two separate ADK Agent instances, each configured with its respective model.
A routing layer or a parent/coordinator agent that determines which specialized agent to delegate the request to based on the input modality or other criteria. This is a multi-agent system design and is more advanced than the scope of this example.
For most use cases, selecting a versatile Gemini model (like gemini-2.0-flash or its future equivalents that support both generateContent and bidiGenerateContent) is the recommended approach for a single agent handling both voice and text.

## 11. RadBot Implementation: Runtime Model Replacement Approach

When implementing the dual-agent architecture in RadBot, we encountered a significant challenge: some streaming-only models would appear to initialize correctly but then fail when the text endpoint attempted to use the `generateContent` API.

Our solution implements a more robust approach by completely replacing the agent at runtime in `session.py`:

1. **Complete Agent Replacement**: Rather than trying to detect problematic models ahead of time, the `process_message` method in `SessionRunner` completely bypasses the existing agent by creating a new agent instance with a hardcoded text-compatible model:

```python
# BYPASS EXISTING AGENT COMPLETELY - Create a new agent on the spot with a guaranteed safe model
from google.adk.agents import Agent
            
# Create the temporary agent without importing from config at all
logger.error("CRITICAL: Creating temporary agent with hardcoded safe model")
safe_agent = Agent(
    name="beto", 
    model="gemini-1.5-pro-latest",  # Hardcoded reliable model for text
    instruction="You are Beto, a helpful assistant for text chat.",
    tools=self.agent_instance.tools  # Reuse the tools from the existing agent
)
            
# COMPLETELY replace both agents
logger.error(f"CRITICAL: Replacing both runner agent and agent_instance with safe model")
self.runner.agent = safe_agent
self.agent_instance = safe_agent
```

2. **Multiple Safety Layers**: We also implement multiple layers of protection:
   - In `agent.py`: Hardcoded safe models for both main and scout agents
   - In `session.py`: Complete agent replacement before message processing
   - In `agent/research_agent/agent.py`: Safety check for sequential thinking calls
   - In `agent/agent.py`: Detection of streaming-only models in various ADK components

3. **Testing**: We validate this approach with a test (`tools/test_dual_agent_fix.py`) that deliberately attempts to use a streaming-only model with the text chat endpoint, confirming that our runtime replacement mechanism functions correctly. The test intentionally sets a streaming-only model and verifies that the agent runtime replacement correctly substitutes a text-compatible model.

While this approach is more complex than the ideal scenario of finding a single versatile model, it provides robust handling of the different model requirements for streaming and text interactions without requiring significant architectural changes to the ADK framework.

This detailed implementation should give you a foundation for implementing a dual-agent architecture that can reliably handle both streaming voice and text chat, even when you must use different models for each modality. Remember to always consult the latest Google Cloud and Gemini documentation for model compatibility and features.


Sources and related content
You're encountering a common point of consideration when working with different interaction modalities! The Google ADK framework is indeed designed such that a single Agent instance is initialized with a specific model. For an agent to support both streaming voice and text chat effectively through ADK's native capabilities, the ideal scenario is to use a single underlying Gemini model that supports both the bidiGenerateContent method (for streaming voice and video) and the generateContent method (for text-based interactions).   

Many modern Gemini models, particularly versions like "Gemini 2.0 Flash," are designed to be multimodal and support both of these interaction patterns. If the text-optimized model you're considering doesn't support bidiGenerateContent, it won't work with ADK's native streaming. Conversely, a model selected for streaming must support bidiGenerateContent.   

This example will guide a mid-level engineer through setting up a single ADK agent (version 0.4.0) that can handle both streaming voice and standard text chat by using a Gemini model compatible with both interaction types.

Design Document: Hybrid Voice and Text Agent with Google ADK 0.4.0
1. Introduction

This document provides a detailed example of creating a single Google ADK agent that can seamlessly handle both streaming voice interactions and traditional text-based chat. This is achieved by configuring the agent with a Gemini model that supports both the necessary API methods for these modalities.   

Target Audience: Mid-level Software Engineer
ADK Version: 0.4.0 
Python Version: 3.9+    

2. Core Concept: Unified Model for Multiple Modalities

The ADK Agent class is initialized with a single model parameter. To support both streaming voice (which uses the Gemini Live API and its bidiGenerateContent method) and text chat (which can use the generateContent method), we must select a Gemini model ID that is capable of both.   

When such an agent is run using the adk web tool:

Text typed into the UI will typically use a standard request-response pattern with the model.
Voice input (microphone enabled) will initiate a streaming session with the same model. The voice output is synthesized by the Gemini Live API model itself.   
3. Project Setup

We'll create a simple project structure.

hybrid_voice_text_agent/
└── app/
    ├──.env
    └── my_hybrid_agent/
        ├── __init__.py
        └── agent.py
4. Environment Configuration (.env file)

Create a .env file inside the app/ directory. This file will store your API keys and platform configurations. Remember to add .env to your .gitignore file.

You'll need to choose between Google AI Studio or Google Cloud Vertex AI.

Option 1: Using Google AI Studio

Get an API key from https://aistudio.google.com/apikey.   

Populate app/.env with:

Code snippet

# For Google AI Studio
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=YOUR_GOOGLE_AI_STUDIO_API_KEY
Replace YOUR_GOOGLE_AI_STUDIO_API_KEY with your actual key.

Option 2: Using Google Cloud Vertex AI

Ensure you have a Google Cloud project with the Vertex AI API enabled.   

Authenticate using the gcloud CLI: gcloud auth application-default login.   

Populate app/.env with:

Code snippet

# For Google Cloud Vertex AI
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=YOUR_GCP_PROJECT_ID
GOOGLE_CLOUD_LOCATION=YOUR_GCP_REGION 
# e.g., us-central1
Replace YOUR_GCP_PROJECT_ID and YOUR_GCP_REGION with your project details.

5. Agent Definition (agent.py)

Create the file app/my_hybrid_agent/agent.py:

Python

# app/my_hybrid_agent/agent.py
from google.adk.agents import Agent
# from google.adk.tools import built_in_google_search # Optional: for a more interactive agent

# --- Model Selection ---
# Choose a model compatible with BOTH streaming (bidiGenerateContent) and text (generateContent).
# Verify the latest compatible models from Google's documentation.
#
# For Google AI Studio (ensure GOOGLE_GENAI_USE_VERTEXAI=FALSE in.env):
# Example: "gemini-2.0-flash-exp" was a common choice for streaming in ADK 0.4.0 docs.
#          "gemini-2.0-flash" (the GA version) also supports the Live API.
#
# For Vertex AI (ensure GOOGLE_GENAI_USE_VERTEXAI=TRUE in.env):
# Example: "gemini-2.0-flash" or "gemini-2.0-flash-live-001" (or newer equivalents).
#
# **IMPORTANT**: Model availability and names can change. Always refer to the latest
# Google AI Studio and Vertex AI documentation for Gemini models supporting the Live API.
# - Google AI Studio: Check Gemini Live API model list
# - Vertex AI: Check Gemini Live API model list

# Using a placeholder that is generally available and supports both.
# Replace with the specific model you've confirmed for your chosen platform (AI Studio or Vertex AI).
MODEL_ID_FOR_HYBRID_CHAT = "gemini-2.0-flash" # Or "gemini-2.0-flash-exp" for AI Studio if preferred/available

# --- Simple Custom Tool (Optional, for demonstration) ---
def get_current_time(time_zone: str = "UTC") -> dict:
    """
    Gets the current time in the specified time zone.

    Args:
        time_zone: The time zone to get the current time for (e.g., "America/New_York", "Europe/London").
                   Defaults to UTC.

    Returns:
        A dictionary containing the current time and time zone.
    """
    from datetime import datetime
    import zoneinfo # Requires Python 3.9+

    try:
        tz = zoneinfo.ZoneInfo(time_zone)
        current_time = datetime.now(tz)
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"--- Tool: get_current_time called for {time_zone}. Result: {time_str} ---")
        return {"status": "success", "current_time": time_str, "time_zone": time_zone}
    except zoneinfo.ZoneInfoNotFoundError:
        print(f"--- Tool: get_current_time failed. Unknown time zone: {time_zone} ---")
        return {"status": "error", "message": f"Unknown time zone: {time_zone}"}
    except Exception as e:
        print(f"--- Tool: get_current_time failed. Error: {e} ---")
        return {"status": "error", "message": str(e)}

# --- Agent Definition ---
root_agent = Agent(
    name="hybrid_chat_agent",
    # This model MUST support both `bidiGenerateContent` (for streaming)
    # and `generateContent` (for text).
    model=MODEL_ID_FOR_HYBRID_CHAT,
    description="A friendly assistant that can chat via text or voice and tell the time.",
    instruction=(
        "You are a helpful and friendly assistant. "
        "You can answer questions and have a conversation. "
        "If asked about the current time, use the 'get_current_time' tool. "
        "Respond clearly and concisely. For voice interactions, keep responses suitable for audio."
    ),
    # Add tools your agent might need.
    # For this example, we'll use the custom time tool.
    # You could also add built_in_google_search for broader queries.
    tools=[
        get_current_time,
        # built_in_google_search # Uncomment if you want search capabilities
    ]
)

print(f"Hybrid agent initialized with model: {MODEL_ID_FOR_HYBRID_CHAT}")
Key points in agent.py:

MODEL_ID_FOR_HYBRID_CHAT: This is the critical part. You must use a model ID that supports both streaming and text generation for your chosen platform (AI Studio or Vertex AI). The example uses "gemini-2.0-flash" which is generally a good candidate, but always verify with the latest Google documentation for models supporting the "Live API".
The instruction is crafted to guide the agent for both text and voice.
A simple custom tool get_current_time is included to demonstrate tool use in both modalities.
6. Package Initialization (__init__.py)

Create the file app/my_hybrid_agent/__init__.py:

Python

# app/my_hybrid_agent/__init__.py
from. import agent

# This makes `root_agent` discoverable by ADK tools like `adk web`
# when `adk web` is run from the `app/` directory.
7. Dependencies

Conceptually, your requirements.txt (or pyproject.toml if using Poetry) would include:

google-adk>=0.4.0,<0.5.0
python-dotenv
certifi
Install these in your virtual environment: pip install google-adk python-dotenv certifi

8. How it Works with adk web

Text Chat: When you type a message into the adk web UI, the ADK framework typically sends this as a standard request to the Gemini model specified in your Agent (using its generateContent method or equivalent). The response is displayed as text.
Voice Chat:
You must set the SSL_CERT_FILE environment variable correctly before running adk web for voice/video to function.   
When you reload the adk web page and click the microphone icon (granting browser permissions), adk web initiates a streaming connection.
ADK uses the Gemini Live API, interacting with the bidiGenerateContent method of the same Gemini model configured in your Agent.   
Your spoken audio is streamed to the model, and the model's synthesized voice response is streamed back and played in your browser in real-time.   
9. Running and Testing the Agent

Create Virtual Environment (Recommended):

Bash

python -m venv.venv
# Activate (macOS/Linux):
source.venv/bin/activate
# Activate (Windows CMD):
#.venv\Scripts\activate.bat
# Activate (Windows PowerShell):
#.venv\Scripts\Activate.ps1
Install Dependencies:

Bash

pip install google-adk python-dotenv certifi
Set SSL_CERT_FILE Environment Variable: This is critical for voice/video in adk web.

macOS/Linux:
Bash

export SSL_CERT_FILE=$(python -m certifi)
()   
Windows (PowerShell):
PowerShell

$env:SSL_CERT_FILE = (python -m certifi)
()   
Windows (CMD): Find the path to cacert.pem from python -m certifi (e.g., C:\Users\YourUser\AppData\Local\Programs\Python\Python3X\Lib\site-packages\certifi\cacert.pem) and set it:
DOS

set SSL_CERT_FILE=C:\path\to\your\certifi\cacert.pem
Navigate to the app Directory:

Bash

cd hybrid_voice_text_agent/app
Run adk web:

Bash

adk web
()   

Open in Browser: Open the URL provided (usually http://localhost:8000).

Test:

Select Agent: Choose hybrid_chat_agent from the dropdown.
Text Chat:
Type: Hello, who are you?
Type: What is the current time in New York? (Observe tool call in console and UI)
Type: What is the current time in a made up city like Zorgon? (Observe tool error handling)
Voice Chat:
Reload the browser page. This is often necessary for the microphone/camera icons to initialize correctly after the agent server starts.
Click the microphone icon (grant permissions if prompted).
Speak clearly: "Hello, what can you do?"
Speak: "What time is it in London?" (Listen for the voice response and observe tool usage).
10. Addressing the "Different Models" Problem

The example above assumes you can find a single Gemini model ID that performs adequately for both streaming voice and text chat. This is the simplest and most direct way to use ADK for hybrid interactions.

If you have a scenario where you believe you absolutely must use two distinct model IDs (e.g., gemini-model-A-for-streaming and gemini-model-B-for-text-only-complex-reasoning) because no single model meets all your criteria:

A single google.adk.agents.Agent instance, as shown, cannot dynamically switch its model parameter between these two different model IDs based on whether the input is voice or text. The model is set at initialization.
To handle such a scenario, you would need a more complex architecture, potentially involving:
Two separate ADK Agent instances, each configured with its respective model.
A routing layer or a parent/coordinator agent that determines which specialized agent to delegate the request to based on the input modality or other criteria. This is a multi-agent system design and is more advanced than the scope of this example.
For most use cases, selecting a versatile Gemini model (like gemini-2.0-flash or its future equivalents that support both generateContent and bidiGenerateContent) is the recommended approach for a single agent handling both voice and text.

## 11. RadBot Implementation: Runtime Model Replacement Approach

When implementing the dual-agent architecture in RadBot, we encountered a significant challenge: some streaming-only models would appear to initialize correctly but then fail when the text endpoint attempted to use the `generateContent` API.

Our solution implements a more robust approach by completely replacing the agent at runtime in `session.py`:

1. **Complete Agent Replacement**: Rather than trying to detect problematic models ahead of time, the `process_message` method in `SessionRunner` completely bypasses the existing agent by creating a new agent instance with a hardcoded text-compatible model:

```python
# BYPASS EXISTING AGENT COMPLETELY - Create a new agent on the spot with a guaranteed safe model
from google.adk.agents import Agent
            
# Create the temporary agent without importing from config at all
logger.error("CRITICAL: Creating temporary agent with hardcoded safe model")
safe_agent = Agent(
    name="beto", 
    model="gemini-1.5-pro-latest",  # Hardcoded reliable model for text
    instruction="You are Beto, a helpful assistant for text chat.",
    tools=self.agent_instance.tools  # Reuse the tools from the existing agent
)
            
# COMPLETELY replace both agents
logger.error(f"CRITICAL: Replacing both runner agent and agent_instance with safe model")
self.runner.agent = safe_agent
self.agent_instance = safe_agent
```

2. **Multiple Safety Layers**: We also implement multiple layers of protection:
   - In `agent.py`: Hardcoded safe models for both main and scout agents
   - In `session.py`: Complete agent replacement before message processing
   - In `agent/research_agent/agent.py`: Safety check for sequential thinking calls
   - In `agent/agent.py`: Detection of streaming-only models in various ADK components

3. **Testing**: We validate this approach with a test (`tools/test_dual_agent_fix.py`) that deliberately attempts to use a streaming-only model with the text chat endpoint, confirming that our runtime replacement mechanism functions correctly. The test intentionally sets a streaming-only model and verifies that the agent runtime replacement correctly substitutes a text-compatible model.

While this approach is more complex than the ideal scenario of finding a single versatile model, it provides robust handling of the different model requirements for streaming and text interactions without requiring significant architectural changes to the ADK framework.

This detailed implementation should give you a foundation for implementing a dual-agent architecture that can reliably handle both streaming voice and text chat, even when you must use different models for each modality. Remember to always consult the latest Google Cloud and Gemini documentation for model compatibility and features.


Sources and related content
Multimodal AI | Google Cloud

cloud.google.com

Gemini flash Live API docs chaos sorted out: - Documentation - Google AI Developers Forum

discuss.ai.google.dev

Quickstart (streaming) - Agent Development Kit - Google

google.github.io

Quickstart (streaming) - Agent Development Kit - Google

google.github.io/adk-docs/get-started/quickstart-streaming
Models - Agent Development Kit - Google

google.github.io/adk-docs/agents/models
