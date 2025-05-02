#!/usr/bin/env python3
"""
Diagnose the search_home_assistant_entities tool issue.

This script examines the tool creation and registration process in detail.
"""

import os
import sys
import logging
import inspect
import json

# Add the parent directory to the path so we can import raderbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def print_tool_details(tool):
    """Print detailed information about a tool."""
    print(f"\nTool details:")
    print(f"  Type: {type(tool).__name__}")
    
    # Check for common attributes
    if hasattr(tool, 'name'):
        print(f"  Name: {tool.name}")
    elif hasattr(tool, '__name__'):
        print(f"  Name (__name__): {tool.__name__}")
    else:
        print("  Name: Unknown")
        
    if hasattr(tool, 'description'):
        print(f"  Description: {tool.description}")
    
    # Check if it's a function tool
    if hasattr(tool, 'function'):
        print(f"  Function: {tool.function.__name__}")
        print(f"  Function signature: {inspect.signature(tool.function)}")
    
    # Check for schema
    if hasattr(tool, 'schema'):
        print("  Schema:")
        try:
            print(json.dumps(tool.schema, indent=2))
        except:
            print(f"    {tool.schema}")
    elif hasattr(tool, 'function_schema'):
        print("  Function schema:")
        try:
            print(json.dumps(tool.function_schema, indent=2))
        except:
            print(f"    {tool.function_schema}")
    
    # Check for additional attributes
    other_attrs = []
    for attr in dir(tool):
        if not attr.startswith('__') and attr not in ['name', 'description', 'function', 'schema', 'function_schema']:
            try:
                value = getattr(tool, attr)
                if not callable(value):
                    other_attrs.append(attr)
            except:
                pass
    
    if other_attrs:
        print("  Other attributes:")
        for attr in other_attrs[:10]:  # Limit to first 10
            try:
                print(f"    {attr}: {getattr(tool, attr)}")
            except:
                print(f"    {attr}: <Error accessing>")

def diagnose_function_tool():
    """Diagnose issues with FunctionTool creation."""
    from google.adk.tools import FunctionTool
    
    # Check FunctionTool initialization
    print("=" * 60)
    print(" FunctionTool Diagnostics ".center(60, "="))
    print("=" * 60)
    
    # Inspect FunctionTool class
    init_sig = inspect.signature(FunctionTool.__init__)
    print(f"FunctionTool.__init__ signature: {init_sig}")
    
    # Try to read the source code
    try:
        init_source = inspect.getsource(FunctionTool.__init__)
        print("\nFunctionTool.__init__ source:")
        print(init_source)
    except Exception as e:
        print(f"Could not get source: {str(e)}")
    
    print("\nTrying different initialization styles...")
    
    # Test function to use
    def simple_test_func(test_param: str) -> str:
        """A simple test function."""
        return f"You sent: {test_param}"
    
    # Test schema
    test_schema = {
        "name": "simple_test_func",
        "description": "A simple test function",
        "parameters": {
            "type": "object",
            "properties": {
                "test_param": {
                    "type": "string",
                    "description": "A test parameter"
                }
            },
            "required": ["test_param"]
        }
    }
    
    # Try old style
    try:
        print("\nTrying old style (positional args):")
        old_tool = FunctionTool(simple_test_func, test_schema)
        print("✅ Old style succeeded")
        print_tool_details(old_tool)
    except Exception as e:
        print(f"❌ Old style failed: {str(e)}")
    
    # Try ADK 0.3.0 style 
    try:
        print("\nTrying ADK 0.3.0 style (named args):")
        new_tool = FunctionTool(function=simple_test_func, function_schema=test_schema)
        print("✅ ADK 0.3.0 style succeeded")
        print_tool_details(new_tool)
    except Exception as e:
        print(f"❌ ADK 0.3.0 style failed: {str(e)}")
    
    # Try another possible syntax
    try:
        print("\nTrying alterative style:")
        wrapped_schema = {"type": "function", "function": test_schema}
        alt_tool = FunctionTool(function=simple_test_func, function_schema=wrapped_schema)
        print("✅ Alternative style succeeded")
        print_tool_details(alt_tool)
    except Exception as e:
        print(f"❌ Alternative style failed: {str(e)}")

