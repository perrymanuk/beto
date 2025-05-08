# Bulletproof chat persistence: FastAPI + WebSockets implementation guide

Chat applications face a common challenge: when users reload the page, their frontend state disappears while the backend maintains conversation context. This comprehensive guide addresses implementing robust chat session persistence for FastAPI WebSocket applications, with a special focus on Google's ADK 0.4.0 and InMemorySessionService.

## The persistence challenge solved

FastAPI WebSocket chat applications need a dual-sided persistence strategy. Your backend already maintains state with ADK's InMemorySessionService, but the frontend loses everything on reload. The solution combines efficient client-side storage with robust reconnection patterns and server synchronization. By implementing the approaches in this guide, your users will maintain their complete chat history and session state even after browser reloads, crashes, or network interruptions.

This implementation approach handles the critical hand-shake between localStorage/sessionStorage on the frontend and your existing FastAPI + ADK backend, ensuring continuous session persistence across the entire application lifecycle.

## Frontend persistence with localStorage/sessionStorage

The browser's Web Storage API offers two main options for persisting chat data:

```javascript
// Store messages in localStorage (persists across browser sessions)
function storeChat(chatId, messages) {
  localStorage.setItem(`chat_${chatId}`, JSON.stringify(messages));
}

// Or use sessionStorage (cleared when the page session ends)
function storeSessionChat(chatId, messages) {
  sessionStorage.setItem(`chat_${chatId}`, JSON.stringify(messages));
}
```

### Efficient message storage structure

Use a lean data structure to maximize storage efficiency:

```javascript
// Define message format
const message = {
  id: "msg-123456",         // Unique identifier
  text: "Hello world!",      // Message content
  sender: "user123",        // User identifier 
  timestamp: 1714497284582, // Milliseconds since epoch
  status: "delivered"       // Message status
};

// Store messages array
const storeMessages = (chatId, messages) => {
  localStorage.setItem(`chat_${chatId}`, JSON.stringify(messages));
};

// Retrieve messages
const getMessages = (chatId) => {
  const stored = localStorage.setItem(`chat_${chatId}`);
  return stored ? JSON.parse(stored) : [];
};
```

### Implementing a complete chat persistence class

This class handles all aspects of frontend chat persistence:

```javascript
class ChatPersistence {
  constructor(options = {}) {
    this.maxMessagesPerChat = options.maxMessagesPerChat || 100;
    this.storagePrefix = options.storagePrefix || 'chat_';
    this.useSessionOnly = options.useSessionOnly || false;
    this.messageCache = {}; // In-memory cache
    this.saveBatchTimeout = null;
    
    // Load active chat on initialization
    this.loadActiveChat();
    
    // Listen for storage events from other tabs
    window.addEventListener('storage', this.handleStorageEvent.bind(this));
  }
  
  // Get the appropriate storage object
  getStorage() {
    return this.useSessionOnly ? sessionStorage : localStorage;
  }
  
  // Save messages with debounced writes to improve performance
  saveMessages(chatId, messages) {
    if (!chatId || !Array.isArray(messages)) return false;
    
    // Update in-memory cache first
    this.messageCache[chatId] = messages.slice(-this.maxMessagesPerChat);
    
    // Batch save to storage
    clearTimeout(this.saveBatchTimeout);
    this.saveBatchTimeout = setTimeout(() => {
      try {
        const storage = this.getStorage();
        const key = `${this.storagePrefix}${chatId}`;
        storage.setItem(key, JSON.stringify(this.messageCache[chatId]));
        return true;
      } catch (e) {
        if (this.isQuotaExceeded(e)) {
          // Try to free space and retry
          this.cleanupOldData();
          try {
            const storage = this.getStorage();
            storage.setItem(key, JSON.stringify(this.messageCache[chatId]));
            return true;
          } catch (e2) {
            console.error('Failed to save chat history even after cleanup');
            // Fall back to session storage
            this.useSessionOnly = true;
            return this.saveMessages(chatId, messages);
          }
        }
        return false;
      }
    }, 300);
    
    return true;
  }
  
  // Get messages for a specific chat
  getMessages(chatId) {
    if (!chatId) return [];
    
    // Check in-memory cache first
    if (this.messageCache[chatId]) {
      return [...this.messageCache[chatId]];
    }
    
    // Try to load from storage
    try {
      const storage = this.getStorage();
      const key = `${this.storagePrefix}${chatId}`;
      const data = storage.getItem(key);
      
      if (data) {
        const messages = JSON.parse(data);
        // Validate and cache
        this.messageCache[chatId] = this.validateMessages(messages);
        return [...this.messageCache[chatId]];
      }
    } catch (e) {
      console.error('Error loading chat data', e);
    }
    
    return [];
  }

  // Additional methods omitted for brevity
  // (See full implementation in source code)
}
```

