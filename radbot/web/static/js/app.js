/**
 * RadBot Web Interface Client
 */

// DOM Elements
let chatMessages;
let chatInput;
let sendButton;
let resetButton;

// Status Bar Elements
let agentStatus;
let timeStatus;
let connectionStatus;

// Event panel buttons 
let toggleEventsButton;
let toggleTasksButton;

// Emoji Suggestions Element
let emojiSuggestionsElement;

// State
let sessionId = localStorage.getItem('radbot_session_id') || null;
let socket = null;
let socketConnected = false;
let events = [];
let tasks = [];
let projects = [];
let selectedProjects = ['all'];
let selectedStatuses = ['all'];
let currentAgentName = "BETO"; // Track current agent name - use uppercase to match status bar
let isDarkTheme = true; // Always use dark theme
// Hardcode task API settings since settings dialog is removed
let taskApiSettings = {
    endpoint: 'http://localhost:8001',
    apiKey: '',
    defaultProject: ''
};

// Emoji autocomplete state
let emojiSuggestions = [];
let activeSuggestionIndex = -1;
let activeShortcodeStart = -1;
let activeShortcodeEnd = -1;

// Initialize
function init() {
    console.log('Initializing app.js');
    
    // Listen for tiling manager ready event
    document.addEventListener('tiling:ready', () => {
        console.log('Received tiling:ready event, initializing UI');
        initializeUI();
    });
    
    // Listen for layout changes to re-initialize UI elements
    document.addEventListener('layout:changed', () => {
        console.log('Layout changed, reinitializing UI');
        initializeUI();
    });
    
    // As a fallback, also wait a moment to try initialization
    setTimeout(() => {
        if (!chatInput) {
            console.log('Attempting UI initialization via timeout');
            initializeUI();
        }
    }, 300);
    
    // Create session ID if not exists
    if (!sessionId) {
        sessionId = generateUUID();
        localStorage.setItem('radbot_session_id', sessionId);
    }
    
    // Connect to WebSocket immediately
    connectWebSocket();
    
    // Fetch tasks, projects, and events directly from API
    fetchTasks();
    fetchEvents();
}

// Make functions globally available for tiling manager
window.initializeUI = initializeUI;
window.renderTasks = renderTasks;
window.renderEvents = renderEvents;

