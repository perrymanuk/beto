#!/usr/bin/env python3
"""
Test direct API call with different models.

This script tests the function invocation directly with different LLM APIs.
"""

import os
import sys
import logging
import json

# Add the parent directory to the path so we can import raderbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def search_home_assistant_entities(search_term: str, domain_filter=None):
    """
    Search for Home Assistant entities matching search term.
    
    Args:
        search_term: Term to search for in entity names, like 'kitchen' or 'plant'
        domain_filter: Optional domain to filter by (light, switch, etc.)
        
    Returns:
        Dictionary with matching entities
    """
    print(f"Search called with: search_term='{search_term}', domain_filter='{domain_filter}'")
    
    # Create dummy results
    results = []
    if "basement" in search_term.lower():
        results.append({"entity_id": "light.basement_main", "score": 2})
    if "plant" in search_term.lower():
        results.append({"entity_id": "light.plant_light", "score": 2})
    if "light" in search_term.lower():
        results.append({"entity_id": "light.living_room", "score": 1})
    
    return {
        "success": True,
        "match_count": len(results),
        "matches": results
    }

def HassTurnOff(entity_id: str):
    """
    Turn off a Home Assistant entity.
    
    Args:
        entity_id: The entity ID to turn off (e.g., light.kitchen)
    """
    print(f"Turn off called with: entity_id='{entity_id}'")
    return {"success": True, "entity_id": entity_id, "state": "off"}

def test_with_google_genai():
    """Test with Google's Generative AI API directly."""
    print("\n" + "=" * 60)
    print(" Testing with Google Gemini API ".center(60, "="))
    print("=" * 60)
    
    try:
        import google.generativeai as genai
        from google.generativeai.types import FunctionDeclaration
        
        # Get API key from environment variable
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY environment variable not found.")
            return
            
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Define function declarations
        search_function = FunctionDeclaration(
            name="search_home_assistant_entities",
            description="Search for Home Assistant entities matching search term.",
            parameters={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Term to search for in entity names, like 'kitchen' or 'plant'"
                    },
                    "domain_filter": {
                        "type": "string",
                        "description": "Optional domain type to filter by (light, switch, etc.)"
                    }
                },
                "required": ["search_term"]
            }
        )
        
        turn_off_function = FunctionDeclaration(
            name="HassTurnOff",
            description="Turn off a Home Assistant entity.",
            parameters={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID to turn off (e.g., light.kitchen)"
                    }
                },
                "required": ["entity_id"]
            }
        )
        
        # Create a Gemini model
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=[search_function, turn_off_function]
        )
        
        # Define function calling
        def tool_callback(name, args):
            print(f"Tool called: {name}")
            print(f"  Args: {args}")
            
            if name == "search_home_assistant_entities":
                return search_home_assistant_entities(**args)
            elif name == "HassTurnOff":
                return HassTurnOff(**args)
            else:
                return {"error": f"Unknown function: {name}"}
        
        # Call the model
        chat = model.start_chat(
            tools=[search_function, turn_off_function],
            system_instruction="""
            You are a home automation assistant that can search for and control Home Assistant entities.
            When a user asks to control devices (turn on/off, etc.):
            
            1. FIRST use search_home_assistant_entities to find the entity
            2. THEN use HassTurnOff or HassTurnOn with the entity ID
            """
        )
        
        # Send a message
        response = chat.send_message(
            "Turn off the basement plant lights",
            tool_config=genai.ToolConfig(
                function_calling_config=genai.FunctionCallingConfig(
                    mode="auto",
                    allowed_function_names=["search_home_assistant_entities", "HassTurnOff"]
                )
            ),
            tool_callback=tool_callback
        )
        
        print("\nModel response:")
        print(response.text)
        
    except ImportError:
        print("❌ Google Generative AI package not installed. Run: pip install google-generativeai")
    except Exception as e:
        print(f"❌ Error testing with Google Gemini: {str(e)}")

def main():
    """Run the tests."""
    # Run tests with different APIs
    test_with_google_genai()
    
    # Could add more direct API tests here in the future
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)