## Synchronizing frontend with backend state

When a user reloads the page, you need to reconcile the browser-stored chat history with the server's state. This synchronization involves three key steps:

### 1. Generate and maintain a persistent session ID

```javascript
// Create or retrieve a persistent session ID
function getSessionId() {
  let sessionId = localStorage.getItem('websocket_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID ? crypto.randomUUID() : generateUUID();
    localStorage.setItem('websocket_session_id', sessionId);
  }
  return sessionId;
}

// Fallback UUID generator
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}
```

### 2. Request latest messages on reconnection

When the WebSocket reconnects, request messages since the last known message:

```javascript
// Connect to WebSocket server
function connectWebSocket(sessionId) {
  const socket = new WebSocket(`wss://your-server.com/ws/${sessionId}`);
  
  socket.onopen = () => {
    console.log('WebSocket connected');
    
    // Get local messages
    const messages = chatPersistence.getMessages(sessionId);
    
    // Request messages since the latest local message
    if (messages.length > 0) {
      const lastMessageId = messages[messages.length - 1].id;
      const lastTimestamp = messages[messages.length - 1].timestamp;
      
      socket.send(JSON.stringify({
        type: 'sync_request',
        lastMessageId: lastMessageId,
        timestamp: lastTimestamp
      }));
    } else {
      // No local messages, request full history
      socket.send(JSON.stringify({
        type: 'history_request',
        limit: 50  // Request last 50 messages
      }));
    }
  };
  
  return socket;
}
```

### 3. Merge server and local messages

When the server sends history, merge it with local messages to create a complete view:

```javascript
// Merge local and server messages
function mergeMessages(localMessages, serverMessages) {
  // Create a map of existing messages by ID
  const messageMap = new Map();
  localMessages.forEach(msg => {
    messageMap.set(msg.id, msg);
  });
  
  // Add new messages, updating existing ones if needed
  serverMessages.forEach(msg => {
    // Server message takes precedence if it exists in both
    messageMap.set(msg.id, msg);
  });
  
  // Convert back to array and sort by timestamp
  return Array.from(messageMap.values())
    .sort((a, b) => a.timestamp - b.timestamp);
}

// Handle incoming server messages
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'history' || data.type === 'sync_response') {
    // Merge with local messages
    const mergedMessages = mergeMessages(
      chatPersistence.getMessages(sessionId),
      data.messages
    );
    
    // Update local storage
    chatPersistence.saveMessages(sessionId, mergedMessages);
    
    // Update UI
    renderChatMessages(mergedMessages);
  } else if (data.type === 'message') {
    // Add single new message
    const messages = chatPersistence.getMessages(sessionId);
    messages.push(data.message);
    chatPersistence.saveMessages(sessionId, messages);
    
    // Update UI with just the new message
    appendChatMessage(data.message);
  }
};
```

## Handling WebSocket reconnections with persistent session IDs

Reliable WebSocket connections require robust reconnection strategies with exponential backoff:

```javascript
class WebSocketManager {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.initialReconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.sessionId = this.getOrCreateSessionId();
    this.messageCallbacks = [];
    this.stateCallbacks = [];
    this.connected = false;
    this.pendingMessages = [];
    
