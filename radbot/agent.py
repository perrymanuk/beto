"""
Radbot agent implementation.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from google.adk.agent import Agent, AgentBuilder
from google.adk.agents import QueryResponse
from google.adk.tools import FunctionTool
from google.protobuf.json_format import MessageToDict

from google.adk.tools.transfer_to_agent_tool import transfer_to_agent

from radbot.tools.crawl4ai.crawl4ai_query import create_crawl4ai_query_tool
from radbot.tools.get_weather import create_weather_tool
from radbot.tools.memory import search_past_conversations, store_important_information
from radbot.tools.mcp import (
    create_fileserver_toolset,
    handle_fileserver_tool_call,
)
from radbot.tools.crawl4ai.mcp_crawl4ai_client import (
    create_crawl4ai_toolset,
    handle_crawl4ai_tool_call,
)

logger = logging.getLogger(__name__)


def agent_error_handler(e: Exception) -> Dict[str, Any]:
    """Handle agent errors by returning a user-friendly error message."""
    logger.error(f"Agent error: {e}", exc_info=True)
    return {
        "error": f"I encountered an error: {str(e)}. Please try again or contact support if the issue persists."
    }


def create_agent(model: str = "gemini-1.5-pro-latest") -> Agent:
    """
    Create a basic agent with default tools.

    Args:
        model: The model to use for the agent.

    Returns:
        An Agent instance.
    """
    # List of basic tools available to all agents
    basic_tools = [
        create_weather_tool(),
        FunctionTool(name="transfer_to_agent", description="Transfer to another agent"),
    ]

    # Add Crawl4AI query tool for searching ingested content
    basic_tools.append(create_crawl4ai_query_tool())

    # Try to add MCP fileserver tools
    try:
        logger.info("Setting up MCP fileserver tools...")
        fileserver_tools = create_fileserver_toolset()
        if fileserver_tools:
            basic_tools.extend(fileserver_tools)
        else:
            logger.warning("MCP fileserver tools not available")
    except Exception as e:
        logger.warning(f"Failed to create MCP fileserver tools: {e}")

    # Try to add Crawl4AI toolset
    logger.info("Creating Crawl4AI toolset...")
    crawl4ai_api_url = os.environ.get(
        "CRAWL4AI_API_URL", "https://crawl4ai.demonsafe.com"
    )
    logger.info(f"Crawl4AI: Using API URL {crawl4ai_api_url}")
    crawl4ai_api_token = os.environ.get("CRAWL4AI_API_TOKEN", "")

    try:
        crawl4ai_tools = create_crawl4ai_toolset(
            api_url=crawl4ai_api_url, api_token=crawl4ai_api_token
        )
        if crawl4ai_tools:
            basic_tools.extend(crawl4ai_tools)
        else:
            logger.warning("Crawl4AI tools not available (returned None)")
    except Exception as e:
        logger.warning(f"Failed to create Crawl4AI tools: {e}")

    # Create the agent
    agent = (
        AgentBuilder()
        .set_model(model)
        .add_tool_group("basic_tools", basic_tools)
        .set_system_instructions(
            """
You are Radbot, a helpful and intelligent research assistant.

# CAPABILITIES

You have access to several tools:
- Web search and browsing capabilities to find information on the internet
- A knowledge base of crawled content that you can search using the crawl4ai_query tool
- File system access to read and manipulate files
- Tools to fetch weather information and more

## RESEARCH AGENT DELEGATION
If the user asks a complex research question, you can delegate to a specialized research agent.
Use the transfer_to_agent tool to transfer to the "technical_research_agent" for deep technical research.
You may transfer to a research agent when:
- The query requires deep domain knowledge
- The question involves complex technical concepts
- The user requests "advanced" or "deep" research

# GUIDELINES

- Be concise and precise in your responses.
- If you don't know an answer, use your tools to find it.
- Always cite sources when providing information.
- Maintain a professional yet friendly tone.
- Prioritize accuracy over speed.
- For code requests, provide well-documented solutions.
- Respect user privacy and data security.
- When searching the crawled knowledge base, use the crawl4ai_query tool.

# AGENT TRANSFER INSTRUCTION
You can transfer the user to the technical research agent using:
transfer_to_agent(agent_name="technical_research_agent", message="[Optional message for the research agent]")

Similarly, the research agent can transfer back to you using:
transfer_to_agent(agent_name="radbot_web", message="[Optional message for you]")
"""
        )
        .set_error_handler(agent_error_handler)
        .build()
    )

    # Register custom tool handlers
    agent.register_tool_handler(
        "list_files", lambda params: handle_fileserver_tool_call("list_files", params)
    )
    agent.register_tool_handler(
        "read_file", lambda params: handle_fileserver_tool_call("read_file", params)
    )
    agent.register_tool_handler(
        "write_file", lambda params: handle_fileserver_tool_call("write_file", params)
    )
    agent.register_tool_handler(
        "delete_file", lambda params: handle_fileserver_tool_call("delete_file", params)
    )
    agent.register_tool_handler(
        "get_file_info",
        lambda params: handle_fileserver_tool_call("get_file_info", params),
    )
    agent.register_tool_handler(
        "search_files", lambda params: handle_fileserver_tool_call("search_files", params)
    )
    agent.register_tool_handler(
        "create_directory",
        lambda params: handle_fileserver_tool_call("create_directory", params),
    )

    # Register Crawl4AI tool handlers
    agent.register_tool_handler(
        "crawl4ai_scrape",
        lambda params: handle_crawl4ai_tool_call("crawl4ai_scrape", params),
    )
    agent.register_tool_handler(
        "crawl4ai_search",
        lambda params: handle_crawl4ai_tool_call("crawl4ai_search", params),
    )
    agent.register_tool_handler(
        "crawl4ai_extract",
        lambda params: handle_crawl4ai_tool_call("crawl4ai_extract", params),
    )
    agent.register_tool_handler(
        "crawl4ai_crawl",
        lambda params: handle_crawl4ai_tool_call("crawl4ai_crawl", params),
    )

    # Register memory tools
    agent.register_tool_handler(
        "search_past_conversations",
        lambda params: MessageToDict(search_past_conversations(params)),
    )
    agent.register_tool_handler(
        "store_important_information",
        lambda params: MessageToDict(store_important_information(params)),
    )

    # Register agent transfer tool
    agent.register_tool_handler(
        "transfer_to_agent",
        lambda params: MessageToDict(QueryResponse(
            transfer_to_agent_response={
                "target_app_name": params["agent_name"],
                "message": params.get("message", ""),
            }
        )),
    )

    # Register Crawl4AI query tool
    agent.register_tool_handler(
        "crawl4ai_query",
        lambda params: {
            "results": search_past_conversations(
                {"query": params["query"], "limit": params.get("limit", 5)}
            )
        },
    )

    return agent