def diagnose_entity_search_tool():
    """Diagnose the entity search tool specifically."""
    from raderbot.tools.mcp_tools import create_find_ha_entities_tool
    
    print("\n" + "=" * 60)
    print(" Entity Search Tool Diagnostics ".center(60, "="))
    print("=" * 60)
    
    try:
        tool = create_find_ha_entities_tool()
        print("✅ Tool created successfully")
        print_tool_details(tool)
        
        # Try to call the function
        from raderbot.tools.mcp_utils import find_home_assistant_entities
        print("\nUnderlying function details:")
        print(f"  Name: {find_home_assistant_entities.__name__}")
        print(f"  Signature: {inspect.signature(find_home_assistant_entities)}")
        print(f"  Module: {find_home_assistant_entities.__module__}")
        
    except Exception as e:
        print(f"❌ Error creating entity search tool: {str(e)}")

def diagnose_agent_tools():
    """Diagnose tools in a sample agent."""
    from google.adk.agents import Agent
    
    print("\n" + "=" * 60)
    print(" Agent Tool Registration Diagnostics ".center(60, "="))
    print("=" * 60)
    
    # Create a test function tool
    from google.adk.tools import FunctionTool
    
    def test_func(param1: str) -> str:
        """A test function."""
        return f"Result: {param1}"
    
    # Try to create a function tool
    try:
        try:
            # Try new style first
            test_tool = FunctionTool(
                function=test_func,
                function_schema={
                    "name": "test_func",
                    "description": "A test function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "param1": {
                                "type": "string",
                                "description": "Parameter 1"
                            }
                        },
                        "required": ["param1"]
                    }
                }
            )
        except TypeError:
            # Fall back to old style
            test_tool = FunctionTool(
                test_func,
                {
                    "name": "test_func",
                    "description": "A test function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "param1": {
                                "type": "string",
                                "description": "Parameter 1"
                            }
                        },
                        "required": ["param1"]
                    }
                }
            )
            
        # Create a simple test agent
        agent = Agent(
            name="test_agent",
            model="gemini-2.5-flash",
            instruction="You are a test agent.",
            tools=[test_tool, test_func]  # Add both a FunctionTool and a raw function
        )
        
        # Check what tools the agent has
        print(f"Agent created with {len(agent.tools)} tools")
        
        for i, tool in enumerate(agent.tools):
            print(f"\nTool {i+1}:")
            print_tool_details(tool)
            
    except Exception as e:
        print(f"❌ Error in agent tools test: {str(e)}")

def diagnose_schema_conversion():
    """Check how schemas are converted by the ADK."""
    print("\n" + "=" * 60)
    print(" ADK Schema Conversion Diagnostics ".center(60, "="))
    print("=" * 60)
    
    from raderbot.tools.mcp_tools import create_find_ha_entities_tool
    
    try:
        # Import the Agent class to examine its schema conversion
        from google.adk.agents import Agent
        
        # Create a schema to test
        entity_search_schema = {
            "name": "search_home_assistant_entities",
            "description": "Search for Home Assistant entities",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Term to search for"
                    }
                },
                "required": ["search_term"]
            }
        }
        
        print("Testing schema conversion...")
        
        # Create a function with the schema
        def test_schema_func(search_term: str) -> dict:
            """Test function."""
            return {"result": search_term}
            
        # Create a test agent to see how it processes the schema
        try:
            # Try with the schema directly
            from google.adk.tools import FunctionTool
            test_tool = FunctionTool(function=test_schema_func, function_schema=entity_search_schema)
            
            # Create a test agent
            agent = Agent(
                name="schema_test_agent",
                model="gemini-2.5-flash",
                instruction="You are a test agent.",
                tools=[test_tool]
            )
            
            print("✅ Agent created with schema")
            
            # Examine the converted tool
            if agent.tools:
                print("Tool in agent:")
                print_tool_details(agent.tools[0])
                
        except Exception as e:
            print(f"❌ Error creating agent with schema: {str(e)}")
            
    except Exception as e:
        print(f"❌ Schema conversion diagnostic error: {str(e)}")

def main():
    """Run diagnostics."""
    # First diagnose FunctionTool
    diagnose_function_tool()
    
    # Diagnose the entity search tool specifically
    diagnose_entity_search_tool()
    
    # Diagnose how tools are registered with an agent
    diagnose_agent_tools()
    
    # Diagnose schema conversion
    diagnose_schema_conversion()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nDiagnostics interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)