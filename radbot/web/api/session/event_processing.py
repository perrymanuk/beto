"""
Event processing for RadBot web interface.

This module provides functions for processing ADK events.
"""

import logging
from typing import Dict, Any

# Import serialization function
from radbot.web.api.session.serialization import _safely_serialize

# Set up logging
logger = logging.getLogger(__name__)

def _process_tool_call_event(event):
    """Process a tool call event."""
    event_data = {
        "category": "tool_call",
        "summary": "Tool Call"
    }
    
    # Process function call events (ADK 0.4.0+)
    if hasattr(event, 'function_call'):
        function_call = event.function_call
        if hasattr(function_call, 'name'):
            event_data["tool_name"] = function_call.name
            event_data["summary"] = f"Tool Call: {function_call.name}"
        
        if hasattr(function_call, 'args'):
            event_data["input"] = _safely_serialize(function_call.args)
            
    # Process tool_calls (ADK 0.4.0+)
    elif hasattr(event, 'tool_calls') and event.tool_calls:
        # Use first tool call for display
        tool_call = event.tool_calls[0]
        if hasattr(tool_call, 'name'):
            event_data["tool_name"] = tool_call.name
            event_data["summary"] = f"Tool Call: {tool_call.name}"
        
        if hasattr(tool_call, 'args'):
            event_data["input"] = _safely_serialize(tool_call.args)
            
    # Process function response / tool results (ADK 0.4.0+)
    elif hasattr(event, 'function_response'):
        if hasattr(event.function_response, 'name'):
            event_data["tool_name"] = event.function_response.name
            event_data["summary"] = f"Tool Response: {event.function_response.name}"
        
        if hasattr(event.function_response, 'response'):
            event_data["output"] = _safely_serialize(event.function_response.response)
            
    elif hasattr(event, 'tool_results') and event.tool_results:
        # Use first tool result for display
        tool_result = event.tool_results[0]
        if hasattr(tool_result, 'name'):
            event_data["tool_name"] = tool_result.name
            event_data["summary"] = f"Tool Response: {tool_result.name}"
        
        if hasattr(tool_result, 'output'):
            event_data["output"] = _safely_serialize(tool_result.output)
    
    # Legacy tool call formats
    else:
        # Extract tool name
        if hasattr(event, 'tool_name'):
            event_data["tool_name"] = event.tool_name
            event_data["summary"] = f"Tool Call: {event.tool_name}"
        elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'toolName' in event.payload:
            event_data["tool_name"] = event.payload['toolName']
            event_data["summary"] = f"Tool Call: {event.payload['toolName']}"
        
        # Extract input
        if hasattr(event, 'input'):
            event_data["input"] = _safely_serialize(event.input)
        elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'input' in event.payload:
            event_data["input"] = _safely_serialize(event.payload['input'])
        
        # Extract output
        if hasattr(event, 'output'):
            event_data["output"] = _safely_serialize(event.output)
        elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'output' in event.payload:
            event_data["output"] = _safely_serialize(event.payload['output'])
    
    # Get the full event for details
    event_data["details"] = _get_event_details(event)
    
    return event_data

def _process_agent_transfer_event(event):
    """Process an agent transfer event."""
    event_data = {
        "category": "agent_transfer",
        "summary": "Agent Transfer"
    }
    
    # Extract to_agent
    to_agent = None
    if hasattr(event, 'to_agent'):
        to_agent = str(event.to_agent)
        event_data["to_agent"] = to_agent
        event_data["summary"] = f"Transfer to: {to_agent}"
    elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'toAgent' in event.payload:
        to_agent = str(event.payload['toAgent'])
        event_data["to_agent"] = to_agent
        event_data["summary"] = f"Transfer to: {to_agent}"
    
    # Extract from_agent if available
    if hasattr(event, 'from_agent'):
        event_data["from_agent"] = str(event.from_agent)
    elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'fromAgent' in event.payload:
        event_data["from_agent"] = str(event.payload['fromAgent'])
    
    # Get the basic event details
    event_details = _get_event_details(event)
    
    # Add model information for the transferred-to agent
    if to_agent:
        # Import here to avoid circular imports
        from radbot.config import config_manager
        
        # Convert agent name to the format expected by config_manager
        agent_config_name = to_agent.lower()
        if agent_config_name == "scout":
            agent_config_name = "scout_agent"
            event_details['model'] = config_manager.get_agent_model(agent_config_name)
        elif agent_config_name in ["code_execution_agent", "search_agent", "todo_agent"]:
            event_details['model'] = config_manager.get_agent_model(agent_config_name)
        elif agent_config_name in ["beto", "radbot"]:
            # Use main model for the root agent
            event_details['model'] = config_manager.get_main_model()
    
    # Add the updated details to the event data
    event_data["details"] = event_details
    
    return event_data