// Initialize UI elements after DOM is ready
function initializeUI() {
    // Initialize DOM references
    chatMessages = document.getElementById('chat-messages');
    chatInput = document.getElementById('chat-input');
    sendButton = document.getElementById('send-button');
    resetButton = document.getElementById('reset-button');
    
    // Status Bar Elements
    agentStatus = document.getElementById('agent-status');
    timeStatus = document.getElementById('time-status');
    connectionStatus = document.getElementById('connection-status');
    
    // Event panel buttons
    toggleEventsButton = document.getElementById('toggle-events-button');
    toggleTasksButton = document.getElementById('toggle-tasks-button');
    
    // Theme and matrix toggle buttons have been removed
    
    // Emoji suggestions
    emojiSuggestionsElement = document.getElementById('emoji-suggestions');
    
    // If any critical elements are missing, try again in a moment
    if (!chatInput || !chatMessages) {
        console.log('Critical UI elements not found, retrying initialization...');
        setTimeout(initializeUI, 200);
        return;
    }
    
    console.log('UI elements initialized successfully');
    
    // Initialize voice wave animation
    initVoiceWaveAnimation();
    
    // Initialize status bar
    updateStatusBar();
    
    // Start clock
    updateClock();
    setInterval(updateClock, 1000);
    
    // Add chat event listeners (only if elements exist)
    if (chatInput) {
        chatInput.addEventListener('keydown', handleInputKeydown);
        
        // Auto-resize textarea as user types
        chatInput.addEventListener('input', function(event) {
            resizeTextarea();
            handleEmojiAutocomplete(event);
            handleCommandAutocomplete(event);
        });
        
        // Handle keyboard navigation for emoji suggestions
        chatInput.addEventListener('keydown', handleEmojiKeyNavigation);
        
        // Handle keyboard navigation for command suggestions
        chatInput.addEventListener('keydown', handleCommandKeyNavigation);
    }
    
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    if (resetButton) {
        resetButton.addEventListener('click', resetConversation);
    }
    
    // Panel toggle buttons
    if (toggleEventsButton) {
        toggleEventsButton.addEventListener('click', () => {
            document.dispatchEvent(new CustomEvent('command:events'));
        });
    }
    
    if (toggleTasksButton) {
        toggleTasksButton.addEventListener('click', () => {
            document.dispatchEvent(new CustomEvent('command:tasks'));
        });
    }
    
    // Theme and matrix toggle functionality has been removed
    // Always set dark theme
    isDarkTheme = true;
    document.body.classList.remove('light-theme');
    
    // Settings functionality has been removed
    
    // Set up slash commands
    setupSlashCommands();
    
    // Set up filter controls
    setupFilterControls();
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
    
    // Special handler for "scout pls" or "scount pls" message - force agent switch
    if (message.toLowerCase() === 'scout pls' || message.toLowerCase() === 'scount pls') {
        console.log("SCOUT REQUEST DETECTED - Forcing agent switch");
        // Force the agent change
        const previousAgent = currentAgentName;
        currentAgentName = 'SCOUT';
        
        // Update CSS and status
        document.documentElement.style.setProperty('--agent-name', `"${currentAgentName}"`);
        
        // Direct update of status bar element to ensure it updates
        if (agentStatus) {
            agentStatus.textContent = `AGENT: ${currentAgentName}`;
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
        updateClock();
        
        // Add a system message
        addMessage('system', `Agent switched to: ${currentAgentName}`);
        
        // Force a status update to update all UI elements consistently
        setStatus('ready');
    }
    
    // Check if this is a slash command
    if (message.startsWith('/')) {
        executeCommand(message);
        chatInput.value = '';
        resizeTextarea();
        return;
    }
    
    // Convert emoji shortcodes to unicode emojis for display, but send original text to server
    const displayMessage = convertEmoji(message);
    
    if (socketConnected) {
        // Send via WebSocket
        socket.send(JSON.stringify({
            message: message
        }));
        
        // Add user message to UI
        addMessage('user', displayMessage);
        
        // Clear input
        chatInput.value = '';
        resizeTextarea();
        
        // Set status to indicate processing
        setStatus('thinking');
    } else {
        // Fallback to REST API if WebSocket is not connected
        sendMessageREST(message, displayMessage);
    }
    
    // Ensure the agent name is visible in status bar
    if (agentStatus) {
        agentStatus.textContent = `AGENT: ${currentAgentName.toUpperCase()}`;
    }
    
    scrollToBottom();
}

// Send message via REST API (fallback)
async function sendMessageREST(message, displayMessage) {
    setStatus('thinking');
    
    // Add user message to UI (use displayMessage if provided, otherwise use original message)
    addMessage('user', displayMessage || message);
    
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

// Emoji data for autocomplete
const commonEmojis = [
    // Hand gestures and popular emojis
    {shortcode: ':hangloose:', emoji: '🤙', description: 'Hang Loose / Shaka'},
    {shortcode: ':call_me_hand:', emoji: '🤙', description: 'Call Me Hand'},
    {shortcode: ':ok_hand:', emoji: '👌', description: 'OK Hand'},
    {shortcode: ':wave:', emoji: '👋', description: 'Waving Hand'},
    {shortcode: ':raised_hands:', emoji: '🙌', description: 'Raised Hands'},
    {shortcode: ':clap:', emoji: '👏', description: 'Clapping Hands'},
    {shortcode: ':handshake:', emoji: '🤝', description: 'Handshake'},
    {shortcode: ':pray:', emoji: '🙏', description: 'Praying Hands'},
    {shortcode: ':metal:', emoji: '🤘', description: 'Metal / Rock On'},
    {shortcode: ':punch:', emoji: '👊', description: 'Fist Bump'},
    
    // Expressions
    {shortcode: ':smile:', emoji: '😊', description: 'Smile'},
    {shortcode: ':grin:', emoji: '😁', description: 'Grin'},
    {shortcode: ':joy:', emoji: '😂', description: 'Joy'},
    {shortcode: ':laughing:', emoji: '😆', description: 'Laughing'},
    {shortcode: ':rofl:', emoji: '🤣', description: 'ROFL'},
    {shortcode: ':smiley:', emoji: '😃', description: 'Smiley'},
    {shortcode: ':wink:', emoji: '😉', description: 'Wink'},
    {shortcode: ':blush:', emoji: '😊', description: 'Blush'},
    {shortcode: ':thinking:', emoji: '🤔', description: 'Thinking'},
    {shortcode: ':sob:', emoji: '😭', description: 'Crying'},
    {shortcode: ':angry:', emoji: '😠', description: 'Angry'},
    {shortcode: ':sunglasses:', emoji: '😎', description: 'Cool / Sunglasses'},
    {shortcode: ':sweat_smile:', emoji: '😅', description: 'Awkward Smile'},
    {shortcode: ':nerd_face:', emoji: '🤓', description: 'Nerd Face'},
    {shortcode: ':innocent:', emoji: '😇', description: 'Innocent'},
    
    // Objects and miscellaneous
    {shortcode: ':heart:', emoji: '❤️', description: 'Heart'},
    {shortcode: ':+1:', emoji: '👍', description: 'Thumbs Up'},
    {shortcode: ':thumbsup:', emoji: '👍', description: 'Thumbs Up'},
    {shortcode: ':-1:', emoji: '👎', description: 'Thumbs Down'},
    {shortcode: ':thumbsdown:', emoji: '👎', description: 'Thumbs Down'},
    {shortcode: ':tada:', emoji: '🎉', description: 'Celebration'},
    {shortcode: ':rocket:', emoji: '🚀', description: 'Rocket'},
    {shortcode: ':fire:', emoji: '🔥', description: 'Fire'},
    {shortcode: ':boom:', emoji: '💥', description: 'Explosion'},
    {shortcode: ':star:', emoji: '⭐', description: 'Star'},
    {shortcode: ':check:', emoji: '✅', description: 'Check Mark'},
    {shortcode: ':x:', emoji: '❌', description: 'Cross Mark'},
    {shortcode: ':warning:', emoji: '⚠️', description: 'Warning'},
    {shortcode: ':question:', emoji: '❓', description: 'Question'},
    {shortcode: ':zap:', emoji: '⚡', description: 'Lightning'},
    {shortcode: ':bulb:', emoji: '💡', description: 'Light Bulb'},
    {shortcode: ':computer:', emoji: '💻', description: 'Computer'},
    {shortcode: ':gear:', emoji: '⚙️', description: 'Gear'},
    {shortcode: ':eyes:', emoji: '👀', description: 'Eyes'},
    {shortcode: ':brain:', emoji: '🧠', description: 'Brain'},
    {shortcode: ':robot:', emoji: '🤖', description: 'Robot'},
    
    // Development related
    {shortcode: ':bug:', emoji: '🐛', description: 'Bug'},
    {shortcode: ':hammer_and_wrench:', emoji: '🛠️', description: 'Tools'},
    {shortcode: ':lock:', emoji: '🔒', description: 'Lock'},
    {shortcode: ':unlock:', emoji: '🔓', description: 'Unlock'},
    {shortcode: ':key:', emoji: '🔑', description: 'Key'},
    {shortcode: ':mag:', emoji: '🔍', description: 'Magnifying Glass'},
    {shortcode: ':clock:', emoji: '🕒', description: 'Clock'},
    {shortcode: ':hourglass:', emoji: '⌛', description: 'Hourglass'},
    {shortcode: ':pushpin:', emoji: '📌', description: 'Pushpin'},
    {shortcode: ':memo:', emoji: '📝', description: 'Memo'},
    {shortcode: ':book:', emoji: '📚', description: 'Books'},
    {shortcode: ':chart:', emoji: '📊', description: 'Chart'}
];

// Convert emoji shortcodes to emoji characters
function convertEmoji(text) {
    if (typeof joypixels !== 'undefined') {
        // Use joypixels library if available
        return joypixels.shortnameToUnicode(text);
    } else {
        // Fallback with basic emoji mappings
        const emojiMap = {};
        commonEmojis.forEach(item => {
            emojiMap[item.shortcode] = item.emoji;
        });
        
        // Replace shortcodes with emojis
        return text.replace(/:[a-z0-9_+-]+:/g, match => {
            return emojiMap[match] || match;
        });
    }
}

// Add a message to the chat UI
function addMessage(role, content) {
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
    
    // Add timestamp for messages
    const timestamp = new Date().toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    
    // Convert emoji shortcodes to actual emojis
    content = convertEmoji(content);
    
    // Set custom prompt for assistant messages based on current agent
    if (role === 'assistant') {
        // Add a custom data attribute for the prompt
        // Use lowercase for the terminal prompt style
        contentDiv.dataset.agentPrompt = `${currentAgentName.toLowerCase()}@radbox:~$ `;
    }
    
    // Use marked.js to render markdown
    if (typeof marked !== 'undefined') {
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

// Handle status updates
function handleStatusUpdate(status) {
    setStatus(status);
    
    // Ensure agent name is always visible in the status bar
    if (agentStatus) {
        agentStatus.textContent = `AGENT: ${currentAgentName.toUpperCase()}`;
    }
}

// Set the UI status indicator
function setStatus(status) {
    // Update the connection status in the main status bar
    if (connectionStatus) {
        switch (status) {
            case 'ready':
                connectionStatus.textContent = 'CONNECTION: ACTIVE';
                sendButton.disabled = false;
                chatInput.disabled = false;
                break;
            case 'thinking':
                connectionStatus.textContent = 'CONNECTION: PROCESSING...';
                sendButton.disabled = true;
                break;
            case 'disconnected':
                connectionStatus.textContent = 'CONNECTION: LOST';
                if (agentStatus) agentStatus.textContent = 'AGENT: OFFLINE';
                break;
            case 'error':
                connectionStatus.textContent = 'CONNECTION: ERROR - REFRESH REQUIRED';
                break;
            default:
                if (status.startsWith('error:')) {
                    connectionStatus.textContent = `CONNECTION: ERROR - ${status.replace('error:', '')}`;
                    sendButton.disabled = false;
                    chatInput.disabled = false;
                } else {
                    connectionStatus.textContent = `CONNECTION: ${status.toUpperCase()}`;
                }
        }
    }
    
    // Make sure the agent status is up to date, except for disconnected state
    if (status !== 'disconnected' && agentStatus) {
        const displayName = currentAgentName.toUpperCase();
        agentStatus.textContent = `AGENT: ${displayName}`;
        
        // Visual feedback to ensure update is visible
        agentStatus.style.color = 'var(--term-blue)';
        setTimeout(() => {
            agentStatus.style.color = 'var(--term-amber)';
        }, 100);
        
        console.log(`Status bar updated with agent: ${displayName} (from setStatus)`);
    }
    
    // Make sure time is up to date
    updateClock();
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
    // Check if command-suggestions element exists
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    
    // If emoji suggestions are showing, don't send on Enter
    if (event.key === 'Enter' && !event.shiftKey && 
        emojiSuggestions.length === 0 && 
        (!commandSuggestionsElement || !commandSuggestionsElement.classList.contains('visible'))) {
        event.preventDefault();
        sendMessage();
    }
}

// Emoji autocomplete
function handleEmojiAutocomplete(event) {
    const input = chatInput;
    const text = input.value;
    const cursorPosition = input.selectionStart;
    
    // Find if we're inside a potential emoji shortcode
    const colonBefore = text.lastIndexOf(':', cursorPosition);
    
    // If there's no colon before cursor, or there's a completed shortcode, hide suggestions
    if (colonBefore === -1 || text.slice(colonBefore, cursorPosition).includes(' ')) {
        hideEmojiSuggestions();
        return;
    }
    
    // Check if there's a completed emoji shortcode (ending with ':')
    const colonAfter = text.indexOf(':', colonBefore + 1);
    if (colonAfter !== -1 && colonAfter < cursorPosition) {
        hideEmojiSuggestions();
        return;
    }
    
    // Extract the current incomplete shortcode (without the leading ':')
    const shortcodeFragment = text.slice(colonBefore + 1, cursorPosition);
    
    // Store the position for replacement later
    activeShortcodeStart = colonBefore;
    activeShortcodeEnd = cursorPosition;
    
    // Filter emoji suggestions based on the shortcode fragment
    updateEmojiSuggestions(shortcodeFragment);
}

// Update emoji suggestions based on input
function updateEmojiSuggestions(fragment) {
    // Filter emoji list based on the fragment
    emojiSuggestions = commonEmojis
        .filter(emoji => emoji.shortcode.slice(1, -1).toLowerCase().includes(fragment.toLowerCase()))
        .sort((a, b) => {
            // Sort exact matches first, then by starts with, then alphabetically
            const aShortcode = a.shortcode.slice(1, -1).toLowerCase();
            const bShortcode = b.shortcode.slice(1, -1).toLowerCase();
            
            // Exact match gets highest priority
            if (aShortcode === fragment.toLowerCase()) return -1;
            if (bShortcode === fragment.toLowerCase()) return 1;
            
            // Starts with gets next priority
            const aStartsWith = aShortcode.startsWith(fragment.toLowerCase());
            const bStartsWith = bShortcode.startsWith(fragment.toLowerCase());
            
            if (aStartsWith && !bStartsWith) return -1;
            if (!aStartsWith && bStartsWith) return 1;
            
            // Finally sort alphabetically
            return aShortcode.localeCompare(bShortcode);
        })
        .slice(0, 8); // Limit to 8 suggestions for performance
    
    if (emojiSuggestions.length > 0) {
        showEmojiSuggestions();
    } else {
        hideEmojiSuggestions();
    }
}

// Show emoji suggestions
function showEmojiSuggestions() {
    // Check if element exists
    if (!emojiSuggestionsElement) return;
    
    // Clear existing suggestions
    emojiSuggestionsElement.innerHTML = '';
    
    // Create suggestion elements
    emojiSuggestions.forEach((emoji, index) => {
        const item = document.createElement('div');
        item.className = 'emoji-suggestion-item';
        item.dataset.index = index;
        
        const emojiSpan = document.createElement('span');
        emojiSpan.className = 'emoji-suggestion-emoji';
        emojiSpan.textContent = emoji.emoji;
        
        const shortcodeSpan = document.createElement('span');
        shortcodeSpan.className = 'emoji-suggestion-shortcode';
        shortcodeSpan.textContent = emoji.shortcode;
        
        const descriptionSpan = document.createElement('span');
        descriptionSpan.className = 'emoji-suggestion-description';
        descriptionSpan.textContent = emoji.description;
        
        item.appendChild(emojiSpan);
        item.appendChild(shortcodeSpan);
        item.appendChild(descriptionSpan);
        
        // Add click handler
        item.addEventListener('click', () => {
            insertEmojiSuggestion(index);
        });
        
        emojiSuggestionsElement.appendChild(item);
    });
    
    // Reset active suggestion
    activeSuggestionIndex = -1;
    
    // Show suggestions
    emojiSuggestionsElement.classList.remove('hidden');
}

// Hide emoji suggestions
function hideEmojiSuggestions() {
    if (!emojiSuggestionsElement) return;
    
    emojiSuggestionsElement.classList.add('hidden');
    emojiSuggestions = [];
    activeSuggestionIndex = -1;
    activeShortcodeStart = -1;
    activeShortcodeEnd = -1;
}

// Handle keyboard navigation for emoji suggestions
function handleEmojiKeyNavigation(event) {
    // Only process if suggestions are visible and element exists
    if (!emojiSuggestionsElement || emojiSuggestions.length === 0 || emojiSuggestionsElement.classList.contains('hidden')) {
        return;
    }
    
    switch (event.key) {
        case 'ArrowDown':
            // Move selection down
            event.preventDefault();
            activeSuggestionIndex = (activeSuggestionIndex + 1) % emojiSuggestions.length;
            updateActiveSuggestion();
            break;
            
        case 'ArrowUp':
            // Move selection up
            event.preventDefault();
            activeSuggestionIndex = (activeSuggestionIndex - 1 + emojiSuggestions.length) % emojiSuggestions.length;
            updateActiveSuggestion();
            break;
            
        case 'Tab':
        case 'Enter':
            // Insert selected emoji
            if (activeSuggestionIndex >= 0) {
                event.preventDefault();
                insertEmojiSuggestion(activeSuggestionIndex);
            }
            break;
            
        case 'Escape':
            // Close suggestions
            event.preventDefault();
            hideEmojiSuggestions();
            break;
    }
}

// Update active suggestion highlighting
function updateActiveSuggestion() {
    // Check if element exists
    if (!emojiSuggestionsElement) return;
    
    // Remove active class from all items
    const items = emojiSuggestionsElement.querySelectorAll('.emoji-suggestion-item');
    items.forEach(item => item.classList.remove('active'));
    
    // Add active class to selected item
    if (activeSuggestionIndex >= 0 && activeSuggestionIndex < items.length) {
        items[activeSuggestionIndex].classList.add('active');
        
        // Ensure the active item is visible in the scroll area
        const activeItem = items[activeSuggestionIndex];
        const container = emojiSuggestionsElement;
        
        const itemTop = activeItem.offsetTop;
        const itemBottom = itemTop + activeItem.offsetHeight;
        const containerTop = container.scrollTop;
        const containerBottom = containerTop + container.offsetHeight;
        
        if (itemTop < containerTop) {
            container.scrollTop = itemTop;
        } else if (itemBottom > containerBottom) {
            container.scrollTop = itemBottom - container.offsetHeight;
        }
    }
}

// Insert emoji suggestion
function insertEmojiSuggestion(index) {
    if (index >= 0 && index < emojiSuggestions.length && 
        activeShortcodeStart >= 0 && activeShortcodeEnd >= 0) {
        
        const emoji = emojiSuggestions[index];
        const input = chatInput;
        const text = input.value;
        
        // Replace the text from : to cursor with the shortcode
        const newText = text.slice(0, activeShortcodeStart) + 
                       emoji.shortcode + 
                       text.slice(activeShortcodeEnd);
        
        // Update input value
        input.value = newText;
        
        // Set cursor position after the inserted emoji
        const newPosition = activeShortcodeStart + emoji.shortcode.length;
        input.setSelectionRange(newPosition, newPosition);
        
        // Focus the input
        input.focus();
        
        // Hide suggestions
        hideEmojiSuggestions();
    }
}

// Slash commands functionality
const commands = [
    { name: '/tasks', description: 'Toggle tasks panel' },
    { name: '/events', description: 'Toggle events panel' },
    { name: '/clear', description: 'Clear conversation history' },
    { name: '/help', description: 'Show available commands' },
    { name: '/details', description: 'Show details for an item by ID', requiresArg: true },
    { name: '/matrix', description: 'Control matrix background - toggle, opacity, speed', requiresArg: true }
];

let activeCommandIndex = -1;
let commandSuggestions = [];

function setupSlashCommands() {
    // Create command suggestions element if it doesn't exist
    let commandSuggestionsElement = document.getElementById('command-suggestions');
    if (!commandSuggestionsElement) {
        commandSuggestionsElement = document.createElement('div');
        commandSuggestionsElement.id = 'command-suggestions';
        commandSuggestionsElement.className = 'command-suggestions';
        document.querySelector('.chat-input-wrapper').appendChild(commandSuggestionsElement);
    }
}

function handleCommandAutocomplete(event) {
    const input = chatInput;
    const text = input.value;
    const cursorPosition = input.selectionStart;
    
    // Find if we're typing a command (line starts with /)
    const lastLineStart = text.lastIndexOf('\n', cursorPosition - 1) + 1;
    const currentLine = text.substring(lastLineStart, cursorPosition);
    
    // If current line starts with slash, show command suggestions
    if (currentLine.startsWith('/')) {
        const commandText = currentLine.split(' ')[0]; // Get just the command part
        
        // Filter matching commands
        commandSuggestions = commands.filter(cmd => 
            cmd.name.startsWith(commandText.toLowerCase())
        );
        
        if (commandSuggestions.length > 0) {
            showCommandSuggestions();
            input.classList.add('has-command');
        } else {
            hideCommandSuggestions();
        }
    } else {
        hideCommandSuggestions();
        input.classList.remove('has-command');
    }
}

function showCommandSuggestions() {
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    commandSuggestionsElement.innerHTML = '';
    
    // Create suggestion elements
    commandSuggestions.forEach((cmd, index) => {
        const item = document.createElement('div');
        item.className = 'command-item';
        item.dataset.index = index;
        
        const name = document.createElement('span');
        name.className = 'command-name';
        name.textContent = cmd.name;
        
        const description = document.createElement('span');
        description.className = 'command-description';
        description.textContent = cmd.description;
        
        item.appendChild(name);
        item.appendChild(description);
        
        // Add click handler
        item.addEventListener('click', () => {
            insertCommand(index);
        });
        
        commandSuggestionsElement.appendChild(item);
    });
    
    // Reset active suggestion
    activeCommandIndex = -1;
    
    // Show suggestions
    commandSuggestionsElement.classList.add('visible');
}

function hideCommandSuggestions() {
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    commandSuggestionsElement.classList.remove('visible');
    commandSuggestions = [];
    activeCommandIndex = -1;
}

function handleCommandKeyNavigation(event) {
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    
    // Only process if command suggestions are visible
    if (!commandSuggestionsElement.classList.contains('visible') || commandSuggestions.length === 0) {
        return;
    }
    
    switch (event.key) {
        case 'ArrowDown':
            // Move selection down
            event.preventDefault();
            activeCommandIndex = (activeCommandIndex + 1) % commandSuggestions.length;
            updateActiveCommand();
            break;
            
        case 'ArrowUp':
            // Move selection up
            event.preventDefault();
            activeCommandIndex = (activeCommandIndex - 1 + commandSuggestions.length) % commandSuggestions.length;
            updateActiveCommand();
            break;
            
        case 'Tab':
        case 'Enter':
            // Insert selected command
            if (activeCommandIndex >= 0) {
                event.preventDefault();
                insertCommand(activeCommandIndex);
            } else if (commandSuggestions.length === 1) {
                event.preventDefault();
                insertCommand(0);
            }
            break;
            
        case 'Escape':
            // Close suggestions
            event.preventDefault();
            hideCommandSuggestions();
            break;
    }
}

function updateActiveCommand() {
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    // Remove active class from all items
    const items = commandSuggestionsElement.querySelectorAll('.command-item');
    items.forEach(item => item.classList.remove('selected'));
    
    // Add active class to selected item
    if (activeCommandIndex >= 0 && activeCommandIndex < items.length) {
        items[activeCommandIndex].classList.add('selected');
        
        // Ensure the active item is visible in the scroll area
        const activeItem = items[activeCommandIndex];
        const container = commandSuggestionsElement;
        
        const itemTop = activeItem.offsetTop;
        const itemBottom = itemTop + activeItem.offsetHeight;
        const containerTop = container.scrollTop;
        const containerBottom = containerTop + container.offsetHeight;
        
        if (itemTop < containerTop) {
            container.scrollTop = itemTop;
        } else if (itemBottom > containerBottom) {
            container.scrollTop = itemBottom - container.offsetHeight;
        }
    }
}

function insertCommand(index) {
    const input = chatInput;
    const text = input.value;
    const cursorPosition = input.selectionStart;
    
    // Find the start of the current line
    const lastLineStart = text.lastIndexOf('\n', cursorPosition - 1) + 1;
    
    // Replace the partial command with the full command
    const cmd = commandSuggestions[index];
    const beforeCommand = text.substring(0, lastLineStart);
    const afterCommand = text.substring(cursorPosition);
    
    input.value = beforeCommand + cmd.name + ' ' + afterCommand;
    
    // Set cursor position after the command
    const newPosition = lastLineStart + cmd.name.length + 1;
    input.setSelectionRange(newPosition, newPosition);
    
    // Focus the input
    input.focus();
    
    // Hide suggestions
    hideCommandSuggestions();
}

function executeCommand(command) {
    const parts = command.split(' ');
    const cmdName = parts[0].toLowerCase();
    const args = parts.slice(1);
    
    switch (cmdName) {
        case '/tasks':
            document.dispatchEvent(new CustomEvent('command:tasks'));
            addMessage('system', 'Tasks panel toggled');
            break;
        
        case '/events':
            document.dispatchEvent(new CustomEvent('command:events'));
            addMessage('system', 'Events panel toggled');
            break;
        
        case '/clear':
            resetConversation();
            break;
        
        case '/help':
            showHelp();
            break;
        
        case '/details':
            if (args.length > 0) {
                showItemDetails(args[0]);
            } else {
                addMessage('system', 'Error: Please provide an item ID');
            }
            break;
            
        case '/matrix':
            if (args.length === 0) {
                addMessage('system', `Matrix background commands:
- /matrix toggle: Turn the effect on/off
- /matrix opacity 0.1-1.0: Set transparency (0.1=subtle, 1.0=opaque)
- /matrix speed 0.5-2.0: Set animation speed
- /matrix density 10-50: Set character density (lower=more characters)`);
                return;
            }
            
            const subcommand = args[0].toLowerCase();
            const param = args[1];
            
            if (subcommand === 'toggle') {
                document.dispatchEvent(new CustomEvent('command:matrix', { 
                    detail: { toggle: true }
                }));
                addMessage('system', 'Matrix background effect toggled');
            } else if (subcommand === 'opacity' && param) {
                const opacity = parseFloat(param);
                if (isNaN(opacity) || opacity < 0 || opacity > 1) {
                    addMessage('system', 'Error: Opacity must be between 0 and 1 (e.g., 0.1, 0.5, 0.8)');
                    return;
                }
                document.dispatchEvent(new CustomEvent('command:matrix', { 
                    detail: { opacity }
                }));
                addMessage('system', `Matrix background opacity set to ${opacity}`);
            } else if (subcommand === 'speed' && param) {
                const speed = parseFloat(param);
                if (isNaN(speed) || speed < 0.1 || speed > 3) {
                    addMessage('system', 'Error: Speed must be between 0.1 and 3 (e.g., 0.5, 1, 2)');
                    return;
                }
                document.dispatchEvent(new CustomEvent('command:matrix', { 
                    detail: { speed }
                }));
                addMessage('system', `Matrix background speed set to ${speed}`);
            } else if (subcommand === 'density' && param) {
                const density = parseFloat(param);
                if (isNaN(density) || density < 5 || density > 100) {
                    addMessage('system', 'Error: Density must be between 5 and 100 (lower = more characters)');
                    return;
                }
                document.dispatchEvent(new CustomEvent('command:matrix', { 
                    detail: { density }
                }));
                addMessage('system', `Matrix background density set to ${density}`);
            } else {
                addMessage('system', `Unknown matrix command. Try: toggle, opacity, speed, density`);
            }
            break;
        
        default:
            addMessage('system', `Unknown command: ${cmdName}`);
    }
}

function showHelp() {
    const helpText = commands.map(cmd => `${cmd.name} - ${cmd.description}`).join('\n');
    addMessage('system', `Available commands:\n\`\`\`\n${helpText}\n\`\`\``);
}

function showItemDetails(id) {
    // Check if this is a task ID
    if (window.tilingManager) {
        // First check if it's a task
        if (tasks && tasks.find(t => t.task_id === id)) {
            window.tilingManager.showTaskDetails(id);
            addMessage('system', `Showing details for task ${id}`);
            return;
        }
        
        // Then check if it's an event
        if (events && events.find(e => e.id === id)) {
            window.tilingManager.showEventDetails(id);
            addMessage('system', `Showing details for event ${id}`);
            return;
        }
        
        addMessage('system', `No item found with ID ${id}`);
    } else {
        addMessage('system', 'The tiling manager is not initialized yet. Try again in a moment.');
    }
}

// Function to show a detail panel for tasks or events
function showDetailPanel(type, item) {
    console.log(`Showing ${type} details:`, item);
    
    // Create or get the detail panel
    let detailPanel = document.getElementById('detail-panel');
    if (!detailPanel) {
        detailPanel = document.createElement('div');
        detailPanel.id = 'detail-panel';
        detailPanel.className = 'detail-panel';
        document.body.appendChild(detailPanel);
    }
    
    // Clear previous content
    detailPanel.innerHTML = '';
    
    // Create close button
    const closeButton = document.createElement('button');
    closeButton.className = 'detail-close-button';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', () => {
        detailPanel.classList.remove('visible');
    });
    
    // Create title
    const title = document.createElement('h2');
    title.className = 'detail-title';
    
    // Create content container
    const content = document.createElement('div');
    content.className = 'detail-content';
    
    // Add class for styling based on type
    detailPanel.className = `detail-panel ${type}-details`;
    
    // Generate content based on type
    if (type === 'task') {
        title.textContent = 'Task Details';
        
        // Format task details
        const taskDetails = document.createElement('div');
        taskDetails.className = 'task-details';
        
        // Description
        const description = document.createElement('div');
        description.className = 'detail-description';
        description.innerHTML = `<strong>Description:</strong> ${item.description || 'No description'}`;
        
        // Status with color
        const status = document.createElement('div');
        status.className = 'detail-status';
        const statusValue = item.status || 'backlog';
        status.innerHTML = `<strong>Status:</strong> <span class="status-${statusValue.toLowerCase()}">${statusValue}</span>`;
        
        // Project
        const project = document.createElement('div');
        project.className = 'detail-project';
        project.innerHTML = `<strong>Project:</strong> ${item.project_name || 'No project'}`;
        
        // Created date
        const created = document.createElement('div');
        created.className = 'detail-created';
        if (item.created_at) {
            try {
                const date = new Date(item.created_at);
                created.innerHTML = `<strong>Created:</strong> ${date.toLocaleString()}`;
            } catch (e) {
                created.innerHTML = `<strong>Created:</strong> ${item.created_at}`;
            }
        } else {
            created.innerHTML = '<strong>Created:</strong> Unknown';
        }
        
        // Category
        if (item.category) {
            const category = document.createElement('div');
            category.className = 'detail-category';
            category.innerHTML = `<strong>Category:</strong> ${item.category}`;
            taskDetails.appendChild(category);
        }
        
        // Origin
        if (item.origin) {
            const origin = document.createElement('div');
            origin.className = 'detail-origin';
            origin.innerHTML = `<strong>Origin:</strong> ${item.origin}`;
            taskDetails.appendChild(origin);
        }
        
        // ID (for reference)
        const id = document.createElement('div');
        id.className = 'detail-id';
        id.innerHTML = `<strong>ID:</strong> <span class="monospace">${item.task_id || 'Unknown'}</span>`;
        
        // Append all sections
        taskDetails.appendChild(description);
        taskDetails.appendChild(status);
        taskDetails.appendChild(project);
        taskDetails.appendChild(created);
        taskDetails.appendChild(id);
        
        content.appendChild(taskDetails);
    } else if (type === 'event') {
        title.textContent = 'Event Details';
        
        // Format event details
        const eventDetails = document.createElement('div');
        eventDetails.className = 'event-details';
        
        // Type/Category
        const eventType = document.createElement('div');
        eventType.className = 'detail-type';
        eventType.innerHTML = `<strong>Type:</strong> ${item.type || item.category || 'Unknown'}`;
        
        // Timestamp
        const timestamp = document.createElement('div');
        timestamp.className = 'detail-timestamp';
        if (item.timestamp) {
            try {
                const date = new Date(item.timestamp);
                timestamp.innerHTML = `<strong>Time:</strong> ${date.toLocaleString()}`;
            } catch (e) {
                timestamp.innerHTML = `<strong>Time:</strong> ${item.timestamp}`;
            }
        } else {
            timestamp.innerHTML = '<strong>Time:</strong> Unknown';
        }
        
        // Summary
        const summary = document.createElement('div');
        summary.className = 'detail-summary';
        summary.innerHTML = `<strong>Summary:</strong> ${
            item.summary || item.description || 'No summary available'
        }`;
        
        // Details (if available)
        if (item.details) {
            const details = document.createElement('div');
            details.className = 'detail-full-details';
            
            // Format based on type
            if (typeof item.details === 'string') {
                details.innerHTML = `<strong>Details:</strong><br>${item.details}`;
            } else {
                try {
                    const detailsStr = JSON.stringify(item.details, null, 2);
                    details.innerHTML = `<strong>Details:</strong><br><pre>${detailsStr}</pre>`;
                } catch (e) {
                    details.innerHTML = `<strong>Details:</strong> Unable to format details`;
                }
            }
            eventDetails.appendChild(details);
        }
        
        // ID (for reference)
        const id = document.createElement('div');
        id.className = 'detail-id';
        id.innerHTML = `<strong>ID:</strong> <span class="monospace">${item.id || 'Unknown'}</span>`;
        
        // Append all sections
        eventDetails.appendChild(eventType);
        eventDetails.appendChild(timestamp);
        eventDetails.appendChild(summary);
        eventDetails.appendChild(id);
        
        content.appendChild(eventDetails);
    }
    
    // Assemble the panel
    detailPanel.appendChild(closeButton);
    detailPanel.appendChild(title);
    detailPanel.appendChild(content);
    
    // Add CSS to the detail panel if it doesn't exist
    if (!document.getElementById('detail-panel-style')) {
        const style = document.createElement('style');
        style.id = 'detail-panel-style';
        style.textContent = `
            .detail-panel {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) scale(0.9);
                width: 80%;
                max-width: 500px;
                max-height: 80vh;
                background-color: var(--panel-bg);
                border: 1px solid var(--border-color);
                border-radius: 4px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
                padding: 20px;
                overflow-y: auto;
                z-index: 1000;
                opacity: 0;
                visibility: hidden;
                transition: all 0.2s ease-in-out;
            }
            
            .detail-panel.visible {
                opacity: 1;
                visibility: visible;
                transform: translate(-50%, -50%) scale(1);
            }
            
            .detail-close-button {
                position: absolute;
                top: 10px;
                right: 10px;
                background: none;
                border: none;
                color: var(--text-color);
                font-size: 20px;
                cursor: pointer;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
            }
            
            .detail-close-button:hover {
                background-color: var(--hover-color);
            }
            
            .detail-title {
                margin: 0 0 15px 0;
                padding-bottom: 10px;
                border-bottom: 1px solid var(--border-color);
                color: var(--term-amber);
            }
            
            .detail-content {
                font-family: var(--terminal-font);
                line-height: 1.5;
            }
            
            .detail-content > div {
                margin-bottom: 15px;
            }
            
            .detail-content strong {
                color: var(--accent-blue);
                font-weight: bold;
            }
            
            .status-backlog {
                color: var(--term-amber);
            }
            
            .status-inprogress, .status-in_progress {
                color: var(--term-blue);
            }
            
            .status-done, .status-completed {
                color: var(--term-green);
            }
            
            .detail-content pre {
                background-color: rgba(0, 0, 0, 0.2);
                padding: 10px;
                border-radius: 4px;
                overflow: auto;
                font-family: var(--mono-font);
                max-height: 200px;
            }
            
            .monospace {
                font-family: var(--mono-font);
            }
            
            .detail-id {
                font-size: 0.9em;
                opacity: 0.7;
                margin-top: 15px;
            }
            
            /* Add an overlay behind the panel */
            .detail-panel::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: -1;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Display the panel
    detailPanel.classList.add('visible');
    
    // Close on ESC key
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            detailPanel.classList.remove('visible');
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
    
    // Close when clicking outside
    const outsideClickHandler = (e) => {
        if (detailPanel.classList.contains('visible') && 
            !detailPanel.contains(e.target)) {
            detailPanel.classList.remove('visible');
            document.removeEventListener('click', outsideClickHandler, true);
        }
    };
    // Use capture phase to handle click before other handlers
    setTimeout(() => {
        document.addEventListener('click', outsideClickHandler, true);
    }, 100); // Small delay to avoid immediate closing
}

// Event handler for events
function handleEvents(newEvents) {
    console.log('Received events:', newEvents);
    
    if (Array.isArray(newEvents) && newEvents.length > 0) {
        // Add event IDs if they don't have them
        newEvents.forEach((event, index) => {
            if (!event.id) {
                event.id = `event-${Date.now()}-${index}`;
            }
            
            // Log all events for debugging
            console.log(`Processing event #${index}:`, event);
            
            // Check for agent transfer events and update current agent name
            if (event.category === 'agent_transfer' || event.type === 'agent_transfer') {
                console.log('Agent transfer event detected:', event);
                
                // Check various properties where agent name might be found
                const targetAgent = event.to_agent || 
                               event.target_agent || 
                               (event.details && (event.details.to_agent || event.details.agent)) || 
                               (event.summary && event.summary.includes('SCOUT') ? 'SCOUT' : null);
                
                if (targetAgent) {
                    // Update the current agent name - force uppercase for consistency
                    const previousAgent = currentAgentName;
                    currentAgentName = targetAgent.toUpperCase();
                    
                    console.log(`Agent name changing from ${previousAgent} to ${currentAgentName}`);
                    
                    // Update the CSS variable for agent name
                    document.documentElement.style.setProperty('--agent-name', `"${currentAgentName}"`);
                    
                    // Direct update of all status elements
                    if (agentStatus) {
                        agentStatus.textContent = `AGENT: ${currentAgentName}`;
                        console.log("Directly updated agent status in status bar: " + agentStatus.textContent);
                        // Force DOM redraw by changing style slightly
                        agentStatus.style.opacity = "0.9";
                        setTimeout(() => { agentStatus.style.opacity = "1"; }, 10);
                    } else {
                        console.error("Cannot find agent-status element in DOM for update:", document.getElementById('agent-status'));
                    }
                    
                    // Update clock and connection status also
                    updateClock();
                    
                    // Add a system message indicating the agent change
                    addMessage('system', `Agent switched to: ${currentAgentName}`);
                    
                    console.log(`Agent changed to: ${currentAgentName}`);
                } else {
                    console.warn('Agent transfer event missing target agent field:', event);
                    console.log('Event properties:', Object.keys(event));
                    
                    // As a fallback, check if this seems to be a transfer to SCOUT
                    if (event.summary && event.summary.toLowerCase().includes('scout')) {
                        const previousAgent = currentAgentName;
                        currentAgentName = 'SCOUT';
                        console.log(`[FALLBACK] Agent name changing from ${previousAgent} to ${currentAgentName}`);
                        
                        // Direct update of all status elements
                        if (agentStatus) {
                            agentStatus.textContent = `AGENT: ${currentAgentName}`;
                            console.log("Directly updated agent status through fallback: " + agentStatus.textContent);
                            // Force DOM redraw by changing style slightly
                            agentStatus.style.opacity = "0.9";
                            setTimeout(() => { agentStatus.style.opacity = "1"; }, 10);
                        } else {
                            console.error("Cannot find agent-status element in DOM for fallback update");
                        }
                        
                        // Update the CSS variable
                        document.documentElement.style.setProperty('--agent-name', `"${currentAgentName}"`);
                        
                        // Add a system message
                        addMessage('system', `Agent switched to: ${currentAgentName} (detected from event summary)`);
                    }
                }
            }
        });
        
        // Add to events array
        events = events.concat(newEvents);
        
        // Update events display if the events panel is visible
        const eventsContainer = document.getElementById('events-container');
        if (eventsContainer) {
            console.log('Events container found, updating display');
            renderEvents();
        } else {
            console.log('Events container not found, skipping render');
        }
    }
}

