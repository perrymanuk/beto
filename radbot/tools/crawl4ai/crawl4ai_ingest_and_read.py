#!/usr/bin/env python3
"""
Crawl4AI Ingest and Read Module

This module combines content ingestion with immediate reading/viewing,
fetching content and also storing it for later search.

Features:
- Single URL reading and ingestion
- Configurable crawl depth for deeper content extraction
- Vector storage integration for semantic search
- Content chunking for large documents
"""

import logging
from typing import Dict, Any, List, Union, Optional

from .utils import run_async_safely
from .crawl4ai_ingest_url import _call_crawl4ai_ingest_api

# Configure logging
logger = logging.getLogger(__name__)

def crawl4ai_ingest_and_read(url: str, crawl_depth: int = 0, include_external: bool = False, max_pages: Optional[int] = None, content_selectors: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fetch a URL using Crawl4AI and return content for immediate use.
    
    This function crawls a webpage and converts it to clean, structured markdown
    that's optimized for AI use. The markdown is returned directly for immediate
    analysis and discussion - it will be included in the conversation context.
    
    The content is also automatically stored in the vector database for later querying
    with crawl4ai_query.
    
    Typical workflow:
    1. Use this function to both view AND store content:
       - Basic usage: crawl4ai_ingest_and_read(url="https://example.com/docs")
       - With deep crawling: crawl4ai_ingest_and_read(url="https://example.com/docs", crawl_depth=2)
    2. Later, search the stored content with: crawl4ai_query("my search terms")
    
    Note: This function is intended for single URLs. For processing multiple URLs,
    use crawl4ai_ingest_url instead (which takes a comma-separated list of URLs).
    
    Args:
        url: The URL of the webpage to crawl (e.g. 'https://example.com')
        crawl_depth: How many levels of links to follow (0 means only the provided URL)
        include_external: Whether to follow links to external domains (default: False to stay within same site)
        max_pages: Maximum number of pages to crawl, acts as a safeguard for deep crawling
        content_selectors: Optional CSS selectors to target specific content
        
    Returns:
        A dictionary containing the result with markdown content for immediate use
    """
    print(f"🔍 Crawl4AI ingesting and reading URL: {url}, crawl_depth={crawl_depth}")
    
    # Use our safe async runner to fetch content
    result = run_async_safely(_call_crawl4ai_ingest_api(
        url=url, 
        crawl_depth=crawl_depth, 
        content_selectors=content_selectors, 
        return_content=True,
        include_external=include_external,
        max_pages=max_pages
    ))
    
    # If we successfully got content, store it in the vector database
    if result.get("success") and result.get("content"):
        try:
            # Import here to avoid circular imports
            from radbot.tools.crawl4ai_vector_store import get_crawl4ai_vector_store
            
            # Get vector store instance
            vector_store = get_crawl4ai_vector_store()
            
            # Store the content in the vector store
            title = result.get("message", "").replace("Successfully generated markdown for ", "")
            if not title:
                title = url.split("/")[-1] if "/" in url else url
            
            # Add a maximum content size check before sending to vector store
            content = result["content"]
            if len(content) > 30000:  # Keep well under the 36000 byte limit
                print(f"Content size ({len(content)} bytes) exceeds recommended limit. Chunking content...")
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
                
                print(f"Split content into {len(chunks)} chunks")
                
                # Process each chunk separately
                chunk_results = []
                for i, chunk in enumerate(chunks):
                    chunk_title = f"{title} (Part {i+1}/{len(chunks)})"
                    chunk_result = vector_store.add_document(
                        url=url,
                        title=chunk_title,
                        content=chunk
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
                    url=url,
                    title=title,
                    content=content
                )
            
            if vector_result["success"]:
                print(f"✅ Successfully stored content in vector database: {vector_result['chunks_count']} chunks")
                # Add vector storage info to result
                result["vector_storage"] = {
                    "success": True,
                    "chunks_stored": vector_result["chunks_count"]
                }
            else:
                print(f"⚠️ Failed to store content in vector database: {vector_result['message']}")
                # Add vector storage error info to result
                result["vector_storage"] = {
                    "success": False,
                    "error": vector_result["message"]
                }
        except Exception as e:
            print(f"⚠️ Error storing content in vector database: {str(e)}")
            # Add vector storage error info to result
            result["vector_storage"] = {
                "success": False,
                "error": str(e)
            }
    
    return result
