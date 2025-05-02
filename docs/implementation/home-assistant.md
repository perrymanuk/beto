Integrating a Google GenAI Agent with Home Assistant via WebSocket Event StreamingI. IntroductionA. Purpose and ScopeThis document outlines a comprehensive plan for integrating an AI agent, developed using the Google Generative AI SDK for Python (googleapis/python-genai) 1, with a Home Assistant instance. The primary objective is to enable the agent to receive real-time event updates from Home Assistant and, potentially, to control Home Assistant entities by calling services. This integration will leverage the Home Assistant WebSocket API for event streaming and the Google Agent SDK's Function Calling mechanism for interaction. The plan provides architectural details, implementation steps, code examples, and library recommendations suitable for execution by a mid-level software engineer.B. Target AudienceThis report is intended for software engineers familiar with Python, asynchronous programming (asyncio), and basic concepts of AI agents and APIs, but who may not have deep expertise in Home Assistant's specific APIs or the nuances of integrating real-time data streams with agent frameworks.C. Background and Problem StatementThe user query involves creating an AI agent capable of interacting with Home Assistant, specifically focusing on receiving events via the "mcp sse endpoint". Initial attempts using the beto repository were unsuccessful.3 Research indicates that while Home Assistant can act as a client to an external Model Context Protocol (MCP) server's Server-Sent Events (SSE) endpoint 4, this is not the standard mechanism for exporting Home Assistant's own events (like state changes) to external clients in real-time. SSE is generally a unidirectional protocol (server-to-client).5A more robust and suitable approach for bidirectional communication and real-time event subscription from Home Assistant is its WebSocket API.8 This API allows clients to subscribe to various event types, including state_changed events 8, and also provides a channel for the client (the AI agent) to send commands back to Home Assistant, such as calling services (e.g., turning lights on/off).8 Therefore, this plan focuses on utilizing the WebSocket API for a reliable and feature-rich integration.D. High-Level Solution OverviewThe proposed solution involves two main components running within the same Python application:
Home Assistant WebSocket Client: A persistent, asynchronous client that connects to the Home Assistant WebSocket API, handles authentication, subscribes to state_changed events, listens for incoming messages, manages reconnections robustly, and potentially exposes methods to call Home Assistant services.
Google GenAI Agent: The agent, built using the google-genai SDK, interacts with the user. It utilizes the SDK's Function Calling (Tool) capability 10 to interact with the Home Assistant WebSocket Client. Tools will be defined to allow the agent to query the current state of Home Assistant entities (retrieved via the WebSocket client's listener) and to trigger actions by calling Home Assistant services through the WebSocket client.
The WebSocket client runs as a background asyncio task, continuously listening for events and updating a shared state or queue accessible by the agent's tools.II. Analysis of Home Assistant APIs for Event StreamingA. Available APIs and ProtocolsHome Assistant offers several APIs for external interaction:
REST API: Provides endpoints for retrieving states, calling services, accessing logs, etc..12 However, obtaining real-time events typically requires polling, which is inefficient.
WebSocket API: Offers a persistent, bidirectional connection at /api/websocket.8 It allows clients to authenticate, subscribe to specific event types (like state_changed, call_service) 8, receive real-time updates, and send commands (like service calls) back to Home Assistant.8 This is the most suitable API for real-time event-driven integration.
MQTT Eventstream: An integration that publishes Home Assistant events to an MQTT broker and can subscribe to events from MQTT.13 This requires setting up and managing an MQTT broker.
Webhooks: Primarily used for receiving data into Home Assistant from external services or mobile apps 15, not ideal for streaming events out.
MCP Integration (Client Role): Home Assistant can act as a client connecting to an external MCP server's SSE endpoint to utilize its tools.4 This is the reverse of what is needed for this project. An external project exists (homeassistant-mcp) that acts as an MCP server bridging to Home Assistant and exposing an SSE endpoint 16, but this adds an extra layer and complexity compared to directly using the native WebSocket API.
B. Why WebSocket is PreferredThe WebSocket API 8 is the recommended choice for this integration due to:
Real-Time Events: It provides push-based notifications for events like state_changed as they happen, eliminating the need for inefficient polling required by the REST API.12
Bidirectional Communication: Unlike SSE which is primarily unidirectional 7, WebSockets allow the agent to both receive events and send commands (service calls) back to Home Assistant over the same connection.8
Efficiency: A single persistent connection is more efficient than repeated HTTP requests (polling) or managing separate connections for sending and receiving.18
Official Support & Documentation: The WebSocket API is a core, well-documented part of Home Assistant for developers.8
C. WebSocket API Specifics
Endpoint: /api/websocket appended to the Home Assistant base URL (e.g., ws://<HA_IP>:8123/api/websocket or wss://<HA_DOMAIN>/api/websocket).8
Authentication: Requires a Long-Lived Access Token.20 The client connects, receives an auth_required message, sends an auth message with the token, and receives auth_ok or auth_invalid.8
Event Subscription: Clients send subscribe_events commands, optionally specifying an event_type (e.g., state_changed).8 The server confirms with a result message and then sends event messages for matching events.8
Message Format: All messages are JSON objects with a type field. Commands and responses use an id field for correlation.8 state_changed events contain detailed data including entity_id, new_state, and old_state objects.8
Service Calls: Clients can send call_service commands specifying domain, service, and optional service_data (including entity_id).8
III. Analysis of Google Agent SDK (python-genai) Integration PointsA. Overview of the SDKThe google-genai Python SDK provides interfaces for interacting with Google's generative models (Gemini) via the Gemini Developer API or Vertex AI.1 It supports various functionalities including text generation, chat sessions, multimodal input, and function calling.1 The SDK primarily operates asynchronously (asyncio) for non-blocking operations.22B. Mechanisms for External InteractionThe primary mechanism for the agent (model) to interact with external systems or APIs is Function Calling, also referred to as using Tools.10
How it Works: Developers define functions (Tools) with specific names, descriptions, and parameter schemas.10 These definitions are provided to the model during the conversation setup or specific request.11 When the model determines, based on the conversation context and the tool descriptions, that calling a function would be beneficial to fulfill the user's request, it responds not with text, but with a FunctionCall object containing the name of the function to call and the arguments.10 The application code is responsible for executing the actual Python function corresponding to the FunctionCall, obtaining the result, and sending it back to the model as a FunctionResponse. The model then uses this result to generate a final textual response for the user.10
Relevance: This pattern fits perfectly for integrating with Home Assistant. The agent can decide when to get the state of a light or when to turn it on, invoking the appropriate tool. The underlying tool implementation will then interact with the persistent WebSocket client.
C. Handling Asynchronous Data StreamsThe python-genai SDK itself, including its live module for real-time interaction with the model 24, is designed for sending/receiving data to/from the Gemini model via WebSockets. It does not appear to offer a direct, built-in mechanism for consuming arbitrary external event streams (like the Home Assistant WebSocket) and proactively feeding them into the agent's context or decision-making process outside the Tool/Function Calling paradigm.Therefore, integrating the Home Assistant event stream requires a separate, persistent task to manage the WebSocket connection and listen for events. The agent interacts with the results of this stream (e.g., cached state) or triggers actions via this stream using the Function Calling mechanism. This separation keeps the agent logic focused on reasoning and interaction, while the dedicated client handles the specifics of the Home Assistant connection. Frameworks like Google's Agent Development Kit (ADK) build upon these concepts, offering more structured ways to define tools and orchestrate agents 25, but the core interaction pattern remains Tool-based.IV. Detailed Integration PlanThis plan outlines the steps to establish the connection, handle events, and integrate with the agent.A. Prerequisites and Setup
Home Assistant: A running Home Assistant instance accessible from where the agent will run.
Long-Lived Access Token: Generate a Long-Lived Access Token from the Home Assistant UI (User Profile page).20 Store this token securely.
Google API Key: Obtain a Google API key enabled for the Gemini API (e.g., via Google AI Studio).30 Store this key securely.
Python Environment: Set up a Python environment (version 3.9+ recommended 1) and install the necessary libraries (see Section V).
Configuration: Prepare configuration management (e.g., using environment variables or a config file) for the HA URL, HA Token, and Google API Key.
B. Step 1: Implementing the Robust Home Assistant WebSocket ClientThis involves creating a Python class using asyncio and the websockets library.
Library Choice: Use the websockets library 31 due to its maturity, asyncio support, and built-in features for handling pings/pongs and robust automatic reconnection.31 Alternatives like aiohttp 18 or websocket-client 19 exist, but websockets provides a convenient high-level API with reconnection logic suitable for this use case. Libraries like homeassistant-api 34 offer abstractions but might lack the desired async WebSocket support or reconnection robustness needed here.34 Building directly with websockets provides maximum control.
Client Class Structure: Define an async class (HomeAssistantWebsocketClient) to encapsulate the connection logic, state, and methods.

Initialization (__init__): Takes HA WebSocket URL, token, and an async callback function (to handle received events) as arguments. Initializes state variables (websocket connection object, message ID counter, task list, subscription tracking).
Connection (connect): The main method that establishes the connection using websockets.connect within an async for loop for automatic reconnection.31 Handles authentication and subscription upon successful connection. Manages listener tasks. Includes error handling and backoff delays.
Authentication (authenticate): Implements the auth flow: receive auth_required, send auth with token, check for auth_ok.8 Raises an error on failure.
Subscription (subscribe_state_changes): Sends the subscribe_events command for state_changed events, storing the subscription ID.8
Listener (listen): An async method that continuously iterates over incoming messages (async for message in self.websocket:). Parses JSON messages, identifies event types (specifically state_changed), and calls the provided event_callback with the relevant event data. Handles result messages and potential connection closure exceptions.8
Service Call (call_service): An async method to send call_service commands to Home Assistant.8 Takes domain, service, service_data, and entity_id as arguments.
Shutdown (close): Cancels running tasks and closes the WebSocket connection gracefully.


Core Implementation Snippet:
Pythonimport asyncio
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class HomeAssistantWebsocketClient:
    def __init__(self, url, token, event_callback):
        """
        Initializes the WebSocket client.

        Args:
            url (str): The WebSocket URL of the Home Assistant instance (e.g., ws://<ip>:8123/api/websocket).
            token (str): A Long-Lived Access Token for Home Assistant.
            event_callback (callable): An async function to call when a relevant event is received.
                                       It will be called with the event data dictionary.
        """
        self.url = url
        self.token = token
        self.event_callback = event_callback
        self.websocket = None
        self.tasks =
        self.message_id = 1
        self.subscriptions = {} # Store subscription IDs (e.g., {'state_changed': 1})

    async def connect(self):
        """Establishes connection, handles auth, subs, and listens. Reconnects on failure."""
        # Use websockets.connect with automatic reconnection support via async for loop
        # ping_interval and ping_timeout help detect dead connections
        async for websocket in websockets.connect(self.url, ping_interval=20, ping_timeout=20, max_size=None): # max_size=None for potentially large state dumps
            logging.info("Attempting to connect to Home Assistant WebSocket...")
            try:
                self.websocket = websocket
                await self.authenticate()
                await self.subscribe_state_changes()
                logging.info("Connection established and subscribed. Starting listener.")

                # Start listener task
                listener_task = asyncio.create_task(self.listen())
                self.tasks.append(listener_task)

                # Keep connection alive and handle tasks
                # This gather will run until the listener task finishes (e.g., due to connection close)
                await asyncio.gather(listener_task)

            except ConnectionClosed as e:
                logging.warning(f"WebSocket connection closed: {e}. Reconnecting in 5 seconds...")
            except ConnectionRefusedError as e:
                 logging.error(f"Authentication failed: {e}. Check URL and Token. Retrying in 60 seconds...")
                 await asyncio.sleep(60) # Longer delay if auth fails
            except Exception as e:
                logging.error(f"WebSocket error: {e}. Retrying in 15 seconds...", exc_info=True)
                await asyncio.sleep(15) # Longer backoff for unexpected errors
            finally:
                # Cleanup before retry/exit
                logging.info("Cleaning up tasks before reconnection attempt.")
                for task in self.tasks:
                    if not task.done():
                        task.cancel()
                self.tasks.clear()
                self.websocket = None # Ensure websocket is None if connection failed/closed
                if isinstance(e, ConnectionClosedOK): # Normal closure, maybe HA shutdown
                     logging.info("Connection closed normally (OK). Reconnecting...")
                await asyncio.sleep(5) # Wait before the next iteration of async for

    async def authenticate(self):
        """Handles the authentication process."""
        try:
            auth_required = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            logging.debug(f"Auth required message received: {auth_required}")
            auth_req_data = json.loads(auth_required)
            if auth_req_data.get("type")!= "auth_required":
                raise ValueError("Expected auth_required message first")

            await self.websocket.send(json.dumps({
                "type": "auth",
                "access_token": self.token
            }))
            logging.debug("Auth message sent.")

            auth_response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            auth_data = json.loads(auth_response)
            logging.debug(f"Auth response received: {auth_response}")

            if auth_data["type"] == "auth_ok":
                logging.info(f"Authentication successful. HA Version: {auth_data.get('ha_version')}")
            else:
                msg = auth_data.get('message', 'Unknown authentication error')
                logging.error(f"Authentication failed: {msg}")
                raise ConnectionRefusedError(f"Home Assistant authentication failed: {msg}")
        except asyncio.TimeoutError:
            logging.error("Timeout during authentication phase.")
            raise ConnectionRefusedError("Timeout during authentication")
        except Exception as e:
             logging.error(f"Error during authentication: {e}", exc_info=True)
             raise ConnectionRefusedError(f"Error during authentication: {e}")


    async def subscribe_state_changes(self):
        """Subscribes to state_changed events."""
        sub_id = self.message_id
        self.message_id += 1
        await self.websocket.send(json.dumps({
            "id": sub_id,
            "type": "subscribe_events",
            "event_type": "state_changed"
        }))
        self.subscriptions['state_changed'] = sub_id
        logging.info(f"Sent subscription request for state_changed events with ID {sub_id}")
        # We don't strictly need to wait for the result, but could add logic here
        # to await self.websocket.recv() and check for {"id": sub_id, "type": "result", "success": True}

    async def listen(self):
        """Listens for messages and calls the event callback."""
        if not self.websocket or not self.websocket.open:
             logging.warning("Listener started but WebSocket is not connected.")
             return # Exit if called when not connected

        logging.info("Listener task started.")
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    msg_id = data.get("id")
                    msg_type = data.get("type")

                    if msg_type == "event" and data.get("event", {}).get("event_type") == "state_changed":
                        if msg_id == self.subscriptions.get('state_changed'):
                            logging.debug(f"Received state_changed event: {data['event']['data'].get('entity_id')}")
                            # Pass relevant event data to the callback
                            await self.event_callback(data["event"]["data"])
                        else:
                            logging.warning(f"Received event for unexpected subscription ID: {msg_id}")
                    elif msg_type == "result":
                        logging.debug(f"Received result for ID {msg_id}: Success={data.get('success')}")
                        # Could add logic here to signal completion of commands based on ID
                    elif msg_type == "pong":
                        logging.debug(f"Received pong for ping ID {data.get('id')}")
                    elif msg_type in ["auth_required", "auth_ok", "auth_invalid"]:
                        # These should be handled during connect/authenticate, ignore here
                        pass
                    else:
                        logging.debug(f"Received unhandled message type '{msg_type}': {message[:200]}...") # Log snippet

                except json.JSONDecodeError:
                    logging.warning(f"Received non-JSON message: {message[:200]}...")
                except Exception as e:
                    logging.error(f"Error processing message: {e}", exc_info=True)

        except ConnectionClosed as e:
            logging.warning(f"Listener connection closed ({e.code} {e.reason}).")
        except asyncio.CancelledError:
             logging.info("Listener task cancelled.")
        except Exception as e:
            logging.error(f"Unhandled error in listener loop: {e}", exc_info=True)
        finally:
            logging.info("Listener task finished.")


    async def call_service(self, domain, service, service_data=None, entity_id=None):
        """Calls a service in Home Assistant."""
        if not self.websocket or not self.websocket.open:
            logging.error("WebSocket not connected, cannot call service.")
            # Optionally raise an exception or return an error status
            raise ConnectionError("WebSocket not connected")

        call_id = self.message_id
        self.message_id += 1
        payload = {
            "id": call_id,
            "type": "call_service",
            "domain": domain,
            "service": service,
        }
        # Ensure service_data exists if entity_id is provided
        if entity_id:
            if service_data is None:
                service_data = {}
            service_data["entity_id"] = entity_id

        if service_data:
            payload["service_data"] = service_data

        try:
            await self.websocket.send(json.dumps(payload))
            logging.info(f"Called service {domain}.{service} for entity '{entity_id or 'N/A'}' with call ID {call_id}")
            # Optionally, wait for and return the result message for this call_id
            # This would require more complex logic in the listener or a separate response handling mechanism
            return {"status": "success", "call_id": call_id}
        except Exception as e:
            logging.error(f"Failed to call service {domain}.{service}: {e}", exc_info=True)
            raise


    async def close(self):
        """Closes the WebSocket connection and cancels tasks."""
        logging.info("Closing WebSocket client...")
        for task in self.tasks:
             if not task.done():
                task.cancel()
        # Wait briefly for tasks to cancel
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

        if self.websocket and self.websocket.open:
            await self.websocket.close()
        self.websocket = None
        logging.info("WebSocket client closed.")

# --- Example Usage Placeholder ---
# async def handle_event_callback(event_data):
#     entity_id = event_data.get("entity_id")
#     new_state = event_data.get("new_state", {}).get("state")
#     logging.info(f"Callback received: {entity_id} is now {new_state}")
#     # Update shared state or put on queue here

# async def run_client():
#     HA_WS_URL = "ws://localhost:8123/api/websocket" # Replace with your URL
#     HA_TOKEN = "YOUR_LONG_LIVED_ACCESS_TOKEN" # Replace with your token
#     client = HomeAssistantWebsocketClient(HA_WS_URL, HA_TOKEN, handle_event_callback)
#     try:
#         await client.connect() # This runs the main connection/reconnection loop
#     except asyncio.CancelledError:
#         logging.info("Client run cancelled.")
#     finally:
#         await client.close()

# if __name__ == "__main__":
#     try:
#         asyncio.run(run_client())
#     except KeyboardInterrupt:
#         logging.info("Interrupted by user.")


Automatic Reconnection: The async for websocket in websockets.connect(...) pattern inherently handles reconnections with exponential backoff for transient errors.31 The try...except...finally block within the loop ensures cleanup and appropriate delays before retrying based on the error type (e.g., longer delay for authentication failure). Ping/pong frames (ping_interval, ping_timeout) help detect unresponsive connections faster than relying solely on TCP timeouts.36
Error Handling: The code includes try...except blocks for ConnectionClosed, ConnectionRefusedError (specifically for auth failures), general Exception, asyncio.TimeoutError during critical phases like authentication, and json.JSONDecodeError during message processing. Logging provides diagnostics.
C. Step 2: Integrating with the Google Agent SDKThe integration hinges on using the Function Calling/Tool mechanism of the Google Agent SDK.

Recommended Approach: Function Calling / Tools: This is the standard, model-agnostic way for Gemini agents to interact with external systems.10 The agent uses its reasoning capabilities to decide when to interact with Home Assistant based on the conversation and the descriptions provided for the tools. This decouples the agent's core logic from the specifics of the Home Assistant API. While Google's ADK 25 provides higher-level abstractions, this plan focuses on the base google-genai SDK as requested.


Defining the Home Assistant Tool: Define the tools using the google.genai.types structures. This involves specifying the function name, a clear description (crucial for the model to understand when to use it), and the expected parameters with their types and descriptions.10
Pythonfrom google.genai import types as genai_types

# Define the Tool for Home Assistant interactions
home_assistant_tool = genai_types.Tool(
    function_declarations=
            )
        ),
        genai_types.FunctionDeclaration(
            name="call_home_assistant_service",
            description="Executes a specific action in Home Assistant by calling a service. Use this to control devices (turn lights on/off, set thermostat temperature), activate scenes, or run scripts.",
            parameters=genai_types.Schema(
                type=genai_types.Type.OBJECT,
                properties={
                    "domain": genai_types.Schema(
                        type=genai_types.Type.STRING,
                        description="The category or domain of the service, e.g., 'light', 'switch', 'climate', 'scene', 'script'."
                    ),
                    "service": genai_types.Schema(
                        type=genai_types.Type.STRING,
                        description="The specific action to perform within the domain, e.g., 'turn_on', 'turn_off', 'set_temperature', 'activate', 'turn_on' (for scripts)."
                    ),
                    "entity_id": genai_types.Schema(
                        type=genai_types.Type.STRING,
                        description="Optional: The specific entity ID to target with the service call, e.g., 'light.living_room_lamp', 'climate.thermostat'. Not required for all services (like scene.activate)."
                    ),
                    "service_data": genai_types.Schema(
                        type=genai_types.Type.OBJECT,
                        description="Optional: A JSON object containing additional parameters for the service call, specific to the service being called. Examples: {'brightness_pct': 50} for light.turn_on, {'temperature': 22} for climate.set_temperature."
                    )
                },
                required=["domain", "service"]
            )
        ),
        # Potential future tool:
        # types.FunctionDeclaration(
        #     name="check_for_recent_ha_events",
        #     description="Checks if any significant Home Assistant events (like doors opening, motion detected) have occurred recently that the user might want to know about.",
        #     parameters=types.Schema(type=types.Type.OBJECT, properties={}) # No parameters needed initially
        # )
    ]
)



