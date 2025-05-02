Implementing Bidirectional Voice Chat for the Beto Agent using Google ADK and ElevenLabsI. IntroductionThis report outlines a plan for integrating bidirectional voice chat functionality into the 'beto' agent, which utilizes Google's Agent Development Kit (ADK) framework.1 The primary goal is to enable users to interact with the agent using voice input and receive spoken responses synthesized by ElevenLabs' Text-to-Speech (TTS) service. The implementation leverages the streaming capabilities inherent in ADK, particularly those demonstrated by the adk web tool, and integrates ElevenLabs for high-quality, low-latency voice output [User Query].The plan details the necessary setup, architectural design, component responsibilities, and code implementation strategies required for a mid-level engineer to execute this integration. It addresses the core challenge of intercepting the agent's text-based responses, converting them to speech via an external service (ElevenLabs), and streaming the resulting audio back to the user in real-time, while utilizing ADK's built-in capabilities for handling voice input (Speech-to-Text). Due to the unavailability of the 'beto' agent's source code repository 2, this plan provides general guidance applicable to an ADK-based agent structure.II. Core Technologies and SetupThis integration relies on several key technologies and requires specific setup steps:
Google Agent Development Kit (ADK): The foundational framework for building the agent.1 ADK provides tools for agent definition, state management, tool usage, and importantly, built-in support for streaming interactions, including bidirectional audio when used with compatible models.4

Installation: Ensure ADK is installed in a Python virtual environment (Python 3.9+ recommended) using pip install google-adk.7
Project Structure: Follow the standard ADK project structure (e.g., agent_folder/, __init__.py, agent.py, .env).7


Google Generative AI SDK (google-genai): ADK utilizes this SDK internally to interact with Google's Gemini models, including the Live API necessary for real-time audio processing.10 While direct interaction with this SDK might be minimal for basic agent definition, understanding its role in handling Live API connections is beneficial.13 Note that the older google-generativeai package is being superseded by google-genai.11 Ensure the latest version is installed as part of ADK or explicitly (pip install -U google-genai).
ElevenLabs API: Used for high-quality Text-to-Speech (TTS) synthesis.

Account & API Key: An ElevenLabs account and API key are required.17 The API key should be stored securely, typically as an environment variable (e.g., ELEVEN_LABS_API_KEY in a .env file).17
SDK/WebSocket: While ElevenLabs offers a Python SDK 18, achieving the lowest latency for real-time streaming necessitates using their WebSocket API directly.20 This plan focuses on the WebSocket approach.


WebSocket Communication: Central to the real-time interaction.

Client <-> Backend: A primary WebSocket connection handles communication between the user's client application and the custom backend server.
Backend <-> ElevenLabs: A secondary WebSocket connection handles communication between the custom backend server and the ElevenLabs TTS API.21
Python Library: The websockets library is recommended for implementing asynchronous WebSocket clients and servers in Python.18


Asynchronous Backend Framework (FastAPI): A custom backend server is required to manage the WebSocket connections and orchestrate the data flow between the ADK agent, ElevenLabs, and the client. FastAPI is a suitable choice due to its native asynchronous support and WebSocket handling capabilities.5 Install using pip install fastapi uvicorn.
Client-Side Technologies (JavaScript):

WebSocket API: Standard browser API for connecting to the backend server.23
Web Audio API: Essential for capturing microphone input (navigator.mediaDevices.getUserMedia) and playing back the received audio stream (AudioContext, AudioBufferSourceNode).23


Environment Setup:

Create a Python virtual environment.7
Install necessary Python packages: google-adk, fastapi, uvicorn, websockets, python-dotenv, httpx (for potential REST fallbacks or utility calls).5
Configure environment variables in a .env file:

Google Cloud credentials (if using Vertex AI backend for ADK) or Google API Key (if using AI Studio).7
ELEVEN_LABS_API_KEY.17




III. Configuring the ADK Agent for Voice InputTo enable the ADK agent to process voice input, specific configurations are required within the agent definition (agent.py). ADK leverages the underlying Google GenAI Live API for Speech-to-Text (STT) when configured correctly.12
Model Selection (model parameter):

This is the most critical step. The agent must be configured to use a Gemini model that supports the Live API for bidirectional audio streaming.7
Consult the official Google AI Studio or Vertex AI documentation for the latest list of Live API-compatible model IDs (e.g., gemini-2.0-flash-live-001 or newer equivalents mentioned in the docs).12 Using a non-Live API model will prevent audio input processing.
Example (agent.py):
Pythonfrom google.adk.agents import Agent

root_agent = Agent(
    name="beto_voice_agent",
    # Ensure this model supports the Live API
    model="gemini-2.0-flash-live-001", # Verify latest model ID in Google docs [12]
    description="A helpful assistant that can chat via voice.",
    instruction="You are a conversational AI assistant. Keep your responses concise and suitable for spoken delivery. Respond naturally.",
    # Add any tools the agent needs, e.g., from the original 'beto' agent
    # tools=[...]
)




Agent Instructions (instruction parameter):

The instructions provided to the agent significantly influence its persona, response style, and behavior.7
For voice interactions, tailor the instructions to encourage outputs suitable for speech. Recommend conciseness, natural language flow, and the avoidance of complex structures like markdown tables, long code blocks, or excessive formatting that doesn't translate well to audio.


When an ADK agent is configured with a Live API-compatible model and interacted with via a streaming mechanism (like the Runner.run_live method used in the custom backend, or the adk web tool), the ADK framework implicitly handles the setup of the underlying Google GenAI Live API session.7 This session manages the connection to Google's backend for STT and, by default, TTS. However, this plan intentionally bypasses the default ADK TTS output path to integrate ElevenLabs. The STT functionality provided by the Live API is still leveraged for processing user voice input.IV. Handling User Audio Input (Speech-to-Text)The conversion of the user's spoken words into text (STT) is managed by the Google GenAI Live API, which ADK utilizes automatically when audio streaming is active with a compatible model 25,.7 The developer using ADK does not need to directly call an STT service; the primary responsibility lies in ensuring the correctly formatted audio data reaches the ADK backend.
Audio Format Requirement:

