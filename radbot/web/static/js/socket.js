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
                window.chatModule.addMessage('assistant', data.content);
                window.chatModule.scrollToBottom();
            } else if (data.type === 'status') {
                window.statusUtils.handleStatusUpdate(data.content);
            } else if (data.type === 'events') {
                // Process incoming events
                console.log('Received events data:', data.content);
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