Implementing the Tool's Python Functions: Write the corresponding asynchronous Python functions. These functions need access to the running HomeAssistantWebsocketClient instance or the state it maintains. The WebSocket client runs persistently in the background. When the agent decides to use a tool, the SDK calls the associated Python function. This function should not create a new WebSocket connection; instead, it should interact with the existing one, either by reading cached data updated by the listener or by calling methods like ws_client.call_service.
Managing Access to the Client/State: A simple approach is to use global variables or a shared context object initialized in the main application scope. For more complex applications, dependency injection or a dedicated state management class might be preferable. The example below uses globals for simplicity. Ensure thread/async safety if the state is accessed concurrently (though asyncio tasks typically run on a single thread, care is needed if using run_in_executor). A simple dictionary is often sufficient for asyncio if access is properly awaited.
Pythonimport logging
import asyncio
from typing import Optional, Dict, Any

# --- Shared State and Client Instance ---
# These would be initialized in your main application setup
# Ensure current_ha_states is updated by the event_callback passed to HomeAssistantWebsocketClient
current_ha_states: Dict[str, Dict[str, Any]] = {}
ws_client_instance: Optional[HomeAssistantWebsocketClient] = None
# Lock for potentially modifying shared state if needed, though simple reads/writes
# in asyncio might be okay if structured carefully. For complex updates, use asyncio.Lock.
# state_lock = asyncio.Lock()

