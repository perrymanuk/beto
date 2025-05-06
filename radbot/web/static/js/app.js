/**
 * RadBot Web Interface Client
 */

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const resetButton = document.getElementById('reset-button');

// Status Bar Elements
const agentStatus = document.getElementById('agent-status');
const timeStatus = document.getElementById('time-status');
const connectionStatus = document.getElementById('connection-status');

// Events Panel Elements
const eventsPanel = document.getElementById('events-panel');
const toggleEventsButton = document.getElementById('toggle-events-button');
const clearEventsButton = document.getElementById('clear-events-button');
const eventTypeFilter = document.getElementById('event-type-filter');
const eventsContainer = document.getElementById('events-container');
const eventDetails = document.getElementById('event-details');
const eventDetailsContent = document.getElementById('event-details-content');
const closeDetailsButton = document.getElementById('close-details-button');

// Tasks Panel Elements
const tasksPanel = document.getElementById('tasks-panel');
const toggleTasksButton = document.getElementById('toggle-tasks-button');
const refreshTasksButton = document.getElementById('refresh-tasks-button');
const settingsTasksButton = document.getElementById('settings-tasks-button');
const projectFilterBtn = document.getElementById('project-filter-btn');
const projectFilterContent = document.getElementById('project-filter-content');
const statusFilterBtn = document.getElementById('status-filter-btn');
const statusFilterContent = document.getElementById('status-filter-content');
const projectAllCheckbox = document.getElementById('project-all');
const statusAllCheckbox = document.getElementById('status-all');
const taskSearch = document.getElementById('task-search');
const tasksContainer = document.getElementById('tasks-container');
const taskSettingsDialog = document.getElementById('task-settings-dialog');
const apiEndpointInput = document.getElementById('api-endpoint');
const apiKeyInput = document.getElementById('api-key');
const defaultProjectSelect = document.getElementById('default-project');
const saveSettingsButton = document.getElementById('save-settings-button');
const testConnectionButton = document.getElementById('test-connection-button');
const closeDialogButton = document.querySelector('.close-dialog-button');

// Task Details View Elements
const taskDetailsView = document.getElementById('task-details-view');
const taskDetailsContent = document.getElementById('task-details-content');
const closeTaskDetailsButton = document.getElementById('close-task-details-button');
const backToTasksButton = document.getElementById('back-to-tasks-button');

// Emoji Suggestions Element
const emojiSuggestionsElement = document.getElementById('emoji-suggestions');

// State
let sessionId = localStorage.getItem('radbot_session_id') || null;
let socket = null;
let socketConnected = false;
let events = [];
let activeEventId = null;
let eventsPanelVisible = false;
let tasksPanelVisible = false;
let tasks = [];
let projects = [];
let selectedProjects = ['all'];
let selectedStatuses = ['all'];
let projectFilterOpen = false;
let statusFilterOpen = false;
let currentAgentName = "BETO"; // Track current agent name - use uppercase to match status bar
let taskApiSettings = {
    endpoint: localStorage.getItem('task_api_endpoint') || 'http://localhost:8001',
    apiKey: localStorage.getItem('task_api_key') || '',
    defaultProject: localStorage.getItem('task_default_project') || ''
};

// Emoji autocomplete state
let emojiSuggestions = [];
let activeSuggestionIndex = -1;
let activeShortcodeStart = -1;
let activeShortcodeEnd = -1;

// Voice animation constants
const VOICE_BAR_COLOR = 'var(--term-text)';

// Fix for border alignment issue
function fixBorderAlignment() {
    // Force the container to be full width but not too wide to cause scrolling
    const appContainer = document.getElementById('app-container');
    if (appContainer) {
        // Set the exact dimensions
        appContainer.style.width = '96vw';
        appContainer.style.height = '96vh';
        appContainer.style.maxWidth = 'none';
        
        // Make sure everything inside stays contained
        appContainer.style.overflow = 'hidden';
        
        // Force the body to center the container
        document.body.style.display = 'flex';
        document.body.style.justifyContent = 'center';
        document.body.style.alignItems = 'center';
        document.body.style.overflow = 'hidden';
        document.body.style.margin = '0';
        document.body.style.padding = '0';
        document.body.style.width = '100%';
        document.body.style.height = '100%';
        
        // Ensure background color extends to edge
        document.body.style.backgroundColor = '#121212';
    }
}

