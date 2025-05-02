"""
Tool schema definitions for Home Assistant WebSocket integration with Google GenAI.

This module defines the function declaration schemas used for the Home Assistant 
integration with Google's function calling mechanism. These schemas define the 
tools that the LLM can use to interact with Home Assistant.
"""

from google.generativeai import types as genai_types


def get_home_assistant_tool_schemas() -> genai_types.Tool:
    """
    Get the tool definitions for Home Assistant interaction.
    
    Returns:
        A Tool object containing function declarations for Home Assistant interaction.
    """
    # Create schema using the dict-based parameter structure
    # to ensure compatibility with different versions of GenAI library
    
    get_entity_state_schema = {
        "type": "OBJECT",
        "properties": {
            "entity_id": {
                "type": "STRING",
                "description": "The entity ID to query, e.g., 'light.living_room' or 'sensor.temperature'."
            }
        },
        "required": ["entity_id"]
    }
    
    call_service_schema = {
        "type": "OBJECT",
        "properties": {
            "domain": {
                "type": "STRING",
                "description": "The domain of the service, e.g., 'light', 'switch', 'climate', 'scene', 'script'."
            },
            "service": {
                "type": "STRING",
                "description": "The specific service to call, e.g., 'turn_on', 'turn_off', 'set_temperature', 'activate'."
            },
            "entity_id": {
                "type": "STRING",
                "description": "Optional: The specific entity ID to target with the service call, e.g., 'light.living_room', 'climate.thermostat'. Not required for all services (like scene.activate)."
            },
            "service_data": {
                "type": "OBJECT",
                "description": "Optional: Additional parameters for the service call. Examples: {'brightness_pct': 50} for light.turn_on, {'temperature': 22} for climate.set_temperature."
            }
        },
        "required": ["domain", "service"]
    }
    
    search_entities_schema = {
        "type": "OBJECT",
        "properties": {
            "search_term": {
                "type": "STRING",
                "description": "The term to search for in entity IDs or friendly names, e.g., 'living room', 'temperature', 'kitchen'."
            }
        },
        "required": ["search_term"]
    }
    
    entities_by_domain_schema = {
        "type": "OBJECT",
        "properties": {
            "domain": {
                "type": "STRING",
                "description": "The domain to filter entities by, e.g., 'light', 'sensor', 'switch', 'climate', etc."
            }
        },
        "required": ["domain"]
    }
    
    domains_schema = {
        "type": "OBJECT",
        "properties": {}  # No parameters needed
    }

    # Create the function declarations using the schemas
    fn_declarations = [
        {
            "name": "get_home_assistant_entity_state",
            "description": "Get the current state of a specific Home Assistant entity. Use this to check the status of devices, sensors, or other entities.",
            "parameters": get_entity_state_schema
        },
        {
            "name": "call_home_assistant_service",
            "description": "Execute a specific action in Home Assistant by calling a service. Use this to control devices (turn lights on/off, set thermostat temperature), activate scenes, or run scripts.",
            "parameters": call_service_schema
        },
        {
            "name": "search_home_assistant_entities",
            "description": "Search for Home Assistant entities by name or ID. Use this when you don't know the exact entity ID but want to find entities based on a search term.",
            "parameters": search_entities_schema
        },
        {
            "name": "get_home_assistant_entities_by_domain",
            "description": "Get all entities of a specific domain in Home Assistant. Use this to list all entities of a certain type, like all lights, all sensors, all switches, etc.",
            "parameters": entities_by_domain_schema
        },
        {
            "name": "get_home_assistant_domains",
            "description": "Get a list of all available domains in the Home Assistant instance. Domains represent different types of entities or services, like lights, switches, sensors, etc.",
            "parameters": domains_schema
        }
    ]
    
    # Return the tool with function declarations
    return {"function_declarations": fn_declarations}