// Handler for tasks data received from server
function handleTasks(newTasks) {
    console.log('Received tasks:', newTasks);
    
    if (Array.isArray(newTasks)) {
        // Add to tasks array
        tasks = newTasks;
        
        // Update tasks display if the tasks panel is visible
        const tasksContainer = document.getElementById('tasks-container');
        if (tasksContainer) {
            console.log('Tasks container found, updating display');
            renderTasks();
        } else {
            console.log('Tasks container not found, skipping render');
        }
    }
}

// Fetch tasks directly from the Task API endpoint
function fetchTasks() {
    console.log('Fetching tasks from Task API');
    
    // Use the task API setting from localStorage or default to localhost:8001
    const taskApiEndpoint = taskApiSettings.endpoint || 'http://localhost:8001';
    
    fetch(`${taskApiEndpoint}/api/v1/tasks`, {
        method: 'GET',
        mode: 'cors',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': taskApiSettings.apiKey || ''
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Successfully fetched tasks from Task API:', data);
            
            // Update tasks array
            if (Array.isArray(data)) {
                // Direct array response format
                tasks = data.map(task => ({
                    task_id: task.task_id,
                    description: task.description,
                    status: task.status,
                    category: task.category,
                    project_id: task.project_id,
                    project_name: task.project_name,
                    created_at: task.created_at,
                    origin: task.origin
                }));
                console.log('Parsed tasks directly from array response');
            } else if (Array.isArray(data.tasks)) {
                // Wrapped in 'tasks' property format
                tasks = data.tasks.map(task => ({
                    task_id: task.id || task.task_id,
                    description: task.description,
                    status: task.status,
                    category: task.category,
                    project_id: task.project_id,
                    project_name: task.project_name,
                    created_at: task.created_at,
                    updated_at: task.updated_at,
                    origin: task.origin
                }));
                console.log('Parsed tasks from data.tasks property');
            } else {
                console.error('No tasks found in response:', data);
            }
            
            // Render tasks if container exists and we have tasks
            if (tasks && tasks.length > 0) {
                const tasksContainer = document.getElementById('tasks-container');
                if (tasksContainer) {
                    console.log('Tasks container found, rendering tasks from API fetch');
                    renderTasks();
                } else {
                    console.log('Tasks container not found when fetching tasks, will render later');
                }
            }
            
            // After fetching tasks, also fetch projects
            fetchProjects();
        })
        .catch(error => {
            console.error('Error fetching tasks:', error);
            
            // Check if it could be a CORS error
            if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
                console.warn('Possible CORS issue when fetching tasks. Make sure the Task API has CORS enabled.');
                addMessage('system', 'Error connecting to Task API. Possible CORS issue - make sure the Task API server is running and has CORS enabled for this origin.');
            } else {
                // Add a system message in the chat
                addMessage('system', 'Error fetching tasks. Tasks feature might not be available.');
            }
            
            // Still try to fetch projects
            fetchProjects();
        });
}

