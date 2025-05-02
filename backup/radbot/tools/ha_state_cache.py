"""
Home Assistant state cache for storing entity states from the WebSocket connection.

This module provides a state cache for Home Assistant entities that is updated
via the WebSocket connection's event callback. It maintains current entity states
and provides methods for accessing them.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Set, Tuple

logger = logging.getLogger(__name__)


class HomeAssistantStateCache:
    """
    Maintains a cache of Home Assistant entity states updated via WebSocket events.
    Provides methods for querying the current state of entities.
    """

    def __init__(self):
        """Initialize an empty state cache."""
        self._state_lock = asyncio.Lock()
        self._states: Dict[str, Dict[str, Any]] = {}
        self._domains: Dict[str, Set[str]] = {}  # Domain -> set of entity_ids
        self._entity_registry: Dict[str, Dict[str, Any]] = {}  # entity_id -> registry entry
        self._device_registry: Dict[str, Dict[str, Any]] = {}  # device_id -> device entry
        self._entity_registry_display: Dict[str, Dict[str, Any]] = {}  # entity_id -> display registry entry
        self._registry_initialized = False  # Flag to track if we've loaded registry data
        
    def _get_registry_info(self, entity_id: str) -> Dict[str, Any]:
        """
        Extract registry information for an entity.
        
        Args:
            entity_id: The entity ID to get registry info for
            
        Returns:
            A dictionary containing registry information, or an empty dict if not available
        """
        registry_info = {}
        
        # First check the display registry which has more info
        display_entry = self._entity_registry_display.get(entity_id)
        if display_entry:
            # The display registry has more comprehensive information
            registry_info = {
                "name": display_entry.get("name"),
                "disabled": display_entry.get("disabled"),
                "icon": display_entry.get("icon"),
                "device_id": display_entry.get("device_id"),
                "has_entity_name": display_entry.get("has_entity_name", False),
                "original_name": display_entry.get("original_name"),
                "original_entity_id": display_entry.get("entity_id"),  # The original ID from registration
                "hidden": display_entry.get("hidden", False),
                "entity_category": display_entry.get("entity_category"),
                "area_id": display_entry.get("area_id"),
                "device_class": display_entry.get("device_class"),
                "capabilities": display_entry.get("capabilities"),
                "options": display_entry.get("options"),
                "platform": display_entry.get("platform"),
                "aliases": display_entry.get("aliases", []),
            }
            
            # Add display-specific info
            if "display_precision" in display_entry:
                registry_info["display_precision"] = display_entry["display_precision"]
                
            # Add additional display information
            if "area" in display_entry and display_entry["area"]:
                registry_info["area"] = display_entry["area"]
            
            if "device" in display_entry and display_entry["device"]:
                registry_info["device"] = display_entry["device"]
                
            return registry_info
            
        # Fall back to standard registry if display registry doesn't have this entity
        registry_entry = self._entity_registry.get(entity_id)
        if not registry_entry:
            return registry_info
            
        # Extract basic entity registry info
        registry_info = {
            "name": registry_entry.get("name"),
            "disabled": registry_entry.get("disabled"),
            "icon": registry_entry.get("icon"),
            "device_id": registry_entry.get("device_id"),
            "has_entity_name": registry_entry.get("has_entity_name", False),
            "original_name": registry_entry.get("original_name"),
            "original_entity_id": registry_entry.get("original_entity_id")
        }
        
        # Add device info if available
        device_id = registry_entry.get("device_id")
        if device_id and device_id in self._device_registry:
            device = self._device_registry[device_id]
            registry_info["device"] = {
                "name": device.get("name"),
                "manufacturer": device.get("manufacturer"),
                "model": device.get("model"),
                "entry_type": device.get("entry_type"),
                "via_device_id": device.get("via_device_id")
            }
            
        return registry_info

    async def update_state(self, event_data: Dict[str, Any]) -> None:
        """
        Update the state cache with new data from a state_changed event.
        
        Args:
            event_data: The data dictionary from a state_changed event
        """
        entity_id = event_data.get("entity_id")
        new_state = event_data.get("new_state")
        
        if not entity_id:
            logger.warning(f"Received event data without entity_id: {event_data}")
            return
            
        async with self._state_lock:
            if new_state is None:
                # Entity was removed
                if entity_id in self._states:
                    domain = entity_id.split(".", 1)[0]
                    self._states.pop(entity_id, None)
                    if domain in self._domains and entity_id in self._domains[domain]:
                        self._domains[domain].remove(entity_id)
                    logger.debug(f"Removed entity {entity_id} from state cache")
            else:
                # Add or update entity
                self._states[entity_id] = new_state
                
                # Update domain tracking
                domain = entity_id.split(".", 1)[0]
                if domain not in self._domains:
                    self._domains[domain] = set()
                self._domains[domain].add(entity_id)
                
                logger.debug(f"Updated state cache for {entity_id}: {new_state.get('state', 'unknown')}")

    async def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of an entity.
        
        Args:
            entity_id: The entity ID to look up
            
        Returns:
            The entity state dictionary or None if not found
        """
        async with self._state_lock:
            return self._states.get(entity_id)

    async def get_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all cached entity states.
        
        Returns:
            A dictionary of all entity states
        """
        async with self._state_lock:
            # Return a copy of the states to avoid external modification
            return self._states.copy()
    
    async def get_entities_by_domain(self, domain: str) -> List[str]:
        """
        Get all entity IDs for a specific domain.
        
        Args:
            domain: The domain to filter by (e.g., 'light', 'switch')
            
        Returns:
            A list of entity IDs belonging to the specified domain
        """
        async with self._state_lock:
            if domain in self._domains:
                return sorted(list(self._domains[domain]))
            return []

    async def get_domains(self) -> List[str]:
        """
        Get all available domains.
        
        Returns:
            A list of all domains that have entities in the cache
        """
        async with self._state_lock:
            return sorted(list(self._domains.keys()))

    async def entity_exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists in the cache.
        
        Args:
            entity_id: The entity ID to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        async with self._state_lock:
            return entity_id in self._states
    
    async def count_entities(self) -> int:
        """
        Get the total number of entities in the cache.
        
        Returns:
            The number of entities
        """
        async with self._state_lock:
            return len(self._states)
    
    async def update_entity_registry(self, registry_entries: List[Dict[str, Any]]) -> None:
        """
        Update the entity registry with data from the Home Assistant API.
        
        Args:
            registry_entries: A list of entity registry entries from Home Assistant
        """
        async with self._state_lock:
            # Clear existing data
            self._entity_registry.clear()
            
            # Process each entry
            for entry in registry_entries:
                entity_id = entry.get("entity_id")
                if entity_id:
                    self._entity_registry[entity_id] = entry
            
            logger.info(f"Updated entity registry with {len(self._entity_registry)} entries")
    
    async def update_entity_registry_display(self, registry_entries: List[Dict[str, Any]]) -> None:
        """
        Update the entity registry display information with data from the Home Assistant API.
        This contains more comprehensive information about entities including area names
        and device information.
        
        Args:
            registry_entries: A list of entity registry display entries from Home Assistant
        """
        async with self._state_lock:
            # Clear existing data
            self._entity_registry_display.clear()
            
            # Process each entry
            for entry in registry_entries:
                entity_id = entry.get("entity_id")
                if entity_id:
                    self._entity_registry_display[entity_id] = entry
            
            # Mark registry as initialized since we have the display data
            self._registry_initialized = True
            
            logger.info(f"Updated entity registry display with {len(self._entity_registry_display)} entries")
    
    async def update_device_registry(self, device_entries: List[Dict[str, Any]]) -> None:
        """
        Update the device registry with data from the Home Assistant API.
        
        Args:
            device_entries: A list of device registry entries from Home Assistant
        """
        async with self._state_lock:
            # Clear existing data
            self._device_registry.clear()
            
            # Process each entry
            for entry in device_entries:
                device_id = entry.get("id")
                if device_id:
                    self._device_registry[device_id] = entry
            
            logger.info(f"Updated device registry with {len(self._device_registry)} entries")
    
    async def get_entity_registry_entry(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the entity registry entry for an entity.
        
        Args:
            entity_id: The entity ID to look up
            
        Returns:
            The entity registry entry or None if not found
        """
        async with self._state_lock:
            return self._entity_registry.get(entity_id)
    
    async def search_entities(self, search_term: str, domain_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for entities by name or ID.
        
        Args:
            search_term: The term to search for in entity IDs or friendly names
            domain_filter: Optional domain to filter by (e.g., 'light', 'switch')
            
        Returns:
            A list of matching entities with their states
        """
        # Handle empty search term - return all entities filtered by domain if provided
        if not search_term or search_term.strip() == "":
            results = []
            async with self._state_lock:
                for entity_id, state_data in self._states.items():
                    # If domain filter is specified, check if entity belongs to that domain
                    if domain_filter and not entity_id.startswith(f"{domain_filter}."):
                        continue
                        
                    results.append({
                        "entity_id": entity_id,
                        "state": state_data.get("state"),
                        "friendly_name": state_data.get("attributes", {}).get("friendly_name", entity_id),
                        "last_changed": state_data.get("last_changed"),
                        "score": 1  # Base score for domain-only matches
                    })
            return sorted(results, key=lambda x: x.get("friendly_name", "").lower())
        
        search_term = search_term.lower().strip()
        search_words = set(search_term.split())
        results = []
        
        async with self._state_lock:
            # For registry-based search, we can include entities that might not have states yet
            # This is important for newly added entities that haven't reported their state
            
            # Create a combined entity set from both state cache and registry data
            all_entity_ids = set(self._states.keys())
            
            # Add entities from display registry
            if self._registry_initialized:
                all_entity_ids.update(self._entity_registry_display.keys())
            
            for entity_id in all_entity_ids:
                # If domain filter is specified, check if entity belongs to that domain
                if domain_filter and not entity_id.startswith(f"{domain_filter}."):
                    continue
                
                # Get state data if available
                state_data = self._states.get(entity_id, {})
                
                # Get domain and name parts from entity_id (e.g., "light.living_room" -> "light", "living_room")
                domain, entity_name = entity_id.split(".", 1) if "." in entity_id else (entity_id, "")
                
                # Get entity attributes from state if available
                attributes = state_data.get("attributes", {})
                friendly_name = attributes.get("friendly_name", "").lower()
                device_class = attributes.get("device_class", "").lower()
                
                # Initialize score
                score = 0
                
                # Get registry information to enhance search capability
                registry_info = self._get_registry_info(entity_id)
                display_entry = self._entity_registry_display.get(entity_id)
                
                # Look for the search term in all available fields
                
                # Exact match on entity_id (highest priority)
                if entity_id.lower() == search_term:
                    score = 100
                # Exact match on friendly_name
                elif friendly_name == search_term:
                    score = 90
                # Exact match on entity name part (after the domain)
                elif entity_name.lower() == search_term:
                    score = 80
                # Entity ID contains the search term as a whole
                elif search_term in entity_id.lower():
                    score = 70
                # Friendly name contains the search term as a whole
                elif friendly_name and search_term in friendly_name:
                    score = 65
                # Device class matches search term
                elif device_class and search_term in device_class:
                    score = 60
                
                # Check in registry display data for additional matches
                if display_entry:
                    # Exact match on name from registry
                    if display_entry.get("name", "").lower() == search_term:
                        score = max(score, 88)
                    # Contains match on name from registry
                    elif search_term in display_entry.get("name", "").lower():
                        score = max(score, 64)
                    
                    # Check for area matches
                    if "area" in display_entry and display_entry["area"]:
                        area_name = display_entry["area"].get("name", "").lower()
                        # Exact match on area name
                        if area_name == search_term:
                            score = max(score, 85)
                        # Contains match on area name
                        elif search_term in area_name:
                            score = max(score, 62)
                    
                    # Check for device matches
                    if "device" in display_entry and display_entry["device"]:
                        device_name = display_entry["device"].get("name", "").lower()
                        # Exact match on device name
                        if device_name == search_term:
                            score = max(score, 83)
                        # Contains match on device name
                        elif search_term in device_name:
                            score = max(score, 60)
                            
                        # Check for manufacturer and model
                        manufacturer = display_entry["device"].get("manufacturer", "").lower()
                        model = display_entry["device"].get("model", "").lower()
                        
                        if manufacturer == search_term:
                            score = max(score, 75)
                        elif search_term in manufacturer:
                            score = max(score, 55)
                            
                        if model == search_term:
                            score = max(score, 72)
                        elif search_term in model:
                            score = max(score, 53)
                
                # If we have a score already, add the entity with that score
                if score > 0:
                    result = {
                        "entity_id": entity_id,
                        "domain": domain,
                        "score": score,
                        "registry_info": registry_info
                    }
                    
                    # Add state information if available
                    if entity_id in self._states:
                        result.update({
                            "state": state_data.get("state"),
                            "friendly_name": attributes.get("friendly_name", entity_id),
                            "last_changed": state_data.get("last_changed"),
                            "attributes": {k: v for k, v in attributes.items() if k != "friendly_name"}
                        })
                    # If no state available but we have registry data
                    elif registry_info:
                        result["friendly_name"] = registry_info.get("name") or entity_id
                        if "device" in registry_info and registry_info["device"]:
                            result["device_name"] = registry_info["device"].get("name")
                        if "area" in registry_info and registry_info["area"]:
                            result["area_name"] = registry_info["area"].get("name")
                    
                    results.append(result)
                    continue
                
                # For word-level matching, prepare word sets with more comprehensive data
                entity_words = set()
                
                # Add words from entity_id (replacing separators)
                entity_id_normalized = entity_id.lower().replace(".", " ").replace("_", " ").replace("-", " ")
                entity_words.update(entity_id_normalized.split())
                
                # Add words from friendly_name if available
                if friendly_name:
                    entity_words.update(friendly_name.split())
                
                # Add device_class if available
                if device_class:
                    entity_words.update(device_class.split())
                
                # Add words from display registry if available 
                if display_entry:
                    # Add name from registry
                    if display_entry.get("name"):
                        entity_words.update(display_entry["name"].lower().split())
                        
                    # Add area info
                    if "area" in display_entry and display_entry["area"]:
                        if display_entry["area"].get("name"):
                            entity_words.update(display_entry["area"]["name"].lower().split())
                    
                    # Add device info
                    if "device" in display_entry and display_entry["device"]:
                        # Add device name
                        if display_entry["device"].get("name"):
                            entity_words.update(display_entry["device"]["name"].lower().split())
                            
                        # Add manufacturer
                        if display_entry["device"].get("manufacturer"):
                            entity_words.update(display_entry["device"]["manufacturer"].lower().split())
                            
                        # Add model
                        if display_entry["device"].get("model"):
                            entity_words.update(display_entry["device"]["model"].lower().split())
                
                # Fallback to regular registry if no display registry
                elif entity_id in self._entity_registry:
                    registry_entry = self._entity_registry[entity_id]
                    
                    # Add original entity ID (might be different from current ID if renamed)
                    if "original_entity_id" in registry_entry:
                        original = registry_entry["original_entity_id"].lower().replace(".", " ").replace("_", " ").replace("-", " ")
                        entity_words.update(original.split())
                    
                    # Add name from registry
                    if registry_entry.get("name"):
                        entity_words.update(registry_entry["name"].lower().split())
                        
                    # Add device info if available
                    device_id = registry_entry.get("device_id")
                    if device_id and device_id in self._device_registry:
                        device = self._device_registry[device_id]
                        
                        # Add device name
                        if device.get("name"):
                            entity_words.update(device["name"].lower().split())
                            
                        # Add manufacturer
                        if device.get("manufacturer"):
                            entity_words.update(device["manufacturer"].lower().split())
                            
                        # Add model
                        if device.get("model"):
                            entity_words.update(device["model"].lower().split())
                
                # Word-level matching
                matching_words = search_words.intersection(entity_words)
                if matching_words:
                    # Score based on percentage of search words found (max 50 points)
                    word_match_score = 50 * len(matching_words) / len(search_words)
                    
                    # Bonus points if matching words are found in friendly_name or domain
                    if friendly_name and any(word in friendly_name for word in matching_words):
                        word_match_score += 10
                    if any(word in domain.lower() for word in matching_words):
                        word_match_score += 5
                    
                    # Bonus for matches in display registry area or device name
                    if display_entry:
                        if "area" in display_entry and display_entry["area"] and display_entry["area"].get("name"):
                            area_name = display_entry["area"]["name"].lower()
                            if any(word in area_name for word in matching_words):
                                word_match_score += 8
                        
                        if "device" in display_entry and display_entry["device"] and display_entry["device"].get("name"):
                            device_name = display_entry["device"]["name"].lower()
                            if any(word in device_name for word in matching_words):
                                word_match_score += 7
                    
                    result = {
                        "entity_id": entity_id,
                        "domain": domain,
                        "score": word_match_score,
                        "registry_info": registry_info
                    }
                    
                    # Add state information if available
                    if entity_id in self._states:
                        result.update({
                            "state": state_data.get("state"),
                            "friendly_name": attributes.get("friendly_name", entity_id),
                            "last_changed": state_data.get("last_changed"),
                            "attributes": {k: v for k, v in attributes.items() if k != "friendly_name"}
                        })
                    # If no state available but we have registry data
                    elif registry_info:
                        result["friendly_name"] = registry_info.get("name") or entity_id
                        if "device" in registry_info and registry_info["device"]:
                            result["device_name"] = registry_info["device"].get("name")
                        if "area" in registry_info and registry_info["area"]:
                            result["area_name"] = registry_info["area"].get("name")
                    
                    results.append(result)
                    continue
                
                # Check for partial matches (substrings in words)
                # This handles cases where search term is part of a compound word
                word_match_score = 0
                for word in entity_words:
                    if search_term in word:
                        word_match_score = max(word_match_score, 20)  # Base score for substring match
                    
                    # Check if any search word is part of this entity word
                    for search_word in search_words:
                        if search_word in word:
                            word_match_score = max(word_match_score, 15)  # Slightly lower score
                
                if word_match_score > 0:
                    result = {
                        "entity_id": entity_id,
                        "domain": domain,
                        "score": word_match_score,
                        "registry_info": registry_info
                    }
                    
                    # Add state information if available
                    if entity_id in self._states:
                        result.update({
                            "state": state_data.get("state"),
                            "friendly_name": attributes.get("friendly_name", entity_id),
                            "last_changed": state_data.get("last_changed"),
                            "attributes": {k: v for k, v in attributes.items() if k != "friendly_name"}
                        })
                    # If no state available but we have registry data
                    elif registry_info:
                        result["friendly_name"] = registry_info.get("name") or entity_id
                        if "device" in registry_info and registry_info["device"]:
                            result["device_name"] = registry_info["device"].get("name")
                        if "area" in registry_info and registry_info["area"]:
                            result["area_name"] = registry_info["area"].get("name")
                    
                    results.append(result)
        
        # Sort results by score (higher first)
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results