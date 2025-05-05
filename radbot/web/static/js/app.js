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

// State
let sessionId = localStorage.getItem('radbot_session_id') || null;
let socket = null;
let socketConnected = false;

// Initialize
function init() {
    // Create session ID if not exists
    if (!sessionId) {
        sessionId = generateUUID();
        localStorage.setItem('radbot_session_id', sessionId);
    }
    
    connectWebSocket();
    
    // Event listeners
    chatInput.addEventListener('keydown', handleInputKeydown);
    sendButton.addEventListener('click', sendMessage);
    resetButton.addEventListener('click', resetConversation);
    
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

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', init);