// Fetch projects directly from the Task API endpoint
function fetchProjects() {
    console.log('Fetching projects from Task API');
    
    // Use the task API setting from localStorage or default to localhost:8001
    const taskApiEndpoint = taskApiSettings.endpoint || 'http://localhost:8001';
    
    fetch(`${taskApiEndpoint}/api/v1/projects`, {
        method: 'GET',
        mode: 'cors',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': taskApiSettings.apiKey || ''
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Successfully fetched projects from Task API:', data);
            
            // Update projects array
            if (Array.isArray(data)) {
                // Direct array response format
                projects = data.map(project => ({
                    project_id: project.project_id,
                    name: project.name,
                    description: project.description,
                    created_at: project.created_at
                }));
                console.log('Parsed projects directly from array response');
            } else if (Array.isArray(data.projects)) {
                // Wrapped in 'projects' property format
                projects = data.projects.map(project => ({
                    project_id: project.id || project.project_id,
                    name: project.name,
                    description: project.description,
                    created_at: project.created_at,
                    updated_at: project.updated_at
                }));
                console.log('Parsed projects from data.projects property');
            } else {
                console.error('No projects found in response:', data);
            }
            
            // Update project filter dropdown if we have projects
            if (projects && projects.length > 0) {
                updateProjectFilterOptions();
            }
        })
        .catch(error => {
            console.error('Error fetching projects:', error);
            
            // Check if it could be a CORS error
            if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
                console.warn('Possible CORS issue when fetching projects. Make sure the Task API has CORS enabled.');
            }
        });
}