async def update_local_state_callback(event_data: Dict[str, Any]):
    """Callback function passed to HomeAssistantWebsocketClient."""
    entity_id = event_data.get("entity_id")
    new_state_obj = event_data.get("new_state")
    if entity_id and new_state_obj:
        # async with state_lock: # Use lock if complex modifications happen
        current_ha_states[entity_id] = new_state_obj # Store the whole state object
        logging.debug(f"Local state cache updated for {entity_id}: {new_state_obj.get('state')}")
    else:
         logging.debug(f"Received state_changed event without entity_id or new_state: {event_data}")


# --- Tool Implementation Functions ---

async def get_home_assistant_entity_state(entity_id: str) -> Dict[str, Any]:
    """Implementation of the 'get_home_assistant_entity_state' tool."""
    logging.info(f"Executing Tool: get_home_assistant_entity_state(entity_id='{entity_id}')")
    # async with state_lock: # Use lock if reading during complex modifications elsewhere
    state_obj = current_ha_states.get(entity_id)

    if state_obj:
        logging.info(f"Found state for '{entity_id}' in cache.")
        # Return a serializable dictionary representing the state
        return {
            "status": "success",
            "entity_id": entity_id,
            "state": state_obj.get("state"),
            "attributes": state_obj.get("attributes", {}),
            "last_changed": state_obj.get("last_changed"),
        }
    else:
        logging.warning(f"State for '{entity_id}' not found in local cache.")
        # Optionally: Implement a direct query via WebSocket if state isn't cached?
        # This adds complexity (managing request IDs and responses).
        # For now, rely on the cache populated by the listener.
        return {
            "status": "error",
            "message": f"Information for entity '{entity_id}' is not currently available. It might be an invalid entity ID or hasn't reported its state recently."
        }