def _process_planner_event(event):
    """Process a planner event."""
    event_data = {
        "category": "planner",
        "summary": "Planner Event"
    }
    
    # Extract plan
    if hasattr(event, 'plan'):
        event_data["plan"] = _safely_serialize(event.plan)
        event_data["summary"] = "Plan Created"
    elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'plan' in event.payload:
        event_data["plan"] = _safely_serialize(event.payload['plan'])
        event_data["summary"] = "Plan Created"
    
    # Extract plan step
    if hasattr(event, 'plan_step'):
        event_data["plan_step"] = _safely_serialize(event.plan_step)
        event_data["summary"] = f"Plan Step: {_get_plan_step_summary(event.plan_step)}"
    elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'planStep' in event.payload:
        event_data["plan_step"] = _safely_serialize(event.payload['planStep'])
        event_data["summary"] = f"Plan Step: {_get_plan_step_summary(event.payload['planStep'])}"
    
    # Get the full event for details
    event_data["details"] = _get_event_details(event)
    
    return event_data

def _process_model_response_event(event):
    """Process a model response event using ADK 0.4.0 structures."""
    event_data = {
        "category": "model_response",
        "summary": "Model Response"
    }

    # Extract text from content - ADK 0.4.0 format
    text = ""

    # Handle message.content structure (primary ADK 0.4.0 format)
    if hasattr(event, 'message'):
        if hasattr(event.message, 'content'):
            # Handle string content
            if isinstance(event.message.content, str):
                text = event.message.content
            # Handle content object with text
            elif hasattr(event.message.content, 'text'):
                text = event.message.content.text
            # Handle content with parts
            elif hasattr(event.message.content, 'parts') and event.message.content.parts:
                for part in event.message.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text += part.text

    # Fall back to direct content if message.content doesn't contain text
    if not text and hasattr(event, 'content'):
        # Handle content as string
        if isinstance(event.content, str):
            text = event.content
        # Handle content object with text
        elif hasattr(event.content, 'text') and event.content.text:
            text = event.content.text
        # Handle content with parts
        elif hasattr(event.content, 'parts') and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    text += part.text

    event_data["text"] = text

    # Check if it's a final response - handle both property and method in ADK 0.4.0
    is_final = False
    if hasattr(event, 'is_final_response'):
        if callable(getattr(event, 'is_final_response')):
            is_final = event.is_final_response()
        else:
            is_final = event.is_final_response

    # In ADK 0.4.0, check message.end_turn if available
    elif hasattr(event, 'message') and hasattr(event.message, 'end_turn'):
        is_final = event.message.end_turn

    event_data["is_final"] = is_final
    event_data["summary"] = "Final Response" if is_final else "Intermediate Response"

    # Save raw response if available (ADK 0.4.0 may use different fields)
    if hasattr(event, 'raw_response'):
        event_data["raw_response"] = event.raw_response
    elif hasattr(event, 'response_raw'):
        event_data["raw_response"] = event.response_raw
    elif hasattr(event, '_raw_response'):
        event_data["raw_response"] = event._raw_response
    elif hasattr(event, '_response'):
        event_data["raw_response"] = event._response
    elif hasattr(event, 'response'):
        event_data["raw_response"] = event.response
    elif hasattr(event, 'message') and hasattr(event.message, 'raw'):
        event_data["raw_response"] = event.message.raw

    # Get the basic event details
    event_details = _get_event_details(event)

    # Add model information if not already present
    if 'model' not in event_details:
        # Check if this event is from a specific agent and add its model information
        agent_name = None
        if hasattr(event, 'agent_name'):
            agent_name = event.agent_name
        elif hasattr(event, 'agent'):
            agent_name = event.agent
        elif hasattr(event, 'message') and hasattr(event.message, 'agent_name'):
            agent_name = event.message.agent_name

        # Set model information based on agent name
        if agent_name:
            # Import here to avoid circular imports
            from radbot.config import config_manager

            # Convert agent name to the format expected by config_manager
            agent_config_name = agent_name.lower()
            if agent_config_name == "scout":
                agent_config_name = "scout_agent"
            elif agent_config_name in ["beto", "radbot"]:
                # Use main model for the root agent
                event_details['model'] = config_manager.get_main_model()

            # For specialized agents, get their specific model
            if agent_config_name in ["code_execution_agent", "search_agent", "scout_agent", "todo_agent"]:
                event_details['model'] = config_manager.get_agent_model(agent_config_name)

    # Add the updated details to the event data
    event_data["details"] = event_details

    return event_data

def _process_generic_event(event):
    """Process a generic event."""
    event_data = {
        "category": "other",
        "summary": "Other Event"
    }
    
    # Try to get a more descriptive summary
    if hasattr(event, '__class__'):
        event_data["summary"] = f"Event: {event.__class__.__name__}"
    
    # Get the full event for details
    event_data["details"] = _get_event_details(event)
    
    return event_data

def _get_plan_step_summary(plan_step):
    """Get a summary string for a plan step."""
    if isinstance(plan_step, dict):
        if 'description' in plan_step:
            return plan_step['description']
        elif 'action' in plan_step:
            return plan_step['action']
    
    # Fallback summary
    return "Plan Step"

def _get_event_details(event):
    """Get detailed information about the event."""
    # Try to convert to dict first
    try:
        if hasattr(event, '__dict__'):
            return _safely_serialize(event.__dict__)
        elif hasattr(event, 'to_dict'):
            return _safely_serialize(event.to_dict())
        elif hasattr(event, '__str__'):
            return str(event)
    except:
        pass
    
    # Fallback to string representation
    return str(event)