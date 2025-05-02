"""
Home Assistant tool implementations for Google GenAI function calling.

This module provides the implementation of the tools that interface with
the Home Assistant WebSocket client and state cache.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from radbot.tools.ha_websocket_client import HomeAssistantWebsocketClient
from radbot.tools.ha_state_cache import HomeAssistantStateCache

logger = logging.getLogger(__name__)

# Singleton instances to be initialized by the setup function
_ws_client: Optional[HomeAssistantWebsocketClient] = None
_state_cache: Optional[HomeAssistantStateCache] = None

async def setup_home_assistant_tools(url: str, token: str) -> None:
    """
    Set up the Home Assistant WebSocket client and state cache.
    
    Must be called before using any of the tool functions.
    
    Args:
        url: The WebSocket URL of the Home Assistant instance
        token: A Long-Lived Access Token for Home Assistant
    """
    global _ws_client, _state_cache
    
    if _ws_client is not None:
        logger.warning("Home Assistant tools already set up, stopping existing client")
        await _ws_client.stop()
    
    # Create state cache
    _state_cache = HomeAssistantStateCache()
    
    # Create callback function that updates the state cache
    async def update_state_callback(event_data: Dict[str, Any]) -> None:
        await _state_cache.update_state(event_data)
    
    try:
        # Create WebSocket client but don't start the listener yet
        _ws_client = HomeAssistantWebsocketClient(url, token, update_state_callback)
        
        # Connect to Home Assistant - this will authenticate and subscribe but not start the listener task
        connection_success = await _ws_client.connect(auto_listen=False)
        
        if not connection_success:
            logger.warning("WebSocket client reported connection issues during startup")
            # Wait a bit longer - the connection might establish after the timeout
            logger.info("Giving WebSocket connection extra time to establish...")
            await asyncio.sleep(5)
        
        # Initialize state cache with all current states and registry information
        initialization_succeeded = False
        max_retries = 2  # Number of retries for state initialization
        retry_count = 0
        
        while not initialization_succeeded and retry_count <= max_retries:
            try:
                if retry_count > 0:
                    logger.info(f"Retry attempt {retry_count}/{max_retries} for state initialization")
                    # Wait a bit before retrying
                    await asyncio.sleep(3)
                
                # Fetch and update entity states
                logger.info("Fetching initial entity states from Home Assistant...")
                all_states = await _ws_client.get_all_states()
                logger.info(f"Received {len(all_states)} entities from Home Assistant")
                
                # Process each state into the cache
                for state_data in all_states:
                    entity_id = state_data.get("entity_id")
                    if entity_id:
                        # Format data in the format expected by the state cache
                        event_data = {
                            "entity_id": entity_id,
                            "new_state": state_data
                        }
                        await _state_cache.update_state(event_data)
                
                # Mark initialization as successful since we got states
                initialization_succeeded = True
                
                # Prioritize fetching the display registry which contains the most comprehensive data
                try:
                    logger.info("Fetching entity registry with display info from Home Assistant...")
                    entity_registry_display = await _ws_client.get_entity_registry_for_display()
                    logger.info(f"Received {len(entity_registry_display)} entity registry display entries")
                    await _state_cache.update_entity_registry_display(entity_registry_display)
                except Exception as display_error:
                    logger.error(f"Error fetching entity registry display: {display_error}", exc_info=True)
                    logger.warning("Entity registry display information will not be available - falling back to regular registry")
                    
                    # Fall back to regular registry if display registry fails
                    try:
                        logger.info("Fetching standard entity registry from Home Assistant...")
                        entity_registry = await _ws_client.get_entity_registry()
                        logger.info(f"Received {len(entity_registry)} entity registry entries")
                        await _state_cache.update_entity_registry(entity_registry)
                    except Exception as registry_error:
                        logger.error(f"Error fetching entity registry: {registry_error}", exc_info=True)
                        logger.warning("Entity registry information will not be available")
                else:
                    # If display registry succeeds, still fetch the standard registry as fallback
                    try:
                        logger.info("Fetching standard entity registry as backup from Home Assistant...")
                        entity_registry = await _ws_client.get_entity_registry()
                        logger.info(f"Received {len(entity_registry)} entity registry entries")
                        await _state_cache.update_entity_registry(entity_registry)
                    except Exception as registry_error:
                        logger.error(f"Error fetching standard entity registry: {registry_error}", exc_info=True)
                        logger.warning("Standard entity registry information will not be available")
                    
                # Fetch and update device registry info
                try:
                    logger.info("Fetching device registry from Home Assistant...")
                    device_registry = await _ws_client.get_device_registry()
                    logger.info(f"Received {len(device_registry)} device registry entries")
                    await _state_cache.update_device_registry(device_registry)
                except Exception as device_error:
                    logger.error(f"Error fetching device registry: {device_error}", exc_info=True)
                    logger.warning("Device registry information will not be available")
                        
                # Log the number of entities by domain for debugging
                domains = await _state_cache.get_domains()
                domain_counts = {}
                for domain in domains:
                    entities = await _state_cache.get_entities_by_domain(domain)
                    domain_counts[domain] = len(entities)
                logger.info(f"Initialized state cache with {len(domains)} domains: {domain_counts}")
            
            except Exception as e:
                retry_count += 1
                logger.error(f"Error initializing state cache (attempt {retry_count}/{max_retries+1}): {e}", exc_info=True)
                
                if retry_count > max_retries:
                    logger.warning("All retry attempts failed. State cache may be incomplete until state_changed events are received")
                    # Even though initialization failed, we'll proceed and hope that events will populate the cache
                else:
                    logger.info(f"Retrying initialization in 3 seconds...")
        
        # Now that initialization is complete, start listening for events
        await _ws_client.start_listening()
        
        # Log success regardless of state initialization
        logger.info("Home Assistant tools set up successfully")
        
        # Return success regardless of state initialization to keep tools available
        # The agent can still work with live events even without initial states
        return True
        
    except Exception as e:
        logger.error(f"Failed to set up Home Assistant tools: {e}", exc_info=True)
        
        # Clean up if initialization fails
        if _ws_client:
            try:
                await _ws_client.stop()
            except:
                pass
        
        return False

async def cleanup_home_assistant_tools() -> None:
    """Clean up the Home Assistant tools and stop the WebSocket client."""
    global _ws_client, _state_cache
    
    if _ws_client is not None:
        await _ws_client.stop()
        _ws_client = None
    
    _state_cache = None
    logger.info("Home Assistant tools cleaned up")

async def get_home_assistant_entity_state(entity_id: str) -> Dict[str, Any]:
    """
    Get the current state of a Home Assistant entity.
    
    Args:
        entity_id: The entity ID to query
        
    Returns:
        Dictionary containing the entity state or an error message
    """
    logger.info(f"Tool called: get_home_assistant_entity_state({entity_id})")
    
    if _state_cache is None:
        return {
            "status": "error",
            "message": "Home Assistant tools not initialized"
        }
    
    state = await _state_cache.get_state(entity_id)
    
    if state is None:
        return {
            "status": "error",
            "message": f"Entity '{entity_id}' not found in state cache"
        }
    
    # Extract relevant information from state object
    return {
        "status": "success",
        "entity_id": entity_id,
        "state": state.get("state"),
        "attributes": state.get("attributes", {}),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated")
    }

async def call_home_assistant_service(
    domain: str,
    service: str,
    entity_id: Optional[str] = None,
    service_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Call a service in Home Assistant.
    
    Args:
        domain: The domain of the service
        service: The service to call
        entity_id: Optional entity ID to target
        service_data: Optional additional service data
        
    Returns:
        Dictionary containing the status of the service call
    """
    logger.info(f"Tool called: call_home_assistant_service({domain}, {service}, {entity_id}, {service_data})")
    
    if _ws_client is None:
        return {
            "status": "error",
            "message": "Home Assistant tools not initialized"
        }
    
    try:
        # Check if websocket is still connected
        if not _ws_client._is_running or _ws_client._shutdown_event.is_set():
            # Try to reconnect
            logger.warning("WebSocket appears disconnected, attempting to reconnect")
            try:
                # Use restart instead of recreating connections
                await _ws_client.stop()
                await asyncio.sleep(1)  # Brief pause
                await _ws_client.start()
                # Give it a moment to connect
                await asyncio.sleep(2)
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect: {str(reconnect_error)}")
                return {
                    "status": "error",
                    "message": f"WebSocket disconnected and reconnection failed: {str(reconnect_error)}"
                }
        
        # Now try the service call
        result = await _ws_client.call_service(domain, service, service_data, entity_id)
        return {
            "status": "success",
            "message": f"Successfully called service {domain}.{service}",
            "details": result
        }
    except ConnectionError as e:
        return {
            "status": "error",
            "message": f"Connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error calling service {domain}.{service}: {str(e)}"
        }

