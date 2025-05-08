"""
Session management for RadBot web interface.

This module handles session management for the RadBot web interface.
It creates and manages ADK Runner instances directly with the root agent from agent.py.
"""
import asyncio
import logging
import os
import sys
from typing import Dict, Optional, Any, Union
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
from google.adk.artifacts import InMemoryArtifactService

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
        
        # Create artifact service for this session
        self.artifact_service = InMemoryArtifactService()
        logger.info("Created InMemoryArtifactService for the session")
        
        # Try to load MCP tools for this session
        self._try_load_mcp_tools()
        
        # Log agent tree structure
        self._log_agent_tree()
        
        # Create the ADK Runner with app_name matching the agent name for ADK 0.4.0+
        app_name = root_agent.name if hasattr(root_agent, 'name') else "beto"
        logger.info(f"Using app_name='{app_name}' for session management")
        
        # Create the Runner with the artifact service
        self.runner = Runner(
            agent=root_agent,
            app_name=app_name,
            session_service=self.session_service,
            artifact_service=self.artifact_service  # Pass artifact service to Runner
        )
    
    def _log_agent_tree(self):
        """Log the agent tree structure for debugging."""
        logger.info("===== AGENT TREE STRUCTURE =====")
        
        # Check root agent
        if hasattr(root_agent, 'name'):
            logger.info(f"ROOT AGENT: name='{root_agent.name}'")
        else:
            logger.warning("ROOT AGENT: No name attribute")
        
        # Check sub-agents
        if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
            sub_agent_names = [sa.name for sa in root_agent.sub_agents if hasattr(sa, 'name')]
            logger.info(f"SUB-AGENTS: {sub_agent_names}")
            
            # Check each sub-agent
            for i, sa in enumerate(root_agent.sub_agents):
                sa_name = sa.name if hasattr(sa, 'name') else f"unnamed-{i}"
                logger.info(f"SUB-AGENT {i}: name='{sa_name}'")
                
                # Check if sub-agent has its own sub-agents
                if hasattr(sa, 'sub_agents') and sa.sub_agents:
                    sa_sub_names = [ssa.name for ssa in sa.sub_agents if hasattr(ssa, 'name')]
                    logger.info(f"  SUB-AGENTS OF '{sa_name}': {sa_sub_names}")
        else:
            logger.warning("ROOT AGENT: No sub_agents found")
        
        logger.info("===============================")
    
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
            
            # Get the app_name from the runner
            app_name = self.runner.app_name if hasattr(self.runner, 'app_name') else "beto"
            
            # Get or create a session with the user_id and session_id
            session = self.session_service.get_session(
                app_name=app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            if not session:
                logger.info(f"Creating new session for user {self.user_id} with app_name='{app_name}'")
                session = self.session_service.create_session(
                    app_name=app_name,
                    user_id=self.user_id,
                    session_id=self.session_id
                )
            
            # Use the runner to process the message
            logger.info(f"Running agent with message: {message[:50]}{'...' if len(message) > 50 else ''}")
            
            # Log key parameters
            logger.info(f"USER_ID: '{self.user_id}'")
            logger.info(f"SESSION_ID: '{self.session_id}'")
            logger.info(f"APP_NAME: '{app_name}'")
            
            # Run with consistent parameters
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
                    final_response = self._extract_response_from_event(event)
            
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
    
    def _extract_response_from_event(self, event):
        """Extract response text from various event types."""
        # Method 1: Check if it's a final response
        if hasattr(event, 'is_final_response') and event.is_final_response():
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            return part.text
                            
        # Method 2: Check for content directly
        if hasattr(event, 'content'):
            if hasattr(event.content, 'text') and event.content.text:
                return event.content.text
                
        # Method 3: Check for message attribute
        if hasattr(event, 'message'):
            if hasattr(event.message, 'content'):
                return event.message.content
        
        return None
        
    def _get_current_timestamp(self):
        """Get the current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def _get_event_type(self, event):
        """Determine the type of event."""
        # For tool events in ADK 0.4.0, check for function_call / tool_calls attribute
        if hasattr(event, 'function_call') or hasattr(event, 'tool_calls'):
            return "tool_call"
            
        # Check for tool result event
        if hasattr(event, 'function_response') or hasattr(event, 'tool_results'):
            return "tool_call"
        
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
        
        # Check for content which indicates model response (ADK 0.4.0+)
        if hasattr(event, 'content') or hasattr(event, 'message'):
            return "model_response"
        
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
        event_details = self._get_event_details(event)
        
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
        
        # Get the basic event details
        event_details = self._get_event_details(event)
        
        # Add model information if not already present
        if 'model' not in event_details:
            # Check if this event is from a specific agent and add its model information
            agent_name = None
            if hasattr(event, 'agent_name'):
                agent_name = event.agent_name
            elif hasattr(event, 'agent'):
                agent_name = event.agent
            
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
    
    def _try_load_mcp_tools(self):
        """Try to load and add MCP tools to the root agent."""
        try:
            # Import necessary modules
            from radbot.config.config_loader import config_loader
            from radbot.tools.mcp.mcp_client_factory import MCPClientFactory
            from google.adk.tools import FunctionTool
            
            # Get enabled MCP servers
            servers = config_loader.get_enabled_mcp_servers()
            if not servers:
                logger.info("No enabled MCP servers found in configuration")
                return
                
            logger.info(f"Loading tools from {len(servers)} MCP servers")
            
            # Initialize clients and collect tools
            tools_to_add = []
            existing_tool_names = set()
            
            # Get existing tool names
            if hasattr(root_agent, "tools"):
                for tool in root_agent.tools:
                    if hasattr(tool, "name"):
                        existing_tool_names.add(tool.name)
                    elif hasattr(tool, "__name__"):
                        existing_tool_names.add(tool.__name__)
            
            # Go through each server and directly initialize the client
            for server in servers:
                server_id = server.get("id")
                server_name = server.get("name", server_id)
                
                try:
                    # Create a client directly instead of using factory
                    transport = server.get("transport", "sse")
                    url = server.get("url")
                    auth_token = server.get("auth_token")
                    
                    if transport == "sse":
                        # Use our custom client implementation
                        from radbot.tools.mcp.client import MCPSSEClient
                        client = MCPSSEClient(url=url, auth_token=auth_token)
                        
                        # Initialize the client (this is synchronous and safe)
                        if client.initialize():
                            # Get tools from the client
                            server_tools = client.tools
                            
                            if server_tools:
                                logger.info(f"Successfully loaded {len(server_tools)} tools from {server_name}")
                                
                                # Add unique tools
                                for tool in server_tools:
                                    tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
                                    if tool_name not in existing_tool_names:
                                        tools_to_add.append(tool)
                                        existing_tool_names.add(tool_name)
                                        logger.info(f"Added tool: {tool_name} from {server_name}")
                        else:
                            logger.warning(f"Failed to initialize MCP client for {server_name}")
                    else:
                        logger.warning(f"Unsupported transport '{transport}' for MCP server {server_name}")
                        
                except Exception as e:
                    logger.warning(f"Error loading tools from MCP server {server_name}: {str(e)}")
            
            # Add all collected tools to the agent
            if tools_to_add and hasattr(root_agent, "tools"):
                root_agent.tools = list(root_agent.tools) + tools_to_add
                logger.info(f"Added {len(tools_to_add)} total MCP tools to agent")
                
        except Exception as e:
            logger.warning(f"Error loading MCP tools: {str(e)}")

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
            # Get the app_name from the runner
            app_name = self.runner.app_name if hasattr(self.runner, 'app_name') else "beto"
            
            # Delete and recreate the session
            self.session_service.delete_session(
                app_name=app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            # Create a new session
            session = self.session_service.create_session(
                app_name=app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            logger.info(f"Reset session for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error resetting session: {str(e)}")
            return False

# Singleton session manager
class SessionManager:
    """Manager for web sessions and their associated runners."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, SessionRunner] = {}
        self.lock = asyncio.Lock()
        logger.info("Session manager initialized")
    
    async def get_runner(self, session_id: str) -> Optional[SessionRunner]:
        """Get runner for a session."""
        async with self.lock:
            return self.sessions.get(session_id)
    
    async def set_runner(self, session_id: str, runner: SessionRunner):
        """Set runner for a session."""
        async with self.lock:
            self.sessions[session_id] = runner
            logger.info(f"Runner set for session {session_id}")
    
    async def reset_session(self, session_id: str):
        """Reset a session."""
        runner = await self.get_runner(session_id)
        if runner:
            runner.reset_session()
            logger.info(f"Reset session {session_id}")
        else:
            logger.warning(f"Attempted to reset non-existent session {session_id}")
    
    async def remove_session(self, session_id: str):
        """Remove a session."""
        async with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Removed session {session_id}")
            else:
                logger.warning(f"Attempted to remove non-existent session {session_id}")

# Singleton session manager instance
_session_manager = SessionManager()

# Session manager dependency
def get_session_manager() -> SessionManager:
    """Get the session manager."""
    return _session_manager

# Runner dependency for FastAPI
async def get_or_create_runner_for_session(
    session_id: str, 
    session_manager: SessionManager = Depends(get_session_manager)
) -> SessionRunner:
    """Get or create a SessionRunner for a session."""
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