// Update project filter options
function updateProjectFilterOptions() {
    const projectFilterContent = document.getElementById('project-filter-content');
    if (!projectFilterContent) {
        console.log('Project filter content not found, skipping update');
        return;
    }
    
    console.log('Updating project filter options with projects:', projects);
    
    // Keep the "All Projects" option
    const allProjectsOption = projectFilterContent.querySelector('#project-all');
    if (!allProjectsOption) {
        console.log('All Projects option not found, cannot update filter options');
        return;
    }
    
    // Clear existing project options (except "All Projects")
    const existingOptions = projectFilterContent.querySelectorAll('.filter-option:not(:first-child)');
    existingOptions.forEach(option => option.remove());
    
    // Add new project options
    projects.forEach(project => {
        const projectId = project.project_id;
        const projectName = project.name || projectId;
        
        // Create new option
        const option = document.createElement('div');
        option.className = 'filter-option';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `project-${projectId}`;
        checkbox.value = projectId;
        
        const label = document.createElement('label');
        label.htmlFor = `project-${projectId}`;
        label.textContent = projectName;
        
        checkbox.addEventListener('change', () => {
            const allCheckbox = document.getElementById('project-all');
            
            if (checkbox.checked) {
                // Uncheck "All Projects"
                if (allCheckbox) allCheckbox.checked = false;
                
                // Add to selected projects
                if (!selectedProjects.includes(projectId)) {
                    selectedProjects = selectedProjects.filter(id => id !== 'all');
                    selectedProjects.push(projectId);
                }
            } else {
                // Remove from selected projects
                selectedProjects = selectedProjects.filter(id => id !== projectId);
                
                // If no projects selected, check "All Projects"
                if (selectedProjects.length === 0 && allCheckbox) {
                    allCheckbox.checked = true;
                    selectedProjects = ['all'];
                }
            }
            
            // Update button text
            const projectFilterBtn = document.getElementById('project-filter-btn');
            if (projectFilterBtn) {
                if (selectedProjects.includes('all')) {
                    projectFilterBtn.textContent = 'All Projects';
                } else if (selectedProjects.length === 1) {
                    const selectedProject = projects.find(p => p.project_id === selectedProjects[0]);
                    projectFilterBtn.textContent = selectedProject ? (selectedProject.name || selectedProject.project_id) : selectedProjects[0];
                } else {
                    projectFilterBtn.textContent = `${selectedProjects.length} Projects`;
                }
            }
            
            renderTasks();
        });
        
        option.appendChild(checkbox);
        option.appendChild(label);
        projectFilterContent.appendChild(option);
    });
    
    console.log('Project filter options updated');
}

