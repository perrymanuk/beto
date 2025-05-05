# Custom Web UI Implementation

This document describes the custom web interface implementation for RadBot using FastAPI and WebSockets.

## Overview

The custom web interface provides a modern, responsive chat interface for interacting with the RadBot agent. It uses:

- **FastAPI**: A modern, fast web framework for building APIs with Python
- **WebSockets**: For real-time bidirectional communication
- **Jinja2 Templates**: For server-side rendering of HTML
- **Vanilla JavaScript**: For client-side interactivity

The implementation follows a clean architecture with separation of concerns:

1. **API Layer**: FastAPI routes and endpoints
2. **Session Management**: Handling user sessions and agent instances
3. **UI Layer**: HTML templates, CSS styling, and JavaScript for user interaction

## Key Components

### 1. FastAPI Application (`app.py`)

The main FastAPI application handles HTTP requests, WebSocket connections, and routes users to the appropriate endpoints. It integrates with the RadBot agent to process user messages and return responses.

Key features:
- REST API endpoint for processing messages (`/api/chat`)
- WebSocket endpoint for real-time chat (`/ws/{session_id}`)
- Session management to persist user conversations
- Serving static files (JavaScript, CSS) and HTML templates

### 2. Session Management (`session.py`)

The session management module handles:
- Creating and tracking user sessions
- Initializing and managing agent instances for each session
- Providing a clean interface for the API layer to interact with agents

### 3. HTML Template (`index.html`)

A clean, responsive chat interface that:
- Displays conversation history with proper formatting for markdown
- Provides a text input area with support for multi-line input
- Shows status indicators for agent processing
- Includes a button to reset the conversation

### 4. JavaScript Client (`app.js`)

Client-side JavaScript that handles:
- WebSocket connection management
- Sending and receiving messages
- Rendering messages with markdown support
- Managing the UI state based on agent status
- Handling session persistence via localStorage

### 5. CSS Styling (`style.css`)

Modern styling with:
- Responsive design that works on mobile and desktop
- Clean message bubbles for user and agent messages
- Support for markdown rendering including code blocks
- Status indicators for agent state

## Interaction Flow

1. **User Loads the Page**:
   - Client generates a session ID or retrieves existing one from localStorage
   - Client establishes WebSocket connection with the server
   - Server initializes or retrieves an agent for the session

2. **User Sends a Message**:
   - Client sends message via WebSocket
   - Message is displayed in the UI immediately
   - Status changes to "thinking"

3. **Server Processes the Message**:
   - Server receives the message via WebSocket
   - RadBot agent processes the message
   - Any tool usage happens on the server side

4. **Server Sends Response**:
   - Agent's response is sent back via WebSocket
   - Client receives and displays the response
   - Status changes back to "ready"

5. **Session Management**:
   - Conversation history is maintained in the agent's session
   - User can reset the conversation via UI button
   - Session persists across page reloads via localStorage

## Running the Web Interface

To run the custom web interface:

```bash
make run-web-custom
```

This will:
1. Install necessary dependencies
2. Start the FastAPI server with auto-reload enabled
3. Make the interface available at http://localhost:8000

## Implementation Details

### WebSocket vs. HTTP

The implementation supports both WebSocket and HTTP communication:
- WebSocket is used for real-time chat experience
- HTTP fallback is available if WebSocket connection fails

### Memory Management

Agent instances are managed by the `SessionManager` which:
- Creates new agent instances for new sessions
- Reuses existing agent instances for returning users
- Handles agent memory and conversation state

### Security Considerations

- CORS is configured to allow secure cross-origin requests
- Session IDs are generated using UUIDs for uniqueness
- Input validation is performed on all API endpoints

## Future Enhancements

Potential improvements for the web interface:

1. **Authentication**: Add user authentication for persistent user profiles
2. **File Uploads**: Support for file uploads to interact with documents
3. **Tool Visualization**: Visual indicators for when tools are being used
4. **Streaming Responses**: Implement streaming for faster perceived response times
5. **More UI Controls**: Additional controls for agent configuration

## Comparison with ADK Web

While the Google ADK includes a built-in web interface (`adk web`), this custom implementation provides:

1. **Greater Flexibility**: Full control over the UI and UX
2. **WebSocket Support**: Real-time communication vs. polling
3. **Custom Session Management**: More control over how sessions are managed
4. **Modern UI**: A more polished, responsive user interface
5. **Integration Options**: Easier to integrate with other services and APIs