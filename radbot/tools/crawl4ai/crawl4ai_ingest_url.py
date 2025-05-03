#!/usr/bin/env python3
"""
Crawl4AI URL Ingestion Module

This module handles the ingestion of web content from URLs using Crawl4AI,
storing content for later retrieval and search.

Features:
- Single URL ingestion
- Multiple URL batch processing
- Vector storage integration for semantic search
"""

import logging
import requests
import asyncio
from typing import Dict, Any, Optional, List, Union

from .utils import run_async_safely, get_crawl4ai_config

# Configure logging
logger = logging.getLogger(__name__)

async def _call_crawl4ai_ingest_api(url: str, content_selectors: Optional[List[str]] = None, return_content: bool = True):
    """Internal function to call the Crawl4AI ingest API.
    
    Args:
        url: The URL to crawl
        content_selectors: CSS selectors to target specific content
        return_content: Whether to return content in the response (default: True)
    """
    # Print input for debugging
    logger.info(f"Crawl4AI processing URL: {url}")
    
    # Validate URL parameter
    if not url or not isinstance(url, str):
        error_msg = f"Invalid URL parameter: {url!r}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "error": "URL must be a non-empty string"
        }
    
    # Get connection parameters from environment variables
    api_url, api_token = get_crawl4ai_config()
    
    # Build the request 
    # Using the '/md' endpoint which directly produces markdown
    md_url = f"{api_url}/md"
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add authentication if token is provided
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    
    # Structure payload according to crawl4ai API requirements
    payload = {
        "url": url,
        "filter_type": "all",
        "markdown_flavor": "github"
    }
    
    # Add selectors if provided
    if content_selectors:
        payload["selectors"] = content_selectors
        
    # Make the API call
    try:
        response = requests.post(md_url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        # Check if we have content in the response - could be in "content" or "markdown" field
        markdown_content = None
        
        if result and "content" in result:
            markdown_content = result["content"]
            logger.info(f"Found content in 'content' field for {url}")
        elif result and "markdown" in result:
            markdown_content = result["markdown"]
            logger.info(f"Found content in 'markdown' field for {url}")
        
        if markdown_content:
            content_length = len(markdown_content)
            logger.info(f"Successfully generated markdown for {url} ({content_length} chars)")
            
            if return_content:
                # Include the content in the response for immediate use
                logger.info(f"Returning {content_length} chars of markdown content to LLM")
                return {
                    "success": True,
                    "message": f"Successfully generated markdown for {url}",
                    "content": markdown_content,
                    "content_length": content_length,
                    "url": url
                }
            else:
                # Don't return the content to avoid filling context window
                logger.info(f"Content generated ({content_length} chars) but not returned to LLM")
                return {
                    "success": True,
                    "message": f"✅ Successfully ingested content from {url}! {content_length} characters of markdown have been stored in the knowledge base and are now available for searching.",
                    "url": url,
                    "content_length": content_length,
                    "status": "completed"
                }
        else:
            logger.warning(f"No markdown content returned for {url}")
            if return_content:
                return {
                    "success": False,
                    "message": f"⚠️ Unable to extract any content from {url}. The page might be empty, blocked, or using unsupported technology.",
                    "content": "",
                    "url": url,
                    "error": "No content found"
                }
            else:
                return {
                    "success": False,
                    "message": f"⚠️ Unable to extract any content from {url}. The page might be empty, blocked, or using unsupported technology.",
                    "url": url,
                    "error": "No content found",
                    "status": "failed"
                }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Crawl4AI markdown API: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to generate markdown for URL: {str(e)}",
            "content": "" if return_content else None,
            "url": url,
            "error": str(e)
        }

async def _batch_process_urls(urls: List[str], content_selectors: Optional[List[str]] = None, return_content: bool = True) -> List[Dict[str, Any]]:
    """Process multiple URLs in batch mode.
    
    Args:
        urls: List of URLs to process
        content_selectors: Optional CSS selectors to target specific content
        return_content: Whether to return content in the response
        
    Returns:
        List of processing results, one for each URL
    """
    results = []
    
    # Use a semaphore to limit concurrency and avoid overloading the system
    # This helps prevent asyncio-related issues
    semaphore = asyncio.Semaphore(3)  # Process at most 3 URLs concurrently
    
    async def process_url(url):
        async with semaphore:
            try:
                return await _call_crawl4ai_ingest_api(
                    url=url,
                    content_selectors=content_selectors,
                    return_content=return_content
                )
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                return {
                    "success": False,
                    "url": url,
                    "error": str(e),
                    "message": f"Failed to process URL: {str(e)}",
                    "status": "failed"
                }
    
    # Create tasks for all URLs
    tasks = []
    for url in urls:
        tasks.append(process_url(url))
    
    # Wait for all tasks to complete
    try:
        results = await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Error in gather operation: {str(e)}")
        # Return whatever results we have so far
        return results
    
    return results

