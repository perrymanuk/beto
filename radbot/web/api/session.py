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
        
        # Create the ADK Runner with explicit app_name
        self.runner = Runner(
            agent=root_agent,
            app_name="radbot",  # Required keyword parameter
            session_service=self.session_service
        )
        
        # Look at tool information for logging
        if hasattr(root_agent, 'tools') and root_agent.tools:
            tool_count = len(root_agent.tools)
            logger.info(f"SessionRunner created with {tool_count} tools")
        
        # Look at subagent information for logging
        if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
            sub_agent_count = len(root_agent.sub_agents)
            sub_agent_names = [sa.name for sa in root_agent.sub_agents if hasattr(sa, 'name')]
            logger.info(f"SessionRunner has {sub_agent_count} sub-agents: {', '.join(sub_agent_names)}")
    
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
            
            # Get or create session
            session = self.session_service.get_session(
                app_name="radbot",
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            if not session:
                session = self.session_service.create_session(
                    app_name="radbot",
                    user_id=self.user_id,
                    session_id=self.session_id
                )
                logger.info(f"Created new session for user {self.user_id}")
            
            # Use the runner to process the message
            logger.info(f"Running agent with message: {message[:50]}{'...' if len(message) > 50 else ''}")
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
        # Try to get type attribute
        if hasattr(event, 'type'):
            return str(event.type)
        
        # Check for tool call events
        if (hasattr(event, 'tool_name') or 
            (hasattr(event, 'payload') and 
             isinstance(event.payload, dict) and 
             'toolName' in event.payload)):
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
            return "model_response"
        
        # Default category
        return "other"
    
    def _process_tool_call_event(self, event):
        """Process a tool call event."""
        event_data = {
            "category": "tool_call",
            "summary": "Tool Call"
        }
        
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
            # Simply delete and recreate the session
            self.session_service.delete_session(
                app_name="radbot",
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            # Create a new session
            self.session_service.create_session(
                app_name="radbot",
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            logger.info(f"Reset session for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error resetting session: {str(e)}")
            return False

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