// Initialize
function init() {
    // Create session ID if not exists
    if (!sessionId) {
        sessionId = generateUUID();
        localStorage.setItem('radbot_session_id', sessionId);
    }
    
    // Initialize panels state
    eventsPanel.classList.add('hidden');
    eventsPanelVisible = false;
    
    tasksPanel.classList.add('hidden');
    tasksPanelVisible = false;
    
    // Apply border fix
    fixBorderAlignment();
    window.addEventListener('resize', fixBorderAlignment);
    
    // Initialize voice wave animation
    initVoiceWaveAnimation();
    
    // Initialize status bar
    updateStatusBar();
    
    // Start clock
    updateClock();
    setInterval(updateClock, 1000);
    
    connectWebSocket();
    
    // Load task API settings
    loadTaskSettings();
    
    // Chat event listeners
    chatInput.addEventListener('keydown', handleInputKeydown);
    sendButton.addEventListener('click', sendMessage);
    resetButton.addEventListener('click', resetConversation);
    
    // Events panel event listeners
    toggleEventsButton.addEventListener('click', toggleEventsPanel);
    clearEventsButton.addEventListener('click', clearEvents);
    eventTypeFilter.addEventListener('change', filterEvents);
    closeDetailsButton.addEventListener('click', closeEventDetails);
    
    // Tasks panel event listeners
    toggleTasksButton.addEventListener('click', toggleTasksPanel);
    refreshTasksButton.addEventListener('click', refreshTasks);
    settingsTasksButton.addEventListener('click', showTaskSettings);
    projectFilterBtn.addEventListener('click', toggleProjectFilter);
    statusFilterBtn.addEventListener('click', toggleStatusFilter);
    projectAllCheckbox.addEventListener('change', handleProjectAllCheckbox);
    statusAllCheckbox.addEventListener('change', handleStatusAllCheckbox);
    taskSearch.addEventListener('input', filterTasks);
    
    // Close the dropdowns when clicking outside of them
    document.addEventListener('click', handleClickOutsideDropdowns);
    
    // Task details view event listeners
    closeTaskDetailsButton.addEventListener('click', closeTaskDetails);
    backToTasksButton.addEventListener('click', closeTaskDetails);
    
    // Settings dialog event listeners
    closeDialogButton.addEventListener('click', hideTaskSettings);
    saveSettingsButton.addEventListener('click', saveTaskSettings);
    testConnectionButton.addEventListener('click', testTaskApiConnection);
    
    // Auto-resize textarea as user types
    chatInput.addEventListener('input', function(event) {
        resizeTextarea();
        handleEmojiAutocomplete(event);
    });
    
    // Handle keyboard navigation for emoji suggestions
    chatInput.addEventListener('keydown', handleEmojiKeyNavigation);
    
    // Initialize task panel if settings are available
    if (taskApiSettings.endpoint) {
        // Setup status checkboxes
        setupStatusCheckboxes();
        
        // Fetch projects and tasks
        fetchProjects().then(() => {
            fetchTasks();
        });
    }
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
    // If emoji suggestions are showing, don't send on Enter
    if (event.key === 'Enter' && !event.shiftKey && emojiSuggestions.length === 0) {
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
    emojiSuggestionsElement.classList.add('hidden');
    emojiSuggestions = [];
    activeSuggestionIndex = -1;
    activeShortcodeStart = -1;
    activeShortcodeEnd = -1;
}

// Handle keyboard navigation for emoji suggestions
function handleEmojiKeyNavigation(event) {
    // Only process if suggestions are visible
    if (emojiSuggestions.length === 0 || emojiSuggestionsElement.classList.contains('hidden')) {
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

// Auto-resize textarea
function resizeTextarea() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
}

// Scroll chat to bottom
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update status bar
function updateStatusBar() {
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
        console.error('Agent status element not found in DOM. Element ID: agent-status');
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

// Event panel functions
function toggleEventsPanel() {
    // If events panel is not visible, we're about to show it
    if (!eventsPanelVisible) {
        // Hide tasks panel if it's visible
        if (tasksPanelVisible) {
            tasksPanel.classList.add('hidden');
            tasksPanelVisible = false;
        }
        
        // Show events panel
        eventsPanel.classList.remove('hidden');
        eventsPanelVisible = true;
    } else {
        // Hide events panel
        eventsPanel.classList.add('hidden');
        eventsPanelVisible = false;
    }
}

function clearEvents() {
    events = [];
    renderEvents();
    closeEventDetails();
}

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
        
        // Update UI
        renderEvents();
    }
}

// Function to update status text with current agent name
function updateStatusText() {
    // Update the agent name in the status bar
    if (agentStatus) {
        // Always display agent name in uppercase in the status bar
        const displayName = currentAgentName.toUpperCase();
        agentStatus.textContent = `AGENT: ${displayName}`;
        console.log(`Status text updated with agent name: ${currentAgentName.toUpperCase()}`);
    }
    
    // Make sure time is up to date
    updateClock();
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
            // If it's not valid JSON, try to extract JSON-like content
            // This helps with string representations of objects
            try {
                // Match content between curly braces including nested structures
                const matches = obj.match(/\{(?:[^{}]|(\{(?:[^{}]|\{[^{}]*\})*\}))*\}/g);
                if (matches && matches.length > 0) {
                    // Try to parse each match
                    const results = matches.map(match => {
                        try {
                            // Replace single quotes with double quotes for JSON parsing
                            const fixedJson = match.replace(/(['"])?([a-zA-Z0-9_]+)(['"])?:/g, '"$2":')
                                                  .replace(/'/g, '"');
                            const parsed = JSON.parse(fixedJson);
                            return JSON.stringify(parsed, null, 2);
                        } catch (e) {
                            return match; // Return as is if parsing fails
                        }
                    });
                    
                    // Join the results
                    return results.join('\n\n');
                }
                
                // Try Python dict format: convert to JSON and parse
                const pyDictMatch = obj.match(/\{[^}]*\}/g);
                if (pyDictMatch) {
                    // Replace Python-style quotes and formatting with JSON style
                    const jsonLike = obj.replace(/'/g, '"')
                                       .replace(/None/g, 'null')
                                       .replace(/True/g, 'true')
                                       .replace(/False/g, 'false');
                    try {
                        const parsed = JSON.parse(jsonLike);
                        return JSON.stringify(parsed, null, 2);
                    } catch (e) {
                        // If still fails, do basic formatting
                        return obj.replace(/,/g, ',\n  ')
                                 .replace(/{/g, '{\n  ')
                                 .replace(/}/g, '\n}');
                    }
                }
            } catch (innerError) {
                // If all fails, return with basic formatting
                return obj.replace(/,/g, ',\n')
                         .replace(/{/g, '{\n  ')
                         .replace(/}/g, '\n}');
            }
            
            // If all formatting attempts fail, return as is
            return obj;
        }
    }
    
    try {
        return JSON.stringify(obj, null, 2);
    } catch (e) {
        // For non-JSON objects, try to format the string representation
        const str = String(obj);
        return str.replace(/,/g, ',\n  ')
                 .replace(/{/g, '{\n  ')
                 .replace(/}/g, '\n}');
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

// Task API Functions

// Tasks Panel Toggle
function toggleTasksPanel() {
    // If tasks panel is not visible, we're about to show it
    if (!tasksPanelVisible) {
        // Hide events panel if it's visible
        if (eventsPanelVisible) {
            eventsPanel.classList.add('hidden');
            eventsPanelVisible = false;
        }
        
        // Show tasks panel
        tasksPanel.classList.remove('hidden');
        tasksPanelVisible = true;
        
        // Fetch tasks if needed
        if (!tasks.length && taskApiSettings.endpoint) {
            refreshTasks();
        }
    } else {
        // Hide tasks panel
        tasksPanel.classList.add('hidden');
        tasksPanelVisible = false;
    }
}

// Load task settings from localStorage
function loadTaskSettings() {
    // Set input values from stored settings
    apiEndpointInput.value = taskApiSettings.endpoint;
    apiKeyInput.value = taskApiSettings.apiKey;
    
    // Populate default project later when projects are loaded
}

// Show task settings dialog
function showTaskSettings() {
    taskSettingsDialog.classList.remove('hidden');
    
    // Load current settings
    apiEndpointInput.value = taskApiSettings.endpoint;
    apiKeyInput.value = taskApiSettings.apiKey;
    
    // If projects are already loaded, set the default project
    populateDefaultProjectDropdown();
}

// Hide task settings dialog
function hideTaskSettings() {
    taskSettingsDialog.classList.add('hidden');
}

// Save task settings
function saveTaskSettings() {
    // Get values from form
    const endpoint = apiEndpointInput.value.trim();
    const apiKey = apiKeyInput.value.trim();
    const defaultProject = defaultProjectSelect.value;
    
    // Update settings
    taskApiSettings.endpoint = endpoint;
    taskApiSettings.apiKey = apiKey;
    taskApiSettings.defaultProject = defaultProject;
    
    // Save to localStorage
    localStorage.setItem('task_api_endpoint', endpoint);
    localStorage.setItem('task_api_key', apiKey);
    localStorage.setItem('task_default_project', defaultProject);
    
    // Hide dialog
    hideTaskSettings();
    
    // Refresh tasks and projects
    fetchProjects().then(() => {
        fetchTasks();
    });
}

// Test connection to task API
async function testTaskApiConnection() {
    const endpoint = apiEndpointInput.value.trim();
    const apiKey = apiKeyInput.value.trim();
    
    if (!endpoint) {
        alert('Please enter an API endpoint');
        return;
    }
    
    try {
        const response = await fetch(`${endpoint}/api/v1/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...apiKey && { 'Authorization': `Bearer ${apiKey}` }
            }
        });
        
        if (response.ok) {
            alert('Connection successful! API is reachable.');
        } else {
            alert(`Connection failed with status: ${response.status}`);
        }
    } catch (error) {
        alert(`Connection failed: ${error.message}`);
    }
}

// Fetch projects from API
async function fetchProjects() {
    if (!taskApiSettings.endpoint) {
        console.warn('Task API endpoint not configured');
        return;
    }
    
    console.log('Fetching projects from:', `${taskApiSettings.endpoint}/api/v1/projects`);
    
    try {
        const response = await fetch(`${taskApiSettings.endpoint}/api/v1/projects`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...taskApiSettings.apiKey && { 'Authorization': `Bearer ${taskApiSettings.apiKey}` }
            }
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log('Projects API response:', data);
        
        // Check if the response is directly an array of projects
        if (Array.isArray(data)) {
            projects = data;
            console.log('Found', projects.length, 'projects');
            
            // Update project filter dropdown
            updateProjectFilter();
            
            // Update default project dropdown in settings
            populateDefaultProjectDropdown();
            
            return projects;
        } 
        // Check if it's wrapped in a data.projects property (API format fallback)
        else if (data.status === 'success' && Array.isArray(data.projects)) {
            projects = data.projects;
            
            // Update project filter dropdown
            updateProjectFilter();
            
            // Update default project dropdown in settings
            populateDefaultProjectDropdown();
            
            return projects;
        } else {
            console.error('Invalid API response format', data);
            return [];
        }
    } catch (error) {
        console.error('Error fetching projects:', error);
        return [];
    }
}

// Update project filter dropdown
function updateProjectFilter() {
    // Remove all dynamically added project options
    const existingOptions = projectFilterContent.querySelectorAll('.filter-option:not(:first-child)');
    existingOptions.forEach(option => option.remove());
    
    // Add project options as checkboxes
    projects.forEach(project => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'filter-option';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `project-${project.project_id}`;
        checkbox.value = project.project_id;
        checkbox.addEventListener('change', function() {
            handleProjectCheckboxChange(this);
        });
        
        const label = document.createElement('label');
        label.htmlFor = `project-${project.project_id}`;
        label.textContent = project.name;
        
        optionDiv.appendChild(checkbox);
        optionDiv.appendChild(label);
        projectFilterContent.appendChild(optionDiv);
    });
}

// Populate default project dropdown in settings
function populateDefaultProjectDropdown() {
    // Clear all options except first empty option
    while (defaultProjectSelect.options.length > 1) {
        defaultProjectSelect.remove(1);
    }
    
    // Add project options
    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project.project_id;
        option.textContent = project.name;
        defaultProjectSelect.appendChild(option);
    });
    
    // Set previously selected default project
    if (taskApiSettings.defaultProject) {
        defaultProjectSelect.value = taskApiSettings.defaultProject;
    }
}

// Fetch tasks from API
async function fetchTasks() {
    if (!taskApiSettings.endpoint) {
        console.warn('Task API endpoint not configured');
        return;
    }
    
    // Always fetch all tasks - the filtering will be done client-side
    const endpoint = `${taskApiSettings.endpoint}/api/v1/tasks`;
    console.log('Fetching tasks from:', endpoint);
    
    try {
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...taskApiSettings.apiKey && { 'Authorization': `Bearer ${taskApiSettings.apiKey}` }
            }
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log('Tasks API response:', data);
        
        // Check if the response is directly an array of tasks
        if (Array.isArray(data)) {
            tasks = data;
            console.log('Found', tasks.length, 'tasks');
            
            // Render tasks
            renderTasks();
            
            return tasks;
        }
        // Check if it's wrapped in a data.tasks property (API format fallback)
        else if (data.status === 'success' && Array.isArray(data.tasks)) {
            tasks = data.tasks;
            
            // Render tasks
            renderTasks();
            
            return tasks;
        } else {
            console.error('Invalid API response format', data);
            return [];
        }
    } catch (error) {
        console.error('Error fetching tasks:', error);
        return [];
    }
}

// Refresh tasks
function refreshTasks() {
    fetchTasks();
}

// Toggle project filter dropdown
function toggleProjectFilter(event) {
    event.stopPropagation();
    
    // Toggle the dropdown
    projectFilterOpen = !projectFilterOpen;
    statusFilterOpen = false; // Close the other dropdown
    
    // Show/hide dropdowns
    projectFilterContent.classList.toggle('show', projectFilterOpen);
    statusFilterContent.classList.remove('show');
}

// Toggle status filter dropdown
function toggleStatusFilter(event) {
    event.stopPropagation();
    
    // Toggle the dropdown
    statusFilterOpen = !statusFilterOpen;
    projectFilterOpen = false; // Close the other dropdown
    
    // Show/hide dropdowns
    statusFilterContent.classList.toggle('show', statusFilterOpen);
    projectFilterContent.classList.remove('show');
}

// Handle click outside dropdowns
function handleClickOutsideDropdowns(event) {
    // Check if click is outside filter dropdowns
    if (!event.target.closest('.filter-dropdown')) {
        projectFilterContent.classList.remove('show');
        statusFilterContent.classList.remove('show');
        projectFilterOpen = false;
        statusFilterOpen = false;
    }
}

// Handle "All Projects" checkbox
function handleProjectAllCheckbox(event) {
    const checked = event.target.checked;
    
    // Get all project checkboxes
    const projectCheckboxes = projectFilterContent.querySelectorAll('input[type="checkbox"]:not(#project-all)');
    
    // If "All Projects" is checked, uncheck all others but don't disable them
    projectCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
        // Remove the disabling of checkboxes so they can still be clicked
        // checkbox.disabled = checked;
    });
    
    // Update selected projects
    if (checked) {
        selectedProjects = ['all'];
    } else {
        selectedProjects = [];
    }
    
    // Update filter button text
    updateProjectFilterButtonText();
    
    // Filter tasks
    filterTasks();
}

// Handle individual project checkbox changes
function handleProjectCheckboxChange(checkbox) {
    // If any individual project is checked, uncheck "All Projects"
    if (checkbox.checked) {
        projectAllCheckbox.checked = false;
        
        // Add to selected projects
        selectedProjects = selectedProjects.filter(p => p !== 'all');
        selectedProjects.push(checkbox.value);
    } else {
        // Remove from selected projects
        selectedProjects = selectedProjects.filter(p => p !== checkbox.value);
        
        // If no projects are selected, check "All Projects"
        if (selectedProjects.length === 0) {
            projectAllCheckbox.checked = true;
            selectedProjects = ['all'];
        }
    }
    
    // Update filter button text
    updateProjectFilterButtonText();
    
    // Filter tasks
    filterTasks();
}

// Handle "All Statuses" checkbox
function handleStatusAllCheckbox(event) {
    const checked = event.target.checked;
    
    // Get all status checkboxes
    const statusCheckboxes = statusFilterContent.querySelectorAll('input[type="checkbox"]:not(#status-all)');
    
    // If "All Statuses" is checked, uncheck all others but don't disable them
    statusCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
        // Remove the disabling of checkboxes so they can still be clicked
        // checkbox.disabled = checked;
    });
    
    // Update selected statuses
    if (checked) {
        selectedStatuses = ['all'];
    } else {
        selectedStatuses = [];
    }
    
    // Update filter button text
    updateStatusFilterButtonText();
    
    // Filter tasks
    filterTasks();
}

// Update project filter button text based on selection
function updateProjectFilterButtonText() {
    if (selectedProjects.includes('all')) {
        projectFilterBtn.textContent = 'All Projects';
    } else if (selectedProjects.length === 1) {
        const project = projects.find(p => p.project_id === selectedProjects[0]);
        projectFilterBtn.textContent = project ? project.name : 'Unknown Project';
    } else {
        projectFilterBtn.textContent = `${selectedProjects.length} Projects`;
    }
}

// Update status filter button text based on selection
function updateStatusFilterButtonText() {
    if (selectedStatuses.includes('all')) {
        statusFilterBtn.textContent = 'All Statuses';
    } else if (selectedStatuses.length === 0) {
        statusFilterBtn.textContent = 'No Status';
    } else if (selectedStatuses.length === 1) {
        const statusMap = {
            'backlog': 'Backlog',
            'inprogress': 'In Progress',
            'done': 'Done'
        };
        statusFilterBtn.textContent = statusMap[selectedStatuses[0]] || selectedStatuses[0];
    } else {
        statusFilterBtn.textContent = `${selectedStatuses.length} Statuses`;
    }
}

// Add status checkbox change event listeners
function setupStatusCheckboxes() {
    const statusCheckboxes = statusFilterContent.querySelectorAll('input[type="checkbox"]:not(#status-all)');
    statusCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            handleStatusCheckboxChange(this);
        });
    });
}

// Handle individual status checkbox changes
function handleStatusCheckboxChange(checkbox) {
    // If any individual status is checked, uncheck "All Statuses"
    if (checkbox.checked) {
        statusAllCheckbox.checked = false;
        
        // Add to selected statuses
        selectedStatuses = selectedStatuses.filter(s => s !== 'all');
        selectedStatuses.push(checkbox.value);
    } else {
        // Remove from selected statuses
        selectedStatuses = selectedStatuses.filter(s => s !== checkbox.value);
        
        // If no statuses are selected, check "All Statuses"
        if (selectedStatuses.length === 0) {
            statusAllCheckbox.checked = true;
            selectedStatuses = ['all'];
        }
    }
    
    // Update filter button text
    updateStatusFilterButtonText();
    
    // Filter tasks
    filterTasks();
}

// Filter tasks based on selected statuses, projects, and search
function filterTasks() {
    const searchQuery = taskSearch.value.toLowerCase();
    
    console.log('Filtering tasks - Statuses:', selectedStatuses, 'Projects:', selectedProjects, 'Search:', searchQuery);
    
    // Get all task elements
    const taskElements = document.querySelectorAll('.task-item');
    
    // Loop through all tasks and show/hide based on filters
    taskElements.forEach(taskElement => {
        const taskId = taskElement.dataset.taskId;
        const task = tasks.find(t => t.task_id === taskId);
        
        if (!task) return;
        
        // Check if task matches status filter
        const statusMatch = selectedStatuses.includes('all') || 
                         selectedStatuses.includes(task.status);
        
        // Check if task matches project filter
        const projectMatch = selectedProjects.includes('all') || 
                          selectedProjects.includes(task.project_id);
        
        // Check if task matches search query
        const searchMatch = searchQuery === '' || 
            task.description.toLowerCase().includes(searchQuery) ||
            (task.category && task.category.toLowerCase().includes(searchQuery));
        
        // Show or hide task
        if (statusMatch && projectMatch && searchMatch) {
            taskElement.style.display = '';
        } else {
            taskElement.style.display = 'none';
        }
    });
}

// Render tasks in container
function renderTasks() {
    // Clear container
    tasksContainer.innerHTML = '';
    
    if (tasks.length === 0) {
        tasksContainer.innerHTML = '<div class="tasks-empty-state">No tasks found.</div>';
        return;
    }
    
    // Sort tasks by status (inprogress first, then backlog, then done)
    const sortedTasks = [...tasks].sort((a, b) => {
        const statusOrder = { 'inprogress': 0, 'backlog': 1, 'done': 2 };
        return statusOrder[a.status] - statusOrder[b.status];
    });
    
    // Add tasks to container
    sortedTasks.forEach(task => {
        const taskElement = createTaskElement(task);
        tasksContainer.appendChild(taskElement);
    });
    
    // Apply filters
    filterTasks();
}

// Create a task element
function createTaskElement(task) {
    const taskElement = document.createElement('div');
    taskElement.className = `task-item ${task.status || 'backlog'}`;
    taskElement.dataset.taskId = task.task_id;
    
    // Status indicator (instead of interactive checkbox)
    const statusIndicator = document.createElement('div');
    statusIndicator.className = `task-status-indicator ${task.status}`;
    statusIndicator.title = `Status: ${task.status}`;
    taskElement.appendChild(statusIndicator);
    
    // Add task content
    const content = document.createElement('div');
    content.className = 'task-content';
    content.textContent = task.description;
    taskElement.appendChild(content);
    
    // Add project label if projects are available
    if (task.project_id) {
        const project = projects.find(p => p.project_id === task.project_id);
        console.log('Task project ID:', task.project_id, 'Found project:', project);
        
        // Check for project_name directly on the task (some APIs return this)
        if (task.project_name) {
            const projectLabel = document.createElement('div');
            projectLabel.className = 'task-project';
            projectLabel.textContent = task.project_name;
            taskElement.appendChild(projectLabel);
        }
        // Otherwise try to look up the project in our projects list
        else if (project) {
            const projectLabel = document.createElement('div');
            projectLabel.className = 'task-project';
            projectLabel.textContent = project.name;
            taskElement.appendChild(projectLabel);
        }
    }
    
    // View details icon
    const viewIcon = document.createElement('div');
    viewIcon.className = 'task-view-icon';
    viewIcon.innerHTML = '→';
    viewIcon.title = 'View task details';
    taskElement.appendChild(viewIcon);
    
    // Add click handler for the entire task item
    taskElement.addEventListener('click', () => {
        showTaskDetails(task);
    });
    
    return taskElement;
}

// Task-related functions have been removed since the UI is now read-only
// The task detail view is now used to display task information when a task is clicked

// Show task details
function showTaskDetails(task) {
    // Clear existing content
    taskDetailsContent.innerHTML = '';
    
    // Create HTML for task details
    let html = '';
    
    // Task ID and Description (header)
    html += `<div class="task-field">
                <div class="task-field-label">Task ID</div>
                <div class="task-field-value">${task.task_id}</div>
            </div>`;
    
    // Description
    html += `<div class="task-field">
                <div class="task-field-label">Description</div>
                <div class="task-field-value description">${task.description}</div>
            </div>`;
    
    // Status
    html += `<div class="task-field">
                <div class="task-field-label">Status</div>
                <div class="task-field-value">
                    <span class="task-status-indicator ${task.status}"></span>
                    ${task.status}
                </div>
            </div>`;
    
    // Project (if available)
    if (task.project_id) {
        const projectName = task.project_name || 
            (projects.find(p => p.project_id === task.project_id)?.name || 'Unknown Project');
        
        html += `<div class="task-field">
                    <div class="task-field-label">Project</div>
                    <div class="task-field-value">${projectName}</div>
                </div>`;
    }
    
    // Created Date (if available)
    if (task.created_at) {
        html += `<div class="task-field">
                    <div class="task-field-label">Created</div>
                    <div class="task-field-value">${new Date(task.created_at).toLocaleString()}</div>
                </div>`;
    }
    
    // Updated Date (if available)
    if (task.updated_at) {
        html += `<div class="task-field">
                    <div class="task-field-label">Last Updated</div>
                    <div class="task-field-value">${new Date(task.updated_at).toLocaleString()}</div>
                </div>`;
    }
    
    // Due Date (if available)
    if (task.due_date) {
        html += `<div class="task-field">
                    <div class="task-field-label">Due Date</div>
                    <div class="task-field-value">${new Date(task.due_date).toLocaleString()}</div>
                </div>`;
    }
    
    // Priority (if available)
    if (task.priority) {
        html += `<div class="task-field">
                    <div class="task-field-label">Priority</div>
                    <div class="task-field-value">${task.priority}</div>
                </div>`;
    }
    
    // Category (if available)
    if (task.category) {
        html += `<div class="task-field">
                    <div class="task-field-label">Category</div>
                    <div class="task-field-value">${task.category}</div>
                </div>`;
    }
    
    // Tags (if available)
    if (task.tags && task.tags.length > 0) {
        html += `<div class="task-field">
                    <div class="task-field-label">Tags</div>
                    <div class="task-field-value">${task.tags.join(', ')}</div>
                </div>`;
    }
    
    // Related Info (if available)
    if (task.related_info) {
        let relatedInfoContent = '';
        
        if (typeof task.related_info === 'string') {
            // Try to parse as JSON first
            try {
                const parsed = JSON.parse(task.related_info);
                relatedInfoContent = formatJSON(parsed);
            } catch (e) {
                relatedInfoContent = task.related_info;
            }
        } else {
            relatedInfoContent = formatJSON(task.related_info);
        }
        
        html += `<div class="task-field">
                    <div class="task-field-label">Related Information</div>
                    <div class="task-field-value related-info">${relatedInfoContent}</div>
                </div>`;
    }
    
    // Set the content
    taskDetailsContent.innerHTML = html;
    
    // Show the task details view
    taskDetailsView.classList.remove('hidden');
}

// Close task details view
function closeTaskDetails() {
    taskDetailsView.classList.add('hidden');
}

// Initialize voice wave animation
function initVoiceWaveAnimation() {
    const voiceBars = document.querySelectorAll('.voice-bar');
    if (!voiceBars.length) return;
    
    // Set random heights for voice bars
    voiceBars.forEach(bar => {
        const randomHeight = 5 + Math.floor(Math.random() * 11); // Random height between 5-15px
        bar.style.height = `${randomHeight}px`;
        
        // Set color to green (term-text)
        bar.style.backgroundColor = 'var(--term-text)';
    });
    
    // Animate voice bars with random heights
    setInterval(() => {
        voiceBars.forEach(bar => {
            setTimeout(() => {
                const randomHeight = 5 + Math.floor(Math.random() * 11); // Random height between 5-15px
                bar.style.height = `${randomHeight}px`;
            }, Math.random() * 200); // Random delay up to 200ms
        });
    }, 300); // Update heights every 300ms
}

// Close emoji suggestions when clicking outside
document.addEventListener('click', function(event) {
    // Check if click is outside the emoji suggestions and input
    if (!emojiSuggestionsElement.contains(event.target) && 
        event.target !== chatInput) {
        hideEmojiSuggestions();
    }
});

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', init);