#!/usr/bin/env python3
"""
Crawl4AI Two-Step Crawling Module

This module implements a two-step crawling process:
1. Get the initial page using crawl4ai_ingest_and_read
2. Extract links from the content
3. Send those links to crawl4ai_ingest_url as a multi-URL request
"""

import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from .crawl4ai_ingest_and_read import crawl4ai_ingest_and_read
from .crawl4ai_ingest_url import crawl4ai_ingest_url

# Configure logging
logger = logging.getLogger(__name__)

def _extract_links_from_markdown(markdown_content: str, base_url: str, include_external: bool = False) -> List[str]:
    """
    Extract links from markdown content.
    
    Args:
        markdown_content: The markdown content to extract links from
        base_url: The base URL for resolving relative links
        include_external: Whether to include external links
        
    Returns:
        List of extracted links
    """
    links = []
    
    # Extract markdown-style links: [text](url)
    markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', markdown_content)
    for text, url in markdown_links:
        # Normalize URL if it's relative
        if not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        links.append(url)
    
    # Extract raw URLs that might be in the text
    raw_urls = re.findall(r'(?<!\()(https?://[^\s)]+)', markdown_content)
    links.extend(raw_urls)
    
    # Filter out external links if not including them
    if not include_external:
        base_domain = urlparse(base_url).netloc
        links = [
            link for link in links 
            if urlparse(link).netloc == base_domain
        ]
    
    # Remove duplicates while preserving order
    unique_links = []
    for link in links:
        if link not in unique_links:
            unique_links.append(link)
    
    return unique_links

def crawl4ai_two_step(
    url: str, 
    max_links: int = 10, 
    include_external: bool = False,
    content_selectors: Optional[List[str]] = None,
    chunk_size: int = 800
) -> Dict[str, Any]:
    """
    Perform a two-step crawl:
    1. Get and read the initial URL
    2. Extract links from the content
    3. Crawl those links in a batch
    
    Args:
        url: The URL to crawl
        max_links: Maximum number of links to process (default: 10)
        include_external: Whether to include external links (default: False)
        content_selectors: Optional CSS selectors to target specific content
        chunk_size: Maximum size of each chunk in characters (default: 800)
        
    Returns:
        Dictionary with the results of both steps
    """
    logger.info(f"🔍 Starting two-step crawl for {url}")
    
    # Step 1: Get the initial URL content
    step1_result = crawl4ai_ingest_and_read(url=url, content_selectors=content_selectors)
    
    if not step1_result.get("success", False):
        return {
            "success": False,
            "message": f"Failed to read initial URL: {step1_result.get('error', 'Unknown error')}",
            "url": url,
            "error": step1_result.get("error", "Failed to read initial URL"),
            "status": "failed"
        }
    
    # Get the content from the result
    content = step1_result.get("content", "")
    
    if not content:
        return {
            "success": False,
            "message": f"No content found in initial URL",
            "url": url,
            "error": "No content found",
            "status": "failed"
        }
    
    # Step 2: Extract links from the content
    links = _extract_links_from_markdown(content, url, include_external)
    
    logger.info(f"📋 Extracted {len(links)} links from {url}")
    
    # Limit the number of links
    if max_links > 0 and len(links) > max_links:
        logger.info(f"⚠️ Limiting to {max_links} links (from {len(links)} total)")
        links = links[:max_links]
    
    # If no links were found, return early
    if not links:
        return {
            "success": True,
            "message": f"✅ Successfully read {url}, but no links were found to crawl",
            "url": url,
            "initial_content": content,
            "links_found": 0,
            "links_crawled": 0,
            "status": "completed"
        }
    
    # Step 3: Crawl the extracted links
    # Updated to match our reverted crawl4ai_ingest_url function
    step3_result = crawl4ai_ingest_url(
        url=",".join(links),  # Pass as comma-separated list for multi-URL mode
        content_selectors=content_selectors,
        chunk_size=chunk_size  # Pass the chunk_size parameter
    )
    
    # Combine the results
    return {
        "success": step3_result.get("success", False),
        "message": f"✅ Two-step crawl complete! Read initial page and crawled {len(links)} extracted links",
        "url": url,
        "initial_content": content,
        "links_found": len(links),
        "links_crawled": step3_result.get("urls_successful", 0),
        "links_failed": step3_result.get("urls_failed", 0),
        "total_chunks": step3_result.get("total_chunks", 0),
        "crawled_links": links,
        "status": "completed" if step3_result.get("success", False) else "partial",
        "initial_step_result": step1_result,
        "links_step_result": step3_result
    }
