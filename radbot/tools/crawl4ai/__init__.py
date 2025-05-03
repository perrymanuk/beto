"""
Crawl4AI Integration for Radbot

This package provides integration with Crawl4AI service through the Model Context Protocol (MCP).
It enables web content ingestion, storage, and semantic search capabilities.
"""

from .mcp_crawl4ai_client import (
    create_crawl4ai_toolset,
    create_crawl4ai_enabled_agent,
    test_crawl4ai_connection,
    get_crawl4ai_config,
)

__all__ = [
    'create_crawl4ai_toolset',
    'create_crawl4ai_enabled_agent',
    'test_crawl4ai_connection',
    'get_crawl4ai_config',
]
