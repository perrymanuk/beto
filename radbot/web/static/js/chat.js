/**
 * Chat functionality module for RadBot UI
 */

// DOM References
let chatMessages;
let chatInput;
let sendButton;
let resetButton;

// Export references to be used by other modules
export function getChatElements() {
    return {
        messages: chatMessages,
        input: chatInput,
        sendButton: sendButton,
        resetButton: resetButton
    };
}

// Initialize chat functionality
export function initChat() {
    console.log('Initializing chat module');
    
    // Initialize DOM references
    chatMessages = document.getElementById('chat-messages');
    chatInput = document.getElementById('chat-input');
    sendButton = document.getElementById('send-button');
    resetButton = document.getElementById('reset-button');
    
    // If any critical elements are missing, return false
    if (!chatInput || !chatMessages) {
        console.log('Critical chat UI elements not found');
        return false;
    }
    
    // Add chat event listeners
    chatInput.addEventListener('keydown', handleInputKeydown);
    
    // Auto-resize textarea as user types
    chatInput.addEventListener('input', function(event) {
        resizeTextarea();
    });
    
    // Set initial compact height
    setTimeout(resizeTextarea, 0);
    
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    if (resetButton) {
        resetButton.addEventListener('click', resetConversation);
    }
    
    return true;
}

// Add a message to the chat UI
export function addMessage(role, content, agentName) {
    // Ensure chatMessages element exists
    if (!chatMessages) {
        chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            console.error('Chat messages container not found, message not added');
            return;
        }
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Note: Emoji conversion now happens right before markdown rendering
    
    // Set custom prompt for assistant messages based on current agent
    if (role === 'assistant') {
        // Allow specifying a custom agent for this message
        const agent = agentName || window.state.currentAgentName;
        
        // Add a custom data attribute for the prompt
        // Use lowercase for the terminal prompt style
        contentDiv.dataset.agentPrompt = `${agent.toLowerCase()}@radbox:~$ `;
        
        // Store the agent name as a data attribute for future reference
        messageDiv.dataset.agent = agent.toUpperCase();
    }
    
    // First convert emoji shortcodes to Unicode emojis
    content = window.emojiUtils.convertEmoji(content);
    
    // Then use marked.js to render markdown with compact options
    if (typeof marked !== 'undefined') {
        // Process content to reduce blank lines for compactness
        content = content.replace(/\n\s*\n/g, '\n');
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }
    
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
    
    // Verify chat messages container exists
    if (!chatMessages) {
        chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            console.error('Chat messages container not found, creating fallback');
            // Create a fallback container if one doesn't exist
            chatMessages = document.createElement('div');
            chatMessages.id = 'chat-messages';
            chatMessages.className = 'chat-messages';
            document.body.appendChild(chatMessages);
        }
    }
    
    // Append the message
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom with a slight delay to ensure DOM updates
    setTimeout(scrollToBottom, 10);
    
    // Also try scrolling after a longer delay just to be sure
    setTimeout(scrollToBottom, 300);
}

// Handle input keydown (send on Enter, new line on Shift+Enter)
function handleInputKeydown(event) {
    // Check if command-suggestions element exists
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    
    // If emoji suggestions are showing, don't send on Enter
    if (event.key === 'Enter' && !event.shiftKey && 
        window.emojiUtils.getSuggestions().length === 0 && 
        (!commandSuggestionsElement || !commandSuggestionsElement.classList.contains('visible'))) {
        event.preventDefault();
        sendMessage();
    }
}