async def call_home_assistant_service(domain: str, service: str, entity_id: Optional[str] = None, service_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Implementation of the 'call_home_assistant_service' tool."""
    logging.info(f"Executing Tool: call_home_assistant_service(domain='{domain}', service='{service}', entity_id='{entity_id}', service_data={service_data})")
    if ws_client_instance:
        try:
            # Delegate the call to the running WebSocket client instance
            result = await ws_client_instance.call_service(domain, service, service_data, entity_id)
            logging.info(f"Service call {domain}.{service} successful (Call ID: {result.get('call_id')}).")
            return {"status": "success", "message": f"Successfully requested action {domain}.{service}."}
        except ConnectionError as e:
             logging.error(f"Service call failed: WebSocket not connected. {e}")
             return {"status": "error", "message": "Unable to send command: Not connected to Home Assistant."}
        except Exception as e:
            logging.error(f"Error calling service {domain}.{service}: {e}", exc_info=True)
            return {"status": "error", "message": f"An error occurred while trying to perform the action: {e}"}
    else:
        logging.error("Service call failed: Home Assistant client instance is not available.")
        return {"status": "error", "message": "Home Assistant connection is not active."}

# --- Mapping for the SDK ---
# The SDK needs a way to map function names from the FunctionCall response
# to the actual Python functions to execute.
tool_function_map = {
    "get_home_assistant_entity_state": get_home_assistant_entity_state,
    "call_home_assistant_service": call_home_assistant_service,
}



Agent Interaction Flow: The core loop involves sending user input to the agent, checking the response for a FunctionCall, executing the mapped Python function if needed, sending the result back as a FunctionResponse, and finally getting the agent's textual reply.

Initialize the genai.Client.1
Start a chat session or use generate_content, providing the tools=[home_assistant_tool] configuration.11
Process the response: Check if response.candidates.content.parts is a FunctionCall.
If it is, extract name and args. Look up the function in tool_function_map and await its execution with the provided arguments.
Construct a FunctionResponse part containing the function's return value and send it back to the model in the next turn.10
The model will then generate a text response based on the function result.

(See Section VI.C for a more complete code example of this flow).

D. Step 3: Managing the Persistent WebSocket ListenerThe HomeAssistantWebsocketClient needs to run continuously in the background to listen for events.
Background Task: The ws_client.connect() coroutine, containing the main connection and listening loop, must be launched as a background task using asyncio.create_task() when the main agent application starts.37 This allows the main agent loop (handling user interaction and SDK calls) to run concurrently.
Python# In your main async function where the agent is run:
global ws_client_instance, current_ha_states
current_ha_states = {} # Initialize shared state store

HA_WS_URL = "ws://YOUR_HA_IP:8123/api/websocket" # Load from config
HA_TOKEN = "YOUR_HA_TOKEN"                     # Load from config

# Create the client instance, passing the callback to update shared state
ws_client_instance = HomeAssistantWebsocketClient(HA_WS_URL, HA_TOKEN, update_local_state_callback)

logging.info("Starting Home Assistant WebSocket client as a background task...")
# Start the connect() method, which contains the persistent loop
ha_client_task = asyncio.create_task(ws_client_instance.connect(), name="HomeAssistantClient")

# Now proceed with agent initialization and the main interaction loop...
#... agent = initialize_agent(...)...
#... run_agent_interaction_loop(agent)...

# Ensure graceful shutdown in a finally block or shutdown handler
# await ws_client_instance.close()
# ha_client_task.cancel()
# await ha_client_task


Lifecycle Management: Implement proper startup and shutdown logic. The ha_client_task should be started after configuration is loaded but before the agent starts interacting. A finally block or signal handler in the main application should call ws_client.close() (which cancels internal tasks and closes the socket) and then ha_client_task.cancel() to ensure the background task is terminated cleanly upon application exit. Awaiting the cancelled task handles any cleanup exceptions.37
Sharing the Client Instance/State: Ensure the agent's tool functions can access the ws_client_instance (to call services) or the current_ha_states dictionary (to get current state). Using global variables (as shown) is simple for smaller applications; dependency injection or context variables might be better for larger systems.
E. Step 4: Handling and Utilizing Home Assistant EventsThe event_callback function passed to the HomeAssistantWebsocketClient is the entry point for incoming HA events.
Parsing Events: The callback receives the data dictionary from state_changed events.8 It should extract entity_id, new_state (which is an object containing state, attributes, last_changed, etc.), and potentially old_state.
Updating Agent State: The primary strategy is using a shared state dictionary (current_ha_states in the examples) mapped by entity_id. The event_callback updates this dictionary with the latest new_state object whenever a state_changed event arrives. This makes the most recent state available to the get_home_assistant_entity_state tool almost instantly.

Alternative: For events requiring immediate agent action (e.g., "notify me when the door opens"), the callback could put the event details onto an asyncio.Queue. A separate agent tool or a dedicated agent task could then monitor this queue. This adds complexity but enables more proactive behavior. Starting with the shared state cache is recommended.


Agent Logic for Reacting to Events: The agent doesn't automatically know or react to state changes. The integration enables awareness and control.

Reactive (Agent Pull): The most common pattern. The user asks a question ("Is the light on?"), the agent decides to use the get_home_assistant_entity_state tool, the tool function reads the latest value from the current_ha_states cache (which was updated by the background listener), and the agent formulates the answer.10
Proactive (Listener Push - Advanced): Requires more complex design. Example: User asks "Tell me if the temperature goes above 25°C".

Agent could use a hypothetical set_alert_threshold tool.
The event_callback, upon receiving a temperature sensor update, checks against registered thresholds.
If a threshold is crossed, the callback puts a notification message onto an asyncio.Queue.
The agent needs a mechanism (e.g., another tool called periodically, or a dedicated monitoring task) to check this queue and deliver the notification to the user. This moves beyond simple state retrieval and requires careful design of the agent's internal processing loop or toolset.




V. Required Libraries and EnvironmentA. Python VersionA Python version of 3.9 or higher is recommended to ensure compatibility with the google-generativeai SDK and modern asyncio features.1 Home Assistant itself often uses recent Python versions.38B. Key Python LibrariesThe following table lists the essential Python libraries for this integration:Library NameRecommended VersionPurposeLink (PyPI)google-generativeai>=0.7.0 (Latest)Core Google Agent SDK for Gemini API interaction and Function Callinghttps://pypi.org/project/google-generativeai/websockets>=12.0 (Latest)Robust asynchronous WebSocket client library with reconnection featureshttps://pypi.org/project/websockets/python-dotenv(Optional) LatestFor loading environment variables from a .env filehttps://pypi.org/project/python-dotenv/Note: Check PyPI for the absolute latest stable versions before installation.C. Environment VariablesThe application will require the following environment variables to be set:
GOOGLE_API_KEY: Your API key for the Google Gemini API.1
HOME_ASSISTANT_URL: The WebSocket URL for your Home Assistant instance (e.g., ws://192.168.1.100:8123/api/websocket or wss://your.domain.com/api/websocket).
HOME_ASSISTANT_TOKEN: Your Home Assistant Long-Lived Access Token.20
(Optional) GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION: If using the Vertex AI backend instead of the Gemini Developer API.1
D. Example requirements.txtgoogle-generativeai>=0.7.0websockets>=12.0python-dotenv>=1.0.0 # Uncomment if using.env filesVI. Code Recipes and ExamplesThis section provides more complete code examples building on the snippets from Section IV.A. Complete WebSocket Client Class (ha_websocket_client.py)Python# ha_websocket_client.py
import asyncio
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
from typing import Callable, Coroutine, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HomeAssistantWebsocketClient:
    """
    Manages a persistent WebSocket connection to Home Assistant,
    handles authentication, event subscription, and reconnection.
    """
    def __init__(self, url: str, token: str, event_callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]):
        self.url = url
        self.token = token
        self.event_callback = event_callback
        self.websocket: Optional = None
        self._listener_task: Optional = None
        self._connection_task: Optional = None # Task managing the connect loop
        self.message_id = 1
        self.subscriptions: Dict[str, int] = {}
        self._is_running = False
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """Starts the connection and listener loop."""
        if self._is_running:
            logger.warning("Client is already running.")
            return
        self._is_running = True
        self._shutdown_event.clear()
        # Run the connection management loop as the main task for this instance
        self._connection_task = asyncio.create_task(self._connection_loop(), name="HA_ConnectionLoop")
        logger.info("Home Assistant WebSocket client started.")

    async def stop(self):
        """Stops the client and closes connections."""
        if not self._is_running:
            logger.warning("Client is not running.")
            return
        logger.info("Stopping Home Assistant WebSocket client...")
        self._is_running = False
        self._shutdown_event.set() # Signal loops to stop

        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()

        if self.websocket and self.websocket.open:
            await self.websocket.close()

        if self._connection_task and not self._connection_task.done():
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                logger.debug("Connection loop task cancelled successfully.")

        self.websocket = None
        logger.info("Home Assistant WebSocket client stopped.")

    async def _connection_loop(self):
        """Internal loop managing connection and reconnection."""
        while self._is_running and not self._shutdown_event.is_set():
            try:
                # Use websockets.connect with automatic reconnection support via async for loop
                async for websocket in websockets.connect(self.url, ping_interval=20, ping_timeout=20, max_size=None):
                    if not self._is_running or self._shutdown_event.is_set(): break # Exit if stopped during connect

                    logger.info("Attempting to connect to Home Assistant WebSocket...")
                    try:
                        self.websocket = websocket
                        await self._authenticate()
                        await self._subscribe_state_changes()
                        logger.info("Connection established and subscribed. Starting listener.")

                        self._listener_task = asyncio.create_task(self._listen(), name="HA_Listener")

                        # Wait for listener to finish (due to disconnect) or shutdown signal
                        done, pending = await asyncio.wait(
                            [self._listener_task, asyncio.create_task(self._shutdown_event.wait())],
                            return_when=asyncio.FIRST_COMPLETED
                        )

                        # If shutdown was triggered, cancel the listener
                        if self._shutdown_event.is_set():
                            logger.info("Shutdown signal received, cancelling listener.")
                            if not self._listener_task.done():
                                self._listener_task.cancel()
                            break # Exit connection loop

                        # Otherwise, listener finished (likely disconnect), loop will reconnect

                    except ConnectionClosed as e:
                        logger.warning(f"WebSocket connection closed: {e}. Reconnecting...")
                    except ConnectionRefusedError as e:
                         logger.error(f"Authentication failed: {e}. Check URL/Token. Retrying...")
                         await asyncio.sleep(60) # Longer delay for auth failure
                    except Exception as e:
                        logger.error(f"WebSocket error in connection phase: {e}. Retrying...", exc_info=True)
                        await asyncio.sleep(15)
                    finally:
                        # Ensure listener task is cancelled if it's still pending after an error
                        if self._listener_task and not self._listener_task.done():
                            self._listener_task.cancel()
                        self.websocket = None # Reset websocket state
                        # Short delay before library handles reconnect via async for
                        await asyncio.sleep(5)

            except Exception as e:
                 # Catch errors during websockets.connect() itself
                 logger.error(f"Failed to establish initial connection: {e}. Retrying...", exc_info=True)
                 await asyncio.sleep(30)

            if not self._is_running: break # Check running state again before looping

        logger.info("Connection loop finished.")


    async def _authenticate(self):
        """Handles the authentication process."""
        # Implementation similar to Section IV.B.3 (ensure timeouts and error handling)
        try:
            auth_required = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            logger.debug(f"Auth required message received: {auth_required}")
            auth_req_data = json.loads(auth_required)
            if auth_req_data.get("type")!= "auth_required":
                raise ValueError("Expected auth_required message first")

            await self.websocket.send(json.dumps({
                "type": "auth",
                "access_token": self.token
            }))
            logger.debug("Auth message sent.")

            auth_response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            auth_data = json.loads(auth_response)
            logger.debug(f"Auth response received: {auth_response}")

            if auth_data["type"] == "auth_ok":
                logger.info(f"Authentication successful. HA Version: {auth_data.get('ha_version')}")
                self.message_id = 1 # Reset message ID on successful auth
            else:
                msg = auth_data.get('message', 'Unknown authentication error')
                logger.error(f"Authentication failed: {msg}")
                raise ConnectionRefusedError(f"Home Assistant authentication failed: {msg}")
        except asyncio.TimeoutError:
            logger.error("Timeout during authentication phase.")
            raise ConnectionRefusedError("Timeout during authentication")
        except Exception as e:
             logger.error(f"Error during authentication: {e}", exc_info=True)
             # Ensure connection is closed if auth fails critically
             if self.websocket and self.websocket.open: await self.websocket.close()
             raise ConnectionRefusedError(f"Error during authentication: {e}")


    async def _subscribe_state_changes(self):
        """Subscribes to state_changed events."""
        # Implementation similar to Section IV.B.3
        sub_id = self.message_id
        self.message_id += 1
        await self.websocket.send(json.dumps({
            "id": sub_id,
            "type": "subscribe_events",
            "event_type": "state_changed"
        }))
        self.subscriptions['state_changed'] = sub_id
        logger.info(f"Sent subscription request for state_changed events with ID {sub_id}")


    async def _listen(self):
        """Listens for messages and calls the event callback."""
        # Implementation similar to Section IV.B.3 (ensure robust parsing and callback invocation)
        if not self.websocket or not self.websocket.open:
             logger.warning("Listener started but WebSocket is not connected.")
             return

        logger.info("Listener task started.")
        try:
            async for message in self.websocket:
                if not self._is_running or self._shutdown_event.is_set(): break # Exit if stopped

                try:
                    data = json.loads(message)
                    msg_id = data.get("id")
                    msg_type = data.get("type")

                    if msg_type == "event" and data.get("event", {}).get("event_type") == "state_changed":
                        if msg_id == self.subscriptions.get('state_changed'):
                            await self.event_callback(data["event"]["data"])
                        # else: ignore events for other subscriptions if any
                    elif msg_type == "result":
                        logger.debug(f"Received result for ID {msg_id}: Success={data.get('success')}, Result={data.get('result')}")
                    elif msg_type == "pong":
                        logger.debug(f"Received pong for ping ID {data.get('id')}")
                    # Ignore auth messages handled elsewhere
                    elif msg_type not in ["auth_required", "auth_ok", "auth_invalid"]:
                        logger.debug(f"Received unhandled message type '{msg_type}'")

                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON message: {message[:200]}...")
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)

        except ConnectionClosed as e:
            logger.warning(f"Listener connection closed ({e.code} {e.reason}).")
        except asyncio.CancelledError:
             logger.info("Listener task cancelled.")
        except Exception as e:
            logger.error(f"Unhandled error in listener loop: {e}", exc_info=True)
        finally:
            logger.info("Listener task finished.")

    async def call_service(self, domain: str, service: str, service_data: Optional[Dict[str, Any]] = None, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """Calls a service in Home Assistant."""
        # Implementation similar to Section IV.B.3 (check connection, raise errors)
        if not self.websocket or not self.websocket.open:
            logger.error("WebSocket not connected, cannot call service.")
            raise ConnectionError("WebSocket not connected")

        call_id = self.message_id
        self.message_id += 1
        payload = {
            "id": call_id,
            "type": "call_service",
            "domain": domain,
            "service": service,
        }
        current_service_data = service_data.copy() if service_data else {}
        if entity_id:
            current_service_data["entity_id"] = entity_id
        if current_service_data:
            payload["service_data"] = current_service_data

        try:
            await self.websocket.send(json.dumps(payload))
            logger.info(f"Called service {domain}.{service} for entity '{entity_id or 'N/A'}' with call ID {call_id}")
            # Note: This implementation doesn't wait for the result confirmation.
            # Waiting would require matching the result ID in the listener.
            return {"status": "success", "call_id": call_id}
        except Exception as e:
            logger.error(f"Failed to call service {domain}.{service}: {e}", exc_info=True)
            raise
B. Google Agent SDK Tool Implementation (agent_tools.py)Python# agent_tools.py
import logging
from google.genai import types as genai_types
from typing import Optional, Dict, Any
# Assume ha_websocket_client.py containing HomeAssistantWebsocketClient is available
# Assume ws_client_instance and current_ha_states are managed globally or via context
from ha_websocket_client import HomeAssistantWebsocketClient # Import the client class

logger = logging.getLogger(__name__)

# --- Shared State and Client Instance Reference ---
# These should be managed/passed by the main application logic
current_ha_states: Dict[str, Dict[str, Any]] = {}
ws_client_instance: Optional[HomeAssistantWebsocketClient] = None

# --- Tool Definition ---
home_assistant_tool = genai_types.Tool(
    function_declarations=
            )
        ),
        genai_types.FunctionDeclaration(
            name="call_home_assistant_service",
            description="Executes a specific action in Home Assistant by calling a service. Use this to control devices (turn lights on/off, set thermostat temperature), activate scenes, or run scripts.",
            parameters=genai_types.Schema(
                type=genai_types.Type.OBJECT,
                properties={
                    "domain": genai_types.Schema(
                        type=genai_types.Type.STRING,
                        description="The category or domain of the service, e.g., 'light', 'switch', 'climate', 'scene', 'script'."
                    ),
                    "service": genai_types.Schema(
                        type=genai_types.Type.STRING,
                        description="The specific action to perform within the domain, e.g., 'turn_on', 'turn_off', 'set_temperature', 'activate', 'turn_on' (for scripts)."
                    ),
                    "entity_id": genai_types.Schema(
                        type=genai_types.Type.STRING,
                        description="Optional: The specific entity ID to target with the service call, e.g., 'light.living_room_lamp', 'climate.thermostat'. Not required for all services (like scene.activate)."
                    ),
                    "service_data": genai_types.Schema(
                        type=genai_types.Type.OBJECT,
                        description="Optional: A JSON object containing additional parameters for the service call, specific to the service being called. Examples: {'brightness_pct': 50} for light.turn_on, {'temperature': 22} for climate.set_temperature."
                    )
                },
                required=["domain", "service"]
            )
        ),
    ]
)

# --- Tool Implementation Functions ---
async def get_home_assistant_entity_state(entity_id: str) -> Dict[str, Any]:
    """Implementation of the 'get_home_assistant_entity_state' tool."""
    logger.info(f"Executing Tool: get_home_assistant_entity_state(entity_id='{entity_id}')")
    state_obj = current_ha_states.get(entity_id) # Read from shared state cache

    if state_obj:
        logger.info(f"Found state for '{entity_id}' in cache: {state_obj.get('state')}")
        # Return a serializable dictionary
        return {
            "status": "success",
            "entity_id": entity_id,
            "state": state_obj.get("state"),
            "attributes": state_obj.get("attributes", {}),
            "last_changed": state_obj.get("last_changed"),
        }
    else:
        logger.warning(f"State for '{entity_id}' not found in local cache.")
        return {
            "status": "error",
            "message": f"Information for entity '{entity_id}' is not currently available."
        }

async def call_home_assistant_service(domain: str, service: str, entity_id: Optional[str] = None, service_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Implementation of the 'call_home_assistant_service' tool."""
    logger.info(f"Executing Tool: call_home_assistant_service(domain='{domain}', service='{service}', entity_id='{entity_id}', service_data={service_data})")
    if ws_client_instance:
        try:
            result = await ws_client_instance.call_service(domain, service, service_data, entity_id)
            logger.info(f"Service call {domain}.{service} successful.")
            # Return simple success message; result details aren't typically needed by the LLM
            return {"status": "success", "message": f"Successfully requested action {domain}.{service}."}
        except ConnectionError as e:
             logger.error(f"Service call failed: WebSocket not connected. {e}")
             return {"status": "error", "message": "Unable to send command: Not connected to Home Assistant."}
        except Exception as e:
            logger.error(f"Error calling service {domain}.{service}: {e}", exc_info=True)
            return {"status": "error", "message": f"An error occurred: {e}"}
    else:
        logger.error("Service call failed: Home Assistant client instance is not available.")
        return {"status": "error", "message": "Home Assistant connection is not active."}

# --- Mapping for SDK ---
tool_function_map = {
    "get_home_assistant_entity_state": get_home_assistant_entity_state,
    "call_home_assistant_service": call_home_assistant_service,
}

# --- Callback for updating shared state ---
async def update_local_state_callback(event_data: Dict[str, Any]):
    """Callback function passed to HomeAssistantWebsocketClient to update the cache."""
    entity_id = event_data.get("entity_id")
    new_state_obj = event_data.get("new_state")
    if entity_id and new_state_obj:
        current_ha_states[entity_id] = new_state_obj # Update cache
        logger.debug(f"Local state cache updated for {entity_id}: {new_state_obj.get('state')}")

C. Agent Interaction Flow Example (main_agent.py)Python# main_agent.py
import asyncio
import os
import logging
from dotenv import load_dotenv
from google import generativeai as genai
from google.generativeai import types as genai_types
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Import local modules
from ha_websocket_client import HomeAssistantWebsocketClient
import agent_tools # This imports the tools and sets up the global references

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HA_WS_URL = os.getenv("HOME_ASSISTANT_URL")
HA_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN")

# --- Main Application Logic ---
async def run_agent_interaction():
    """Initializes clients and runs the main agent interaction loop."""
    if not all():
        logger.error("Missing required environment variables (GOOGLE_API_KEY, HOME_ASSISTANT_URL, HOME_ASSISTANT_TOKEN)")
        return

    # Configure Google AI Client
    genai.configure(api_key=GOOGLE_API_KEY)

    # Initialize and start the Home Assistant WebSocket client in the background
    logger.info("Initializing Home Assistant WebSocket client...")
    # Assign the global instance and state cache defined in agent_tools
    agent_tools.current_ha_states = {}
    ha_client = HomeAssistantWebsocketClient(HA_WS_URL, HA_TOKEN, agent_tools.update_local_state_callback)
    agent_tools.ws_client_instance = ha_client
    await ha_client.start() # Start the connection loop

    # Give the client a moment to connect and authenticate
    await asyncio.sleep(5)

    # Setup the Generative Model with the Home Assistant tool
    # Use a model that supports function calling, like gemini-1.5-flash or newer
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", # Or another suitable model
        tools=[agent_tools.home_assistant_tool],
         # Adjust safety settings if needed, e.g., for less filtering on HA entity names/states
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    )
    chat = model.start_chat(enable_automatic_function_calling=False) # Manual function calling control

    print("\nAgent initialized. Type 'quit' to exit.")
    print("Example prompts:")
    print("- Is the light.living_room_lamp on?")
    print("- Turn on switch.coffee_machine")
    print("- What's the state of sensor.office_temperature?")

    try:
        while True:
            user_input = await asyncio.to_thread(input, "\nYou: ")
            if user_input.lower() == 'quit':
                break

            if not user_input:
                continue

            print("Agent thinking...", end="", flush=True)
            try:
                # Send message to the model
                response = await chat.send_message_async(user_input)
                print("\r" + " " * 15 + "\r", end="") # Clear "Agent thinking..."

                # Check for function calls
                while response.candidates.content.parts.function_call.name:
                    function_call = response.candidates.content.parts.function_call
                    fn_name = function_call.name
                    fn_args = function_call.args

                    if fn_name in agent_tools.tool_function_map:
                        print(f"Agent wants to call: {fn_name}({fn_args})")
                        # Execute the corresponding Python function
                        function_to_call = agent_tools.tool_function_map[fn_name]

                        # Convert args from FunctionCall object to dict if necessary
                        args_dict = {key: value for key, value in fn_args.items()}

                        print("Executing tool...", end="", flush=True)
                        function_response_data = await function_to_call(**args_dict)
                        print("\r" + " " * 17 + "\r", end="") # Clear "Executing tool..."
                        print(f"Tool response: {function_response_data}")

                        # Send the function response back to the model
                        print("Sending tool response to agent...", end="", flush=True)
                        response = await chat.send_message_async(
                            genai_types.FunctionResponse(name=fn_name, response=function_response_data)
                        )
                        print("\r" + " " * 31 + "\r", end="") # Clear message
                    else:
                        print(f"\nError: Agent requested unknown function '{fn_name}'")
                        # Send back an error response
                        response = await chat.send_message_async(
                             genai_types.FunctionResponse(name=fn_name, response={"status": "error", "message": f"Unknown function '{fn_name}' requested."})
                        )

                # Print the final text response from the agent
                if response.candidates.content.parts.text:
                     print(f"Agent: {response.candidates.text}")
                else:
                     # Handle cases where no text response is generated after function call
                     print("Agent: (Completed action, no further text response)")


            except Exception as e:
                logger.error(f"Error during agent interaction: {e}", exc_info=True)
                print(f"\nAn error occurred: {e}")

    finally:
        logger.info("Shutting down...")
        await ha_client.stop()
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(run_agent_interaction())
    except KeyboardInterrupt:
        print("\nExiting...")