// Fetch events directly from the API endpoint
function fetchEvents() {
    console.log('Fetching events from API directly');
    
    fetch('/api/events')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Successfully fetched events from API:', data);
            
            // Update events array
            if (Array.isArray(data)) {
                events = data;
                
                // Render events if container exists
                const eventsContainer = document.getElementById('events-container');
                if (eventsContainer) {
                    console.log('Events container found, rendering events from API fetch');
                    renderEvents();
                } else {
                    console.log('Events container not found when fetching events, will render later');
                }
            }
        })
        .catch(error => {
            console.error('Error fetching events:', error);
        });
}

// Auto-resize textarea
function resizeTextarea() {
    if (!chatInput) return;
    
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
}

// Render tasks to tasks container
function renderTasks() {
    console.log('Rendering tasks to container');
    const tasksContainer = document.getElementById('tasks-container');
    if (!tasksContainer) {
        console.error('Tasks container not found');
        return;
    }
    
    // Clear the container completely
    tasksContainer.innerHTML = '';
    
    // Create empty state message if needed
    const emptyState = document.createElement('div');
    emptyState.className = 'tasks-empty-state';
    emptyState.textContent = 'No tasks found.';
    
    // If no tasks array or it's empty, show empty state
    if (!tasks || !Array.isArray(tasks) || tasks.length === 0) {
        console.log('No tasks to display');
        tasksContainer.appendChild(emptyState);
        return;
    }
    
    console.log(`Rendering ${tasks.length} tasks`);
    
    // Apply filters
    let filteredTasks = [...tasks];
    
    // Log selected projects and statuses for debugging
    console.log('Selected projects:', selectedProjects);
    console.log('Selected statuses:', selectedStatuses);
    
    // Filter by project (make sure we handle both project_id and project_name)
    if (selectedProjects.length > 0 && !selectedProjects.includes('all')) {
        console.log('Filtering by projects:', selectedProjects);
        filteredTasks = filteredTasks.filter(task => {
            // Check if either project_id or project_name matches any selected project
            const taskProjectId = task.project_id ? String(task.project_id) : null;
            const taskProjectName = task.project_name ? String(task.project_name) : null;
            
            return selectedProjects.some(projectId => 
                projectId === taskProjectId || projectId === taskProjectName
            );
        });
        console.log(`After project filtering: ${filteredTasks.length} tasks`);
    }
    
    // Filter by status
    if (selectedStatuses.length > 0 && !selectedStatuses.includes('all')) {
        console.log('Filtering by statuses:', selectedStatuses);
        filteredTasks = filteredTasks.filter(task => {
            const taskStatus = task.status ? String(task.status).toLowerCase() : 'backlog';
            return selectedStatuses.includes(taskStatus);
        });
        console.log(`After status filtering: ${filteredTasks.length} tasks`);
    }
    
    // Filter by search term
    const searchInput = document.getElementById('task-search');
    if (searchInput && searchInput.value.trim()) {
        const searchTerm = searchInput.value.trim().toLowerCase();
        console.log('Filtering by search term:', searchTerm);
        
        filteredTasks = filteredTasks.filter(task => {
            // Safely access properties
            const description = task.description ? String(task.description).toLowerCase() : '';
            const project = task.project_name ? String(task.project_name).toLowerCase() : 
                           (task.project_id ? String(task.project_id).toLowerCase() : '');
            const category = task.category ? String(task.category).toLowerCase() : '';
            
            return description.includes(searchTerm) || 
                   project.includes(searchTerm) || 
                   category.includes(searchTerm);
        });
        console.log(`After search filtering: ${filteredTasks.length} tasks`);
    }
    
    // Sort tasks (in progress first, then backlog, then done)
    filteredTasks.sort((a, b) => {
        const statusOrder = { 'inprogress': 0, 'in_progress': 0, 'backlog': 1, 'pending': 1, 'done': 2, 'completed': 2 };
        
        // Get status with fallback
        const statusA = (a.status ? String(a.status).toLowerCase() : 'backlog');
        const statusB = (b.status ? String(b.status).toLowerCase() : 'backlog');
        
        // Get order value with fallback to backlog (1)
        const orderA = statusOrder[statusA] !== undefined ? statusOrder[statusA] : 1;
        const orderB = statusOrder[statusB] !== undefined ? statusOrder[statusB] : 1;
        
        return orderA - orderB;
    });
    
    console.log(`Final filtered tasks count: ${filteredTasks.length}`);
    
    // If no filtered tasks, show empty state
    if (filteredTasks.length === 0) {
        console.log('No tasks match the filters');
        tasksContainer.appendChild(emptyState);
        return;
    }
    
    // Create task items
    filteredTasks.forEach(task => {
        // Create task item container
        const taskItem = document.createElement('div');
        
        // Get status with fallback
        const status = task.status ? String(task.status).toLowerCase() : 'backlog';
        
        // Map various status formats to standard ones
        let normalizedStatus = status;
        if (status === 'in_progress' || status === 'inprogress') normalizedStatus = 'inprogress';
        if (status === 'pending' || status === 'backlog') normalizedStatus = 'backlog';
        if (status === 'completed' || status === 'done') normalizedStatus = 'done';
        
        // Set classes
        taskItem.className = `task-item ${normalizedStatus}`;
        taskItem.dataset.taskId = task.task_id ? String(task.task_id) : "unknown";
        
        // Status indicator
        const statusIndicator = document.createElement('div');
        statusIndicator.className = `task-status-indicator ${normalizedStatus}`;
        
        // Task content
        const taskContent = document.createElement('div');
        taskContent.className = 'task-content';
        taskContent.textContent = task.description ? String(task.description) : "No description";
        
        // Project tag
        const taskProject = document.createElement('div');
        taskProject.className = 'task-project';
        taskProject.textContent = task.project_name ? String(task.project_name) : 
                                 (task.project_id ? String(task.project_id) : 'Default');
        
        // Assemble task item
        taskItem.appendChild(statusIndicator);
        taskItem.appendChild(taskContent);
        taskItem.appendChild(taskProject);
        
        // Add click handler to show task details
        taskItem.addEventListener('click', () => {
            // Get the task ID from the data attribute
            const taskId = taskItem.dataset.taskId;
            console.log('Task clicked:', taskId);
            
            // Show task details using our panel function
            showDetailPanel('task', task);
        });
        
        // Add task item to container
        tasksContainer.appendChild(taskItem);
    });
    
    console.log('Tasks rendering complete');
}