    // Connect immediately
    this.connect();
  }
  
  getOrCreateSessionId() {
    let sessionId = localStorage.getItem('websocket_session_id');
    if (!sessionId) {
      sessionId = this.generateUUID();
      localStorage.setItem('websocket_session_id', sessionId);
    }
    return sessionId;
  }
  
  connect() {
    if (this.socket) {
      this.socket.close();
    }
    
    this.socket = new WebSocket(`${this.baseUrl}/ws/${this.sessionId}`);
    
    this.socket.onopen = () => {
      console.log('Connected to WebSocket server');
      this.connected = true;
      this.reconnectAttempts = 0;
      
      // Send any pending messages
      while (this.pendingMessages.length > 0) {
        const msg = this.pendingMessages.shift();
        this.sendMessage(msg);
      }
      
      // Notify state change
      this.notifyStateChange({ connected: true });
    };
    
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Handle special message types
      if (data.type === 'reconnect_state') {
        this.notifyStateChange({ 
          reconnected: true, 
          state: data.data 
        });
      } else {
        this.notifyMessage(data);
      }
    };
    
    this.socket.onclose = () => {
      this.connected = false;
      this.notifyStateChange({ connected: false });
      
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = this.calculateReconnectDelay();
        console.log(`Connection closed. Reconnecting in ${delay}ms...`);
        
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, delay);
      } else {
        console.error('Max reconnection attempts reached');
      }
    };
  }
  
  calculateReconnectDelay() {
    // Exponential backoff with jitter
    const baseDelay = Math.min(
      this.maxReconnectDelay,
      this.initialReconnectDelay * Math.pow(2, this.reconnectAttempts)
    );
    // Add up to 30% jitter
    return baseDelay + (Math.random() * 0.3 * baseDelay);
  }
  
  // Additional methods omitted for brevity
}
```

### Implementing heartbeat for connection monitoring

Add a heartbeat mechanism to detect silent disconnections:

```javascript
class HeartbeatMonitor {
  constructor(websocket, intervalMs = 30000, timeoutMs = 5000) {
    this.websocket = websocket;
    this.intervalMs = intervalMs;
    this.timeoutMs = timeoutMs;
    this.timeoutId = null;
    this.intervalId = null;
    this.missedHeartbeats = 0;
    this.maxMissedHeartbeats = 3;
  }
  
  start() {
    this.intervalId = setInterval(() => this.sendHeartbeat(), this.intervalMs);
    this.websocket.addEventListener('message', this.handleMessage.bind(this));
  }
  
  stop() {
    clearInterval(this.intervalId);
    clearTimeout(this.timeoutId);
  }
  
  sendHeartbeat() {
    if (this.websocket.readyState === WebSocket.OPEN) {
      this.timeoutId = setTimeout(() => {
        this.missedHeartbeats++;
        if (this.missedHeartbeats >= this.maxMissedHeartbeats) {
          console.error('Too many missed heartbeats, closing connection');
          this.websocket.close();
        }
      }, this.timeoutMs);
      
      this.websocket.send(JSON.stringify({ type: 'heartbeat' }));
    }
  }
  
  handleMessage(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'heartbeat') {
      clearTimeout(this.timeoutId);
      this.missedHeartbeats = 0;
    }
  }
}
```

## FastAPI backend implementation for chat history persistence 

On the server side, implement these key components to support frontend persistence:

### Connection manager with session tracking

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import json
import asyncio
import time
import uuid

app = FastAPI()

# In-memory session store
session_states: Dict[str, Dict[str, Any]] = {}
# Track disconnection times for cleanup
session_disconnect_times: Dict[str, float] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Clear disconnection time if exists
        if session_id in session_disconnect_times:
            del session_disconnect_times[session_id]
        
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            self.active_connections.pop(session_id)
            # Record disconnection time for potential cleanup
            session_disconnect_times[session_id] = time.time()
            
    async def send_personal_message(self, message: Any, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

manager = ConnectionManager()
```

### Main WebSocket endpoint with ADK integration