D. Event Handling Callback Example (agent_tools.py)This example focuses on updating the shared state dictionary.Python# In agent_tools.py (or wherever the callback is defined)
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Assume current_ha_states is the shared dictionary
# current_ha_states: Dict[str, Dict[str, Any]] = {} # Managed by main app

async def update_local_state_callback(event_data: Dict[str, Any]):
    """
    Callback function passed to HomeAssistantWebsocketClient.
    Parses state_changed events and updates the shared state cache.
    """
    try:
        entity_id = event_data.get("entity_id")
        new_state_obj = event_data.get("new_state")

        if entity_id and new_state_obj and isinstance(new_state_obj, dict):
            # Store the entire new_state object, which includes state, attributes, last_changed, etc.
            # This makes more information available to the tool if needed.
            current_ha_states[entity_id] = new_state_obj
            state = new_state_obj.get('state')
            logger.debug(f"State cache updated via event: {entity_id} -> {state}")
        elif entity_id and new_state_obj is None:
             # Handle entity removal event
             if entity_id in current_ha_states:
                 del current_ha_states[entity_id]
                 logger.debug(f"Entity removed from cache via event: {entity_id}")
        else:
            logger.debug(f"Ignoring state_changed event with missing data: {event_data}")

    except Exception as e:
        logger.error(f"Error in event callback processing event data {event_data}: {e}", exc_info=True)