// Render events to events container
function renderEvents() {
    console.log('Rendering events to container');
    const eventsContainer = document.getElementById('events-container');
    if (!eventsContainer) {
        console.error('Events container not found');
        return;
    }
    
    // Clear the container completely
    eventsContainer.innerHTML = '';
    
    // Create empty state message if needed
    const emptyState = document.createElement('div');
    emptyState.className = 'event-empty-state';
    emptyState.textContent = 'No events recorded yet.';
    
    // If no events array or it's empty, show empty state
    if (!events || !Array.isArray(events) || events.length === 0) {
        console.log('No events to display');
        eventsContainer.appendChild(emptyState);
        return;
    }
    
    console.log(`Rendering ${events.length} events`);
    
    // Filter events based on selected type
    const eventTypeFilter = document.getElementById('event-type-filter');
    const selectedType = eventTypeFilter ? eventTypeFilter.value : 'all';
    
    console.log('Event type filter value:', selectedType);
    
    let filteredEvents = [...events];
    
    // Apply type filter if not 'all'
    if (selectedType !== 'all') {
        console.log('Filtering events by type:', selectedType);
        filteredEvents = filteredEvents.filter(event => {
            // Apply case-insensitive comparison for safety
            const eventType = event.type ? String(event.type).toLowerCase() : '';
            const eventCategory = event.category ? String(event.category).toLowerCase() : '';
            
            return eventType === selectedType.toLowerCase() || 
                   eventCategory === selectedType.toLowerCase();
        });
        console.log(`After type filtering: ${filteredEvents.length} events`);
    }
    
    // Sort events by timestamp (newest first)
    try {
        filteredEvents.sort((a, b) => {
            // Try parsing timestamp strings as Date objects first
            const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
            const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
            
            // If both timestamps are valid numbers, compare them
            if (!isNaN(timeA) && !isNaN(timeB)) {
                return timeB - timeA;
            }
            
            // Otherwise, sort lexicographically as fallback
            const strA = a.timestamp ? String(a.timestamp) : '';
            const strB = b.timestamp ? String(b.timestamp) : '';
            return strB.localeCompare(strA);
        });
    } catch (e) {
        console.error('Error sorting events by timestamp:', e);
    }
    
    console.log(`Final filtered events count: ${filteredEvents.length}`);
    
    // If no filtered events, show empty state
    if (filteredEvents.length === 0) {
        console.log('No events match the filter');
        eventsContainer.appendChild(emptyState);
        return;
    }
    
    // Create event items
    filteredEvents.forEach(event => {
        try {
            // Create event item container
            const eventItem = document.createElement('div');
            
            // Determine event category for styling
            let eventCategory = 'other';
            
            // Safely check event type and category
            const type = event.type ? String(event.type).toLowerCase() : '';
            const category = event.category ? String(event.category).toLowerCase() : '';
            
            if (type === 'tool_call' || category === 'tool_call') {
                eventCategory = 'tool-call';
            } else if (type === 'agent_transfer' || category === 'agent_transfer') {
                eventCategory = 'agent-transfer';
            } else if (type === 'planner' || category === 'planner') {
                eventCategory = 'planner';
            }
            
            // Set classes
            eventItem.className = `event-item ${eventCategory}`;
            eventItem.dataset.eventId = event.id ? String(event.id) : "event-" + Math.random().toString(36).substring(2, 9);
            
            // Event type
            const eventType = document.createElement('div');
            eventType.className = 'event-type';
            eventType.textContent = event.type || event.category || 'Event';
            
            // Event timestamp
            const eventTimestamp = document.createElement('div');
            eventTimestamp.className = 'event-timestamp';
            
            if (event.timestamp) {
                // Try to format timestamp
                try {
                    const date = new Date(event.timestamp);
                    if (!isNaN(date.getTime())) {
                        // Valid date, use time format
                        eventTimestamp.textContent = date.toLocaleTimeString();
                    } else {
                        // Not a valid date, use as-is
                        eventTimestamp.textContent = event.timestamp;
                    }
                } catch (e) {
                    // If there's an error formatting, use the original string
                    eventTimestamp.textContent = String(event.timestamp);
                }
            } else {
                eventTimestamp.textContent = 'Unknown time';
            }
            
            // Event summary
            const eventSummary = document.createElement('div');
            eventSummary.className = 'event-summary';
            
            // Get the summary from any available field, in order of preference
            const summaryText = event.summary || 
                              event.description || 
                              (event.details ? (typeof event.details === 'string' ? event.details : JSON.stringify(event.details)) : 
                              'No details available');
                              
            eventSummary.textContent = summaryText;
            
            // Append elements
            eventItem.appendChild(eventType);
            eventItem.appendChild(eventTimestamp);
            eventItem.appendChild(eventSummary);
            
            // Set click handler to show full details
            eventItem.addEventListener('click', () => {
                // Log the event details for now
                console.log('Event clicked:', event.id);
                
                // Show task details using our panel
                showDetailPanel('event', event);
            });
            
            // Add the event item to the container
            eventsContainer.appendChild(eventItem);
        } catch (error) {
            console.error('Error rendering event:', error, event);
        }
    });
    
    console.log('Events rendering complete');
}