```python
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event, EventActions

# Initialize session service
session_service = InMemorySessionService()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    
    try:
        # Get or create session with ADK
        sessions = session_service.list_sessions(
            app_name="chat_app",
            user_id=session_id
        )
        
        if sessions:
            session = sessions[0]
        else:
            session = session_service.create_session(
                app_name="chat_app",
                user_id=session_id,
                session_id=session_id,
                state={"connected": True}
            )
        
        # Send current state/history to client for reconnection
        await send_session_history(websocket, session)
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                # Store message in session
                content = data.get("content", "")
                message_id = str(uuid.uuid4())
                
                # Update ADK session with new message
                session_service.append_event(
                    app_name="chat_app",
                    user_id=session_id,
                    session_id=session.id,
                    event=Event(
                        id=message_id,
                        author="user",
                        content={"text": content}
                    ),
                    actions=EventActions(
                        state_delta={
                            "last_message_id": message_id,
                            "last_activity": time.time()
                        }
                    )
                )
                
                # Broadcast to other clients if needed
                # ...
                
            elif data.get("type") == "sync_request":
                # Client is requesting messages since a specific point
                last_message_id = data.get("lastMessageId")
                await send_messages_since(websocket, session, last_message_id)
                
            elif data.get("type") == "history_request":
                # Client is requesting chat history
                limit = data.get("limit", 50)
                await send_session_history(websocket, session, limit)
                
            elif data.get("type") == "heartbeat":
                # Respond to heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"Client disconnected: {session_id}")
        
        # Update session state to disconnected
        session_service.append_event(
            app_name="chat_app",
            user_id=session_id,
            session_id=session.id,
            event=Event(
                author="system",
                content={"text": "Disconnected"}
            ),
            actions=EventActions(
                state_delta={"connected": False}
            )
        )

async def send_session_history(websocket: WebSocket, session, limit=50):
    """Extract and send message history from ADK session"""
    if not hasattr(session, 'events') or not session.events:
        await websocket.send_json({
            "type": "history",
            "messages": []
        })
        return
    
    # Extract messages from session events
    messages = []
    for event in session.events[-limit:]:
        if hasattr(event, 'content') and event.content:
            message = {
                "id": event.id,
                "author": event.author,
                "timestamp": getattr(event, 'timestamp', time.time()),
                "content": event.content
            }
            messages.append(message)
    
    await websocket.send_json({
        "type": "history",
        "messages": messages
    })

async def send_messages_since(websocket: WebSocket, session, last_message_id):
    """Send messages since a specific message ID"""
    if not hasattr(session, 'events') or not session.events:
        await websocket.send_json({
            "type": "sync_response",
            "messages": []
        })
        return
    
    # Find index of the last known message
    last_index = -1
    for i, event in enumerate(session.events):
        if event.id == last_message_id:
            last_index = i
            break
    
    # Extract messages after the last known one
    messages = []
    if last_index >= 0 and last_index < len(session.events) - 1:
        for event in session.events[last_index + 1:]:
            if hasattr(event, 'content') and event.content:
                message = {
                    "id": event.id,
                    "author": event.author,
                    "timestamp": getattr(event, 'timestamp', time.time()),
                    "content": event.content
                }
                messages.append(message)
    
    await websocket.send_json({
        "type": "sync_response",
        "messages": messages
    })
```

### API endpoint for retrieving chat history

Add a REST endpoint for initial history retrieval:

```python
@app.get("/api/chat/{session_id}/history")
async def get_chat_history(session_id: str, limit: int = 50):
    """Retrieve chat history for a specific session"""
    try:
        sessions = session_service.list_sessions(
            app_name="chat_app",
            user_id=session_id
        )
        
        if not sessions:
            return {"messages": []}
        
        session = sessions[0]
        
        # Extract messages from session events
        messages = []
        if hasattr(session, 'events') and session.events:
            for event in session.events[-limit:]:
                if hasattr(event, 'content') and event.content:
                    message = {
                        "id": event.id,
                        "author": event.author,
                        "timestamp": getattr(event, 'timestamp', time.time()),
                        "content": event.content
                    }
                    messages.append(message)
        
        return {"messages": messages}
    except Exception as e:
        return {"error": str(e), "messages": []}
```

## Complete implementation example

Here's how to combine all components into a working implementation:

### Frontend code (complete example)