The Google Live API has a strict requirement for the input audio format: Raw 16-bit PCM audio, sampled at 16kHz, using little-endian byte order.12 Audio sent in any other format will likely fail to be processed.
The client application (e.g., the web interface) is responsible for capturing audio from the microphone and encoding or transcoding it into this specific format before sending it over the WebSocket connection. Libraries like PyAudio 24 or client-side JavaScript Web Audio API manipulation are needed for this.


Data Flow (STT):

The user speaks into their microphone.
The client application (web browser or other) captures the raw audio using appropriate APIs (e.g., JavaScript navigator.mediaDevices.getUserMedia and Web Audio API).
The client processes the captured audio, resampling it to 16kHz and ensuring it's in 16-bit PCM little-endian format.
The client sends these processed audio chunks via the primary WebSocket connection to the custom backend server.
The custom backend server receives the audio chunks and forwards them to the ADK's LiveRequestQueue associated with the user's session.7
The ADK Runner, managing the run_live session, passes the audio data to the underlying google-genai Live API session.
The Google Live API performs the STT, converting the audio stream to text.
The transcribed text is then treated as the user's input and fed into the ADK Agent's processing logic (based on its instruction and available tools).


The abstraction provided by ADK and the Live API simplifies the STT process for the developer integrating this feature. The main implementation effort related to STT is on the client-side, ensuring audio is captured, correctly formatted (PCM 16kHz 16-bit LE), and streamed efficiently to the backend. The adk web tool serves as a useful reference implementation for how a client can capture and send audio for ADK processing.6V. Handling Agent Audio Output (Text-to-Speech via ElevenLabs)The core architectural challenge is to replace ADK's default text streaming output with low-latency synthesized speech from ElevenLabs. ADK's live_events stream provides text chunks generated by the agent.7 We need to intercept this text, send it to ElevenLabs for TTS, receive the resulting audio bytes, and forward those bytes to the client, maintaining a real-time feel.
Solution: Custom WebSocket Backend as Intermediary:

Rationale: Directly modifying the internal workings of adk web is impractical and prone to breaking with updates. Using ADK callbacks (like after_model or after_agent) 28 to perform external, potentially long-running asynchronous operations like streaming TTS is not their intended purpose and risks blocking the agent's event loop or introducing unacceptable latency. Callbacks are more suitable for synchronous tasks like logging, validation, modifying state, or altering the final response content, not intercepting and transforming a stream mid-flight.28 Therefore, a dedicated custom backend server, managing the primary client WebSocket connection, is the most robust and controllable approach. This backend acts as a proxy and transformation layer for the agent's output. This mirrors the custom streaming application pattern shown in ADK documentation 7, but extends it by adding the TTS processing layer.
Implementation Strategy:

FastAPI Backend: Use an asynchronous framework like FastAPI to build the server.5
Primary WebSocket Endpoint: Define an endpoint (e.g., /ws/voice/{session_id}) to handle connections from the client application.7
Connection Handler Logic: Within the handler for each client connection:

Initialize ADK components: Create an ADK Runner instance for the agent and a LiveRequestQueue for the specific session ID.7 Start the live session using runner.run_live().
Task 1: ADK Event Processing: Start an asynchronous task (asyncio.create_task) that listens to the live_events stream coming from runner.run_live().7 When text chunks are received from the agent, instead of sending them directly to the client, put them onto a dedicated asyncio.Queue (e.g., text_for_tts_queue). Handle non-text events (like turn_complete) appropriately, perhaps by putting special markers onto a separate queue or directly sending status messages to the client.
Task 2: ElevenLabs Interaction: Start a second concurrent asynchronous task responsible for managing the WebSocket connection to ElevenLabs TTS API.21 This task will:

