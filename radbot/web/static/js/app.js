/**
 * RadBot Web Interface Client
 */

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const resetButton = document.getElementById('reset-button');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const eventsPanel = document.getElementById('events-panel');
const toggleEventsButton = document.getElementById('toggle-events-button');
const clearEventsButton = document.getElementById('clear-events-button');
const eventTypeFilter = document.getElementById('event-type-filter');
const eventsContainer = document.getElementById('events-container');
const eventDetails = document.getElementById('event-details');
const eventDetailsContent = document.getElementById('event-details-content');
const closeDetailsButton = document.getElementById('close-details-button');

// State
let sessionId = localStorage.getItem('radbot_session_id') || null;
let socket = null;
let socketConnected = false;
let events = [];
let activeEventId = null;
let eventsPanelVisible = false;

// Initialize
function init() {
    // Create session ID if not exists
    if (!sessionId) {
        sessionId = generateUUID();
        localStorage.setItem('radbot_session_id', sessionId);
    }
    
    // Initialize events panel state
    eventsPanel.classList.add('hidden');
    eventsPanelVisible = false;
    
    connectWebSocket();
    
    // Chat event listeners
    chatInput.addEventListener('keydown', handleInputKeydown);
    sendButton.addEventListener('click', sendMessage);
    resetButton.addEventListener('click', resetConversation);
    
    // Events panel event listeners
    toggleEventsButton.addEventListener('click', toggleEventsPanel);
    clearEventsButton.addEventListener('click', clearEvents);
    eventTypeFilter.addEventListener('change', filterEvents);
    closeDetailsButton.addEventListener('click', closeEventDetails);
    
    // Auto-resize textarea as user types
    chatInput.addEventListener('input', resizeTextarea);
}

// Connect to WebSocket
function connectWebSocket() {
    try {
        socket = new WebSocket(`ws://${window.location.host}/ws/${sessionId}`);
        
        socket.onopen = () => {
            console.log('WebSocket connected');
            socketConnected = true;
            setStatus('ready');
        };
        
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'message') {
                addMessage('assistant', data.content);
                scrollToBottom();
            } else if (data.type === 'status') {
                handleStatusUpdate(data.content);
            } else if (data.type === 'events') {
                // Process incoming events
                handleEvents(data.content);
            }
        };
        
        socket.onclose = () => {
            console.log('WebSocket disconnected');
            socketConnected = false;
            setStatus('disconnected');
            
            // Attempt to reconnect after a delay
            setTimeout(() => {
                connectWebSocket();
            }, 3000);
        };
        
        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            socketConnected = false;
            setStatus('error');
        };
    } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        setStatus('error');
    }
}

// Send message via WebSocket
function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    if (socketConnected) {
        // Send via WebSocket
        socket.send(JSON.stringify({
            message: message
        }));
        
        // Add user message to UI
        addMessage('user', message);
        
        // Clear input
        chatInput.value = '';
        resizeTextarea();
        
        // Set status to indicate processing
        setStatus('thinking');
    } else {
        // Fallback to REST API if WebSocket is not connected
        sendMessageREST(message);
    }
    
    scrollToBottom();
}

// Send message via REST API (fallback)
async function sendMessageREST(message) {
    setStatus('thinking');
    
    // Add user message to UI
    addMessage('user', message);
    
    try {
        const formData = new FormData();
        formData.append('message', message);
        formData.append('session_id', sessionId);
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add assistant message to UI
        addMessage('assistant', data.response);
        
        // Clear input
        chatInput.value = '';
        resizeTextarea();
        
        setStatus('ready');
    } catch (error) {
        console.error('Error sending message:', error);
        setStatus('error');
        addMessage('system', 'Error: Could not send message. Please try again later.');
    }
    
    scrollToBottom();
}

// Add a message to the chat UI
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Add timestamp for messages
    const timestamp = new Date().toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    
    // Use marked.js to render markdown
    contentDiv.innerHTML = marked.parse(content);
    
    // For system messages, add animations to simulate terminal loading
    if (role === 'system') {
        messageDiv.classList.add('system-message');
        
        // Add a small delay before showing the message
        setTimeout(() => {
            messageDiv.style.opacity = "1";
        }, 100);
    }
    
    // For assistant messages, simulate typing effect with the cursor
    if (role === 'assistant') {
        // Add typing cursor animation to the last message
        const messages = document.querySelectorAll('.message.assistant');
        messages.forEach(msg => {
            const lastPara = msg.querySelector('.message-content p:last-child');
            if (lastPara && lastPara.classList.contains('with-cursor')) {
                lastPara.classList.remove('with-cursor');
            }
        });
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
}

