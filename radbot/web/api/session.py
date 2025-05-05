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
    
    def process_message(self, message: str) -> str:
        """Process a user message and return the agent's response.
        
        Args:
            message: The user's message text
                
        Returns:
            The agent's response as a string
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
            
            # Extract text response
            logger.info(f"Received {len(events)} events from runner")
            
            # Find the final response text
            final_response = None
            for event in events:
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
                        
                # Break once we have a response
                if final_response:
                    break
            
            if final_response:
                return final_response
            else:
                logger.warning("No text response found in events")
                return "I apologize, but I couldn't generate a response."
        
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            return f"I apologize, but I encountered an error processing your message. Please try again. Error: {str(e)}"
    
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