Connect to the ElevenLabs WebSocket endpoint (e.g., wss://api.elevenlabs.io/.../stream-input).
Continuously try to get text chunks from the text_for_tts_queue.
Send these text chunks to the ElevenLabs WebSocket.
Receive PCM audio chunks back from ElevenLabs.18
Put the received audio chunks onto another asyncio.Queue (e.g., audio_for_client_queue).


Task 3: Client Input Handling: Start a task to receive messages (primarily user audio chunks) from the client's WebSocket and forward them to the ADK LiveRequestQueue.
Task 4: Client Output Handling: Start a task that continuously tries to get items (audio chunks or status markers) from the audio_for_client_queue (and potentially a separate status queue). Encode the audio chunks (e.g., Base64) and send them as JSON messages over the primary WebSocket connection to the client. Send status messages directly.






Data Flow (TTS):

The ADK Agent (e.g., beto_voice_agent) generates a text response chunk.
The runner.run_live() method yields this text chunk via the live_events stream.7
Task 1 (ADK Event Processor) in the custom backend intercepts the text event.
The text chunk is placed onto the text_for_tts_queue.
Task 2 (ElevenLabs Handler) retrieves the text chunk from the queue.
Task 2 sends the text chunk via its WebSocket connection to the ElevenLabs TTS API.18
ElevenLabs synthesizes the speech and streams back PCM audio chunks over its WebSocket.18
Task 2 receives the PCM audio chunk.
Task 2 places the audio chunk onto the audio_for_client_queue.
Task 4 (Client Output Handler) retrieves the audio chunk from the queue.
Task 4 encodes the audio chunk (e.g., using Base64) into a JSON payload.
Task 4 sends the JSON payload containing the encoded audio over the primary WebSocket to the client application 7 (modified approach).


This architecture represents a significant shift from the standard ADK streaming example.7 The custom backend actively transforms the agent's text output stream into an audio stream using ElevenLabs before relaying it to the client, rather than the client consuming text directly.
Latency Management: Introducing an external TTS service inevitably adds latency. To minimize this impact:

ElevenLabs Model: Select ElevenLabs' lowest-latency models, such as "Flash v2.5", which offers ~75ms inference time (excluding network latency).20
ElevenLabs API: Use the ElevenLabs WebSocket API, designed for real-time streaming, rather than their REST streaming endpoint.20
Chunking Strategy: Carefully manage how text is chunked and sent to ElevenLabs. Use the try_trigger_generation: True flag or flush: True option in the WebSocket messages to encourage immediate audio generation for each chunk, reducing perceived latency.21 Sending very short chunks might slightly degrade quality, requiring balancing.36
Backend Efficiency: Ensure the custom backend uses efficient asynchronous programming patterns (asyncio) to avoid blocking operations.37
Geographic Proximity: Network latency between the backend server and ElevenLabs' servers (primarily US-based) will contribute to the overall delay.20 Deploying the backend geographically closer can help.


VI. Client-Side ImplementationThe client-side application (likely a web application using JavaScript) requires significant logic to handle both audio input and playback.
WebSocket Connection:

Establish a single WebSocket connection to the custom backend server's endpoint (e.g., /ws/voice/{session_id}) using the standard browser WebSocket API.23 Manage the connection lifecycle (open, message, error, close).


Sending User Audio Input (STT):

Microphone Access: Use navigator.mediaDevices.getUserMedia({ audio: true }) to request microphone access from the user.23
Audio Processing (Web Audio API):

Create an AudioContext.
Create a source node from the microphone stream (createMediaStreamSource).
Use a ScriptProcessorNode (older API, potentially deprecated but widely supported) or preferably an AudioWorkletNode (newer, more performant API running off the main thread) to access raw audio sample data buffers.
Crucial Step: Format Conversion: Within the audio processing node/worklet, process the incoming audio buffers:

Downsample: Resample the audio from the microphone's native sample rate (often 44.1kHz or 48kHz) down to 16kHz as required by the Google Live API.12 This typically involves interpolation algorithms.
Convert to 16-bit PCM: Convert the floating-point samples (usually -1.0 to 1.0) provided by the Web Audio API into signed 16-bit integers.
Ensure Little-Endian: JavaScript TypedArrays handle endianness; ensure the final Int16Array or DataView uses little-endian format when converting to bytes.


Send the resulting 16kHz, 16-bit PCM audio data chunks (as ArrayBuffer or Blob) over the WebSocket connection to the backend server.23




Receiving Messages from Backend:

Implement the onmessage event handler for the WebSocket connection.23
Messages from the backend will be JSON strings. Parse them using JSON.parse().
Differentiate Message Types: The client must inspect the parsed message object to determine its type and act accordingly:

Audio Data: Messages containing synthesized speech (e.g., {"audio_chunk": "base64_encoded_string"}).
Status Updates: Standard ADK signals forwarded by the backend (e.g., {"turn_complete": true}, {"interrupted": true}).7
Fallback Text: Plain text messages (e.g., {"message": "Agent text response"}) if TTS fails or is disabled.7
Error Messages: Custom error indicators from the backend.




Audio Playback (Web Audio API):

Handling audio_chunk: When a message containing base64-encoded audio is received:

Decode: Decode the Base64 string back into binary data (an ArrayBuffer) using atob() and manual byte manipulation or a helper library.
Buffering: Maintain a queue or buffer for these incoming audio ArrayBuffer chunks. Since audio arrives incrementally, direct playback of each tiny chunk is impractical and inefficient.
Web Audio Playback:

Use the same AudioContext instance.
When enough audio data has accumulated in the buffer (e.g., a few hundred milliseconds worth), decode the raw PCM data from the ArrayBuffer into an AudioBuffer using audioContext.decodeAudioData(). Note: decodeAudioData expects encoded formats (like WAV, MP3), not raw PCM directly. For raw PCM, you need to manually create an AudioBuffer (audioContext.createBuffer) and copy the PCM data into its channels (audioBuffer.copyToChannel). Ensure the AudioBuffer is created with the correct sample rate (e.g., 24000 or 44100, matching the output_format requested from ElevenLabs).
Create an AudioBufferSourceNode (audioContext.createBufferSource()).
Set its buffer property to the created AudioBuffer.
Connect the source node to the audioContext.destination (speakers).
Schedule playback using sourceNode.start(startTime). Crucially, startTime needs to be carefully calculated based on the audioContext.currentTime and the duration of previously scheduled buffers to ensure seamless, gapless playback of the audio stream. This requires tracking the total duration of audio queued for playback.


Buffer Management: Remove played chunks from the buffer queue. Handle potential buffer under-runs (pauses if data arrives too slowly) or over-runs (discarding data if it arrives too quickly, though less likely).




The client-side implementation involves significant complexity, particularly in handling the raw audio processing for both input (encoding to 16kHz PCM) and output (decoding Base64, managing PCM buffers, and scheduling gapless playback with the Web Audio API). This is considerably more involved than a standard text-based chat interface.
Managing Multiple Tabs/Connections: For applications where users might open multiple tabs, the default behavior would create a separate WebSocket connection per tab, leading to inefficiency.39 Advanced techniques like using JavaScript SharedWorkers to manage a single WebSocket connection across multiple tabs and BroadcastChannels to communicate between the worker and tabs can mitigate this, but add substantial implementation complexity.40 For initial development targeting a mid-level engineer, focusing on a single-tab experience is recommended.
VII. ElevenLabs WebSocket Integration DetailsConnecting the custom backend to the ElevenLabs WebSocket API requires specific configuration and message handling using the websockets Python library.

Connection Endpoint:

The URL follows the pattern: wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input.18 Replace {voice_id} with the desired voice ID (e.g., "21m00Tcm4TlvDq8ikWAM").
Query Parameters: Append necessary configuration parameters to the URL:

model_id: Specify the TTS model. For lowest latency, use eleven_flash_v2_5.20 Other options like eleven_multilingual_v2 offer higher quality but more latency.34
output_format: Crucial. Specify the desired audio format and sample rate for the output stream. For raw PCM data suitable for client-side Web Audio API playback, use formats like pcm_16000, pcm_24000, or pcm_44100.18 The chosen sample rate must be supported by ElevenLabs for the selected model and playable by the client. 24kHz (pcm_24000) or 44.1kHz (pcm_44100) are common choices balancing quality and data size.
Example URL: wss://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM/stream-input?model_id=eleven_flash_v2_5&output_format=pcm_24000





Authentication:

The primary method is to include the API key within the initial JSON configuration message sent after connecting, using the xi_api_key field.18 Sending it as a custom header during the WebSocket handshake might also be possible depending on the library's capabilities, but the JSON method is documented.



Initial Configuration Message:

Immediately after the WebSocket connection is established, the backend must send a specific JSON message to configure the stream.18
Required Fields:

"text": " " (A single space character is required to initiate the stream).
"xi_api_key": "YOUR_ELEVENLABS_API_KEY"


Optional Fields:

"voice_settings": {"stability": 0.5, "similarity_boost": 0.8}: Fine-tune the voice characteristics.21
"generation_config": {"chunk_length_schedule": }: Controls internal buffering and generation triggers, impacting the trade-off between latency and audio quality/consistency.21 Lower values might reduce latency but potentially affect naturalness.





Sending Text Chunks:

Subsequent text generated by the ADK agent should be sent as individual JSON messages.18
Payload Structure: {"text": "Text chunk from agent ", "try_trigger_generation": True}
Trailing Space: It's recommended that each text chunk ends with a space " " for optimal processing by ElevenLabs.22
try_trigger_generation: True: This flag (or the similar flush: True 21) instructs ElevenLabs to attempt synthesizing audio for the received chunk immediately, minimizing latency, rather than waiting for more text according to the chunk_length_schedule.22 This is vital for conversational responsiveness.



Receiving Audio Chunks:

The backend needs to listen for messages coming back from the ElevenLabs WebSocket.
Audio Data: Synthesized speech arrives as raw binary WebSocket messages (bytes) containing the PCM audio data.18
Status/Error Messages: ElevenLabs also sends JSON messages to indicate the end of the stream ({"isFinal": true}) or report errors ({"error": "Error message"}).18 The receiving logic must differentiate between binary audio data and these JSON status messages.



Closing the Connection:

To signal that no more text will be sent for the current utterance, the backend should send a final JSON message containing only {"text": ""}.21 This allows ElevenLabs to flush any remaining audio buffers and gracefully close the stream for that utterance.



ElevenLabs Model Comparison (TTS): Selecting the appropriate ElevenLabs model is key to balancing latency, quality, and features.


Featureeleven_flash_v2_5 eleven_turbo_v2_5 eleven_multilingual_v2 Primary FocusLowest LatencyQuality & Low LatencyHighest Quality & EmotionLatency (Model)~75ms~250-300msHigher (not specified)Audio QualityGoodHighHighest / Most ExpressiveLanguages323229Character Limit40,00040,00010,000CostLowerHigherHigherUse CaseReal-time conversationBalanced quality/speedNarration, Audiobooks
*Note: Latency figures are model inference times and exclude network latency.[35] For real-time voice chat, `eleven_flash_v2_5` is the recommended starting point due to its focus on speed.[20]*
VIII. Asynchronous Stream ManagementThe proposed architecture involves multiple concurrent, asynchronous data streams. Effective management using Python's asyncio library is crucial for performance and correctness.

Concurrency Challenges: The backend server must simultaneously:

Maintain the WebSocket connection with the client (receiving user audio, sending agent audio/status).
Run the ADK agent's live interaction loop (runner.run_live).
Process the stream of events (live_events) generated by the ADK agent.
Maintain the WebSocket connection with the ElevenLabs TTS API.
Send text chunks derived from ADK events to ElevenLabs.
Receive audio chunks back from ElevenLabs.
Pass data safely between these concurrent operations.



asyncio Primitives: The implementation will rely heavily on:

async def: To define coroutines (asynchronous functions) for each task (e.g., handling client input, processing ADK events, managing ElevenLabs connection).37
await: To pause a coroutine while waiting for an I/O operation (like receiving a WebSocket message or getting an item from a queue) to complete, allowing the event loop to run other tasks.37
asyncio.create_task(): To schedule coroutines to run concurrently, managed by the asyncio event loop.7
asyncio.gather(): To run multiple tasks concurrently and wait for their completion (often used at the top level of the WebSocket handler).7
asyncio.Queue: To provide thread-safe (or rather, coroutine-safe) communication channels for passing data between the different concurrently running tasks. This is essential for decoupling the tasks, for example, passing text from the ADK event processor to the ElevenLabs sender, and passing audio from the ElevenLabs receiver to the client sender.18 Using queues avoids complex locking mechanisms and potential race conditions.



Conceptual Backend Structure (FastAPI Example):The core logic within the FastAPI WebSocket endpoint handler would orchestrate these tasks:
Python# Simplified conceptual structure - requires detailed implementation
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
# Assume necessary imports for ADK, ElevenLabs function, etc.

# Queues for inter-task communication
text_to_tts_queue = asyncio.Queue(maxsize=100) # Limit queue size
audio_to_client_queue = asyncio.Queue(maxsize=100) # Limit queue size

async def process_adk_events(live_events, tts_queue, client_queue):
    """Task 1: Listens to ADK, puts text on tts_queue, status on client_queue."""
    try:
        async for event in live_events:
            # Simplified: Extract text, handle turn_complete, interrupted etc.
            if event.content and event.content.parts and event.content.parts.text:
                text = event.content.parts.text
                await tts_queue.put(text)
            if event.turn_complete:
                await client_queue.put({"type": "status", "data": "turn_complete"})
            # Handle other event types (interrupted, errors)
    except Exception as e:
        print(f"Error processing ADK events: {e}")
        await client_queue.put({"type": "error", "data": "ADK processing error"})
    finally:
        await tts_queue.put(None) # Signal end to TTS task
        await client_queue.put(None) # Signal end to client output task

async def manage_elevenlabs_connection(tts_queue, client_queue):
    """Task 2: Connects to ElevenLabs, gets text from tts_queue, puts audio on client_queue."""
    # Implementation using websockets library based on [18]
    # Connect to ElevenLabs WS
    # Loop:
    #   text_chunk = await tts_queue.get()
    #   if text_chunk is None: break
    #   Send text_chunk to ElevenLabs WS
    #   Receive audio/status from ElevenLabs WS
    #   if audio_bytes: await client_queue.put({"type": "audio", "data": audio_bytes})
    #   if is_final: pass # Or potentially signal client
    # Close ElevenLabs WS connection
    pass # Placeholder for full implementation

async def process_client_input(websocket: WebSocket, adk_queue: LiveRequestQueue):
    """Task 3: Receives audio from client, sends to ADK queue."""
    try:
        while True:
            data = await websocket.receive_bytes() # Assuming client sends raw PCM bytes
            # Forward to ADK's LiveRequestQueue (needs proper formatting/wrapping)
            # adk_queue.send_audio(data) # Conceptual - ADK API might differ
            print(f"Received client audio chunk: {len(data)} bytes")
    except WebSocketDisconnect:
        print("Client disconnected (input task)")
    except Exception as e:
        print(f"Error processing client input: {e}")

async def send_to_client(websocket: WebSocket, client_queue):
    """Task 4: Gets audio/status from client_queue, sends to client WS."""
    try:
        while True:
            item = await client_queue.get()
            if item is None:
                break # End signal received
            if item["type"] == "audio":
                # Encode audio (e.g., base64) before sending
                encoded_audio = base64.b64encode(item["data"]).decode('utf-8')
                await websocket.send_json({"audio_chunk": encoded_audio})
            elif item["type"] == "status":
                await websocket.send_json({item["data"]: True}) # e.g., {"turn_complete": True}
            elif item["type"] == "error":
                 await websocket.send_json({"error": item["data"]})
            client_queue.task_done() # Mark item as processed
    except WebSocketDisconnect:
        print("Client disconnected (output task)")
    except Exception as e:
        print(f"Error sending to client: {e}")

@app.websocket("/ws/voice/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    # 1. Initialize ADK Runner, LiveRequestQueue for session
    # live_events, live_request_queue = start_adk_session(session_id) # Assume this function exists

    # Placeholder for ADK initialization
    live_events = None # Replace with actual ADK stream
    live_request_queue = None # Replace with actual ADK queue

    if live_events is None or live_request_queue is None:
         print("ERROR: ADK Session not initialized")
         await websocket.close(code=1011)
         return

    # 2. Create tasks
    adk_task = asyncio.create_task(process_adk_events(live_events, text_to_tts_queue, audio_to_client_queue))
    eleven_task = asyncio.create_task(manage_elevenlabs_connection(text_to_tts_queue, audio_to_client_queue))
    input_task = asyncio.create_task(process_client_input(websocket, live_request_queue))
    output_task = asyncio.create_task(send_to_client(websocket, audio_to_client_queue))

    # Wait for tasks to complete (implement proper cancellation)
    done, pending = await asyncio.wait(
        {adk_task, eleven_task, input_task, output_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    # Basic cancellation logic (needs refinement)
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)

    print(f"WebSocket session {session_id} ended.")


(Note: The above code is conceptual and requires filling in details for ADK initialization, ElevenLabs interaction based on 18, error handling, and graceful task cancellation.)

The use of asyncio.Queue is fundamental here. It allows the different parts of the system (ADK processing, ElevenLabs interaction, client communication) to operate concurrently and hand off data without blocking each other, which is essential for maintaining responsiveness in a real-time voice application.IX. Code Implementation ExamplesThis section provides more concrete code snippets for key parts of the implementation. These should be adapted and integrated into the full application structure.

ADK Agent Configuration (agent.py):
Python# In your multi_tool_agent/agent.py (or similar)
from google.adk.agents import Agent
# from your_agent_tools import tool1, tool2 # Import any custom tools

# Verify the latest Live API compatible model ID from Google documentation
# https://ai.google.dev/gemini-api/docs/models#live-api
# https://cloud.google.com/vertex-ai/generative-ai/docs/live-api
LIVE_API_MODEL = "gemini-2.0-flash-live-001" # Replace if outdated [12]

root_agent = Agent(
    name="beto_voice_agent",
    model=LIVE_API_MODEL, # Critical for voice input [7, 12]
    description="A helpful assistant that responds via voice.",
    instruction=(
        "You are a friendly and helpful voice assistant. "
        "Keep your answers concise and conversational. "
        "Avoid using markdown, lists, or code blocks in your responses "
        "as they will be spoken aloud."
    ),
    # tools=[tool1, tool2], # Add necessary tools [8, 43]
    # Callbacks are generally not suitable for intercepting streams for TTS
    # before_agent_callback=None, # [28, 29]
    # after_agent_callback=None,
)

# Ensure __init__.py exists and imports the agent
# In multi_tool_agent/__init__.py:
# from. import agent



Custom WebSocket Backend Skeleton (FastAPI - main.py):
Pythonimport asyncio
import base64
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv

# Assume ADK setup functions (start_adk_session) and
# ElevenLabs interaction function (manage_elevenlabs_connection) exist
# from adk_setup import start_adk_session # Placeholder
# from elevenlabs_handler import manage_elevenlabs_connection # Placeholder

load_dotenv()

app = FastAPI()

# Define Queues globally or manage per connection appropriately
text_to_tts_queue = asyncio.Queue(maxsize=100)
audio_to_client_queue = asyncio.Queue(maxsize=100)

# Placeholder task functions (implement based on Section VIII conceptual code)
async def process_adk_events(live_events, tts_queue, client_queue):
    print("ADK Event Processor Started")
    #... implementation...
    await asyncio.sleep(1) # Simulate work
    print("ADK Event Processor Finished")
    await tts_queue.put(None)
    await client_queue.put(None)


async def process_client_input(websocket: WebSocket, adk_queue):
     print("Client Input Handler Started")
     try:
         while True:
             data = await websocket.receive_bytes()
             print(f"Received {len(data)} bytes from client")
             # Process/forward data to adk_queue (requires ADK LiveRequestQueue knowledge)
             # Example: adk_queue.send_audio(data) # Conceptual
     except WebSocketDisconnect:
         print("Client disconnected (input task)")
     except Exception as e:
         print(f"Client input error: {e}")
     finally:
          print("Client Input Handler Finished")


async def send_to_client(websocket: WebSocket, client_queue):
    print("Client Output Handler Started")
    try:
        while True:
            item = await client_queue.get()
            if item is None:
                break
            if item.get("type") == "audio":
                encoded_audio = base64.b64encode(item["data"]).decode('utf-8')
                await websocket.send_json({"audio_chunk": encoded_audio})
            elif item.get("type") == "status":
                 await websocket.send_json({item["data"]: True})
            elif item.get("type") == "error":
                 await websocket.send_json({"error": item["data"]})
            client_queue.task_done()
    except WebSocketDisconnect:
        print("Client disconnected (output task)")
    except Exception as e:
        print(f"Send to client error: {e}")
    finally:
        print("Client Output Handler Finished")


@app.websocket("/ws/voice/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    print(f"WebSocket connection accepted for session: {session_id}")

    adk_live_events = None # Replace with result of start_adk_session(...).live_events
    adk_request_queue = None # Replace with result of start_adk_session(...).live_request_queue

    # --- TODO: Implement ADK Session Initialization ---
    # try:
    #    adk_live_events, adk_request_queue = start_adk_session(session_id)
    # except Exception as e:
    #    print(f"Failed to initialize ADK session {session_id}: {e}")
    #    await websocket.close(code=1011)
    #    return
    # --- Remove this placeholder check once ADK init is implemented ---
    if adk_live_events is None or adk_request_queue is None:
         print("Placeholder: ADK Session not initialized")
         # Simulate some dummy events for testing structure
         async def dummy_events():
             await asyncio.sleep(2)
             yield type('obj', (object,), {'content': type('obj', (object,), {'parts': [type('obj', (object,), {'text': 'Hello from dummy ADK.'})]})})()
             await asyncio.sleep(1)
             yield type('obj', (object,), {'turn_complete': True})()
         adk_live_events = dummy_events()
         adk_request_queue = asyncio.Queue() # Dummy queue
    # -----------------------------------------------------------------


    tasks = {
        asyncio.create_task(process_adk_events(adk_live_events, text_to_tts_queue, audio_to_client_queue)),
        # --- TODO: Implement and add ElevenLabs Task ---
        # asyncio.create_task(manage_elevenlabs_connection(text_to_tts_queue, audio_to_client_queue)),
        # ---------------------------------------------
        asyncio.create_task(process_client_input(websocket, adk_request_queue)),
        asyncio.create_task(send_to_client(websocket, audio_to_client_queue)),
    }

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    print(f"A task finished for session {session_id}. Cleaning up...")
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True) # Wait for cancellations

    # Ensure queues are cleared if needed (or handle in tasks)
    while not text_to_tts_queue.empty(): await text_to_tts_queue.get()
    while not audio_to_client_queue.empty(): await audio_to_client_queue.get()

    print(f"WebSocket session {session_id} closed.")

# Command to run: uvicorn main:app --reload --port 8000



ElevenLabs WebSocket Interaction Function (elevenlabs_handler.py):

Refer to the detailed example provided in research snippet.18 That example covers connection, authentication via the initial message, sending text chunks from a queue, receiving audio/status messages, and handling closure. Ensure the output_format in the WS_URL is set correctly (e.g., pcm_24000).



Client-Side Audio Capture (JavaScript - Conceptual):
JavaScript// --- Client-side JavaScript ---
let audioContext;
let microphoneStream;
let audioProcessorNode; // Could be ScriptProcessorNode or AudioWorkletNode
let websocket; // Assume websocket connection is established

const TARGET_SAMPLE_RATE = 16000; // For Google Live API [12]

async function startAudioCapture() {
    try {
        audioContext = new (window.AudioContext |


| window.webkitAudioContext)();microphoneStream = await navigator.mediaDevices.getUserMedia({ audio: true });const source = audioContext.createMediaStreamSource(microphoneStream);const sourceSampleRate = audioContext.sampleRate;        // --- Using AudioWorklet (Recommended) ---
        if (audioContext.audioWorklet) {
            await audioContext.audioWorklet.addModule('audio-processor.js'); // Separate JS file for worklet
            audioProcessorNode = new AudioWorkletNode(audioContext, 'audio-processor');

            audioProcessorNode.port.onmessage = (event) => {
                if (event.data.type === 'audioData' && websocket && websocket.readyState === WebSocket.OPEN) {
                    // event.data.buffer contains Int16Array with 16kHz PCM data
                    websocket.send(event.data.buffer); // Send as ArrayBuffer
                }
            };
            source.connect(audioProcessorNode).connect(audioContext.destination); // Connect through worklet
             console.log("AudioWorklet processor connected.");

        } else {
            // --- Fallback: ScriptProcessorNode (Less Performant/Deprecated) ---
             console.warn("AudioWorklet not supported, using ScriptProcessorNode.");
            const bufferSize = 4096; // Adjust as needed
            audioProcessorNode = audioContext.createScriptProcessor(bufferSize, 1, 1); // Input channels, output channels

            audioProcessorNode.onaudioprocess = (audioProcessingEvent) => {
                const inputBuffer = audioProcessingEvent.inputBuffer;
                const inputData = inputBuffer.getChannelData(0); // Get Float32Array data

                // --- Manual Resampling and PCM Conversion (Complex) ---
                // 1. Resample from sourceSampleRate to TARGET_SAMPLE_RATE
                const resampledData = resample(inputData, sourceSampleRate, TARGET_SAMPLE_RATE); // Requires a resampling library/function

                // 2. Convert Float32 (-1.0 to 1.0) to Int16 (-32768 to 32767)
                const pcmData = float32ToInt16(resampledData); // Requires conversion function

                if (websocket && websocket.readyState === WebSocket.OPEN) {
                    websocket.send(pcmData.buffer); // Send the underlying ArrayBuffer
                }
            };
            source.connect(audioProcessorNode);
            audioProcessorNode.connect(audioContext.destination); // Connect processor to output
        }


    } catch (err) {
        console.error("Error accessing microphone:", err);
        // Handle error - display message to user
    }
}

function stopAudioCapture() {
    if (microphoneStream) {
        microphoneStream.getTracks().forEach(track => track.stop());
    }
    if (audioProcessorNode) {
        audioProcessorNode.disconnect();
    }
    if (audioContext && audioContext.state!== 'closed') {
        audioContext.close();
    }
     console.log("Audio capture stopped.");
}

// --- Helper functions (need implementation or library) ---
function resample(inputData, fromRate, toRate) {
    // Placeholder: Implement or use a library for resampling
     console.warn("Resampling not implemented!");
    return inputData; // Passthrough for now
}

function float32ToInt16(buffer) {
    // Placeholder: Implement conversion
     console.warn("Float32 to Int16 conversion not implemented!");
    let l = buffer.length;
    const output = new Int16Array(l);
    // Simple scaling (example only, may need clipping/dithering)
    // while (l--) { output[l] = Math.min(1, buffer[l]) * 0x7FFF; }
    return output;
}

// --- AudioWorklet Processor Code (audio-processor.js) ---
/*
class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        // Add state for resampling if needed
    }

    process(inputs, outputs, parameters) {
        const input = inputs;
        if (input.length > 0) {
            const inputData = input; // Float32Array

            // --- Resample and Convert to Int16 PCM ---
            // (Similar logic as ScriptProcessorNode but runs off-main-thread)
            const targetSampleRate = 16000;
            const resampledData = resample(inputData, sampleRate, targetSampleRate); // sampleRate is global in worklet
            const pcmData = float32ToInt16(resampledData);

            // Post message back to main thread
            this.port.postMessage({ type: 'audioData', buffer: pcmData.buffer }, [pcmData.buffer]); // Transfer buffer ownership
        }
        return true; // Keep processor alive
    }
    // Add resample and float32ToInt16 functions here or import them
}
registerProcessor('audio-processor', AudioProcessor);
*/
```
*Note: Client-side audio processing, especially resampling and PCM conversion, is non-trivial. Using libraries or well-tested implementations for `resample` and `float32ToInt16` is highly recommended.*

Client-Side Audio Playback (JavaScript - Conceptual):
JavaScript// --- Client-side JavaScript ---
let audioContext; // Reuse from capture or create new
let audioQueue =; // Buffer for incoming audio ArrayBuffers
let nextPlayTime = 0;
let isPlaying = false;
const PLAYBACK_SAMPLE_RATE = 24000; // MUST match output_format from ElevenLabs

function initializeAudioPlayback() {
    if (!audioContext |


| audioContext.state === 'closed') {audioContext = new (window.AudioContext || window.webkitAudioContext)();nextPlayTime = audioContext.currentTime; // Initialize play timeconsole.log("Audio playback initialized. Sample Rate:", audioContext.sampleRate);// May need user interaction to start AudioContextaudioContext.resume();}}function handleWebSocketMessage(event) {
    try {
        const message = JSON.parse(event.data);

        if (message.audio_chunk) {
            // Decode Base64 to ArrayBuffer
            const binaryString = atob(message.audio_chunk);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            audioQueue.push(bytes.buffer); // Add ArrayBuffer to queue
            schedulePlayback(); // Attempt to play buffered audio

        } else if (message.turn_complete) {
            console.log("Agent turn complete.");
            // Optionally signal end of utterance playback
        } else if (message.interrupted) {
             console.log("Agent interrupted.");
             // Clear audio queue and stop playback?
             audioQueue =;
             // Need logic to stop any currently playing AudioBufferSourceNode
        } else if (message.message) {
            console.log("Received text message (TTS fallback?):", message.message);
            // Display text message to user
        } else if (message.error) {
             console.error("Received error from backend:", message.error);
        }

    } catch (e) {
        console.error("Error handling WebSocket message:", e);
    }
}

function schedulePlayback() {
    if (!audioContext |
| audioContext.state!== 'running') {console.warn("AudioContext not running. Cannot schedule playback.");// Attempt to resume context (might require user gesture)audioContext?.resume();return;}if (isPlaying || audioQueue.length === 0) {return; // Already playing or nothing to play}    isPlaying = true;
    const audioBufferChunk = audioQueue.shift(); // Get next chunk (ArrayBuffer)

    // --- Manually create AudioBuffer from raw PCM data ---
    // Assumes PCM is 16-bit mono (adjust channels if needed)
    const pcm16Data = new Int16Array(audioBufferChunk);
    const numFrames = pcm16Data.length;
    const audioBuffer = audioContext.createBuffer(1, numFrames, PLAYBACK_SAMPLE_RATE); // 1 channel
    const channelData = audioBuffer.getChannelData(0); // Float32Array

    // Convert Int16 PCM back to Float32 for Web Audio API
    for (let i = 0; i < numFrames; i++) {
        channelData[i] = pcm16Data[i] / 32768.0; // Normalize to -1.0 to 1.0
    }
    // ----------------------------------------------------

    const sourceNode = audioContext.createBufferSource();
    sourceNode.buffer = audioBuffer;
    sourceNode.connect(audioContext.destination);

    const currentTime = audioContext.currentTime;
    const startTime = Math.max(currentTime, nextPlayTime); // Schedule immediately or after previous chunk

    console.log(`Scheduling chunk: ${numFrames} frames at ${startTime.toFixed(3)}s (Context time: ${currentTime.toFixed(3)}s)`);
    sourceNode.start(startTime);

    // Calculate when this chunk will finish playing
    const duration = audioBuffer.duration;
    nextPlayTime = startTime + duration;

    sourceNode.onended = () => {
        console.log(`Chunk finished playing (duration: ${duration.toFixed(3)}s)`);
        isPlaying = false;
        // Immediately try to schedule the next chunk if available
        schedulePlayback();
    };
}

// Example usage:
// websocket.onmessage = handleWebSocketMessage;
// Call initializeAudioPlayback() potentially after user interaction
```
*Note: Client-side streaming audio playback requires careful buffer management and timing with the Web Audio API to avoid gaps or glitches. The manual creation of `AudioBuffer` from raw PCM is necessary.*
X. Testing and Debugging StrategiesThorough testing and debugging are essential due to the complexity of the asynchronous streams and audio processing involved.
Component Testing:

ElevenLabs Function (manage_elevenlabs_connection): Test this function in isolation. Create a test script that puts text chunks onto a mock asyncio.Queue, runs the function, connects to the actual ElevenLabs WebSocket API, and verifies that audio chunks (bytes) are received and put onto a mock output queue. Check for correct handling of the isFinal message and connection closure.18
Backend WebSocket Handler (websocket_endpoint): Use a WebSocket client testing tool or library (like pytest-asyncio with websockets) to connect to the FastAPI backend. Send mock client audio messages (bytes). Mock the start_adk_session function to return predictable live_events (including text chunks and status events). Mock the manage_elevenlabs_connection task to simulate receiving audio chunks. Verify that the correct sequence of audio chunks (Base64 encoded) and status messages are sent back to the test client.
Client-Side Audio Input: Create test cases for the JavaScript audio processing functions (resample, float32ToInt16). Use known audio samples and verify the output format and sample rate match the required 16kHz 16-bit PCM LE.
Client-Side Audio Playback: Test the handleWebSocketMessage and schedulePlayback functions with sample Base64 encoded PCM audio chunks. Verify that the audio plays back smoothly without audible gaps or clicks using the Web Audio API.


End-to-End Testing:

Initial STT Test: Use the standard adk web command-line tool with the configured agent (agent.py with the Live API model). Speak into the microphone and verify in the adk web UI or logs that the agent receives the correct transcribed text input.7 This confirms the ADK agent and Google Live API STT part are working correctly.
Full System Test: Develop a minimal HTML/JavaScript client that connects to the custom FastAPI backend's WebSocket endpoint. Implement basic microphone input (sending PCM) and audio playback (receiving Base64). Conduct full conversations, testing various inputs and monitoring:

Perceived Latency: Time from end of user speech to start of agent audio response.
Audio Quality: Check for clarity, naturalness, and absence of artifacts (clicks, pops, stuttering).
Robustness: Test handling of long pauses, interruptions, and potential network issues.




Debugging Techniques:

Logging: Implement extensive logging on both the backend (FastAPI, ADK runner via configuration, ElevenLabs handler task) and the client-side JavaScript. Log key events like WebSocket connections/disconnections, message sending/receiving (including data types and sizes), task starts/stops, queue interactions, and errors.
Browser Developer Tools: Use the Network tab (specifically the WS filter) to inspect the messages flowing between the client and the custom backend WebSocket. Check message content, timing, and potential errors.45 Use the Console tab for JavaScript logs.
Audio Debugging:

Input: Log the sample rate and format of audio captured by the client before processing. Log the format and sample rate after processing to ensure it's 16kHz 16-bit PCM. Save intermediate audio buffers to files for analysis if needed.
Output: Log the received Base64 chunk sizes. Decode and save the received PCM audio chunks to a file on the client or backend for analysis using audio editing software (like Audacity) to check for corruption, incorrect sample rates, or discontinuities. Use Web Audio API debugging tools if available in the browser.


Backend Debugging: Use standard Python debugging tools (like pdb or IDE debuggers) to step through the asyncio tasks and inspect queue states and variable values. Be mindful that debugging highly concurrent asynchronous code can be challenging.


An incremental development approach is strongly recommended. Build and test each component (ADK agent text I/O, STT via adk web, custom backend text relay, ElevenLabs integration, client audio input, client audio output) individually before integrating them. This isolates potential issues and simplifies debugging.XI. ConclusionIntegrating bidirectional voice chat into the 'beto' agent using Google ADK and ElevenLabs involves leveraging ADK's streaming capabilities for Speech-to-Text (STT) via the Google Live API, while implementing a custom solution for Text-to-Speech (TTS) using ElevenLabs' WebSocket API. The core of this solution is a custom asynchronous backend server (e.g., using FastAPI and websockets) that acts as an intermediary. This backend manages the client WebSocket connection, orchestrates the ADK agent's live session, intercepts the agent's text output, streams it to ElevenLabs for synthesis, receives the resulting PCM audio, and streams that audio back to the client.Key implementation considerations include:
ADK Configuration: Using a Gemini model compatible with the Live API is mandatory for processing voice input.12 Agent instructions should be tailored for voice output.26
Audio Formats: Strict adherence to audio formats is crucial: 16kHz 16-bit PCM little-endian for input to ADK/Google Live API 13, and a suitable PCM format (e.g., 24kHz or 44.1kHz) for output from ElevenLabs.33
Latency: Achieving low end-to-end latency requires using ElevenLabs' fastest models (e.g., Flash v2.5) via their WebSocket API, optimizing text chunking, and ensuring efficient asynchronous backend processing.20
Asynchronous Management: Robust handling of multiple concurrent asynchronous streams using asyncio tasks and queues is essential on the backend.18
Client Complexity: The client-side requires significant Web Audio API implementation for capturing, encoding (to 16kHz PCM), decoding (Base64), buffering, and playing back streamed PCM audio data.23
Potential challenges include managing the inherent latency introduced by the external TTS step, handling WebSocket connection interruptions and reconnections gracefully 46, scaling the custom backend for multiple users, and the intricacies of real-time audio processing on the client.Successful implementation will provide a significantly more natural and engaging user experience compared to text-only interaction. Future enhancements could involve adding visual feedback for speaking/listening states, implementing user interruption capabilities, exploring alternative TTS providers, or deploying the agent and custom backend using scalable solutions like Google Cloud Run 44 or Vertex AI Agent Engine.4
