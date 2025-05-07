"""
Session management for RadBot web interface.

This module handles session management for the RadBot web interface.
It creates and manages ADK Runner instances directly with the root agent from agent.py.
"""
import asyncio
import logging
import os
import sys
from typing import Dict, Optional, Any
from google.genai.types import Content, Part

from fastapi import Depends

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import needed ADK components
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Import root_agent directly from agent.py
from agent import root_agent

# Session class that manages Runner
class SessionRunner:
    """Enhanced ADK Runner for web sessions."""
    
    def __init__(self, user_id: str, session_id: str):
        """Initialize a SessionRunner for a specific user.
        
        Args:
            user_id: Unique user identifier
            session_id: Session identifier
        """
        self.user_id = user_id
        self.session_id = session_id
        self.session_service = InMemorySessionService()
        
        # Debug the root_agent directly for diagnosis of transfers
        if hasattr(root_agent, 'name'):
            logger.info(f"DIRECT AGENT NAME CHECK: root_agent.name='{root_agent.name}'")
        else:
            logger.warning("root_agent has no 'name' attribute!")
            
        # This is critical: explicitly set the name of the root_agent to match what the scout agent uses in transfers
        if hasattr(root_agent, 'name') and root_agent.name != 'beto':
            logger.warning(f"CRITICAL NAME MISMATCH: root_agent.name='{root_agent.name}' should be 'beto' - attempting to fix")
            root_agent.name = 'beto'
            logger.info(f"FIXED: root_agent.name now set to '{root_agent.name}'")
        
        # CRITICAL FIX: Check if any sub_agent exists and ensure its name is consistent too
        if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
            logger.info(f"Found {len(root_agent.sub_agents)} sub-agents in root_agent")
            for i, sa in enumerate(root_agent.sub_agents):
                if hasattr(sa, 'name'):
                    sa_name = sa.name
                    if sa_name != 'scout':
                        logger.warning(f"CRITICAL NAME MISMATCH: sub_agent[{i}].name='{sa_name}' should be 'scout' - fixing")
                        sa.name = 'scout'
                        logger.info(f"Fixed sub_agent name to 'scout'")
                    
                    # CRITICAL FIX: Ensure bidirectional relationship is maintained
                    if hasattr(sa, 'parent'):
                        if sa.parent is not root_agent:
                            logger.warning(f"CRITICAL PARENT MISMATCH: sub_agent '{sa_name}' has wrong parent - fixing")
                            sa.parent = root_agent
                            logger.info(f"Fixed sub_agent parent reference")
                    else:
                        logger.warning(f"Sub-agent has no parent attribute - attempting to add")
                        try:
                            sa.parent = root_agent
                            logger.info(f"Added parent reference to sub_agent")
                        except Exception as e:
                            logger.error(f"Failed to add parent reference: {e}")
        
        # CRITICAL FIX: Verify transfer_to_agent in all tools lists
        from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
        
        # Check root agent transfer tool
        has_root_transfer = False
        if hasattr(root_agent, 'tools') and root_agent.tools:
            for tool in root_agent.tools:
                tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                if tool_name == 'transfer_to_agent':
                    has_root_transfer = True
                    break
                    
            if not has_root_transfer:
                logger.warning("Root agent missing transfer_to_agent tool - adding")
                try:
                    root_agent.tools.append(transfer_to_agent)
                    logger.info("Added transfer_to_agent tool to root agent")
                except Exception as e:
                    logger.error(f"Failed to add transfer tool to root agent: {e}")
                
        # Check all sub-agents for transfer tool
        if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
            for i, sa in enumerate(root_agent.sub_agents):
                if hasattr(sa, 'tools') and sa.tools:
                    has_sa_transfer = False
                    for tool in sa.tools:
                        tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                        if tool_name == 'transfer_to_agent':
                            has_sa_transfer = True
                            break
                            
                    if not has_sa_transfer:
                        logger.warning(f"Sub-agent {i} missing transfer_to_agent tool - adding")
                        try:
                            sa.tools.append(transfer_to_agent)
                            logger.info(f"Added transfer_to_agent tool to sub-agent {i}")
                        except Exception as e:
                            logger.error(f"Failed to add transfer tool to sub-agent {i}: {e}")
        
        # CRITICAL FIX JULY 2025: COMPLETELY REBUILD THE AGENT TREE FIRST
        self._verify_agent_structure()
        
        # Force the app_name to be "beto" - this is what scout agent expects to transfer to
        # This is the most critical fix for ADK 0.4.0 transfers - app_name MUST match agent.name for transfers
        app_name_for_runner = "beto"
        logger.info(f"CRITICAL FIX: Forcing app_name='{app_name_for_runner}' for consistency")
            
        # Create the ADK Runner with explicit app_name matching agent's name
        self.runner = Runner(
            agent=root_agent,
            app_name=app_name_for_runner,  # CRITICAL: Must match agent.name for transfers
            session_service=self.session_service
        )
        
        # CRITICAL FIX: Triple-check runner's app_name
        if hasattr(self.runner, 'app_name') and self.runner.app_name != 'beto':
            logger.warning(f"CRITICAL APP_NAME MISMATCH: runner.app_name='{self.runner.app_name}' should be 'beto'")
            # Try to fix if possible
            try:
                self.runner.app_name = 'beto'
                logger.info("Fixed runner app_name to 'beto'")
            except Exception as e:
                logger.error(f"Unable to fix runner app_name: {e}")
        
        # CRITICAL FIX: Debug the full agent tree in extreme detail
        logger.info("============= DETAILED AGENT TREE DUMP =============")
        logger.info(f"ROOT AGENT: name='{root_agent.name if hasattr(root_agent, 'name') else 'UNNAMED'}'")
        logger.info(f"RUNNER APP_NAME: '{self.runner.app_name if hasattr(self.runner, 'app_name') else 'NO APP_NAME'}'")
        
        if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
            sub_agent_count = len(root_agent.sub_agents)
            sub_agent_names = [sa.name for sa in root_agent.sub_agents if hasattr(sa, 'name')]
            logger.info(f"SUB-AGENTS COUNT: {sub_agent_count}")
            logger.info(f"SUB-AGENT NAMES: {sub_agent_names}")
            
            for i, sa in enumerate(root_agent.sub_agents):
                sa_name = sa.name if hasattr(sa, 'name') else f"unnamed-{i}"
                sa_parent = "CORRECT-PARENT" if (hasattr(sa, 'parent') and sa.parent is root_agent) else "WRONG-PARENT"
                logger.info(f"SUB-AGENT {i}: NAME='{sa_name}', PARENT={sa_parent}")
                
                # Check if sub-agent also knows root agent is 'beto'
                if hasattr(sa, 'parent') and hasattr(sa.parent, 'name'):
                    logger.info(f"SUB-AGENT {i}'s PARENT NAME: '{sa.parent.name}'")
        else:
            logger.warning("NO SUB-AGENTS FOUND IN ROOT AGENT!")
            
        # Log tool information
        if hasattr(root_agent, 'tools') and root_agent.tools:
            tool_count = len(root_agent.tools)
            tool_names = []
            for tool in root_agent.tools:
                if hasattr(tool, 'name'):
                    tool_names.append(tool.name)
                elif hasattr(tool, '__name__'):
                    tool_names.append(tool.__name__)
                else:
                    tool_names.append(str(tool))
            
            logger.info(f"ROOT AGENT TOOLS: {tool_count} tools")
            logger.info(f"HAS TRANSFER TOOL: {'transfer_to_agent' in tool_names}")
            
        logger.info("=====================================================")
    
    def process_message(self, message: str) -> dict:
        """Process a user message and return the agent's response with event data.
        
        Args:
            message: The user's message text
                
        Returns:
            Dictionary containing the agent's response text and event data
        """
        try:
            # Create Content object with the user's message
            user_message = Content(
                parts=[Part(text=message)],
                role="user"
            )
            
            # CRITICAL: Verify agent tree before processing
            self._verify_agent_structure()
            
            # ALWAYS use "beto" as app_name consistently for all session operations
            # This is the most critical fix for ADK 0.4.0 transfers
            session_app_name = "beto"
            
            # Get or create session with consistent app_name
            logger.info(f"CRITICAL FIX: Forcing session with app_name='{session_app_name}' for consistency")
            session = self.session_service.get_session(
                app_name=session_app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            if not session:
                logger.info(f"Creating new session for user {self.user_id} with app_name='{session_app_name}'")
                session = self.session_service.create_session(
                    app_name=session_app_name,  # CRITICAL: Must be "beto" for consistency
                    user_id=self.user_id,
                    session_id=self.session_id
                )
                
                # TRIPLE CHECK session app_name
                if hasattr(session, 'app_name') and session.app_name != 'beto':
                    logger.error(f"SESSION APP_NAME MISMATCH: '{session.app_name}' should be 'beto' - fixing")
                    try:
                        session.app_name = 'beto'
                        logger.info(f"Fixed session.app_name = 'beto'")
                    except Exception as e:
                        logger.error(f"Failed to fix session app_name: {e}")
                
                # CRITICAL FIX: Verify session app_name after creation
                if hasattr(session, 'app_name') and session.app_name != 'beto':
                    logger.error(f"SESSION APP_NAME MISMATCH: Created session has app_name='{session.app_name}' instead of 'beto'")
                    try:
                        session.app_name = 'beto'
                        logger.info("Fixed session app_name to 'beto'")
                    except Exception as e:
                        logger.error(f"Failed to fix session app_name: {e}")
                
                logger.info(f"Created new session for user {self.user_id}")
            
            # CRITICAL FIX: Verify agent tree structure before processing
            self._verify_agent_structure()
            
            # Use the runner to process the message
            logger.info(f"Running agent with message: {message[:50]}{'...' if len(message) > 50 else ''}")
            
            # CRITICAL FIX: Log critical runner and session parameters for debugging
            logger.info(f"RUNNER APP_NAME: '{self.runner.app_name if hasattr(self.runner, 'app_name') else 'unknown'}'")
            logger.info(f"SESSION APP_NAME: '{session.app_name if hasattr(session, 'app_name') else 'unknown'}'")
            logger.info(f"SESSION ID: '{session.id}'")
            logger.info(f"USER ID: '{self.user_id}'")
            
            # Run with double-checked parameters
            events = list(self.runner.run(
                user_id=self.user_id,
                session_id=session.id,
                new_message=user_message
            ))
            
            # Process events
            logger.info(f"Received {len(events)} events from runner")
            
            # Initialize variables for collecting event data
            final_response = None
            processed_events = []
            
            for event in events:
                # Extract event type and create a base event object
                event_type = self._get_event_type(event)
                event_data = {
                    "type": event_type,
                    "timestamp": self._get_current_timestamp()
                }
                
                # Process based on event type
                if event_type == "tool_call":
                    event_data.update(self._process_tool_call_event(event))
                elif event_type == "agent_transfer":
                    event_data.update(self._process_agent_transfer_event(event))
                elif event_type == "planner":
                    event_data.update(self._process_planner_event(event))
                elif event_type == "model_response":
                    event_data.update(self._process_model_response_event(event))
                    # Check if this is the final response
                    if hasattr(event, 'is_final_response') and event.is_final_response():
                        final_response = event_data.get("text", "")
                else:
                    # Generic event processing
                    event_data.update(self._process_generic_event(event))
                
                processed_events.append(event_data)
                
                # Store the event in the events storage
                # Import here to avoid circular imports
                from radbot.web.api.events import add_event
                add_event(self.session_id, event_data)
                
                # If no final response has been found yet, try to extract it
                if final_response is None:
                    # Method 1: Check if it's a final response
                    if hasattr(event, 'is_final_response') and event.is_final_response():
                        if hasattr(event, 'content') and event.content:
                            if hasattr(event.content, 'parts') and event.content.parts:
                                for part in event.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        final_response = part.text
                                        break
                                
                    # Method 2: Check for content directly
                    if final_response is None and hasattr(event, 'content'):
                        if hasattr(event.content, 'text') and event.content.text:
                            final_response = event.content.text
                            
                    # Method 3: Check for message attribute
                    if final_response is None and hasattr(event, 'message'):
                        if hasattr(event.message, 'content'):
                            final_response = event.message.content
            
            if not final_response:
                logger.warning("No text response found in events")
                final_response = "I apologize, but I couldn't generate a response."
            
            # Return both the text response and the processed events
            return {
                "response": final_response,
                "events": processed_events
            }
        
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            error_message = f"I apologize, but I encountered an error processing your message. Please try again. Error: {str(e)}"
            return {
                "response": error_message,
                "events": []
            }
            
    def _get_current_timestamp(self):
        """Get the current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def _get_event_type(self, event):
        """Determine the type of event."""
        # Debug: Log event attributes for debugging
        logger.debug(f"Event class: {event.__class__.__name__}, dir(event): {dir(event)}")
        
        # For tool events in ADK 0.4.0, check for function_call / tool_calls attribute
        if hasattr(event, 'function_call') or hasattr(event, 'tool_calls'):
            logger.info(f"Detected tool call via function_call/tool_calls: {event}")
            return "tool_call"
            
        # Check for tool result event
        if hasattr(event, 'function_response') or hasattr(event, 'tool_results'):
            logger.info(f"Detected tool result: {event}")
            return "tool_call"
        
        # Try to get type attribute
        if hasattr(event, 'type'):
            event_type = str(event.type)
            logger.debug(f"Event has explicit type: {event_type}")
            return event_type
        
        # Check for tool call events
        if (hasattr(event, 'tool_name') or 
            (hasattr(event, 'payload') and 
             isinstance(event.payload, dict) and 
             'toolName' in event.payload)):
            logger.info(f"Detected tool call via tool_name or payload.toolName")
            return "tool_call"
        
        # Check for agent transfer events
        if (hasattr(event, 'to_agent') or 
            (hasattr(event, 'payload') and 
             isinstance(event.payload, dict) and 
             'toAgent' in event.payload)):
            return "agent_transfer"
        
        # Check for planner events
        if (hasattr(event, 'plan') or 
            (hasattr(event, 'payload') and 
             isinstance(event.payload, dict) and 
             ('plan' in event.payload or 'planStep' in event.payload))):
            return "planner"
        
        # Check for model response events
        if hasattr(event, 'is_final_response'):
            is_final = event.is_final_response()
            final_status = "final" if is_final else "intermediate"
            logger.debug(f"Detected model response ({final_status})")
            return "model_response"
        
        # Check for content which indicates model response (ADK 0.4.0+)
        if hasattr(event, 'content') or hasattr(event, 'message'):
            logger.debug(f"Detected model response via content/message attributes")
            return "model_response"
            
        # Log the event for debugging
        logger.warning(f"Unrecognized event type: {event.__class__.__name__}")
        
        # Default category
        return "other"
    
    def _process_tool_call_event(self, event):
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
                event_data["input"] = self._safely_serialize(function_call.args)
                
        # Process tool_calls (ADK 0.4.0+)
        elif hasattr(event, 'tool_calls') and event.tool_calls:
            # Use first tool call for display
            tool_call = event.tool_calls[0]
            if hasattr(tool_call, 'name'):
                event_data["tool_name"] = tool_call.name
                event_data["summary"] = f"Tool Call: {tool_call.name}"
            
            if hasattr(tool_call, 'args'):
                event_data["input"] = self._safely_serialize(tool_call.args)
                
        # Process function response / tool results (ADK 0.4.0+)
        elif hasattr(event, 'function_response'):
            if hasattr(event.function_response, 'name'):
                event_data["tool_name"] = event.function_response.name
                event_data["summary"] = f"Tool Response: {event.function_response.name}"
            
            if hasattr(event.function_response, 'response'):
                event_data["output"] = self._safely_serialize(event.function_response.response)
                
        elif hasattr(event, 'tool_results') and event.tool_results:
            # Use first tool result for display
            tool_result = event.tool_results[0]
            if hasattr(tool_result, 'name'):
                event_data["tool_name"] = tool_result.name
                event_data["summary"] = f"Tool Response: {tool_result.name}"
            
            if hasattr(tool_result, 'output'):
                event_data["output"] = self._safely_serialize(tool_result.output)
        
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
                event_data["input"] = self._safely_serialize(event.input)
            elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'input' in event.payload:
                event_data["input"] = self._safely_serialize(event.payload['input'])
            
            # Extract output
            if hasattr(event, 'output'):
                event_data["output"] = self._safely_serialize(event.output)
            elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'output' in event.payload:
                event_data["output"] = self._safely_serialize(event.payload['output'])
        
        # Log the processed event data for debugging
        logger.debug(f"Processed tool event data: {event_data}")
        
        # Get the full event for details
        event_data["details"] = self._get_event_details(event)
        
        return event_data
    
    def _process_agent_transfer_event(self, event):
        """Process an agent transfer event."""
        event_data = {
            "category": "agent_transfer",
            "summary": "Agent Transfer"
        }
        
        # Extract to_agent
        if hasattr(event, 'to_agent'):
            event_data["to_agent"] = str(event.to_agent)
            event_data["summary"] = f"Transfer to: {event.to_agent}"
        elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'toAgent' in event.payload:
            event_data["to_agent"] = str(event.payload['toAgent'])
            event_data["summary"] = f"Transfer to: {event.payload['toAgent']}"
        
        # Extract from_agent if available
        if hasattr(event, 'from_agent'):
            event_data["from_agent"] = str(event.from_agent)
        elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'fromAgent' in event.payload:
            event_data["from_agent"] = str(event.payload['fromAgent'])
        
        # Get the full event for details
        event_data["details"] = self._get_event_details(event)
        
        return event_data
    
    def _process_planner_event(self, event):
        """Process a planner event."""
        event_data = {
            "category": "planner",
            "summary": "Planner Event"
        }
        
        # Extract plan
        if hasattr(event, 'plan'):
            event_data["plan"] = self._safely_serialize(event.plan)
            event_data["summary"] = "Plan Created"
        elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'plan' in event.payload:
            event_data["plan"] = self._safely_serialize(event.payload['plan'])
            event_data["summary"] = "Plan Created"
        
        # Extract plan step
        if hasattr(event, 'plan_step'):
            event_data["plan_step"] = self._safely_serialize(event.plan_step)
            event_data["summary"] = f"Plan Step: {self._get_plan_step_summary(event.plan_step)}"
        elif hasattr(event, 'payload') and isinstance(event.payload, dict) and 'planStep' in event.payload:
            event_data["plan_step"] = self._safely_serialize(event.payload['planStep'])
            event_data["summary"] = f"Plan Step: {self._get_plan_step_summary(event.payload['planStep'])}"
        
        # Get the full event for details
        event_data["details"] = self._get_event_details(event)
        
        return event_data
    
    def _process_model_response_event(self, event):
        """Process a model response event."""
        event_data = {
            "category": "model_response",
            "summary": "Model Response"
        }
        
        # Extract text from content
        text = ""
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts') and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text += part.text
            elif hasattr(event.content, 'text') and event.content.text:
                text = event.content.text
        
        # Extract text from message
        if not text and hasattr(event, 'message'):
            if hasattr(event.message, 'content'):
                text = event.message.content
        
        event_data["text"] = text
        
        # Check if it's a final response
        if hasattr(event, 'is_final_response') and event.is_final_response():
            event_data["is_final"] = True
            event_data["summary"] = "Final Response"
        else:
            event_data["is_final"] = False
            event_data["summary"] = "Intermediate Response"
        
        # Get the full event for details
        event_data["details"] = self._get_event_details(event)
        
        return event_data
    
    def _process_generic_event(self, event):
        """Process a generic event."""
        event_data = {
            "category": "other",
            "summary": "Other Event"
        }
        
        # Try to get a more descriptive summary
        if hasattr(event, '__class__'):
            event_data["summary"] = f"Event: {event.__class__.__name__}"
        
        # Get the full event for details
        event_data["details"] = self._get_event_details(event)
        
        return event_data
    
    def _get_plan_step_summary(self, plan_step):
        """Get a summary string for a plan step."""
        if isinstance(plan_step, dict):
            if 'description' in plan_step:
                return plan_step['description']
            elif 'action' in plan_step:
                return plan_step['action']
        
        # Fallback summary
        return "Plan Step"
    
    def _get_event_details(self, event):
        """Get detailed information about the event."""
        # Try to convert to dict first
        try:
            if hasattr(event, '__dict__'):
                return self._safely_serialize(event.__dict__)
            elif hasattr(event, 'to_dict'):
                return self._safely_serialize(event.to_dict())
            elif hasattr(event, '__str__'):
                return str(event)
        except:
            pass
        
        # Fallback to string representation
        return str(event)
    
    def _safely_serialize(self, obj):
        """Safely serialize objects to JSON-compatible structures."""
        import json
        
        try:
            # Try direct JSON serialization
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError, ValueError):
            # If that fails, try converting to string
            try:
                if hasattr(obj, '__dict__'):
                    return str(obj.__dict__)
                elif hasattr(obj, 'to_dict'):
                    return str(obj.to_dict())
                else:
                    return str(obj)
            except:
                return f"<Unserializable object of type {type(obj).__name__}>"
    
    def reset_session(self):
        """Reset the session conversation history."""
        try:
            # CRITICAL FIX: Re-check agent tree structure before reset
            self._verify_agent_structure()
            
            # ALWAYS use "beto" for app_name to ensure consistency
            session_app_name = "beto"
            logger.info(f"CRITICAL FIX: Forcing app_name='{session_app_name}' for session reset")
            
            # Simply delete and recreate the session
            logger.info(f"Deleting session for user {self.user_id} with app_name='{session_app_name}'")
            self.session_service.delete_session(
                app_name=session_app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            # Create a new session
            logger.info(f"Recreating session for user {self.user_id} with app_name='{session_app_name}'")
            session = self.session_service.create_session(
                app_name=session_app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            # CRITICAL FIX: Verify session app_name after recreation
            if hasattr(session, 'app_name') and session.app_name != 'beto':
                logger.error(f"SESSION APP_NAME MISMATCH: Recreated session has app_name='{session.app_name}' instead of 'beto'")
                try:
                    session.app_name = 'beto'
                    logger.info("Fixed session app_name to 'beto'")
                except Exception as e:
                    logger.error(f"Failed to fix session app_name: {e}")
            
            # CRITICAL FIX: Re-check agent tree structure after reset
            self._verify_agent_structure()
            
            logger.info(f"Reset session for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error resetting session: {str(e)}")
            return False
    
    def _verify_agent_structure(self):
        """Verify and fix agent tree structure issues for ADK 0.4.0+ compatibility."""
        logger.info("STARTING COMPREHENSIVE AGENT TREE VERIFICATION")

        # CRITICAL: Get reference to agent with the right name for the runner
        runner_agent = None
        
        # CRITICAL FIX (July 2025): Completely rebuild agent tree from scratch
        # ADK 0.4.0 requires a very specific initialization to get agent transfers working
        try:
            # 1. First, ensure root_agent has the right name
            if hasattr(root_agent, 'name') and root_agent.name != 'beto':
                logger.warning(f"ROOT AGENT NAME MISMATCH: '{root_agent.name}' should be 'beto' - fixing")
                root_agent.name = 'beto'
                logger.info(f"Set root_agent.name = '{root_agent.name}'")
            elif not hasattr(root_agent, 'name'):
                logger.error("CRITICAL ERROR: root_agent has no 'name' attribute!")
                try:
                    # Try to add the name attribute
                    setattr(root_agent, 'name', 'beto')
                    logger.info("Added name='beto' attribute to root_agent")
                except Exception as e:
                    logger.error(f"Failed to add name attribute: {e}")
            
            runner_agent = root_agent  # Store reference to agent with name='beto'
            
            # 2. Look for scout agent and fix it
            scout_agent = None
            if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
                # Find the scout agent, if it exists
                for i, sa in enumerate(root_agent.sub_agents):
                    if hasattr(sa, 'name') and sa.name == 'scout':
                        scout_agent = sa
                        logger.info(f"Found existing scout agent in sub_agents[{i}]")
                        break
                    elif hasattr(sa, 'name'):
                        logger.warning(f"Found non-scout agent: '{sa.name}' in sub_agents")
            
            # 3. If we don't have a scout agent, create one (last resort)
            if not scout_agent:
                logger.warning("No scout agent found in root_agent sub_agents - creating a copy")
                try:
                    # Create a minimal scout agent as placeholder
                    from google.adk.agents import Agent
                    scout_agent = Agent(
                        name="scout",
                        model=getattr(root_agent, 'model', None),
                        instruction="You are the scout agent. Transfer back to 'beto' for a more complete experience."
                    )
                    logger.info("Created emergency scout agent placeholder")
                except Exception as e:
                    logger.error(f"Failed to create emergency scout agent: {e}")
                    
            # 4. COMPLETELY REBUILD THE AGENT TREE FROM SCRATCH
            if scout_agent:
                # First, forcibly clear the agent's sub_agents list
                logger.info("Completely rebuilding agent tree from scratch")
                if hasattr(root_agent, 'sub_agents'):
                    root_agent.sub_agents = []
                    logger.info("Cleared root_agent.sub_agents list")
                else:
                    try:
                        setattr(root_agent, 'sub_agents', [])
                        logger.info("Created new root_agent.sub_agents list")
                    except Exception as e:
                        logger.error(f"Failed to create sub_agents list: {e}")
                
                # Add scout to the root agent
                if hasattr(root_agent, 'sub_agents'):
                    # First make sure the name is correct
                    if hasattr(scout_agent, 'name') and scout_agent.name != 'scout':
                        logger.warning(f"FIXING scout_agent name: '{scout_agent.name}' to 'scout'")
                        scout_agent.name = 'scout'
                    
                    # Now add it to the tree
                    root_agent.sub_agents.append(scout_agent)
                    logger.info(f"Added scout_agent to root_agent.sub_agents")
                    
                    # Set bidirectional relationship
                    if hasattr(scout_agent, 'parent'):
                        scout_agent.parent = root_agent
                        logger.info("Set scout_agent.parent = root_agent")
                    else:
                        try:
                            setattr(scout_agent, 'parent', root_agent)
                            logger.info("Added parent attribute to scout_agent")
                        except Exception as e:
                            logger.error(f"Failed to set parent attribute: {e}")
                    
                    # Set _parent attribute for maximum compatibility
                    if hasattr(scout_agent, '_parent'):
                        scout_agent._parent = root_agent
                        logger.info("Set scout_agent._parent = root_agent")
                    else:
                        try:
                            setattr(scout_agent, '_parent', root_agent)
                            logger.info("Added _parent attribute to scout_agent")
                        except Exception as e:
                            logger.error(f"Failed to set _parent attribute: {e}")
                
                # 5. Add transfer_to_agent tool to BOTH agents
                from google.adk.tools.transfer_to_agent_tool import transfer_to_agent, TRANSFER_TO_AGENT_TOOL
                
                # Add to root agent
                if hasattr(root_agent, 'tools'):
                    # Check if tool already exists
                    has_transfer_tool = False
                    for tool in root_agent.tools:
                        tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                        if tool_name == 'transfer_to_agent':
                            has_transfer_tool = True
                            break
                            
                    if not has_transfer_tool:
                        root_agent.tools.append(transfer_to_agent)
                        logger.info("Added transfer_to_agent to root_agent.tools")
                        
                        if TRANSFER_TO_AGENT_TOOL:
                            root_agent.tools.append(TRANSFER_TO_AGENT_TOOL)
                            logger.info("Added TRANSFER_TO_AGENT_TOOL to root_agent.tools")
                
                # Add to scout agent
                if hasattr(scout_agent, 'tools'):
                    # Check if tool already exists
                    has_transfer_tool = False
                    for tool in scout_agent.tools:
                        tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                        if tool_name == 'transfer_to_agent':
                            has_transfer_tool = True
                            break
                            
                    if not has_transfer_tool:
                        scout_agent.tools.append(transfer_to_agent)
                        logger.info("Added transfer_to_agent to scout_agent.tools")
                        
                        if TRANSFER_TO_AGENT_TOOL:
                            scout_agent.tools.append(TRANSFER_TO_AGENT_TOOL)
                            logger.info("Added TRANSFER_TO_AGENT_TOOL to scout_agent.tools")
                else:
                    # Create tools list if missing
                    try:
                        scout_agent.tools = [transfer_to_agent]
                        if TRANSFER_TO_AGENT_TOOL:
                            scout_agent.tools.append(TRANSFER_TO_AGENT_TOOL)
                        logger.info("Created tools list for scout_agent with transfer_to_agent")
                    except Exception as e:
                        logger.error(f"Failed to create tools list: {e}")
                
                # 6. Register transfer handlers with both agents
                try:
                    from google.adk.events import QueryResponse
                    from google.protobuf.json_format import MessageToDict
                    
                    # Helper function for transfer_to_agent handler
                    def create_transfer_handler():
                        return lambda params: MessageToDict(QueryResponse(
                            transfer_to_agent_response={
                                "target_app_name": params["agent_name"],
                                "message": params.get("message", ""),
                            }
                        ))
                    
                    # Register with root agent
                    if hasattr(root_agent, 'register_tool_handler'):
                        root_agent.register_tool_handler("transfer_to_agent", create_transfer_handler())
                        logger.info("Registered transfer_to_agent handler with root_agent")
                    
                    # Register with scout agent
                    if hasattr(scout_agent, 'register_tool_handler'):
                        scout_agent.register_tool_handler("transfer_to_agent", create_transfer_handler())
                        logger.info("Registered transfer_to_agent handler with scout_agent")
                except Exception as e:
                    logger.error(f"Failed to register transfer handlers: {e}")
                    
            # Final debug log of the rebuilt tree
            logger.info("==== AGENT TREE AFTER COMPLETE REBUILD ====")
            if hasattr(root_agent, 'name'):
                logger.info(f"ROOT AGENT: name='{root_agent.name}'")
            if hasattr(root_agent, 'sub_agents'):
                subagent_names = [sa.name if hasattr(sa, 'name') else "unnamed" for sa in root_agent.sub_agents]
                logger.info(f"SUB-AGENTS: {subagent_names}")
                
                for i, sa in enumerate(root_agent.sub_agents):
                    # Check bidirectional relationship
                    has_parent = hasattr(sa, 'parent') and sa.parent is root_agent
                    has_private_parent = hasattr(sa, '_parent') and sa._parent is root_agent
                    in_parent_list = sa in root_agent.sub_agents
                    
                    logger.info(f"  Sub-agent[{i}]: name='{getattr(sa, 'name', 'unnamed')}'")
                    logger.info(f"  Relationships: parent={has_parent}, _parent={has_private_parent}, in_list={in_parent_list}")
                    
                    # Check tools
                    if hasattr(sa, 'tools'):
                        tool_names = []
                        for tool in sa.tools:
                            if hasattr(tool, 'name'):
                                tool_names.append(tool.name)
                            elif hasattr(tool, '__name__'):
                                tool_names.append(tool.__name__)
                            else:
                                tool_names.append(str(type(tool)))
                        logger.info(f"  Tools: {tool_names}")
            logger.info("=========================================")
            
        except Exception as e:
            logger.error(f"Error in agent tree rebuild: {str(e)}", exc_info=True)
        else:
            # If we have no sub-agents, there may be an issue with the agent setup
            logger.warning("NO SUB-AGENTS FOUND IN ROOT AGENT - this may indicate an incomplete setup")
        
        # CRITICAL: Verify transfer_to_agent tool is available to all agents
        from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
        
        # Try to get the TRANSFER_TO_AGENT_TOOL constant as well
        transfer_tool_constant = None
        try:
            from google.adk.tools.transfer_to_agent_tool import TRANSFER_TO_AGENT_TOOL
            transfer_tool_constant = TRANSFER_TO_AGENT_TOOL
        except (ImportError, Exception):
            pass
        
        # 1. Check root agent tools
        if hasattr(root_agent, 'tools') and root_agent.tools:
            has_root_transfer = False
            for tool in root_agent.tools:
                tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                if tool_name == 'transfer_to_agent':
                    has_root_transfer = True
                    break
            
            if not has_root_transfer:
                logger.warning("ROOT AGENT MISSING TRANSFER TOOL - adding")
                try:
                    # Add both the function and constant if available
                    root_agent.tools.append(transfer_to_agent)
                    logger.info("Added transfer_to_agent function to root_agent.tools")
                    
                    if transfer_tool_constant:
                        root_agent.tools.append(transfer_tool_constant)
                        logger.info("Added TRANSFER_TO_AGENT_TOOL constant to root_agent.tools")
                except Exception as e:
                    logger.error(f"Failed to add transfer_to_agent tool: {e}")
        
        # 2. Check all sub-agents for transfer tool
        if hasattr(root_agent, 'sub_agents'):
            for i, sa in enumerate(root_agent.sub_agents):
                if hasattr(sa, 'tools') and sa.tools:
                    has_sa_transfer = False
                    for tool in sa.tools:
                        tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                        if tool_name == 'transfer_to_agent':
                            has_sa_transfer = True
                            break
                    
                    if not has_sa_transfer:
                        logger.warning(f"SUB-AGENT[{i}] MISSING TRANSFER TOOL - adding")
                        try:
                            # Add both the function and constant if available
                            sa.tools.append(transfer_to_agent)
                            logger.info(f"Added transfer_to_agent function to sub-agent[{i}].tools")
                            
                            if transfer_tool_constant:
                                sa.tools.append(transfer_tool_constant)
                                logger.info(f"Added TRANSFER_TO_AGENT_TOOL constant to sub-agent[{i}].tools")
                        except Exception as e:
                            logger.error(f"Failed to add transfer tool to sub-agent[{i}]: {e}")
        
        # 3. Check and register the transfer_to_agent handler with both agents
        try:
            # Import required classes for handler registration
            from google.adk.events import QueryResponse
            from google.protobuf.json_format import MessageToDict
            
            # Check and register with root agent if needed
            if hasattr(root_agent, 'register_tool_handler'):
                tool_handlers = getattr(root_agent, '_tool_handlers', {})
                if 'transfer_to_agent' not in tool_handlers:
                    root_agent.register_tool_handler(
                        "transfer_to_agent",
                        lambda params: MessageToDict(QueryResponse(
                            transfer_to_agent_response={
                                "target_app_name": params["agent_name"],
                                "message": params.get("message", ""),
                            }
                        )),
                    )
                    logger.info("Registered transfer_to_agent handler with root_agent")
            
            # Check and register with all sub-agents
            if hasattr(root_agent, 'sub_agents'):
                for i, sa in enumerate(root_agent.sub_agents):
                    if hasattr(sa, 'register_tool_handler'):
                        sa_tool_handlers = getattr(sa, '_tool_handlers', {})
                        if 'transfer_to_agent' not in sa_tool_handlers:
                            sa.register_tool_handler(
                                "transfer_to_agent",
                                lambda params: MessageToDict(QueryResponse(
                                    transfer_to_agent_response={
                                        "target_app_name": params["agent_name"],
                                        "message": params.get("message", ""),
                                    }
                                )),
                            )
                            logger.info(f"Registered transfer_to_agent handler with sub-agent[{i}]")
        except Exception as e:
            logger.error(f"Failed to register transfer_to_agent handlers: {e}")
        
        # 4. Verify the runner's app_name is consistent with agent name
        if hasattr(self, 'runner') and hasattr(self.runner, 'app_name'):
            if self.runner.app_name != 'beto':
                logger.warning(f"RUNNER APP_NAME MISMATCH: '{self.runner.app_name}' should be 'beto'")
                try:
                    # Fix the runner app_name if possible
                    self.runner.app_name = 'beto'
                    logger.info("Fixed runner.app_name = 'beto'")
                except Exception as e:
                    logger.error(f"Failed to fix runner.app_name: {e}")
        
        # 5. Provide detailed report on agent tree structure
        logger.info("=============== AGENT TREE VERIFICATION REPORT ================")
        logger.info(f"ROOT AGENT: name='{root_agent.name if hasattr(root_agent, 'name') else 'MISSING'}'")
        
        # Check agent tools and handlers
        root_tools_count = len(root_agent.tools) if hasattr(root_agent, 'tools') and root_agent.tools else 0
        root_handlers_count = len(getattr(root_agent, '_tool_handlers', {}))
        logger.info(f"ROOT TOOLS: {root_tools_count} tools, {root_handlers_count} handlers")
        
        # Check sub-agents
        if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
            sub_agent_names = [sa.name if hasattr(sa, 'name') else 'UNNAMED' for sa in root_agent.sub_agents]
            logger.info(f"SUB-AGENTS: {', '.join(sub_agent_names)}")
            
            # Check all individual sub-agents
            for i, sa in enumerate(root_agent.sub_agents):
                sa_name = sa.name if hasattr(sa, 'name') else f"UNNAMED-{i}"
                sa_tools_count = len(sa.tools) if hasattr(sa, 'tools') and sa.tools else 0
                sa_handlers_count = len(getattr(sa, '_tool_handlers', {}))
                
                # Check bidirectional relationship
                has_parent = hasattr(sa, 'parent') and sa.parent is root_agent
                parent_in_tree = sa in root_agent.sub_agents
                
                logger.info(f"  SUB-AGENT[{i}]: name='{sa_name}', tools={sa_tools_count}, handlers={sa_handlers_count}")
                logger.info(f"  SUB-AGENT[{i}] RELATIONSHIP: parent={has_parent}, in_tree={parent_in_tree}")
        else:
            logger.warning("  NO SUB-AGENTS FOUND")
            
        # Check runner
        if hasattr(self, 'runner'):
            runner_app_name = self.runner.app_name if hasattr(self.runner, 'app_name') else 'MISSING'
            logger.info(f"RUNNER: app_name='{runner_app_name}'")
        else:
            logger.warning("  NO RUNNER FOUND")
        
        logger.info("==============================================================")
        logger.info("AGENT TREE VERIFICATION COMPLETED")

class SessionManager:
    """Manager for web sessions and their associated runners."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, SessionRunner] = {}
        self.lock = asyncio.Lock()
        logger.info("Session manager initialized")
    
    async def get_runner(self, session_id: str) -> Optional[SessionRunner]:
        """Get runner for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionRunner instance or None if session not found
        """
        async with self.lock:
            return self.sessions.get(session_id)
    
    async def set_runner(self, session_id: str, runner: SessionRunner):
        """Set runner for a session.
        
        Args:
            session_id: Session ID
            runner: SessionRunner instance
        """
        async with self.lock:
            self.sessions[session_id] = runner
            logger.info(f"Runner set for session {session_id}")
    
    async def reset_session(self, session_id: str):
        """Reset a session.
        
        Args:
            session_id: Session ID to reset
        """
        runner = await self.get_runner(session_id)
        if runner:
            runner.reset_session()
            logger.info(f"Reset session {session_id}")
        else:
            logger.warning(f"Attempted to reset non-existent session {session_id}")

    async def remove_session(self, session_id: str):
        """Remove a session.
        
        Args:
            session_id: Session ID to remove
        """
        async with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Removed session {session_id}")
            else:
                logger.warning(f"Attempted to remove non-existent session {session_id}")

# Singleton session manager
_session_manager = SessionManager()

def get_session_manager() -> SessionManager:
    """Get the session manager.
    
    Returns:
        SessionManager instance
    """
    return _session_manager

async def get_or_create_runner_for_session(
    session_id: str, 
    session_manager: SessionManager = Depends(get_session_manager)
) -> SessionRunner:
    """Get or create a SessionRunner for a session.
    
    Args:
        session_id: Session ID
        session_manager: SessionManager instance
        
    Returns:
        SessionRunner instance
    """
    # Check if we already have a runner for this session
    runner = await session_manager.get_runner(session_id)
    if runner:
        logger.info(f"Using existing runner for session {session_id}")
        return runner
    
    # Create a new runner for this session
    logger.info(f"Creating new session runner for session {session_id}")
    
    try:
        # Create user_id from session_id
        user_id = f"web_user_{session_id}"
        
        # Create new runner
        runner = SessionRunner(user_id=user_id, session_id=session_id)
        logger.info(f"Created new SessionRunner for user {user_id}")
        
        # Store the runner in the session manager
        await session_manager.set_runner(session_id, runner)
        
        return runner
    except Exception as e:
        logger.error(f"Error creating session runner: {str(e)}", exc_info=True)
        raise