```javascript
// main.js
class ChatApp {
  constructor(serverUrl) {
    this.serverUrl = serverUrl;
    this.chatPersistence = new ChatPersistence({
      maxMessagesPerChat: 200
    });
    this.websocketManager = new WebSocketManager(serverUrl);
    this.heartbeatMonitor = null;
    this.sessionId = this.getOrCreateSessionId();
    this.setupEventListeners();
    this.initialize();
  }
  
  getOrCreateSessionId() {
    let sessionId = localStorage.getItem('websocket_session_id');
    if (!sessionId) {
      sessionId = crypto.randomUUID ? crypto.randomUUID() : this.generateUUID();
      localStorage.setItem('websocket_session_id', sessionId);
    }
    return sessionId;
  }
  
  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  
  initialize() {
    // Try to load messages from local storage first
    const messages = this.chatPersistence.getMessages(this.sessionId);
    if (messages.length > 0) {
      this.renderChatMessages(messages);
    }
    
    // Then connect to server for latest updates
    this.connectWebSocket();
  }
  
  connectWebSocket() {
    this.websocket = new WebSocket(`${this.serverUrl}/ws/${this.sessionId}`);
    
    this.websocket.onopen = () => {
      console.log('WebSocket connected');
      
      // Setup heartbeat monitoring
      this.heartbeatMonitor = new HeartbeatMonitor(this.websocket);
      this.heartbeatMonitor.start();
      
      // Request sync with server if we have local messages
      const messages = this.chatPersistence.getMessages(this.sessionId);
      if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        this.websocket.send(JSON.stringify({
          type: 'sync_request',
          lastMessageId: lastMessage.id,
          timestamp: lastMessage.timestamp
        }));
      } else {
        // Otherwise request full history
        this.websocket.send(JSON.stringify({
          type: 'history_request',
          limit: 50
        }));
      }
    };
    
    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'history' || data.type === 'sync_response') {
        // Merge with local messages
        const localMessages = this.chatPersistence.getMessages(this.sessionId);
        const mergedMessages = this.mergeMessages(localMessages, data.messages);
        
        // Update local storage
        this.chatPersistence.saveMessages(this.sessionId, mergedMessages);
        
        // Update UI
        this.renderChatMessages(mergedMessages);
      } else if (data.type === 'message') {
        // Add single new message
        const messages = this.chatPersistence.getMessages(this.sessionId);
        messages.push(data.message);
        this.chatPersistence.saveMessages(this.sessionId, messages);
        
        // Update UI with just the new message
        this.appendChatMessage(data.message);
      }
    };
    
    this.websocket.onclose = () => {
      console.log('WebSocket connection closed');
      if (this.heartbeatMonitor) {
        this.heartbeatMonitor.stop();
      }
      
      // Implement reconnection logic here
      setTimeout(() => this.connectWebSocket(), 5000);
    };
    
    this.websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  mergeMessages(localMessages, serverMessages) {
    const messageMap = new Map();
    
    // Add local messages to map
    localMessages.forEach(msg => {
      messageMap.set(msg.id, msg);
    });
    
    // Add/update with server messages
    serverMessages.forEach(msg => {
      messageMap.set(msg.id, msg);
    });
    
    // Convert to array and sort by timestamp
    return Array.from(messageMap.values())
      .sort((a, b) => a.timestamp - b.timestamp);
  }
  
  sendMessage(content) {
    if (!content.trim()) return;
    
    // Create message object
    const message = {
      id: crypto.randomUUID ? crypto.randomUUID() : this.generateUUID(),
      content: content,
      author: 'user',
      timestamp: Date.now()
    };
    
    // Add to local storage immediately for responsive UI
    const messages = this.chatPersistence.getMessages(this.sessionId);
    messages.push(message);
    this.chatPersistence.saveMessages(this.sessionId, messages);
    
    // Append to UI
    this.appendChatMessage(message);
    
    // Send to server if connected
    if (this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify({
        type: 'message',
        content: content
      }));
    }
  }
  
  // UI methods omitted for brevity
  // ...
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  const app = new ChatApp('wss://your-server.com');
});
```

### Backend code (complete example)

