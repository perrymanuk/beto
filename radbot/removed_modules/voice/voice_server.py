"""
Voice server for bidirectional voice chat using FastAPI.

This module provides a FastAPI server that handles WebSocket connections
for bidirectional voice chat, using Google ADK for speech-to-text and
Google Cloud Text-to-Speech for TTS.
"""

import asyncio
import base64
import json
import logging
import os
import uuid
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from google.adk.agents import BaseAgent
from google.adk import Runner  # Use the standard Runner 

from radbot.voice.google_cloud_tts_adapter import GoogleCloudTTSAdapter, create_google_cloud_tts_client

# Set up logging
logger = logging.getLogger(__name__)

class VoiceServer:
    """
    Server for handling bidirectional voice chat.
    
    This server manages WebSocket connections for streaming audio between
    the client and the agent, using Google ADK for speech-to-text and
    Google Cloud Text-to-Speech for TTS.
    """
    
    def __init__(
        self, 
        agent: BaseAgent,
        tts_adapter: Optional[GoogleCloudTTSAdapter] = None,
        host: str = "localhost",
        port: int = 8000
    ):
        """
        Initialize the voice server.
        
        Args:
            agent: Google ADK agent to use for processing input
            tts_adapter: Google Cloud TTS adapter for text-to-speech
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.agent = agent
        self.tts_adapter = tts_adapter
        self.host = host
        self.port = port
        
        # Create FastAPI app
        self.app = FastAPI(title="RadBot Voice Server")
        self._setup_routes()
        
        # Active session tracking
        self.active_sessions: Dict[str, Tuple[Runner, asyncio.Queue]] = {}
        
    def _setup_routes(self):
        """Set up FastAPI routes for the voice server."""
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "ok"}
            
        @self.app.websocket("/ws/voice/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """
            WebSocket endpoint for bidirectional voice chat.
            
            Args:
                websocket: WebSocket connection
                session_id: Unique session ID
            """
            await websocket.accept()
            logger.info(f"WebSocket connection accepted for session: {session_id}")
            
            # Create queues for inter-task communication
            text_to_tts_queue = asyncio.Queue(maxsize=100)  # Text chunks for TTS
            audio_to_client_queue = asyncio.Queue(maxsize=100)  # Audio chunks to client
            user_input_queue = asyncio.Queue(maxsize=100)  # Input from user (text or audio)
            
            try:
                # Initialize ADK components for this session
                runner, _ = self._start_adk_session(session_id, user_input_queue)
                
                # Create tasks
                tasks = set()
                
                # Task 1: Process ADK events (text from agent)
                tasks.add(asyncio.create_task(
                    self._process_adk_events(
                        runner,
                        text_to_tts_queue,
                        audio_to_client_queue,
                        session_id
                    )
                ))
                
                # Task 2: Only add Google Cloud TTS task if adapter is available
                if self.tts_adapter and self.tts_adapter.client:
                    tasks.add(asyncio.create_task(
                        self._manage_tts_connection(
                            text_to_tts_queue,
                            audio_to_client_queue,
                            session_id
                        )
                    ))
                else:
                    # No TTS available, just forward text directly
                    tasks.add(asyncio.create_task(
                        self._forward_text_to_client(
                            text_to_tts_queue,
                            audio_to_client_queue,
                            session_id
                        )
                    ))
                
                # Task 3: Handle client input (audio from client to ADK)
                tasks.add(asyncio.create_task(
                    self._process_client_input(
                        websocket,
                        user_input_queue,
                        session_id
                    )
                ))
                
                # Task 4: Send to client (audio or text from audio_to_client_queue)
                tasks.add(asyncio.create_task(
                    self._send_to_client(
                        websocket,
                        audio_to_client_queue,
                        session_id
                    )
                ))
                
                # Wait for any task to complete (or fail)
                done, pending = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                
                try:
                    # Wait for tasks to be cancelled
                    await asyncio.gather(*pending, return_exceptions=True)
                except asyncio.CancelledError:
                    pass
                    
                # Check if any task raised an exception
                for task in done:
                    try:
                        task.result()
                    except Exception as e:
                        logger.error(f"Task error in session {session_id}: {e}")
            
            except Exception as e:
                logger.error(f"Error in WebSocket handler for session {session_id}: {e}")
                await websocket.close(code=1011, reason=f"Server error: {str(e)}")
            
            finally:
                # Clean up
                self._clean_up_session(session_id)
                logger.info(f"WebSocket session {session_id} closed")
                
    def _start_adk_session(self, session_id: str, user_input_queue: asyncio.Queue) -> Tuple[Runner, asyncio.Queue]:
        """
        Start an ADK session for the given session ID.
        
        Args:
            session_id: Unique session ID
            user_input_queue: Queue for user input
            
        Returns:
            Tuple[Runner, asyncio.Queue]: ADK runner and user input queue
        """
        # Check if session already exists
        if session_id in self.active_sessions:
            logger.info(f"Returning existing session for {session_id}")
            return self.active_sessions[session_id]
        
        # Create new ADK runner
        runner = Runner(agent=self.agent)
        
        # Store session
        self.active_sessions[session_id] = (runner, user_input_queue)
        logger.info(f"Started new ADK session for {session_id}")
        
        # Start a task to run the conversation with the agent
        asyncio.create_task(self._run_conversation(runner, user_input_queue, session_id))
        
        return runner, user_input_queue
        
    async def _run_conversation(self, runner: Runner, input_queue: asyncio.Queue, session_id: str):
        """
        Run a conversation with the agent.
        
        Args:
            runner: ADK Runner
            input_queue: Queue for user input
            session_id: Unique session ID
        """
        try:
            # Start the conversation
            logger.info(f"Starting conversation for session {session_id}")
            
            while True:
                # Wait for user input
                user_input = await input_queue.get()
                
                # None signals the end
                if user_input is None:
                    break
                
                # Run the agent with the user input
                if isinstance(user_input, dict) and user_input.get("type") == "interrupt":
                    # Handle interruption
                    logger.info(f"Interrupting conversation for session {session_id}")
                    # Let any current run finish
                    continue
                
                elif isinstance(user_input, dict) and user_input.get("type") == "text":
                    # Text input
                    text = user_input.get("text", "")
                    logger.info(f"Processing text input: {text}")
                    
                    # Run the agent with the text input
                    try:
                        await runner.run_text(text)
                    except Exception as e:
                        logger.error(f"Error running agent with text for session {session_id}: {e}")
                
                elif isinstance(user_input, bytes):
                    # Audio input (PCM 16-bit 16kHz LE)
                    try:
                        # Simply running text for now - ADK audio input is complex
                        logger.info(f"Received audio input of {len(user_input)} bytes")
                        
                        # In a full implementation, this would use Google APIs to convert
                        # audio to text and then run the agent with the text
                        # For now, we'll log this and acknowledge receipt
                        
                        # ADK versions have different APIs for handling audio input
                        # This would need to adapt based on the specific ADK version
                        # Newer version's Runner.run_audio() might be able to handle this direct
                        
                        # For now, without converting audio to text:
                        # Just inform user we received audio but text is preferred for now
                        logger.info(f"Audio input received but not processed")
                    except Exception as e:
                        logger.error(f"Error processing audio input for session {session_id}: {e}")
                
                # Mark as done
                input_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info(f"Conversation task cancelled for session {session_id}")
        except Exception as e:
            logger.error(f"Error running conversation for session {session_id}: {e}")
        
    def _clean_up_session(self, session_id: str):
        """
        Clean up resources for the given session ID.
        
        Args:
            session_id: Unique session ID
        """
        if session_id in self.active_sessions:
            # For now, just remove from active sessions
            # Future: consider proper cleanup of runner
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up session {session_id}")
    
    async def _process_adk_events(
        self,
        runner: Runner,
        tts_queue: asyncio.Queue,
        client_queue: asyncio.Queue,
        session_id: str
    ):
        """
        Process events from the ADK agent.
        
        Args:
            runner: ADK Runner that provides events
            tts_queue: Queue for text to be synthesized
            client_queue: Queue for messages to be sent to client
            session_id: Unique session ID
        """
        logger.info(f"Started ADK event processor for session {session_id}")
        
        try:
            # Monitor for new responses in the runner's conversation
            last_response_text = ""
            
            while True:
                # Check for new responses (polling approach)
                try:
                    # Get the latest conversation turns
                    conversation = runner.conversation
                    
                    if conversation and conversation.turns:
                        # Get the latest agent turn
                        latest_turn = conversation.turns[-1]
                        
                        if hasattr(latest_turn, 'agent_response') and latest_turn.agent_response:
                            # Get the response text
                            response_text = str(latest_turn.agent_response)
                            
                            # Only process if it's new
                            if response_text != last_response_text:
                                # Get the new content (the difference)
                                new_content = response_text[len(last_response_text):]
                                
                                if new_content:
                                    logger.debug(f"New content: {new_content}")
                                    
                                    # Put on TTS queue
                                    await tts_queue.put(new_content)
                                    
                                # Update last response
                                last_response_text = response_text
                                
                                # If the turn is complete (no ... at the end)
                                if not response_text.endswith("..."):
                                    # Signal turn completion
                                    await client_queue.put({
                                        "type": "status",
                                        "data": "turn_complete"
                                    })
                                    logger.debug(f"Turn complete for session {session_id}")
                                    
                                    # Reset for next turn
                                    last_response_text = ""
                
                except Exception as e:
                    logger.error(f"Error checking for new responses: {e}")
                
                # Wait a bit before checking again
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info(f"ADK event processor cancelled for session {session_id}")
            raise
        except Exception as e:
            logger.error(f"Error processing ADK events for session {session_id}: {e}")
            await client_queue.put({
                "type": "error",
                "data": f"Agent processing error: {str(e)}"
            })
            # Pass the exception up
            raise
            
    async def _manage_tts_connection(
        self,
        tts_queue: asyncio.Queue,
        client_queue: asyncio.Queue,
        session_id: str
    ):
        """
        Manage connection to Google Cloud TTS.
        
        Args:
            tts_queue: Queue of text chunks to synthesize
            client_queue: Queue for sending audio to client
            session_id: Unique session ID
        """
        logger.info(f"Started Google Cloud TTS connection manager for session {session_id}")
        
        if not self.tts_adapter or not self.tts_adapter.client:
            logger.error("Google Cloud TTS adapter not available")
            await client_queue.put({
                "type": "error",
                "data": "Text-to-speech service not available"
            })
            return
            
        try:
            while True:
                # Get next text chunk from queue
                text_chunk = await tts_queue.get()
                
                # None signals the end
                if text_chunk is None:
                    break
                    
                if not text_chunk.strip():
                    tts_queue.task_done()
                    continue
                
                try:
                    # Send text to Google Cloud TTS and stream audio back
                    logger.debug(f"Sending to Google Cloud TTS: {text_chunk[:50]}...")
                    
                    # Stream audio chunks from Google Cloud TTS
                    async for audio_chunk in self.tts_adapter.stream_speech(text_chunk):
                        # Put audio on client queue
                        await client_queue.put({
                            "type": "audio",
                            "data": audio_chunk
                        })
                except Exception as e:
                    logger.error(f"Error with Google Cloud TTS for session {session_id}: {e}")
                    # Send error to client
                    await client_queue.put({
                        "type": "error",
                        "data": f"Speech synthesis error: {str(e)}"
                    })
                    # Fall back to text
                    await client_queue.put({
                        "type": "text",
                        "data": text_chunk
                    })
                
                # Mark as done
                tts_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info(f"Google Cloud TTS manager cancelled for session {session_id}")
            raise
        except Exception as e:
            logger.error(f"Error in Google Cloud TTS manager for session {session_id}: {e}")
            # Send error to client
            await client_queue.put({
                "type": "error",
                "data": f"Speech synthesis service error: {str(e)}"
            })
            # Pass the exception up
            raise
    
    async def _forward_text_to_client(
        self,
        tts_queue: asyncio.Queue,
        client_queue: asyncio.Queue,
        session_id: str
    ):
        """
        Forward text directly to client (when TTS is not available).
        
        Args:
            tts_queue: Queue of text chunks
            client_queue: Queue for sending to client
            session_id: Unique session ID
        """
        logger.info(f"Started text forwarder for session {session_id}")
        
        try:
            while True:
                # Get next text chunk from queue
                text_chunk = await tts_queue.get()
                
                # None signals the end
                if text_chunk is None:
                    break
                    
                if not text_chunk.strip():
                    tts_queue.task_done()
                    continue
                
                # Forward text to client
                await client_queue.put({
                    "type": "text",
                    "data": text_chunk
                })
                
                # Mark as done
                tts_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info(f"Text forwarder cancelled for session {session_id}")
            raise
        except Exception as e:
            logger.error(f"Error in text forwarder for session {session_id}: {e}")
            # Send error to client
            await client_queue.put({
                "type": "error",
                "data": f"Text processing error: {str(e)}"
            })
            # Pass the exception up
            raise
            
    async def _process_client_input(
        self,
        websocket: WebSocket,
        input_queue: asyncio.Queue,
        session_id: str
    ):
        """
        Process input from client and send to ADK.
        
        Args:
            websocket: WebSocket connection to client
            input_queue: Queue for input to the agent
            session_id: Unique session ID
        """
        logger.info(f"Started client input processor for session {session_id}")
        
        try:
            while True:
                # Receive data from client
                message = await websocket.receive()
                
                # Check if we got bytes (audio) or text (JSON control message)
                if "bytes" in message:
                    # Audio data
                    audio_data = message["bytes"]
                    
                    # Skip empty chunks
                    if not audio_data:
                        continue
                        
                    logger.debug(f"Received {len(audio_data)} bytes of audio from client")
                    
                    # Add to input queue
                    await input_queue.put(audio_data)
                    
                elif "text" in message:
                    # Control message
                    try:
                        control = json.loads(message["text"])
                        
                        if control.get("type") == "interrupt":
                            # User interrupted
                            logger.info(f"User interrupt received for session {session_id}")
                            
                            # Put interrupt message on input queue
                            await input_queue.put({
                                "type": "interrupt"
                            })
                            
                            # Also send status to client
                            await websocket.send_json({
                                "interrupted": True
                            })
                            
                        elif control.get("type") == "text_input":
                            # Text input instead of audio
                            text = control.get("text", "")
                            logger.info(f"Text input received: {text}")
                            
                            # Put text on input queue
                            await input_queue.put({
                                "type": "text",
                                "text": text
                            })
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Received invalid JSON from client: {message['text']}")
                        
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from session {session_id}")
        except asyncio.CancelledError:
            logger.info(f"Client input processor cancelled for session {session_id}")
            raise
        except Exception as e:
            logger.error(f"Error processing client input for session {session_id}: {e}")
            # Pass the exception up
            raise
    
    async def _send_to_client(
        self,
        websocket: WebSocket,
        client_queue: asyncio.Queue,
        session_id: str
    ):
        """
        Send audio or text to client.
        
        Args:
            websocket: WebSocket connection to client
            client_queue: Queue of messages to send
            session_id: Unique session ID
        """
        logger.info(f"Started client output processor for session {session_id}")
        
        try:
            while True:
                # Get next item from queue
                item = await client_queue.get()
                
                # None signals the end
                if item is None:
                    break
                
                try:
                    if item["type"] == "audio":
                        # Audio data needs to be base64 encoded for JSON
                        encoded_audio = base64.b64encode(item["data"]).decode("utf-8")
                        await websocket.send_json({
                            "audio_chunk": encoded_audio
                        })
                        
                    elif item["type"] == "text":
                        # Text message
                        await websocket.send_json({
                            "message": item["data"]
                        })
                        
                    elif item["type"] == "status":
                        # Status update
                        await websocket.send_json({
                            item["data"]: True  # e.g., {"turn_complete": true}
                        })
                        
                    elif item["type"] == "error":
                        # Error message
                        await websocket.send_json({
                            "error": item["data"]
                        })
                except Exception as e:
                    logger.error(f"Error sending to client for session {session_id}: {e}")
                    
                # Mark as done
                client_queue.task_done()
                
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from session {session_id}")
        except asyncio.CancelledError:
            logger.info(f"Client output processor cancelled for session {session_id}")
            raise
        except Exception as e:
            logger.error(f"Error sending to client for session {session_id}: {e}")
            # Pass the exception up
            raise
    
    def run(self):
        """Run the voice server."""
        logger.info(f"Starting voice server on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)

def create_voice_server(
    agent: BaseAgent,
    host: Optional[str] = None,
    port: Optional[int] = None
) -> VoiceServer:
    """
    Create a voice server for the given agent.
    
    Args:
        agent: Google ADK agent to use
        host: Host to bind the server to (default: from env or localhost)
        port: Port to bind the server to (default: from env or 8000)
        
    Returns:
        VoiceServer: Voice server instance
    """
    # Create Google Cloud TTS adapter
    tts_adapter = GoogleCloudTTSAdapter()
    
    # Get host and port from environment if not provided
    if not host:
        host = os.environ.get("VOICE_SERVER_HOST", "localhost")
    if not port:
        port_str = os.environ.get("VOICE_SERVER_PORT", "8000")
        try:
            port = int(port_str)
        except ValueError:
            logger.warning(f"Invalid port {port_str}, using default 8000")
            port = 8000
    
    # Create and return server
    return VoiceServer(
        agent=agent,
        tts_adapter=tts_adapter,
        host=host,
        port=port
    )

def run_voice_server(agent: BaseAgent, host: Optional[str] = None, port: Optional[int] = None):
    """
    Create and run a voice server for the given agent.
    
    Args:
        agent: Google ADK agent to use
        host: Host to bind the server to (default: from env or localhost)
        port: Port to bind the server to (default: from env or 8000)
    """
    server = create_voice_server(agent, host, port)
    server.run()