// Setup filter controls
function setupFilterControls() {
    console.log('Setting up filter controls');
    
    // Event type filter
    const eventTypeFilter = document.getElementById('event-type-filter');
    if (eventTypeFilter) {
        eventTypeFilter.addEventListener('change', () => {
            console.log(`Event type filter changed to: ${eventTypeFilter.value}`);
            renderEvents();
        });
    }
    
    // Project filter
    const projectFilterBtn = document.getElementById('project-filter-btn');
    const projectFilterContent = document.getElementById('project-filter-content');
    
    if (projectFilterBtn && projectFilterContent) {
        // Toggle dropdown
        projectFilterBtn.addEventListener('click', () => {
            projectFilterContent.classList.toggle('show');
        });
        
        // Handle "All Projects" checkbox
        const allProjectsCheckbox = document.getElementById('project-all');
        if (allProjectsCheckbox) {
            allProjectsCheckbox.addEventListener('change', (e) => {
                const projectCheckboxes = projectFilterContent.querySelectorAll('input[type="checkbox"]:not(#project-all)');
                
                if (e.target.checked) {
                    // Uncheck all other projects
                    projectCheckboxes.forEach(cb => {
                        cb.checked = false;
                    });
                    
                    selectedProjects = ['all'];
                    projectFilterBtn.textContent = 'All Projects';
                } else {
                    // Ensure at least one project is selected
                    const anyChecked = Array.from(projectCheckboxes).some(cb => cb.checked);
                    if (!anyChecked) {
                        e.target.checked = true;  // Recheck "All Projects" if nothing else is selected
                    }
                }
                
                renderTasks();
            });
        }
        
        // Add project checkboxes dynamically from available projects
        if (projects && projects.length > 0) {
            projects.forEach(project => {
                const projectId = project.project_id;
                const projectName = project.name || projectId;
                
                // Check if this project checkbox already exists
                const existingCheckbox = document.getElementById(`project-${projectId}`);
                if (!existingCheckbox) {
                    const option = document.createElement('div');
                    option.className = 'filter-option';
                    
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.id = `project-${projectId}`;
                    checkbox.value = projectId;
                    
                    const label = document.createElement('label');
                    label.htmlFor = `project-${projectId}`;
                    label.textContent = projectName;
                    
                    checkbox.addEventListener('change', () => {
                        const allCheckbox = document.getElementById('project-all');
                        
                        if (checkbox.checked) {
                            // Uncheck "All Projects"
                            if (allCheckbox) allCheckbox.checked = false;
                            
                            // Add to selected projects
                            if (!selectedProjects.includes(projectId)) {
                                selectedProjects = selectedProjects.filter(id => id !== 'all');
                                selectedProjects.push(projectId);
                            }
                        } else {
                            // Remove from selected projects
                            selectedProjects = selectedProjects.filter(id => id !== projectId);
                            
                            // If no projects selected, check "All Projects"
                            if (selectedProjects.length === 0 && allCheckbox) {
                                allCheckbox.checked = true;
                                selectedProjects = ['all'];
                            }
                        }
                        
                        // Update button text
                        if (selectedProjects.includes('all')) {
                            projectFilterBtn.textContent = 'All Projects';
                        } else if (selectedProjects.length === 1) {
                            const selectedProject = projects.find(p => p.project_id === selectedProjects[0]);
                            projectFilterBtn.textContent = selectedProject ? (selectedProject.name || selectedProject.project_id) : selectedProjects[0];
                        } else {
                            projectFilterBtn.textContent = `${selectedProjects.length} Projects`;
                        }
                        
                        renderTasks();
                    });
                    
                    option.appendChild(checkbox);
                    option.appendChild(label);
                    projectFilterContent.appendChild(option);
                }
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!projectFilterBtn.contains(e.target) && !projectFilterContent.contains(e.target)) {
                projectFilterContent.classList.remove('show');
            }
        });
    }
    
    // Status filter
    const statusFilterBtn = document.getElementById('status-filter-btn');
    const statusFilterContent = document.getElementById('status-filter-content');
    
    if (statusFilterBtn && statusFilterContent) {
        // Toggle dropdown
        statusFilterBtn.addEventListener('click', () => {
            statusFilterContent.classList.toggle('show');
        });
        
        // Handle "All Statuses" checkbox
        const allStatusesCheckbox = document.getElementById('status-all');
        if (allStatusesCheckbox) {
            allStatusesCheckbox.addEventListener('change', (e) => {
                const statusCheckboxes = statusFilterContent.querySelectorAll('input[type="checkbox"]:not(#status-all)');
                
                if (e.target.checked) {
                    // Uncheck all other statuses
                    statusCheckboxes.forEach(cb => {
                        cb.checked = false;
                    });
                    
                    selectedStatuses = ['all'];
                    statusFilterBtn.textContent = 'All Statuses';
                } else {
                    // Ensure at least one status is selected
                    const anyChecked = Array.from(statusCheckboxes).some(cb => cb.checked);
                    if (!anyChecked) {
                        e.target.checked = true;  // Recheck "All Statuses" if nothing else is selected
                    }
                }
                
                renderTasks();
            });
        }
        
        // Status checkboxes event handlers
        const statusCheckboxes = statusFilterContent.querySelectorAll('input[type="checkbox"]:not(#status-all)');
        statusCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const allCheckbox = document.getElementById('status-all');
                
                if (checkbox.checked) {
                    // Uncheck "All Statuses"
                    if (allCheckbox) allCheckbox.checked = false;
                    
                    // Add to selected statuses
                    if (!selectedStatuses.includes(checkbox.value)) {
                        selectedStatuses = selectedStatuses.filter(status => status !== 'all');
                        selectedStatuses.push(checkbox.value);
                    }
                } else {
                    // Remove from selected statuses
                    selectedStatuses = selectedStatuses.filter(status => status !== checkbox.value);
                    
                    // If no statuses selected, check "All Statuses"
                    if (selectedStatuses.length === 0 && allCheckbox) {
                        allCheckbox.checked = true;
                        selectedStatuses = ['all'];
                    }
                }
                
                // Update button text
                if (selectedStatuses.includes('all')) {
                    statusFilterBtn.textContent = 'All Statuses';
                } else if (selectedStatuses.length === 1) {
                    const statusLabel = {
                        'backlog': 'Backlog',
                        'inprogress': 'In Progress',
                        'done': 'Done'
                    }[selectedStatuses[0]] || selectedStatuses[0];
                    statusFilterBtn.textContent = statusLabel;
                } else {
                    statusFilterBtn.textContent = `${selectedStatuses.length} Statuses`;
                }
                
                renderTasks();
            });
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!statusFilterBtn.contains(e.target) && !statusFilterContent.contains(e.target)) {
                statusFilterContent.classList.remove('show');
            }
        });
    }
    
    // Task search
    const taskSearch = document.getElementById('task-search');
    if (taskSearch) {
        taskSearch.addEventListener('input', () => {
            renderTasks();
        });
    }
}

// Scroll chat to bottom
function scrollToBottom() {
    if (!chatMessages) {
        chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
    }
    
    // Define a function to perform the scroll
    const performScroll = () => {
        // Check if element exists and has scrollHeight
        if (!chatMessages || !chatMessages.scrollHeight) return;
        
        // Calculate the amount to scroll (full height - visible height)
        const scrollAmount = chatMessages.scrollHeight - chatMessages.clientHeight;
        if (scrollAmount > 0) {
            chatMessages.scrollTop = scrollAmount;
            
            // Log for debugging
            console.log(`Scrolling to ${scrollAmount}px (scrollHeight: ${chatMessages.scrollHeight}px, clientHeight: ${chatMessages.clientHeight}px)`);
        }
    };
    
    // First attempt - immediate
    performScroll();
    
    // Second attempt - after a short delay (for browsers that need it)
    setTimeout(performScroll, 10);
    
    // Third attempt - after layout (most reliable)
    requestAnimationFrame(() => {
        performScroll();
        
        // Fourth attempt - after another layout cycle (for extreme cases)
        requestAnimationFrame(performScroll);
    });
    
    // Final attempt - after everything else has settled
    setTimeout(performScroll, 100);
}

// Update status bar
function updateStatusBar() {
    // Try to get status elements if they're not already defined
    if (!agentStatus) agentStatus = document.getElementById('agent-status');
    if (!timeStatus) timeStatus = document.getElementById('time-status');
    if (!connectionStatus) connectionStatus = document.getElementById('connection-status');
    
    if (agentStatus) {
        // Always display agent name in uppercase in the status bar
        const displayName = currentAgentName.toUpperCase();
        
        // Special handling for SCOUT agent
        if (currentAgentName.toUpperCase() === 'SCOUT') {
            console.log("SCOUT AGENT DETECTED - Updating status bar");
        }
        
        agentStatus.textContent = `AGENT: ${displayName}`;
        console.log(`Updated status bar with agent name: ${displayName}`);
        
        // Force the status bar to update immediately
        agentStatus.style.color = displayName === 'SCOUT' ? 'var(--term-blue)' : 'var(--term-amber)';
        setTimeout(() => {
            agentStatus.style.color = 'var(--term-amber)';
        }, 100);
    } else {
        console.log('Agent status element not found yet, will retry later');
    }
    
    // Update clock
    updateClock();
    
    // Set initial connection status if needed
    if (connectionStatus && !connectionStatus.textContent) {
        connectionStatus.textContent = 'CONNECTION: ACTIVE';
    }
}

// Update clock in status bar
function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    
    // Try to get time status element if it's not already defined
    if (!timeStatus) timeStatus = document.getElementById('time-status');
    
    if (timeStatus) {
        timeStatus.textContent = `TIME: ${timeString}`;
    }
}

// Generate a UUID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Initialize voice wave animation
function initVoiceWaveAnimation() {
    const voiceBars = document.querySelectorAll('.voice-bar');
    if (!voiceBars.length) return;
    
    // Set random heights for voice bars
    voiceBars.forEach(bar => {
        const randomHeight = 4 + Math.floor(Math.random() * 9); // Random height between 4-12px
        bar.style.height = `${randomHeight}px`;
        
        // Set color to accent blue
        bar.style.backgroundColor = 'var(--accent-blue)';
    });
    
    // Animate voice bars with random heights
    setInterval(() => {
        voiceBars.forEach(bar => {
            setTimeout(() => {
                const randomHeight = 4 + Math.floor(Math.random() * 9); // Random height between 4-12px
                bar.style.height = `${randomHeight}px`;
            }, Math.random() * 200); // Random delay up to 200ms
        });
    }, 300); // Update heights every 300ms
}

// Close emoji suggestions when clicking outside
document.addEventListener('click', function(event) {
    // Check if emoji suggestions element exists and if click is outside of it
    if (emojiSuggestionsElement && 
        !emojiSuggestionsElement.contains(event.target) && 
        event.target !== chatInput) {
        hideEmojiSuggestions();
    }
    
    // Check if click is outside the command suggestions and input
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    if (commandSuggestionsElement && 
        !commandSuggestionsElement.contains(event.target) && 
        event.target !== chatInput) {
        hideCommandSuggestions();
    }
});

// Theme functionality has been removed

// Matrix effect functionality has been removed

// Settings dialog functionality has been removed

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', init);