// Send message via WebSocket
export function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Special handler for "scout pls" or "scount pls" message - force agent switch
    if (message.toLowerCase() === 'scout pls' || message.toLowerCase() === 'scount pls') {
        console.log("SCOUT REQUEST DETECTED - Forcing agent switch");
        // Force the agent change
        window.state.currentAgentName = 'SCOUT';
        
        // Update CSS and status
        document.documentElement.style.setProperty('--agent-name', `"${window.state.currentAgentName}"`);
        
        // Direct update of status bar element to ensure it updates
        const agentStatus = document.getElementById('agent-status');
        if (agentStatus) {
            agentStatus.textContent = `AGENT: ${window.state.currentAgentName}`;
            console.log("Directly updated agent status element text: " + agentStatus.textContent);
            
            // Visual feedback for the change
            agentStatus.style.color = 'var(--term-blue)';
            setTimeout(() => {
                agentStatus.style.color = '';
            }, 500);
        } else {
            console.error("Cannot find agent-status element in DOM");
        }
        
        // Update other UI elements
        window.statusUtils.updateClock();
        
        // Add a system message
        addMessage('system', `Agent switched to: ${window.state.currentAgentName}`);
        
        // Force a status update to update all UI elements consistently
        window.statusUtils.setStatus('ready');
    }
    
    // Check if this is a slash command
    if (message.startsWith('/')) {
        window.commandUtils.executeCommand(message);
        chatInput.value = '';
        resizeTextarea();
        return;
    }
    
    // Convert emoji shortcodes to unicode emojis for display, but send original text to server
    const displayMessage = window.emojiUtils.convertEmoji(message);
    
    // Add user message to UI
    addMessage('user', displayMessage);
    
    // Clear input immediately after adding the message to UI
    chatInput.value = '';
    resizeTextarea();
    
    if (window.socket && window.socket.socketConnected) {
        // Send via WebSocket
        window.socket.send(JSON.stringify({
            message: message
        }));
        
        // Set status to indicate processing
        window.statusUtils.setStatus('thinking');
    } else {
        // Fallback to REST API if WebSocket is not connected
        sendMessageREST(message, displayMessage);
    }
    
    // Ensure the agent name is visible in status bar
    const agentStatus = document.getElementById('agent-status');
    if (agentStatus) {
        agentStatus.textContent = `AGENT: ${window.state.currentAgentName.toUpperCase()}`;
    }
    
    scrollToBottom();
}

// Reset the conversation
async function resetConversation() {
    try {
        const response = await fetch(`/api/sessions/${window.state.sessionId}/reset`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        // Clear all messages except the first one (welcome message)
        const messages = chatMessages.querySelectorAll('.message');
        
        for (let i = 1; i < messages.length; i++) {
            messages[i].remove();
        }
        
        // Also clear events
        if (window.events && Array.isArray(window.events)) {
            console.log('Clearing event history');
            window.events = [];
            
            // If events are currently displayed, refresh the view
            const eventsContainer = document.getElementById('events-container');
            if (eventsContainer) {
                console.log('Refreshing events view');
                // If renderEvents is available, call it
                if (typeof window.renderEvents === 'function') {
                    window.renderEvents();
                }
                // Otherwise just clear the container
                else {
                    eventsContainer.innerHTML = '<div class="event-empty-state">No events recorded yet.</div>';
                }
            }
        }
        
        addMessage('system', 'Session cleared. New terminal started.');
    } catch (error) {
        console.error('Error resetting conversation:', error);
        addMessage('system', 'Error: Could not reset conversation.');
    }
}

// Send message via REST API (fallback)
async function sendMessageREST(message, displayMessage) {
    window.statusUtils.setStatus('thinking');
    
    // Note: User message is already added to UI by sendMessage function
    // and input is already cleared before this function is called
    
    try {
        const formData = new FormData();
        formData.append('message', message);
        formData.append('session_id', window.state.sessionId);
        
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
        
        window.statusUtils.setStatus('ready');
    } catch (error) {
        console.error('Error sending message:', error);
        window.statusUtils.setStatus('error');
        addMessage('system', 'Error: Could not send message. Please try again later.');
    }
    
    scrollToBottom();
}

// Resize textarea based on content
export function resizeTextarea() {
    if (!chatInput) return;
    
    // Reset height to auto to correctly calculate new height
    chatInput.style.height = 'auto';
    
    // Limit to max-height defined in CSS
    let newHeight = Math.min(chatInput.scrollHeight, 120);
    
    // Set minimum height
    newHeight = Math.max(newHeight, 30);
    
    chatInput.style.height = newHeight + 'px';
}

// Scroll chat to bottom
export function scrollToBottom() {
    if (!chatMessages) return;
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}