// Handle status updates
function handleStatusUpdate(status) {
    setStatus(status);
}

// Set the UI status indicator
function setStatus(status) {
    statusIndicator.className = 'status-indicator';
    statusIndicator.classList.add(status);
    
    const timestamp = new Date().toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    
    switch (status) {
        case 'ready':
            statusText.innerHTML = `system: online | time: ${timestamp} | memory: 64mb | connection: active`;
            sendButton.disabled = false;
            chatInput.disabled = false;
            break;
        case 'thinking':
            statusText.innerHTML = `system: processing | time: ${timestamp} | cpu: 99% | please wait...`;
            sendButton.disabled = true;
            break;
        case 'disconnected':
            statusText.innerHTML = `system: error | time: ${timestamp} | connection lost | attempting reconnect...`;
            break;
        case 'error':
            statusText.innerHTML = `system: failure | time: ${timestamp} | segmentation fault | refresh required`;
            break;
        default:
            if (status.startsWith('error:')) {
                statusText.innerHTML = `system: error | time: ${timestamp} | errno: ${Math.floor(Math.random() * 255)} | ${status.replace('error:', '')}`;
                sendButton.disabled = false;
                chatInput.disabled = false;
            } else {
                statusText.innerHTML = `system: info | time: ${timestamp} | ${status}`;
            }
    }
}

// Reset the conversation
async function resetConversation() {
    try {
        const response = await fetch(`/api/sessions/${sessionId}/reset`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        // Clear all messages except the first one (welcome message)
        const messages = chatMessages.querySelectorAll('.message');
        
        for (let i = 1; i < messages.length; i++) {
            messages[i].remove();
        }
        
        addMessage('system', 'Session cleared. New terminal started.');
    } catch (error) {
        console.error('Error resetting conversation:', error);
        addMessage('system', 'Error: Could not reset conversation.');
    }
}

// Handle input keydown (send on Enter, new line on Shift+Enter)
function handleInputKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Auto-resize textarea
function resizeTextarea() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
}

// Scroll chat to bottom
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Generate a UUID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Event panel functions
function toggleEventsPanel() {
    eventsPanelVisible = !eventsPanelVisible;
    
    if (eventsPanelVisible) {
        eventsPanel.classList.remove('hidden');
    } else {
        eventsPanel.classList.add('hidden');
    }
}

function clearEvents() {
    events = [];
    renderEvents();
    closeEventDetails();
}

function handleEvents(newEvents) {
    if (Array.isArray(newEvents) && newEvents.length > 0) {
        // Add event IDs if they don't have them
        newEvents.forEach((event, index) => {
            if (!event.id) {
                event.id = `event-${Date.now()}-${index}`;
            }
        });
        
        // Add to events array
        events = events.concat(newEvents);
        
        // Update UI
        renderEvents();
    }
}

function renderEvents() {
    const currentFilter = eventTypeFilter.value;
    const filteredEvents = filterEventsByType(currentFilter);
    
    // Clear container
    eventsContainer.innerHTML = '';
    
    if (filteredEvents.length === 0) {
        eventsContainer.innerHTML = '<div class="event-empty-state">No events recorded yet.</div>';
        return;
    }
    
    // Add events to container
    filteredEvents.forEach(event => {
        const eventElement = createEventElement(event);
        eventsContainer.appendChild(eventElement);
    });
    
    // Scroll to bottom
    eventsContainer.scrollTop = eventsContainer.scrollHeight;
}

function filterEvents() {
    renderEvents();
}

function filterEventsByType(filter) {
    if (filter === 'all') {
        return events;
    }
    
    return events.filter(event => event.type === filter || event.category === filter);
}

