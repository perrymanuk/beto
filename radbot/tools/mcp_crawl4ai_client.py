#!/usr/bin/env python3
"""
MCP Crawl4AI Client

This module provides utilities for connecting to Crawl4AI from
within the radbot framework using the Model Context Protocol (MCP).
"""

# Import from the new modular implementation for backward compatibility
from radbot.tools.crawl4ai.mcp_crawl4ai_client import (
    create_crawl4ai_toolset,
    create_crawl4ai_toolset_async,
    create_crawl4ai_enabled_agent,
    test_crawl4ai_connection,
    main
)
from radbot.tools.crawl4ai.utils import (
    run_async_safely,
    get_crawl4ai_config
)
from radbot.tools.crawl4ai.crawl4ai_query import crawl4ai_query
from radbot.tools.crawl4ai.crawl4ai_ingest_url import crawl4ai_ingest_url
from radbot.tools.crawl4ai.crawl4ai_ingest_and_read import crawl4ai_ingest_and_read

# For backward compatibility, expose all the public functions and classes
__all__ = [
    'create_crawl4ai_toolset',
    'create_crawl4ai_toolset_async',
    'create_crawl4ai_enabled_agent',
    'test_crawl4ai_connection',
    'run_async_safely',
    'get_crawl4ai_config',
    'crawl4ai_query',
    'crawl4ai_ingest_url',
    'crawl4ai_ingest_and_read',
    'main'
]

if __name__ == "__main__":
    main()