VII. Conclusion and Next StepsA. Summary of Recommended SolutionThe recommended approach integrates a Google GenAI agent with Home Assistant by establishing a persistent, robust WebSocket connection using the websockets library in a background asyncio task. This client listens for state_changed events and maintains a local cache of entity states. The agent, built with the google-genai SDK, utilizes its Function Calling (Tool) capability to interact with Home Assistant. Defined tools allow the agent to query the cached entity states or call Home Assistant services via the background WebSocket client, enabling both monitoring and control.B. Key BenefitsThis architecture offers several advantages:
Real-time Awareness: Leverages Home Assistant's native WebSocket API for immediate event updates 8, avoiding inefficient polling.
Robust Connectivity: Employs the websockets library's features for automatic reconnection and connection health monitoring.31
Standard Agent Integration: Uses the idiomatic Function Calling pattern for agent-tool interaction within the Google GenAI ecosystem.10
Bidirectional Control: Enables the agent not only to query state but also to actively control Home Assistant devices and services.8
Separation of Concerns: Isolates the complexities of WebSocket management and Home Assistant protocol details from the core agent logic.
C. Considerations and Potential Enhancements
State Consistency: The local state cache (current_ha_states) reflects the state received via events. There might be edge cases or initial connection scenarios where the cache is incomplete or slightly delayed compared to Home Assistant's actual state. Implementing a mechanism to fetch the full state on initial connection could mitigate this.
Error Handling Granularity: The provided error handling is functional but could be enhanced. For instance, call_service could wait for and parse the result message from Home Assistant to confirm successful execution, providing more detailed feedback to the agent.
Scalability: For extremely large Home Assistant instances with thousands of entities generating rapid events, the single listener task and simple dictionary cache might become a bottleneck. This is unlikely in typical home environments but could be addressed with more sophisticated event queuing and processing if needed.
Security: Secure storage and handling of the HOME_ASSISTANT_TOKEN and GOOGLE_API_KEY are paramount. Avoid hardcoding credentials.
Advanced Event Handling: To enable proactive notifications (agent speaks based on an HA event without direct user prompt), implement an event queue (asyncio.Queue) populated by the callback and monitored by the agent or a dedicated tool (as discussed in IV.E.3).
Tool Granularity: More specific tools could be created (e.g., turn_light_on, get_temperature) instead of the generic call_home_assistant_service, potentially simplifying the agent's decision-making process, although the current approach is more flexible.
D. Recommendations for Testing and Deployment
Incremental Testing: Begin by verifying the WebSocket client's connection, authentication, and event receiving capabilities independently. Test the get_home_assistant_entity_state tool thoroughly. Then, implement and test the call_home_assistant_service tool.
Reconnection Tests: Simulate connection failures by restarting Home Assistant or temporarily blocking network access to ensure the client reconnects reliably as expected. Monitor logs for reconnection attempts and success messages.
Logging: Implement comprehensive logging, especially within the WebSocket client and tool functions, to aid debugging during development and operation. Use different log levels (DEBUG, INFO, WARNING, ERROR) appropriately.
Deployment: The agent application (including the background WebSocket client) needs to run persistently. Consider containerization (e.g., Docker) and deployment methods suitable for long-running Python applications (e.g., systemd service, Kubernetes deployment, or potentially cloud platforms if applicable). Ensure the necessary environment variables are securely provided to the deployed application.