async def search_home_assistant_entities(
    search_term: str, 
    domain_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for Home Assistant entities by name or ID.
    
    Args:
        search_term: The term to search for
        domain_filter: Optional domain to filter by (e.g., 'light', 'switch')
        
    Returns:
        Dictionary containing matching entities
    """
    logger.info(f"Tool called: search_home_assistant_entities({search_term}, {domain_filter})")
    
    if _state_cache is None:
        return {
            "status": "error",
            "message": "Home Assistant tools not initialized"
        }
    
    try:
        # Use the enhanced search_entities method directly
        results = await _state_cache.search_entities(search_term, domain_filter)
        
        # If no results found with the provided domain filter, but we have a search term,
        # try with common domains that often contain important entities
        if not results and search_term and not domain_filter:
            logger.info(f"No results found for '{search_term}', trying with common domains")
            
            # Try searching in common domains with higher priority
            common_domains = ["light", "switch", "binary_sensor", "sensor", "climate", 
                             "media_player", "scene", "script", "automation"]
                
            for domain in common_domains:
                domain_results = await _state_cache.search_entities(search_term, domain)
                # Add domain name to results for better context
                for result in domain_results:
                    if "domain" not in result:
                        result["domain"] = domain
                results.extend(domain_results)
                
            # If we found results in common domains, return them
            if results:
                # Re-sort by score since we combined results from multiple searches
                results.sort(key=lambda x: x.get("score", 0), reverse=True)
                logger.info(f"Found {len(results)} results in common domains")
        
        # If we still have no results, try all domains
        if not results and search_term:
            logger.info(f"No results in common domains for '{search_term}', trying all domains")
            
            # Get all available domains
            all_domains = await _state_cache.get_domains()
            
            # Skip domains we already tried
            additional_domains = [d for d in all_domains if d not in (common_domains if 'common_domains' in locals() else [])]
            
            # Try each domain that we haven't checked yet
            for domain in additional_domains:
                domain_results = await _state_cache.search_entities(search_term, domain)
                # Add domain name to results for better context
                for result in domain_results:
                    if "domain" not in result:
                        result["domain"] = domain
                results.extend(domain_results)
        
        # Add entity count by domain for better understanding of results
        domain_counts = {}
        for item in results:
            domain = item.get("domain") or item.get("entity_id", "").split(".", 1)[0]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
        # Sort results by score (higher first)
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # For very large result sets, limit to top results
        max_results = 50
        if len(results) > max_results:
            logger.info(f"Limiting from {len(results)} to top {max_results} results")
            results = results[:max_results]
        
        return {
            "status": "success",
            "count": len(results),
            "entities": results,
            "domain_counts": domain_counts,
            "search_term": search_term,
            "domain_filter": domain_filter
        }
    except Exception as e:
        logger.error(f"Error searching entities: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error searching entities: {str(e)}"
        }

async def get_home_assistant_entities_by_domain(domain: str) -> Dict[str, Any]:
    """
    Get all entities of a specific domain.
    
    Args:
        domain: The domain to filter by
        
    Returns:
        Dictionary containing entities in the specified domain
    """
    logger.info(f"Tool called: get_home_assistant_entities_by_domain({domain})")
    
    if _state_cache is None:
        return {
            "status": "error",
            "message": "Home Assistant tools not initialized"
        }
    
    entity_ids = await _state_cache.get_entities_by_domain(domain)
    
    # Get full state for each entity
    entities = []
    for entity_id in entity_ids:
        state = await _state_cache.get_state(entity_id)
        if state:
            entities.append({
                "entity_id": entity_id,
                "state": state.get("state"),
                "friendly_name": state.get("attributes", {}).get("friendly_name", entity_id),
                "last_changed": state.get("last_changed")
            })
    
    return {
        "status": "success",
        "domain": domain,
        "count": len(entities),
        "entities": entities
    }

async def get_home_assistant_domains() -> Dict[str, Any]:
    """
    Get all available domains in Home Assistant.
    
    Returns:
        Dictionary containing all domains and their entity counts
    """
    logger.info("Tool called: get_home_assistant_domains()")
    
    if _state_cache is None:
        return {
            "status": "error",
            "message": "Home Assistant tools not initialized"
        }
    
    domains = await _state_cache.get_domains()
    
    # Get entity count for each domain
    domain_counts = {}
    for domain in domains:
        entity_ids = await _state_cache.get_entities_by_domain(domain)
        domain_counts[domain] = len(entity_ids)
    
    return {
        "status": "success",
        "count": len(domains),
        "domains": domains,
        "domain_counts": domain_counts
    }

# Tool function mapping for google-genai's function calling
tool_function_map = {
    "get_home_assistant_entity_state": get_home_assistant_entity_state,
    "call_home_assistant_service": call_home_assistant_service,
    "search_home_assistant_entities": search_home_assistant_entities,
    "get_home_assistant_entities_by_domain": get_home_assistant_entities_by_domain,
    "get_home_assistant_domains": get_home_assistant_domains,
}