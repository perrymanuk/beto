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
const projectFilter = document.getElementById('project-filter');
const statusFilter = document.getElementById('status-filter');
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
    projectFilter.addEventListener('change', handleProjectFilterChange);
    statusFilter.addEventListener('change', filterTasks);
    taskSearch.addEventListener('input', filterTasks);
    
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
            statusText.innerHTML = `Agent: RadBot | time: ${timestamp} | connection: active`;
            sendButton.disabled = false;
            chatInput.disabled = false;
            break;
        case 'thinking':
            statusText.innerHTML = `Agent: RadBot | time: ${timestamp} | processing...`;
            sendButton.disabled = true;
            break;
        case 'disconnected':
            statusText.innerHTML = `Agent: offline | time: ${timestamp} | connection lost`;
            break;
        case 'error':
            statusText.innerHTML = `Agent: error | time: ${timestamp} | refresh required`;
            break;
        default:
            if (status.startsWith('error:')) {
                statusText.innerHTML = `Agent: error | time: ${timestamp} | ${status.replace('error:', '')}`;
                sendButton.disabled = false;
                chatInput.disabled = false;
            } else {
                statusText.innerHTML = `Agent: RadBot | time: ${timestamp} | ${status}`;
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
    tasksPanelVisible = !tasksPanelVisible;
    
    if (tasksPanelVisible) {
        tasksPanel.classList.remove('hidden');
        if (!tasks.length && taskApiSettings.endpoint) {
            refreshTasks();
        }
    } else {
        tasksPanel.classList.add('hidden');
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
    // Clear all options except "All Projects"
    while (projectFilter.options.length > 1) {
        projectFilter.remove(1);
    }
    
    // Add project options
    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project.project_id;
        option.textContent = project.name;
        projectFilter.appendChild(option);
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
    
    const projectId = projectFilter.value === 'all' ? null : projectFilter.value;
    const endpoint = projectId 
        ? `${taskApiSettings.endpoint}/api/v1/projects/${projectId}/tasks` 
        : `${taskApiSettings.endpoint}/api/v1/tasks`;
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

// Handle project filter change
function handleProjectFilterChange() {
    console.log('Project filter changed to:', projectFilter.value);
    fetchTasks(); // Re-fetch tasks with the new project filter
}

// Filter tasks based on status and search (not project - that's handled by re-fetching)
function filterTasks() {
    const searchQuery = taskSearch.value.toLowerCase();
    const statusValue = statusFilter.value;
    
    console.log('Filtering tasks - Status:', statusValue, 'Search:', searchQuery);
    
    // Get all task elements
    const taskElements = document.querySelectorAll('.task-item');
    
    // Loop through all tasks and show/hide based on filters
    taskElements.forEach(taskElement => {
        const taskId = taskElement.dataset.taskId;
        const task = tasks.find(t => t.task_id === taskId);
        
        if (!task) return;
        
        // Check if task matches status filter
        const statusMatch = statusValue === 'all' || task.status === statusValue;
        
        // Check if task matches search query
        const searchMatch = searchQuery === '' || 
            task.description.toLowerCase().includes(searchQuery) ||
            (task.category && task.category.toLowerCase().includes(searchQuery));
        
        // Show or hide task
        if (statusMatch && searchMatch) {
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
    
    // Add tasks to container
    tasks.forEach(task => {
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