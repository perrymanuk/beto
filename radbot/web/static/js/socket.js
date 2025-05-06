/**
 * WebSocket management module for RadBot UI
 */

// WebSocket instance
let socket = null;
let socketConnected = false;

// Initialize WebSocket connection
export function initSocket(sessionId) {
    console.log('Initializing WebSocket connection');
    
    connectWebSocket(sessionId);
    
    return {
        socket,
        socketConnected,
        send: (data) => {
            if (socket && socketConnected) {
                socket.send(data);
            } else {
                console.error('Cannot send message - WebSocket not connected');
            }
        }
    };
}

// Connect to WebSocket server
function connectWebSocket(sessionId) {
    try {
        socket = new WebSocket(`ws://${window.location.host}/ws/${sessionId}`);
        
        socket.onopen = () => {
            console.log('WebSocket connected');
            socketConnected = true;
            window.statusUtils.setStatus('ready');
        };
        
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'message') {
                // Check if the message includes agent information
                let agentName = window.state.currentAgentName;
                if (data.agent) {
                    agentName = data.agent;
                    // Update the global state if the agent has changed
                    if (agentName.toUpperCase() !== window.state.currentAgentName) {
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
                                
                                // Update the agent status using the dedicated function
                                window.statusUtils.updateAgentStatus(newAgent);
                                
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
                                window.statusUtils.updateAgentStatus(agentName);
                            }
                            
                            // Add message to chat with the specific agent name
                            window.chatModule.addMessage('assistant', event.text, agentName);
                            window.chatModule.scrollToBottom();
                        }
                    });
                }
                
                // Pass to event handler
                handleEvents(data.content);
            } else if (data.type === 'tasks') {
                // Process incoming tasks
                console.log('Received tasks data:', data.content);
                handleTasks(data.content);
            }
        };
        
        socket.onclose = () => {
            console.log('WebSocket disconnected');
            socketConnected = false;
            window.statusUtils.setStatus('disconnected');
            
            // Attempt to reconnect after a delay
            setTimeout(() => {
                connectWebSocket(sessionId);
            }, 3000);
        };
        
        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            socketConnected = false;
            window.statusUtils.setStatus('error');
        };
    } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        window.statusUtils.setStatus('error');
    }
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