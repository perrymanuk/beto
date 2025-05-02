#!/usr/bin/env python3
"""
Fileserver Agent Example

This example demonstrates using an ADK agent with the MCP fileserver.
"""

import os
import sys
import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple

# Add the parent directory to the path so we can import radbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.load_web_page import load_web_page

# Import MCP fileserver client
from radbot.tools.mcp_fileserver_client import create_fileserver_toolset_async

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Basic tool: get current time
async def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def setup_agent():
    """
    Set up the agent with tools and services.
    
    Returns:
        Tuple of (agent, exit_stack)
    """
    # Basic tools
    basic_tools = [
        FunctionTool(get_current_time),
        FunctionTool(load_web_page),
    ]
    
    # MCP fileserver tools
    fs_tools, exit_stack = await create_fileserver_toolset_async()
    
    # Combine tools
    all_tools = basic_tools
    if fs_tools:
        all_tools.extend(fs_tools)
        logger.info(f"Added {len(fs_tools)} MCP fileserver tools")
    else:
        logger.warning("MCP fileserver tools not available")
    
    # Create the agent
    agent = LlmAgent(
        model='gemini-1.5-pro',  # Update model name if needed
        name='fileserver_assistant',
        instruction="""
        You are a helpful assistant with access to the