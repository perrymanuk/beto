"""
Home Assistant WebSocket Client for connecting to a Home Assistant instance.

This module provides a robust WebSocket client for connecting to a Home Assistant instance,
handling authentication, event subscription, and service calls via the WebSocket API.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK

logger = logging.getLogger(__name__)


class HomeAssistantWebsocketClient:
    """
    Manages a persistent WebSocket connection to Home Assistant,
    handles authentication, event subscription, and reconnection.
    """

    def __init__(
        self,
        url: str,
        token: str,
        event_callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]],
    ):
        """
        Initialize the WebSocket client.

        Args:
            url: The WebSocket URL of the Home Assistant instance (e.g., ws://<ip>:8123/api/websocket).
            token: A Long-Lived Access Token for Home Assistant.
            event_callback: An async function to call when a relevant event is received.
                           It will be called with the event data dictionary.
        """
        self.url = url
        self.token = token
        self.event_callback = event_callback
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._connection_task: Optional[asyncio.Task] = None
        self.message_id = 1
        self.subscriptions: Dict[str, int] = {}
        self._is_running = False
        self._shutdown_event = asyncio.Event()
        # Add a websocket lock to prevent concurrent access to the websocket
        self._ws_lock = asyncio.Lock()
        # Add a message queue for sending/receiving
        self._message_queue = asyncio.Queue()

    async def connect(self, auto_listen: bool = True):
        """
        Connect to Home Assistant and authenticate, but don't start listening yet.
        
        Args:
            auto_listen: Whether to automatically start the listener loop after connecting
            
        Returns:
            True if connection was successful, False otherwise
        """
        if self._is_running:
            logger.warning("Client is already running.")
            return True
        
        self._is_running = True
        self._shutdown_event.clear()
        
        # Create a connection established event for synchronization
        self._connection_established = asyncio.Event()
        
        # Direct connect without a background task
        try:
            logger.info("Connecting to Home Assistant WebSocket...")
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                self.url, ping_interval=20, ping_timeout=20, max_size=None
            )
            
            # Authenticate
            await self._authenticate()
            
            # Subscribe to state changes
            await self._subscribe_state_changes()
            
            # Mark connection as established
            self._connection_established.set()
            logger.info("Home Assistant WebSocket connection established successfully")
            
            # Optionally start listening for events
            if auto_listen:
                await self.start_listening()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Home Assistant: {e}", exc_info=True)
            
            # Clean up
            if self.websocket:
                try:
                    await self.websocket.close()
                except:
                    pass
                self.websocket = None
                
            return False
    
    async def start_listening(self):
        """Start the listener loop for events."""
        if not self.websocket:
            logger.error("Cannot start listener: WebSocket not connected")
            return False
            
        if self._listener_task and not self._listener_task.done():
            logger.warning("Listener already running")
            return True
            
        # Create the listener task
        self._listener_task = asyncio.create_task(self._listen(), name="HA_Listener")
        logger.info("Home Assistant WebSocket listener started")
        
        return True
    
    async def start(self):
        """
        Legacy method that connects and starts listening in one step.
        This maintains compatibility with existing code.
        """
        return await self.connect(auto_listen=True)

    async def stop(self):
        """Stop the client and close connections."""
        if not self._is_running:
            logger.warning("Client is not running.")
            return
            
        logger.info("Stopping Home Assistant WebSocket client...")
        self._is_running = False
        self._shutdown_event.set()  # Signal loops to stop

        # Cancel listener task if it exists
        if self._listener_task and not self._listener_task.done():
            try:
                self._listener_task.cancel()
                await asyncio.wait_for(asyncio.shield(self._listener_task), timeout=2)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            except Exception as e:
                logger.warning(f"Error cancelling listener task: {e}")

        # Close the websocket if it exists
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")

        self.websocket = None
        logger.info("Home Assistant WebSocket client stopped.")

    async def _send_message(self, message_dict: Dict[str, Any]) -> None:
        """
        Send a message to the WebSocket with proper synchronization.
        This is for one-way messages that don't expect a response.
        
        Args:
            message_dict: The message to send as a dictionary
            
        Raises:
            ConnectionError: If the WebSocket is not connected
        """
        if not self.websocket:
            raise ConnectionError("WebSocket not connected, cannot send message")
        
        message_str = json.dumps(message_dict)
        
        # Use the lock to ensure exclusive access to the websocket
        async with self._ws_lock:
            try:
                await self.websocket.send(message_str)
                logger.debug(f"Sent message: {message_str[:100]}...")
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                raise
                
    async def _request_response(self, request: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """
        Send a request and wait for the corresponding response.
        
        Args:
            request: The request message to send
            timeout: Maximum time to wait for the response
            
        Returns:
            The response message
            
        Raises:
            ConnectionError: If the WebSocket is not connected
            asyncio.TimeoutError: If no response is received within the timeout
            ValueError: If the response is not as expected
        """
        if "id" not in request:
            request["id"] = self.message_id
            self.message_id += 1
            
        request_id = request["id"]
        logger.debug(f"Starting request-response cycle for ID {request_id}")
        
        # We're not going to use the _send_message and _receive_message methods here
        # Because we need direct access to the websocket in one locked operation
        if not self.websocket:
            raise ConnectionError("WebSocket not connected, cannot send request")
            
        # Lock the entire request-response cycle to ensure message pairs stay together
        async with self._ws_lock:
            # Send the request directly
            try:
                message_str = json.dumps(request)
                await self.websocket.send(message_str)
                logger.debug(f"Sent request with ID {request_id}")
                
                # Use a single timeout for the entire operation
                end_time = asyncio.get_event_loop().time() + timeout
                
                # Maximum number of messages to process before giving up
                max_messages = 20  # Prevent infinite loops
                message_count = 0
                
                # Wait for response with matching ID
                while asyncio.get_event_loop().time() < end_time and message_count < max_messages:
                    message_count += 1
                    remaining = end_time - asyncio.get_event_loop().time()
                    
                    # Break if no time left
                    if remaining <= 0:
                        break
                        
                    try:
                        # Wait for a response with the time remaining
                        message_str = await asyncio.wait_for(self.websocket.recv(), timeout=remaining)
                        response = json.loads(message_str)
                        
                        # Check if this is our response
                        if response.get("id") == request_id and response.get("type") == "result":
                            logger.debug(f"Received response for ID {request_id}")
                            return response
                            
                        # Process other message types separately
                        elif response.get("type") == "event":
                            logger.debug(f"Received event during request {request_id}")
                            # Queue the event for processing but don't block
                            asyncio.create_task(self._process_event(response))
                        else:
                            logger.debug(f"Received other message type during request {request_id}: {response.get('type')}")
                    except asyncio.TimeoutError:
                        # We've reached the total timeout
                        logger.warning(f"Timeout waiting for response to request {request_id}")
                        raise
                    except json.JSONDecodeError as e:
                        logger.warning(f"Received invalid JSON: {e}")
                        continue
                
                # If we get here, we've either exceeded max_messages or the timeout
                if message_count >= max_messages:
                    logger.error(f"Processed {max_messages} messages without finding response for ID {request_id}")
                    raise ValueError(f"Failed to find response for request {request_id} after processing {max_messages} messages")
                else:
                    logger.error(f"Timed out waiting for response to request {request_id}")
                    raise asyncio.TimeoutError(f"Timed out waiting for response to request {request_id}")
                    
            except Exception as e:
                logger.error(f"Error in request-response cycle for ID {request_id}: {e}")
                raise
    
    async def _process_event(self, event_message: Dict[str, Any]) -> None:
        """Process an event message separately from request/response pairs"""
        try:
            if event_message.get("type") == "event" and event_message.get("event", {}).get("event_type") == "state_changed":
                await self.event_callback(event_message["event"]["data"])
        except Exception as e:
            logger.error(f"Error processing event: {e}")
                
    async def _authenticate(self):
        """Handle the authentication process."""
        try:
            # For authentication, we handle the special sequence separately
            # since it doesn't fit the normal request-response pattern
            
            # Wait for auth_required message
            message_str = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            auth_required = json.loads(message_str)
            logger.debug(f"Auth required message received: {message_str[:100]}...")
            
            if auth_required.get("type") != "auth_required":
                raise ValueError("Expected auth_required message first")

            # Send auth message
            auth_message = {"type": "auth", "access_token": self.token}
            await self.websocket.send(json.dumps(auth_message))
            logger.debug("Auth message sent.")

            # Wait for auth response
            message_str = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            auth_response = json.loads(message_str)
            logger.debug(f"Auth response received: {message_str[:100]}...")
            
            if auth_response.get("type") == "auth_ok":
                logger.info(f"Authentication successful. HA Version: {auth_response.get('ha_version')}")
                self.message_id = 1  # Reset message ID on successful auth
            else:
                msg = auth_response.get("message", "Unknown authentication error")
                logger.error(f"Authentication failed: {msg}")
                raise ConnectionRefusedError(f"Home Assistant authentication failed: {msg}")
                
        except asyncio.TimeoutError:
            logger.error("Timeout during authentication phase.")
            raise ConnectionRefusedError("Timeout during authentication")
        except Exception as e:
            logger.error(f"Error during authentication: {e}", exc_info=True)
            # Ensure connection is closed if auth fails critically
            if self.websocket:
                try:
                    await self.websocket.close()
                except:
                    pass  # Ignore errors during close
            raise ConnectionRefusedError(f"Error during authentication: {e}")

    async def _subscribe_state_changes(self):
        """Subscribe to state_changed events."""
        try:
            # Create the request
            request = {
                "id": self.message_id,
                "type": "subscribe_events",
                "event_type": "state_changed"
            }
            sub_id = request["id"]
            self.message_id += 1
            
            # Send request and wait for the response
            logger.info(f"Subscribing to state_changed events with ID {sub_id}")
            response = await self._request_response(request, timeout=10)
            
            if response and response.get("success", False):
                self.subscriptions["state_changed"] = sub_id
                logger.info("Successfully subscribed to state_changed events")
            else:
                error = response.get("error", {}).get("message", "Unknown error")
                logger.error(f"Failed to subscribe to state changes: {error}")
                raise Exception(f"Failed to subscribe to events: {error}")
                
        except Exception as e:
            logger.error(f"Failed to subscribe to state changes: {e}")
            raise

    async def get_all_states(self) -> List[Dict[str, Any]]:
        """
        Fetch all current states from Home Assistant.
        
        Returns:
            A list of all entity states
        
        Raises:
            ConnectionError: If the WebSocket is not connected
            Exception: If the query fails
        """
        # More robust connection check
        if not self.websocket:
            # If there's no websocket object but the connection task is running,
            # we might just need to wait a bit for the connection to establish
            if self._is_running and not self._shutdown_event.is_set() and self._connection_task and not self._connection_task.done():
                logger.warning("WebSocket connection still initializing, waiting up to 5 seconds...")
                try:
                    if hasattr(self, '_connection_established') and not self._connection_established.is_set():
                        # Wait up to 5 more seconds for connection to establish
                        await asyncio.wait_for(self._connection_established.wait(), timeout=5)
                    else:
                        # Just wait a bit hoping connection will establish
                        await asyncio.sleep(5)
                    
                    # Check again after waiting
                    if not self.websocket:
                        logger.error("WebSocket still not connected after waiting")
                        raise ConnectionError("WebSocket connection failed to establish after waiting")
                except asyncio.TimeoutError:
                    logger.error("Timed out waiting for WebSocket connection to become ready")
                    raise ConnectionError("Timed out waiting for WebSocket connection")
            else:
                logger.error("WebSocket not connected, cannot get states.")
                raise ConnectionError("WebSocket not connected")
        
        # Use the new request-response method
        try:
            logger.info("Fetching all entity states from Home Assistant...")
            
            # Create the request
            request = {
                "id": self.message_id,
                "type": "get_states"
            }
            self.message_id += 1
            
            # Send request and wait for response
            response = await self._request_response(request, timeout=15)
            
            # Check for successful response
            if not response.get("success", False):
                error = response.get("error", {}).get("message", "Unknown error")
                logger.error(f"Failed to get states: {error}")
                raise Exception(f"Failed to get states: {error}")
                
            result = response.get("result", [])
            logger.info(f"Successfully retrieved {len(result)} entity states")
            return result
            
        except Exception as e:
            logger.error(f"Error getting all states: {e}", exc_info=True)
            raise
            
    async def get_entity_registry(self) -> List[Dict[str, Any]]:
        """
        Fetch the entity registry from Home Assistant.
        
        Returns:
            A list of all entity registry entries
        
        Raises:
            ConnectionError: If the WebSocket is not connected
            Exception: If the query fails
        """
        if not self.websocket:
            logger.error("WebSocket not connected, cannot get entity registry.")
            raise ConnectionError("WebSocket not connected")
        
        # Use the new request-response method
        try:
            logger.info("Fetching entity registry from Home Assistant...")
            
            # Create the request
            request = {
                "id": self.message_id,
                "type": "config/entity_registry/list"
            }
            self.message_id += 1
            
            # Send request and wait for response (longer timeout for registry which can be large)
            response = await self._request_response(request, timeout=30)
            
            # Check for successful response
            if not response.get("success", False):
                error = response.get("error", {}).get("message", "Unknown error")
                logger.error(f"Failed to get entity registry: {error}")
                raise Exception(f"Failed to get entity registry: {error}")
            
            result = response.get("result", [])
            logger.info(f"Successfully retrieved {len(result)} entity registry entries")
            return result
            
        except Exception as e:
            logger.error(f"Error getting entity registry: {e}", exc_info=True)
            raise
            
    async def get_entity_registry_for_display(self) -> List[Dict[str, Any]]:
        """
        Fetch the entity registry from Home Assistant using the list_for_display command.
        This provides more comprehensive information about entities, including additional metadata.
        
        Returns:
            A list of all entity registry entries with enhanced display information
        
        Raises:
            ConnectionError: If the WebSocket is not connected
            Exception: If the query fails
        """
        if not self.websocket:
            logger.error("WebSocket not connected, cannot get entity registry for display.")
            raise ConnectionError("WebSocket not connected")
        
        try:
            logger.info("Fetching entity registry with display info from Home Assistant...")
            
            # Create the request
            request = {
                "id": self.message_id,
                "type": "config/entity_registry/list_for_display"
            }
            self.message_id += 1
            
            # Send request and wait for response (longer timeout for registry which can be large)
            response = await self._request_response(request, timeout=30)
            
            # Check for successful response
            if not response.get("success", False):
                error = response.get("error", {}).get("message", "Unknown error")
                logger.error(f"Failed to get entity registry for display: {error}")
                raise Exception(f"Failed to get entity registry for display: {error}")
            
            result = response.get("result", [])
            logger.info(f"Successfully retrieved {len(result)} entity registry display entries")
            return result
            
        except Exception as e:
            logger.error(f"Error getting entity registry for display: {e}", exc_info=True)
            raise

    async def get_device_registry(self) -> List[Dict[str, Any]]:
        """
        Fetch the device registry from Home Assistant.
        
        Returns:
            A list of all device registry entries
        
        Raises:
            ConnectionError: If the WebSocket is not connected
            Exception: If the query fails
        """
        if not self.websocket:
            logger.error("WebSocket not connected, cannot get device registry.")
            raise ConnectionError("WebSocket not connected")
        
        # Use the new request-response method
        try:
            logger.info("Fetching device registry from Home Assistant...")
            
            # Create the request
            request = {
                "id": self.message_id,
                "type": "config/device_registry/list"
            }
            self.message_id += 1
            
            # Send request and wait for response (longer timeout for registry which can be large)
            response = await self._request_response(request, timeout=30)
            
            # Check for successful response
            if not response.get("success", False):
                error = response.get("error", {}).get("message", "Unknown error")
                logger.error(f"Failed to get device registry: {error}")
                raise Exception(f"Failed to get device registry: {error}")
            
            result = response.get("result", [])
            logger.info(f"Successfully retrieved {len(result)} device registry entries")
            return result
            
        except Exception as e:
            logger.error(f"Error getting device registry: {e}", exc_info=True)
            raise

    async def _listen(self):
        """
        Listen for messages and process events.
        
        This task runs in the background to receive events and unsolicited messages.
        The request/response pairs are handled separately by _request_response.
        """
        if not self.websocket:
            logger.warning("Listener started but WebSocket is not connected.")
            return
            
        logger.info("Listener task started.")
        
        try:
            while self._is_running and not self._shutdown_event.is_set():
                try:
                    # We don't use the lock here because _receive_message uses it internally
                    # And _request_response will handle its own messages
                    # This is only for events and other unsolicited messages
                    
                    # Short timeout to allow checking for shutdown
                    message = None
                    try:
                        # Try to get a message without the lock first
                        # If there's an active request/response cycle, this will fail
                        # but that's ok - we'll just try again next loop
                        if not self._ws_lock.locked():
                            # Only try to receive if the lock is available
                            message_str = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                            message = json.loads(message_str)
                    except asyncio.TimeoutError:
                        # This is expected, just continue the loop
                        continue
                    except json.JSONDecodeError as e:
                        logger.warning(f"Received invalid JSON in listener: {e}")
                        continue
                    except Exception as e:
                        # This includes the ConcurrencyError when another coroutine
                        # is already receiving - that's expected and we ignore it
                        if "cannot call recv while another coroutine is already running recv" not in str(e):
                            logger.debug(f"Non-critical error in listener receive: {e}")
                        # Just continue the loop and try again
                        await asyncio.sleep(0.1)
                        continue
                    
                    # If we got a message, process it
                    if message:
                        msg_type = message.get("type")
                        msg_id = message.get("id")
                        
                        # Handle state_changed events
                        if (msg_type == "event" and 
                            message.get("event", {}).get("event_type") == "state_changed"):
                            entity_id = message.get("event", {}).get("data", {}).get("entity_id", "unknown")
                            logger.debug(f"Received state_changed event for {entity_id}")
                            await self.event_callback(message["event"]["data"])
                        elif msg_type == "result":
                            # Results are normally handled by _request_response, but just in case
                            logger.debug(f"Received unhandled result for ID {msg_id}")
                        elif msg_type == "pong":
                            logger.debug(f"Received pong for ping ID {msg_id}")
                        # Ignore auth messages handled elsewhere
                        elif msg_type not in ["auth_required", "auth_ok", "auth_invalid"]:
                            logger.debug(f"Received unhandled message type '{msg_type}'")
                
                except asyncio.CancelledError:
                    # Allow cancellation to propagate
                    raise
                except Exception as e:
                    logger.error(f"Error in listener loop: {e}", exc_info=True)
                    # Short delay to avoid tight loop on persistent errors
                    await asyncio.sleep(0.5)
        
        except asyncio.CancelledError:
            logger.info("Listener task cancelled.")
        except Exception as e:
            logger.error(f"Unhandled error in listener loop: {e}", exc_info=True)
        finally:
            logger.info("Listener task finished.")

    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: Optional[Dict[str, Any]] = None,
        entity_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call a service in Home Assistant.

        Args:
            domain: The domain of the service (e.g., 'light', 'switch')
            service: The service to call (e.g., 'turn_on', 'turn_off')
            service_data: Optional additional data for the service call
            entity_id: Optional entity ID to target with the service call

        Returns:
            Dict containing status information about the service call
        
        Raises:
            ConnectionError: If the WebSocket is not connected
            Exception: If the service call fails for any other reason
        """
        if not self.websocket:
            logger.error("WebSocket not connected, cannot call service.")
            raise ConnectionError("WebSocket not connected")

        # Prepare the payload
        call_id = self.message_id
        self.message_id += 1
        payload = {
            "id": call_id,
            "type": "call_service",
            "domain": domain,
            "service": service,
        }
        
        # Handle service data and entity_id
        current_service_data = service_data.copy() if service_data else {}
        if entity_id:
            current_service_data["entity_id"] = entity_id
        if current_service_data:
            payload["service_data"] = current_service_data

        try:
            # Use the synchronized send
            logger.info(f"Calling service {domain}.{service} for entity '{entity_id or 'N/A'}'")
            await self._send_message(payload)
            
            # We could wait for a response with _request_response, but for now
            # we'll maintain compatibility with the current implementation
            return {"status": "success", "call_id": call_id}
        except Exception as e:
            logger.error(f"Failed to call service {domain}.{service}: {e}", exc_info=True)
            raise