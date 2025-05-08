/**
 * Enhanced WebSocket management module for RadBot UI
 * With persistent connections, reconnection logic, and message queueing
 */

// WebSocket instance
let socket = null;
let socketConnected = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;
const INITIAL_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_DELAY = 30000;
let pendingMessages = [];

/**
 * WebSocketManager class for handling WebSocket connections with reconnection logic
 */
class WebSocketManager {
  constructor(baseUrl, sessionId) {
    this.baseUrl = baseUrl || `ws://${window.location.host}`;
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = MAX_RECONNECT_ATTEMPTS;
    this.initialReconnectDelay = INITIAL_RECONNECT_DELAY;
    this.maxReconnectDelay = MAX_RECONNECT_DELAY;
    this.sessionId = sessionId;
    this.messageCallbacks = [];
    this.stateCallbacks = [];
    this.connected = false;
    this.pendingMessages = [];
    this.heartbeatInterval = null;
    this.missedHeartbeats = 0;
    
    // Connect immediately
    this.connect();
  }
  
  connect() {
    if (this.socket) {
      this.socket.close();
    }
    
    const wsUrl = `${this.baseUrl}/ws/${this.sessionId}`;
    console.log(`Connecting to WebSocket at ${wsUrl}`);
    
    try {
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.connected = true;
        this.reconnectAttempts = 0;
        socketConnected = true;
        window.statusUtils.setStatus('ready');
        
        // Start heartbeat after successful connection
        this.startHeartbeat();
        
        // Send any pending messages
        this.sendPendingMessages();
        
        // Request sync with server for any new messages
        if (window.chatPersistence) {
          const messages = window.chatPersistence.getMessages(this.sessionId);
          if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            console.log('Requesting sync with server since last message:', lastMessage.id);
            
            this.send(JSON.stringify({
              type: 'sync_request',
              lastMessageId: lastMessage.id,
              timestamp: lastMessage.timestamp
            }));
          } else {
            // If no local messages, request limited history
            console.log('No local messages, requesting recent history');
            this.send(JSON.stringify({
              type: 'history_request',
              limit: 50
            }));
          }
        }
      };
      
      this.socket.onmessage = (event) => {
        this.handleMessage(event);
      };
      
      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
        this.connected = false;
        socketConnected = false;
        window.statusUtils.setStatus('disconnected');
        
        // Stop heartbeat on disconnection
        this.stopHeartbeat();
        