def crawl4ai_ingest_url(url: str, content_selectors: Optional[List[str]] = None, chunk_size: int = 800) -> Dict[str, Any]:
    """
    Ingest one or more URLs with Crawl4AI for later searching (content NOT returned).
    
    This function crawls webpages and converts them to clean, structured markdown
    that's optimized for AI use. The markdown is stored in the vector database
    for later searching with crawl4ai_query but is NOT returned to avoid
    filling up the conversation context.
    
    Typical workflow:
    1. Use this function to store content without viewing it: 
       - Single URL: crawl4ai_ingest_url(url="https://example.com/docs")
       - Multiple URLs: crawl4ai_ingest_url(url="https://example.com/docs,https://example.com/about")
    2. Then search that content with: crawl4ai_query("my search terms")
    
    Note: If you want to both view AND store content, use crawl4ai_ingest_and_read instead,
    but be aware that this will use more of your context window.
    
    Args:
        url: URL or comma-separated list of URLs to crawl (e.g. 'https://example.com' or 'https://example.com,https://example.org')
        content_selectors: Optional CSS selectors to target specific content
        chunk_size: Maximum size of each chunk in characters for vector storage (default: 800)
        
    Returns:
        A dictionary containing success/failure information
    """
    # Handle both single URL and comma-separated list of URLs
    if ',' in url:
        url_list = [u.strip() for u in url.split(',') if u.strip()]
        multi_url_mode = True
        logger.info(f"Processing multiple URLs ({len(url_list)}): {url_list}")
    else:
        url_list = [url]
        multi_url_mode = False
        logger.info(f"Processing single URL: {url}")
        
    # Input validation
    if not url_list:
        return {
            "success": False,
            "message": "No URLs provided",
            "error": "Empty URL list",
            "status": "failed"
        }
    
    logger.info(f"🔍 Crawl4AI ingesting {len(url_list)} URL(s) to knowledge base")
    
    # Process URLs and get content for vector storage
    try:
        results = run_async_safely(_batch_process_urls(
            urls=url_list,
            content_selectors=content_selectors,
            return_content=True  # Need content for vector database
        ))
    except Exception as e:
        logger.error(f"Error during batch processing: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to process URLs: {str(e)}",
            "error": str(e),
            "status": "failed"
        }
    
    # For single URL mode (and not part of a multi-URL request), process like before
    if not multi_url_mode and results and len(results) > 0:
        # Make sure we have a valid result
        result = results[0]
        
        # Handle single URL results
        if result.get("success") and result.get("content"):
            try:
                # Import here to avoid circular imports
                from radbot.tools.crawl4ai_vector_store import get_crawl4ai_vector_store
                
                # Get vector store instance
                vector_store = get_crawl4ai_vector_store()
                
                # Content from the API
                content = result.get("content", "")
                if not content:
                    return {
                        "success": False,
                        "message": f"No content found to store for {url}",
                        "url": url,
                        "error": "No content available",
                        "status": "failed"
                    }
                
                # Store the content in the vector store
                title = result.get("message", "").replace("Successfully generated markdown for ", "")
                if not title:
                    title = result.get("url", url).split("/")[-1] if "/" in result.get("url", url) else result.get("url", url)
                
                # Add a maximum content size check before sending to vector store
                if len(content) > 30000:  # Keep well under the 36000 byte limit
                    logger.info(f"Content size ({len(content)} bytes) exceeds recommended limit. Chunking content...")
                    # Simple chunking by paragraphs
                    paragraphs = content.split('\n\n')
                    chunks = []
                    current_chunk = ""
                    
                    for paragraph in paragraphs:
                        if len(current_chunk) + len(paragraph) < 25000:  # Conservative limit
                            current_chunk += paragraph + "\n\n"
                        else:
                            if current_chunk:  # Don't append empty chunks
                                chunks.append(current_chunk)
                            current_chunk = paragraph + "\n\n"
                    
                    # Add the last chunk if it's not empty
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    logger.info(f"Split content into {len(chunks)} chunks")
                    
                    # Process each chunk separately
                    chunk_results = []
                    for i, chunk in enumerate(chunks):
                        chunk_title = f"{title} (Part {i+1}/{len(chunks)})"
                        chunk_result = vector_store.add_document(
                            url=result.get("url", url),
                            title=chunk_title,
                            content=chunk,
                            chunk_size=chunk_size
                        )
                        chunk_results.append(chunk_result)
                    
                    # Combine the results
                    total_chunks = sum(r.get("chunks_count", 0) for r in chunk_results if r.get("success", False))
                    any_success = any(r.get("success", False) for r in chunk_results)
                    error_msgs = [r.get("message") for r in chunk_results if not r.get("success", False)]
                    
                    vector_result = {
                        "success": any_success,
                        "chunks_count": total_chunks,
                        "message": f"Successfully stored {len(chunks)} document chunks" if any_success else "Failed to store chunks: " + "; ".join(error_msgs)
                    }
                else:
                    # Process as a single document
                    vector_result = vector_store.add_document(
                        url=result.get("url", url),
                        title=title,
                        content=content,
                        chunk_size=chunk_size
                    )
                
                # Create a new response that doesn't include the content
                response = {
                    "success": vector_result["success"],
                    "message": f"✅ Successfully ingested content from {result.get('url', url)}! {vector_result['chunks_count']} chunks have been stored in the knowledge base and are now available for searching.",
                    "url": result.get("url", url),
                    "chunks_count": vector_result["chunks_count"],
                    "status": "completed" if vector_result["success"] else "failed"
                }
                
                if not vector_result["success"]:
                    response["error"] = vector_result["message"]
                
                return response
                
            except Exception as e:
                logger.error(f"⚠️ Error storing content in vector database: {str(e)}")
                return {
                    "success": False,
                    "message": f"Failed to ingest content: {str(e)}",
                    "url": result.get("url", url),
                    "error": str(e),
                    "status": "failed"
                }
        else:
            # If there was an error getting the content, return the error
            error_message = result.get("error", "Unknown error")
            return {
                "success": False,
                "message": f"Failed to ingest content: {error_message}",
                "url": result.get("url", url),
                "error": error_message,
                "status": "failed"
            }
    
    # For multiple URLs, process all results
    # Here we'll create a combined summary response
    total_urls = len(url_list)
    successful_urls = sum(1 for r in results if r.get("success", False))
    failed_urls = total_urls - successful_urls
    
    # Track total chunks across all successful results
    total_chunks = 0
    stored_urls = []
    failed_details = []
    
    # Store each successful result in vector database
    for result in results:
        if result.get("success") and result.get("content"):
            try:
                # Import here to avoid circular imports
                from radbot.tools.crawl4ai_vector_store import get_crawl4ai_vector_store
                
                # Get vector store instance
                vector_store = get_crawl4ai_vector_store()
                
                # Store the content in the vector store
                title = result.get("message", "").replace("Successfully generated markdown for ", "")
                if not title:
                    title = result.get("url", "").split("/")[-1] if "/" in result.get("url", "") else result.get("url", "")
                
                # Process content with chunking if needed
                content = result["content"]
                if len(content) > 30000:
                    # Simple chunking by paragraphs
                    paragraphs = content.split('\n\n')
                    chunks = []
                    current_chunk = ""
                    
                    for paragraph in paragraphs:
                        if len(current_chunk) + len(paragraph) < 25000:  # Conservative limit
                            current_chunk += paragraph + "\n\n"
                        else:
                            if current_chunk:  # Don't append empty chunks
                                chunks.append(current_chunk)
                            current_chunk = paragraph + "\n\n"
                    
                    # Add the last chunk if it's not empty
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    logger.info(f"Split content into {len(chunks)} chunks")
                    
                    # Process each chunk separately
                    chunk_results = []
                    for i, chunk in enumerate(chunks):
                        chunk_title = f"{title} (Part {i+1}/{len(chunks)})"
                        chunk_result = vector_store.add_document(
                            url=result.get("url", ""),
                            title=chunk_title,
                            content=chunk,
                            chunk_size=chunk_size
                        )
                        chunk_results.append(chunk_result)
                    
                    # Combine the results
                    chunks_count = sum(r.get("chunks_count", 0) for r in chunk_results if r.get("success", False))
                    any_success = any(r.get("success", False) for r in chunk_results)
                    
                    if any_success:
                        total_chunks += chunks_count
                        stored_urls.append(result.get("url", ""))
                    else:
                        error_msgs = [r.get("message") for r in chunk_results if not r.get("success", False)]
                        failed_details.append({
                            "url": result.get("url", ""),
                            "error": "Failed to store chunks: " + "; ".join(error_msgs)
                        })
                else:
                    # Process as a single document
                    vector_result = vector_store.add_document(
                        url=result.get("url", ""),
                        title=title,
                        content=content,
                        chunk_size=chunk_size
                    )
                    
                    if vector_result["success"]:
                        total_chunks += vector_result.get("chunks_count", 0)
                        stored_urls.append(result.get("url", ""))
                    else:
                        failed_details.append({
                            "url": result.get("url", ""),
                            "error": vector_result.get("message", "Unknown vector storage error")
                        })
            except Exception as e:
                failed_details.append({
                    "url": result.get("url", ""),
                    "error": str(e)
                })
        else:
            # No content available
            failed_details.append({
                "url": result.get("url", ""),
                "error": "No content available to store"
            })
    
    # Create a comprehensive response
    return {
        "success": successful_urls > 0,
        "message": f"✅ Processed {total_urls} URLs: {successful_urls} successful, {failed_urls} failed. {total_chunks} total chunks stored in the knowledge base.",
        "urls_processed": total_urls,
        "urls_successful": successful_urls,
        "urls_failed": failed_urls,
        "total_chunks": total_chunks,
        "stored_urls": stored_urls,
        "failed_details": failed_details,
        "status": "completed" if successful_urls > 0 else "failed"
    }
