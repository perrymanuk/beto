#!/usr/bin/env python3
"""
Utilities for Crawl4AI Integration

This module provides common utility functions used across the Crawl4AI integration.
"""

import os
import logging
import asyncio
import concurrent.futures
from typing import Dict, Any, Callable, Coroutine, Tuple

from radbot.config.config_loader import config_loader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_async_safely(coro):
    """
    Run a coroutine safely in any context.
    
    This function handles the complexities of running a coroutine in different contexts:
    - If called from an already running event loop
    - If called outside any event loop
    - If called in a thread without an event loop
    
    Args:
        coro: A coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        
        # Check if the loop is already running
        if loop.is_running():
            # Use an executor to run the async function in a separate thread with a new event loop
            with concurrent.futures.ThreadPoolExecutor() as pool:
                try:
                    future = pool.submit(_run_in_new_thread, coro)
                    return future.result(timeout=120)  # Add timeout to prevent hanging
                except concurrent.futures.TimeoutError:
                    logger.error("Async operation timed out after 120 seconds")
                    return {"success": False, "error": "Operation timed out", "message": "Request took too long to complete"}
                except Exception as e:
                    logger.error(f"Error running async function in executor: {str(e)}")
                    return {"success": False, "error": str(e), "message": f"Error during execution: {str(e)}"}
        else:
            # If the loop is not running, use run_until_complete with timeout protection
            try:
                return asyncio.wait_for(coro, timeout=120)
            except asyncio.TimeoutError:
                logger.error("Async operation timed out after 120 seconds")
                return {"success": False, "error": "Operation timed out", "message": "Request took too long to complete"}
            except Exception as e:
                logger.error(f"Error in run_until_complete: {str(e)}")
                return {"success": False, "error": str(e), "message": f"Error during execution: {str(e)}"}
    except RuntimeError:
        # If there's no event loop in the current thread, create a new one
        return _run_in_new_thread(coro)

def _run_in_new_thread(coro):
    """
    Run a coroutine in a new thread with its own event loop.
    
    Args:
        coro: A coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run with timeout protection
            return loop.run_until_complete(asyncio.wait_for(coro, timeout=120))
        except asyncio.TimeoutError:
            logger.error("Async operation timed out after 120 seconds")
            return {"success": False, "error": "Operation timed out", "message": "Request took too long to complete"}
        except Exception as e:
            logger.error(f"Error in new event loop execution: {str(e)}")
            return {"success": False, "error": str(e), "message": f"Error during execution: {str(e)}"}
        finally:
            # Always clean up the loop
            try:
                # Cancel all running tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # Run the event loop until all tasks are cancelled
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                # Close the loop
                loop.close()
            except Exception as e:
                logger.error(f"Error cleaning up event loop: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create new event loop: {str(e)}")
        return {"success": False, "error": str(e), "message": f"Failed to create event loop: {str(e)}"}

def get_crawl4ai_config() -> Tuple[str, str]:
    """
    Get Crawl4AI configuration from config.yaml or environment variables.
    
    Returns:
        Tuple of (api_url, api_token)
    """
    # Try to get configuration from config.yaml first
    crawl4ai_config = config_loader.get_integrations_config().get("crawl4ai", {})
    
    # Get values from config or fall back to environment variables
    api_url = crawl4ai_config.get("api_url")
    if not api_url:
        # Fall back to environment variable
        api_url = os.getenv("CRAWL4AI_API_URL", "http://localhost:11235")
    
    api_token = crawl4ai_config.get("api_token")
    if not api_token:
        # Fall back to environment variable
        api_token = os.getenv("CRAWL4AI_API_TOKEN", "")  # Default to empty string instead of None
    
    # Log configuration
    if api_token:
        logger.info(f"Crawl4AI Config: api_url={api_url}, token=****")
    else:
        logger.info(f"Crawl4AI Config: api_url={api_url}, no token provided - proceeding with anonymous access")
    
    return api_url, api_token