function createEventElement(event) {
    const eventElement = document.createElement('div');
    eventElement.className = `event-item ${event.category || 'other'}`;
    eventElement.dataset.eventId = event.id;
    
    // Add event type
    const eventType = document.createElement('div');
    eventType.className = 'event-type';
    eventType.textContent = event.type || 'Unknown';
    eventElement.appendChild(eventType);
    
    // Add timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'event-timestamp';
    timestamp.textContent = event.timestamp || formatTimestamp(new Date());
    eventElement.appendChild(timestamp);
    
    // Add summary
    const summary = document.createElement('div');
    summary.className = 'event-summary';
    summary.textContent = event.summary || (event.category ? `${event.category} event` : 'Event');
    eventElement.appendChild(summary);
    
    // Add click handler
    eventElement.addEventListener('click', () => {
        showEventDetails(event);
        
        // Mark this event as active
        document.querySelectorAll('.event-item.active').forEach(item => {
            item.classList.remove('active');
        });
        eventElement.classList.add('active');
        activeEventId = event.id;
    });
    
    return eventElement;
}

function showEventDetails(event) {
    // Unhide details panel
    eventDetails.classList.remove('hidden');
    
    // Clear existing content
    const detailsContent = document.querySelector('.event-details-content');
    detailsContent.innerHTML = '';
    
    // Create details content
    const detailsHTML = createEventDetailsHTML(event);
    detailsContent.innerHTML = detailsHTML;
}

function closeEventDetails() {
    eventDetails.classList.add('hidden');
    
    // Remove active state from events
    document.querySelectorAll('.event-item.active').forEach(item => {
        item.classList.remove('active');
    });
    activeEventId = null;
}

function createEventDetailsHTML(event) {
    let html = '';
    
    // Event type and category
    html += `<div class="detail-section">
                <h4>Type: <span>${event.type || 'Unknown'}</span></h4>
                ${event.category ? `<h4>Category: <span>${event.category}</span></h4>` : ''}
                <div class="detail-timestamp">${event.timestamp || formatTimestamp(new Date())}</div>
            </div>`;
    
    // Event summary
    if (event.summary) {
        html += `<div class="detail-section">
                    <h4>Summary</h4>
                    <div>${event.summary}</div>
                </div>`;
    }
    
    // Tool call specific details
    if (event.category === 'tool_call') {
        // Tool name
        if (event.tool_name) {
            html += `<div class="detail-section">
                        <h4>Tool Name</h4>
                        <div>${event.tool_name}</div>
                    </div>`;
        }
        
        // Input
        if (event.input) {
            html += `<div class="detail-section">
                        <h4>Input</h4>
                        <pre>${formatJSON(event.input)}</pre>
                    </div>`;
        }
        
        // Output
        if (event.output) {
            html += `<div class="detail-section">
                        <h4>Output</h4>
                        <pre>${formatJSON(event.output)}</pre>
                    </div>`;
        }
    }
    
    // Agent transfer specific details
    if (event.category === 'agent_transfer') {
        // From agent
        if (event.from_agent) {
            html += `<div class="detail-section">
                        <h4>From Agent</h4>
                        <div>${event.from_agent}</div>
                    </div>`;
        }
        
        // To agent
        if (event.to_agent) {
            html += `<div class="detail-section">
                        <h4>To Agent</h4>
                        <div>${event.to_agent}</div>
                    </div>`;
        }
    }
    
    // Planner specific details
    if (event.category === 'planner') {
        // Plan
        if (event.plan) {
            html += `<div class="detail-section">
                        <h4>Plan</h4>
                        <pre>${formatJSON(event.plan)}</pre>
                    </div>`;
        }
        
        // Plan step
        if (event.plan_step) {
            html += `<div class="detail-section">
                        <h4>Plan Step</h4>
                        <pre>${formatJSON(event.plan_step)}</pre>
                    </div>`;
        }
    }
    
    // Model response specific details
    if (event.category === 'model_response') {
        // Text
        if (event.text) {
            html += `<div class="detail-section">
                        <h4>Response Text</h4>
                        <div>${event.text}</div>
                    </div>`;
        }
    }
    
    // Raw details (if available)
    if (event.details) {
        html += `<div class="detail-section">
                    <h4>Raw Details</h4>
                    <pre>${formatJSON(event.details)}</pre>
                </div>`;
    }
    
    return html;
}

function formatJSON(obj) {
    if (typeof obj === 'string') {
        try {
            // Try to parse it as JSON first
            const parsed = JSON.parse(obj);
            return JSON.stringify(parsed, null, 2);
        } catch (e) {
            // If it's not valid JSON, return as is
            return obj;
        }
    }
    
    try {
        return JSON.stringify(obj, null, 2);
    } catch (e) {
        return String(obj);
    }
}

function formatTimestamp(date) {
    return date.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
    });
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', init);