        // Attempt to reconnect with exponential backoff
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
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.connected = false;
        socketConnected = false;
        window.statusUtils.setStatus('error');
      };
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      window.statusUtils.setStatus('error');
      
      // Try to reconnect after a delay
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = this.calculateReconnectDelay();
        console.log(`Connection attempt failed. Retrying in ${delay}ms...`);
        
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, delay);
      }
    }
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
  
  send(data) {
    if (this.socket && this.connected) {
      this.socket.send(data);
    } else {
      console.log('WebSocket not connected, queueing message');
      this.pendingMessages.push(data);
    }
  }
  
  sendPendingMessages() {
    if (this.pendingMessages.length > 0) {
      console.log(`Sending ${this.pendingMessages.length} pending messages`);
      
      while (this.pendingMessages.length > 0) {
        const message = this.pendingMessages.shift();
        if (this.socket && this.connected) {
          this.socket.send(message);
        }
      }
    }
  }
  
  startHeartbeat() {
    this.stopHeartbeat(); // Clear any existing interval
    
    // Send heartbeat every 30 seconds
    this.heartbeatInterval = setInterval(() => {
      if (this.connected) {
        // Send heartbeat message
        this.send(JSON.stringify({ type: 'heartbeat' }));
        
        // Increment missed heartbeats counter
        this.missedHeartbeats++;
        
        // If we've missed too many heartbeats, close the connection and reconnect
        if (this.missedHeartbeats >= 3) {
          console.warn('Too many missed heartbeats, closing connection');
          this.stopHeartbeat();
          if (this.socket) {
            this.socket.close();
          }
        }
      }
    }, 30000);
  }
  
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    this.missedHeartbeats = 0;
  }
  
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      // Reset missed heartbeats on any message
      this.missedHeartbeats = 0;
      
      if (data.type === 'heartbeat') {
        // Just handle the heartbeat silently
        console.log('Received heartbeat response');
        return;
      }
      
      if (data.type === 'sync_response' || data.type === 'history') {
        // Handle server providing message history
        console.log(`Received ${data.type} with ${data.messages ? data.messages.length : 0} messages`);
        
        if (data.messages && data.messages.length > 0 && window.chatPersistence) {
          const localMessages = window.chatPersistence.getMessages(this.sessionId);
          
          // Merge server messages with local messages
          if (window.mergeMessages) {
            const mergedMessages = window.mergeMessages(localMessages, data.messages);
            window.chatPersistence.saveMessages(this.sessionId, mergedMessages);
            
            // Refresh the UI if it's a full history update
            if (data.type === 'history') {
              console.log('Refreshing UI with merged messages');
              
              // Clear chat messages
              const chatMessages = window.chatModule.getChatElements().messages;
              if (chatMessages) {
                chatMessages.innerHTML = '';
              }
              
              // Render merged messages
              mergedMessages.forEach(msg => {
                if (msg.role && msg.content) {
                  window.chatModule.addMessage(msg.role, msg.content, msg.agent);
                }
              });
              
              window.chatModule.scrollToBottom();
            }
          }
        }
        return;
      }
      
      if (data.type === 'message') {
        // Check if the message includes agent information
        let agentName = window.state.currentAgentName;
        if (data.agent) {
          agentName = data.agent;
          // Update the global state if the agent has changed
          if (agentName.toUpperCase() !== window.state.currentAgentName) {
            console.log(`Agent changed in message: ${window.state.currentAgentName} → ${agentName.toUpperCase()}`);
            
            // First try to update the model based on the new agent
            if (typeof window.updateModelForCurrentAgent === 'function') {
              // Temporarily set current agent name for model lookup
              const previousAgent = window.state.currentAgentName;
              window.state.currentAgentName = agentName.toUpperCase();
              
              // Update model using the agent name
              window.updateModelForCurrentAgent();
              console.log(`Updated model for agent ${agentName} via updateModelForCurrentAgent`);
              
              // Restore previous agent name since updateAgentStatus will set it properly
              window.state.currentAgentName = previousAgent;
            }
            
            // Now update the agent name
            window.statusUtils.updateAgentStatus(agentName);
          }
        }
        
        window.chatModule.addMessage('assistant', data.content, agentName);
        window.chatModule.scrollToBottom();
      } else if (data.type === 'status') {
        window.statusUtils.handleStatusUpdate(data.content);
      } else if (data.type === 'events') {
        // Process incoming events
        console.log('Received events data:', data.content);
        
        // Process various event types
        if (Array.isArray(data.content)) {
          data.content.forEach(event => {
            // Handle agent transfer events
            if (event.type === 'agent_transfer' || event.category === 'agent_transfer') {
              console.log('Agent transfer event detected:', event);
              
              // Check if the target agent is specified
              if (event.to_agent) {
                const newAgent = event.to_agent;
                console.log(`Agent transfer detected: ${window.state.currentAgentName} → ${newAgent}`);
                
                // IMPORTANT: First update the model before updating the agent status
                // This ensures the model update isn't overridden by updateAgentStatus
                
                // Get model from event details if available
                if (event.details && event.details.model) {
                  window.statusUtils.updateModelStatus(event.details.model);
                  console.log(`Updated model from event details: ${event.details.model}`);
                } 
                // Try to get model from agentModels if available
                else if (window.state.agentModels) {
                  // Convert to lowercase for case-insensitive lookup
                  const agentKey = newAgent.toLowerCase();
                  
                  // Handle 'scout' agent specially since it's stored as scout_agent in backend
                  if (agentKey === 'scout' && window.state.agentModels['scout_agent']) {
                    window.statusUtils.updateModelStatus(window.state.agentModels['scout_agent']);
                    console.log(`Updated model from agentModels for scout: ${window.state.agentModels['scout_agent']}`);
                  }
                  // Try exact match
                  else if (window.state.agentModels[agentKey]) {
                    window.statusUtils.updateModelStatus(window.state.agentModels[agentKey]);
                    console.log(`Updated model from agentModels: ${window.state.agentModels[agentKey]}`);
                  }
                  // Try agent_name format
                  else if (window.state.agentModels[agentKey + '_agent']) {
                    window.statusUtils.updateModelStatus(window.state.agentModels[agentKey + '_agent']);
                    console.log(`Updated model from agentModels with _agent suffix: ${window.state.agentModels[agentKey + '_agent']}`);
                  }
                  // Fallback to updateModelForCurrentAgent
                  else {
                    console.log(`Agent ${agentKey} not found in agentModels, using fallback lookup...`);
                    if (typeof window.updateModelForCurrentAgent === 'function') {
                      // Temporarily set the agent name so updateModelForCurrentAgent works
                      const savedAgent = window.state.currentAgentName;
                      window.state.currentAgentName = newAgent;
                      window.updateModelForCurrentAgent();
                      window.state.currentAgentName = savedAgent; // Restore
                    }
                  }
                }
                // Last resort fallback
                else if (typeof window.updateModelForCurrentAgent === 'function') {
                  // Temporarily set the agent name so updateModelForCurrentAgent works
                  const savedAgent = window.state.currentAgentName;
                  window.state.currentAgentName = newAgent;
                  window.updateModelForCurrentAgent();
                  window.state.currentAgentName = savedAgent; // Restore
                }
                
                // Now update the agent status
                window.statusUtils.updateAgentStatus(newAgent);
                
                // Force an update of the status bar
                if (window.statusUtils.updateStatusBar) {
                  window.statusUtils.updateStatusBar();
                }
                
                // Add a system message to notify the user about the agent change
                window.chatModule.addMessage('system', `Agent switched to: ${newAgent.toUpperCase()}`);
              }
            }
            
            // Process model_response events to display in chat
            if ((event.type === 'model_response' || event.category === 'model_response') && event.text) {
              console.log('Model response event detected with text, adding to chat:', event);
              
              // Check for model information in event details
              if (event.details && event.details.model) {
                // Update model status
                window.statusUtils.updateModelStatus(event.details.model);
              }
              
              // Check if the response indicates a specific agent
              let agentName = window.state.currentAgentName;
              
              // Check all possible places in the event where the agent name might be stored
              if (event.agent_name) {
                agentName = event.agent_name.toUpperCase();
              } else if (event.details && event.details.agent_name) {
                agentName = event.details.agent_name.toUpperCase();
              } else if (event.details && event.details.agent) {
                agentName = event.details.agent.toUpperCase();
              }
              
              // Update the current agent if it has changed
              if (agentName !== window.state.currentAgentName) {
                console.log(`Agent change detected from model_response: ${window.state.currentAgentName} → ${agentName}`);
                
                // If we have model info in the event, use it
                if (event.details && event.details.model) {
                  window.statusUtils.updateModelStatus(event.details.model);
                  console.log(`Updated model from event details: ${event.details.model}`);
                }
                // Otherwise try to update model based on the agent name
                else if (typeof window.updateModelForCurrentAgent === 'function') {
                  // Temporarily set current agent name for model lookup
                  const previousAgent = window.state.currentAgentName;
                  window.state.currentAgentName = agentName;
                  
                  // Update model using the agent name
                  window.updateModelForCurrentAgent();
                  console.log(`Updated model for ${agentName} via updateModelForCurrentAgent`);
                  
                  // Restore previous agent name since updateAgentStatus will set it properly
                  window.state.currentAgentName = previousAgent;
                }
                
                // Now update the agent name
                window.statusUtils.updateAgentStatus(agentName);
                
                // Force a visual refresh of the status bar
                if (window.statusUtils && window.statusUtils.updateStatusBar) {
                  window.statusUtils.updateStatusBar();
                }
              }
              
              // Add message to chat with the specific agent name
              window.chatModule.addMessage('assistant', event.text, agentName);
              window.chatModule.scrollToBottom();
            }
          });
        }
        
        // Pass to event handler if it exists
        if (typeof handleEvents === 'function') {
          handleEvents(data.content);
        }
      } else if (data.type === 'tasks') {
        // Process incoming tasks
        console.log('Received tasks data:', data.content);
        if (typeof handleTasks === 'function') {
          handleTasks(data.content);
        }
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }
}