```python
# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import json
import asyncio
import time
import uuid
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event, EventActions

app = FastAPI()

# Initialize ADK session service
session_service = InMemorySessionService()

# Connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            self.active_connections.pop(session_id)

manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    
    try:
        # Get or create session with ADK
        try:
            session = session_service.get_session(
                app_name="chat_app",
                user_id=session_id,
                session_id=session_id
            )
        except:
            session = session_service.create_session(
                app_name="chat_app",
                user_id=session_id,
                session_id=session_id,
                state={"connected": True}
            )
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                # Handle new message
                content = data.get("content", "")
                message_id = str(uuid.uuid4())
                timestamp = time.time()
                
                # Create event in ADK session
                session_service.append_event(
                    app_name="chat_app",
                    user_id=session_id,
                    session_id=session.id,
                    event=Event(
                        id=message_id,
                        author="user",
                        content={"parts": [{"text": content}]}
                    ),
                    actions=EventActions(
                        state_delta={
                            "last_message_id": message_id,
                            "last_activity": timestamp
                        }
                    )
                )
                
                # Get updated session
                session = session_service.get_session(
                    app_name="chat_app",
                    user_id=session_id,
                    session_id=session.id
                )
                
                # Echo message back to confirm receipt
                await websocket.send_json({
                    "type": "message",
                    "message": {
                        "id": message_id,
                        "content": content,
                        "author": "user",
                        "timestamp": timestamp * 1000  # Convert to JS timestamp
                    }
                })
                
            elif data.get("type") == "sync_request":
                # Client requesting messages since last_message_id
                last_message_id = data.get("lastMessageId")
                await send_messages_since(websocket, session, last_message_id)
                
            elif data.get("type") == "history_request":
                # Client requesting full/partial history
                limit = data.get("limit", 50)
                await send_session_history(websocket, session, limit)
                
            elif data.get("type") == "heartbeat":
                # Respond to heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"Client disconnected: {session_id}")
        
        # Update session state
        try:
            session_service.append_event(
                app_name="chat_app",
                user_id=session_id,
                session_id=session.id,
                event=Event(
                    author="system",
                    content={"parts": [{"text": "Disconnected"}]}
                ),
                actions=EventActions(
                    state_delta={"connected": False}
                )
            )
        except Exception as e:
            print(f"Error updating session state: {e}")

async def send_session_history(websocket: WebSocket, session, limit=50):
    """Send chat history from session"""
    messages = extract_messages_from_session(session, limit)
    
    await websocket.send_json({
        "type": "history",
        "messages": messages
    })

async def send_messages_since(websocket: WebSocket, session, last_message_id):
    """Send messages since a specific message ID"""
    # Extract all messages first
    all_messages = extract_messages_from_session(session)
    
    # Find the index of the last known message
    last_index = -1
    for i, msg in enumerate(all_messages):
        if msg["id"] == last_message_id:
            last_index = i
            break
    
    # Get messages after that index
    new_messages = all_messages[last_index+1:] if last_index >= 0 else all_messages
    
    await websocket.send_json({
        "type": "sync_response",
        "messages": new_messages
    })

def extract_messages_from_session(session, limit=None):
    """Helper to extract messages from ADK session events"""
    messages = []
    
    if hasattr(session, 'events') and session.events:
        events = session.events[-limit:] if limit else session.events
        
        for event in events:
            if hasattr(event, 'content') and event.content:
                # Extract text content
                text_content = ""
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text'):
                            text_content += part.text
                
                message = {
                    "id": event.id,
                    "author": event.author,
                    "content": text_content,
                    "timestamp": int(getattr(event, 'timestamp', time.time()) * 1000)  # Convert to JS timestamp
                }
                messages.append(message)
    
    return messages

# Run with: uvicorn main:app --reload
```

## Conclusion

Implementing chat session persistence in FastAPI WebSocket applications requires coordinated frontend and backend strategies. By using localStorage for client-side persistence, maintaining persistent session IDs, implementing robust reconnection logic, and integrating with Google's ADK on the backend, you can create a seamless chat experience that survives page reloads.

The techniques in this guide directly address the challenge where "the backend state persists but the frontend loses state on page reload" by implementing bidirectional synchronization between browser storage and server-side sessions. This approach works well with FastAPI's WebSocket capabilities and the InMemorySessionService from Google's ADK, creating a comprehensive solution for persistent chat applications.