// Initialize WebSocket connection
export function initSocket(sessionId) {
  console.log('Initializing WebSocket connection with session ID:', sessionId);
  
  // Create a WebSocketManager instance
  const manager = new WebSocketManager(`ws://${window.location.host}`, sessionId);
  
  // Extract socket from manager
  socket = manager.socket;
  
  // Return a simplified interface for backward compatibility
  return {
    socket,
    socketConnected,
    send: (data) => {
      if (manager && typeof data === 'string') {
        manager.send(data);
      } else if (typeof data === 'object') {
        manager.send(JSON.stringify(data));
      } else {
        console.error('Invalid data format for WebSocket send:', data);
      }
    },
    // Expose the manager for advanced usage
    manager
  };
}

// Handle incoming tasks data
function handleTasks(tasksData) {
  if (!tasksData || !Array.isArray(tasksData)) {
    console.error('Invalid tasks data received:', tasksData);
    return;
  }
  
  window.tasks = tasksData;
  
  // Check if tasks view is available before rendering
  if (typeof window.renderTasks === 'function') {
    window.renderTasks();
  }
}

// Handle incoming events data
function handleEvents(eventsData) {
  if (!eventsData || !Array.isArray(eventsData)) {
    console.error('Invalid events data received:', eventsData);
    return;
  }
  
  window.events = eventsData;
  
  // Check if events view is available before rendering
  if (typeof window.renderEvents === 'function') {
    window.renderEvents();
  }
}