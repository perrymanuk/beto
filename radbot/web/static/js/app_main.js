/**
 * RadBot Web Interface Client - Main Module
 * 
 * This is the entry point for the RadBot UI application,
 * responsible for initializing all the modules and managing the application state.
 */

// Import all modules
import * as chatModule from './chat.js';
import * as emojiUtils from './emoji.js';
import * as commandUtils from './commands.js';
import * as statusUtils from './status.js';
import * as selectsUtils from './selects.js';
import * as socketClient from './socket.js';
import { ChatPersistence, mergeMessages } from './chat_persistence.js';

// Global state
const state = {
    sessionId: localStorage.getItem('radbot_session_id') || null,
    currentAgentName: "BETO", // Track current agent name - use uppercase to match status bar
    currentModel: "gemini-2.5-pro", // Default model - will be updated with actual model info from events
    isDarkTheme: true, // Always use dark theme
    // Hardcode task API settings since settings dialog is removed
    taskApiSettings: {
        endpoint: 'http://localhost:8001',
        apiKey: '',
        defaultProject: ''
    }
};

// Initialize chat persistence
const chatPersistence = new ChatPersistence({
    maxMessagesPerChat: 200,
    storagePrefix: 'radbot_chat_'
});

// Log the expected storage key for the current session
console.log('Expected localStorage key:', `radbot_chat_${state.sessionId || 'undefined'}`);

// Global data
let events = [];
let tasks = [];
let projects = [];
let socket = null;

// Make modules and utilities globally available
window.chatModule = chatModule;
window.emojiUtils = emojiUtils;
window.commandUtils = commandUtils;
window.statusUtils = statusUtils;
window.selectsUtils = selectsUtils;
window.socket = null;
window.state = state;
window.events = events;
window.tasks = tasks;
window.projects = projects;
window.chatPersistence = chatPersistence;

// Make chat persistence utilities globally available
window.mergeMessages = mergeMessages;

// Test localStorage directly to ensure it's working
function testLocalStorage() {
    try {
        const testKey = 'radbot_test_key';
        const testValue = { test: true, timestamp: Date.now() };
        const testString = JSON.stringify(testValue);
        
        // Save test value
        localStorage.setItem(testKey, testString);
        console.log('Test localStorage.setItem succeeded:', testKey, testString);
        
        // Retrieve test value
        const retrieved = localStorage.getItem(testKey);
        console.log('Test localStorage.getItem retrieved:', retrieved);
        
        // Cleanup
        localStorage.removeItem(testKey);
        console.log('Test localStorage.removeItem succeeded');
        
        return retrieved === testString;
    } catch (error) {
        console.error('localStorage test failed:', error);
        return false;
    }
}

// Initialize
function init() {
    console.log('Initializing app_main.js');
    
    // Test localStorage
    const localStorageWorking = testLocalStorage();
    console.log('localStorage working:', localStorageWorking);
    
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
        if (!chatModule.getChatElements().input) {
            console.log('Attempting UI initialization via timeout');
            initializeUI();
        }
    }, 300);
    
    // Create or retrieve persistent session ID
    if (!state.sessionId) {
        state.sessionId = crypto.randomUUID ? crypto.randomUUID() : generateUUID();
        localStorage.setItem('radbot_session_id', state.sessionId);
        console.log('Created new session ID:', state.sessionId);
    } else {
        console.log('Using existing session ID:', state.sessionId);
    }
    
    // Set up event listener for chat data changes from other tabs
    window.addEventListener('chatDataChanged', (event) => {
        console.log('Chat data changed event received:', event.detail);
        
        // Only reload if the change was for our current session
        if (event.detail.chatId === state.sessionId) {
            // Load and render chat messages from local storage
            loadChatFromStorage();
        }
    });
    
    // Set flag to prevent duplicate message storage during initial load
    window.initialLoadInProgress = true;
    
    // Load any existing chat messages from local storage
    loadChatFromStorage();
    
    // Clear the flag after loading completes
    window.initialLoadInProgress = false;
    
    // Connect to WebSocket immediately
    window.socket = socketClient.initSocket(state.sessionId);
    
    // Fetch tasks, projects, and events directly from API
    fetchTasks();
    fetchEvents();
    
    // Get initial agent and model information
    fetchAgentInfo();
}

// Load chat messages from local storage
function loadChatFromStorage() {
    if (!state.sessionId) {
        console.error('Cannot load chat: No session ID available');
        return;
    }
    
    console.log(`Attempting to load messages for session ${state.sessionId}`);
    
    try {
        // Store original storage items for inspection
        const storage = localStorage;
        const allItems = {};
        const relevantItems = {};
        
        // Log all localStorage keys for debugging
        console.log('All localStorage keys:');
        for (let i = 0; i < storage.length; i++) {
            const key = storage.key(i);
            allItems[key] = storage.getItem(key);
            console.log(`${i}: ${key} = ${storage.getItem(key).substring(0, 50)}...`);
            
            if (key && (key.includes('radbot') || key.includes('chat_'))) {
                relevantItems[key] = storage.getItem(key);
            }
        }
        
        console.log('Current localStorage items:', allItems);
        console.log('Relevant chat items:', relevantItems);
        
        // Get messages from storage
        const messages = chatPersistence.getMessages(state.sessionId);
        
        if (messages && messages.length > 0) {
            console.log(`Loaded ${messages.length} messages from storage for session ${state.sessionId}`);
            
            // Clear existing messages from UI
            if (chatModule.getChatElements().messages) {
                chatModule.getChatElements().messages.innerHTML = '';
            }
            
            // Add each message to the UI
            let loadCount = 0;
            messages.forEach(msg => {
                // Only add messages with valid roles
                if (msg.role && msg.content) {
                    chatModule.addMessage(msg.role, msg.content, msg.agent);
                    loadCount++;
                } else {
                    console.warn('Skipping invalid message:', msg);
                }
            });
            
            console.log(`Successfully rendered ${loadCount} messages`);
            
            // Scroll to the bottom after rendering all messages
            chatModule.scrollToBottom();
        } else {
            console.log('No stored messages found for this session');
        }
    } catch (error) {
        console.error('Error loading chat from storage:', error);
    }
}

// Make functions globally available for tiling manager
window.initializeUI = initializeUI;
window.renderTasks = renderTasks;
window.renderEvents = renderEvents;
window.updateModelForCurrentAgent = updateModelForCurrentAgent;

// Fetch data immediately when panels are opened
document.addEventListener('command:tasks', function() {
    console.log("Tasks panel opened - fetching latest data");
    fetchTasks();
});

document.addEventListener('command:events', function() {
    console.log("Events panel opened - fetching latest data");
    // Clear events cache before fetching to ensure we get fresh data
    events = [];
    window.events = [];
    
    // Wait for DOM to update, then fetch events
    setTimeout(() => {
        fetchEvents();
    }, 100);
});

// Initialize UI elements after DOM is ready
function initializeUI() {
    console.log('Initializing UI elements');
    
    // Initialize each module
    const chatInitialized = chatModule.initChat();
    const emojiInitialized = emojiUtils.initEmoji();
    const commandsInitialized = commandUtils.initCommands();
    const statusInitialized = statusUtils.initStatus();
    
    // If any critical modules failed to initialize, try again in a moment
    if (!chatInitialized) {
        console.log('Critical UI elements not found, retrying initialization...');
        setTimeout(initializeUI, 200);
        return;
    }
    
    console.log('UI elements initialized successfully');
    
    // Initialize voice wave animation
    initVoiceWaveAnimation();
    
    // Set up select components
    selectsUtils.initSelects();
    
    // Initialize event panel buttons
    initEventPanelButtons();
    
    // Initialize event type filter
    initEventTypeFilter();
    
    // Check if WebSocket needs to be initialized or reinitialized
    if (!window.socket) {
        window.socket = socketClient.initSocket(state.sessionId);
    }
}

// Initialize event panel buttons
function initEventPanelButtons() {
    const toggleEventsButton = document.getElementById('toggle-events-button');
    const toggleTasksButton = document.getElementById('toggle-tasks-button');
    
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
}

// Initialize event type filter
function initEventTypeFilter() {
    const eventTypeFilter = document.getElementById('event-type-filter');
    
    // Check if the events panel exists yet
    const eventsPanel = document.querySelector('[data-content="events"]');
    if (!eventsPanel) {
        // No need to spam console logs if panel isn't open yet
        return false;
    }
    
    if (eventTypeFilter) {
        console.log('Setting up event type filter');
        
        // Remove old event listeners by cloning
        const newFilter = eventTypeFilter.cloneNode(true);
        if (eventTypeFilter.parentNode) {
            eventTypeFilter.parentNode.replaceChild(newFilter, eventTypeFilter);
        }
        
        // Set up the new event listener
        newFilter.addEventListener('change', function() {
            console.log('Event type filter changed to:', this.value);
            renderEvents();
        });
        
        return true;
    } else {
        // Only retry a few times to avoid excessive logs
        console.log('Event type filter element not found, will retry once events panel opens');
        
        // Set up a mutation observer to detect when the events panel is created
        const observer = new MutationObserver((mutations) => {
            if (document.getElementById('event-type-filter')) {
                console.log('Event filter detected in DOM, initializing');
                observer.disconnect();
                setTimeout(initEventTypeFilter, 100);
            }
        });
        
        // Only observe if the events panel exists
        if (eventsPanel) {
            observer.observe(eventsPanel, { childList: true, subtree: true });
        }
        
        // Also listen for the events panel opening
        document.addEventListener('command:events', function eventsPanelOpened() {
            console.log('Events panel opened event detected');
            document.removeEventListener('command:events', eventsPanelOpened);
            setTimeout(initEventTypeFilter, 300);
        });
        
        return false;
    }
}

// Initialize voice wave animation
function initVoiceWaveAnimation() {
    const voiceWave = document.querySelector('.voice-wave-animation');
    if (!voiceWave) return;
    
    // Clear existing bars
    voiceWave.innerHTML = '';
    
    // Create bars
    const bars = 20;
    for (let i = 0; i < bars; i++) {
        const bar = document.createElement('div');
        bar.className = 'voice-bar';
        
        // Set random initial height and animation delay
        const height = 4 + Math.floor(Math.random() * 8);
        const delay = Math.random() * 0.5;
        
        bar.style.height = `${height}px`;
        bar.style.animation = `voice-wave-animation 1.5s ease-in-out ${delay}s infinite`;
        
        voiceWave.appendChild(bar);
    }
}

// Fetch tasks from API
async function fetchTasks() {
    console.log("Fetching tasks data...");
    try {
        // Try to fetch from the real API first
        try {
            const apiUrl = 'http://localhost:8001/api/tasks'; // Use the actual task API endpoint
            console.log(`Attempting to fetch real tasks data from ${apiUrl}`);
            
            const response = await fetch(apiUrl);
            
            if (response.ok) {
                const tasksData = await response.json();
                console.log("Successfully fetched real task data:", tasksData);
                
                // The API returns tasks as a direct array
                tasks = tasksData || [];
                
                // We need to fetch projects separately
                try {
                    const projectsResponse = await fetch('http://localhost:8001/api/projects');
                    if (projectsResponse.ok) {
                        projects = await projectsResponse.json();
                        console.log("Successfully fetched real projects data:", projects);
                    } else {
                        console.warn("Failed to fetch projects, using default project");
                        projects = [{project_id: "unknown", name: "Default"}];
                    }
                } catch (projectError) {
                    console.warn("Error fetching projects:", projectError);
                    projects = [{project_id: "unknown", name: "Default"}];
                }
                
                // Make available globally
                window.tasks = tasks;
                window.projects = projects;
                
                // Update selects module with projects
                selectsUtils.setProjects(projects);
                
                renderTasks();
                return;
            } else {
                console.warn(`Real API returned error status: ${response.status}. Will use mock data instead.`);
            }
        } catch (apiError) {
            console.warn("Failed to connect to real API:", apiError);
        }
        
        // If we get here, the real API failed - use mock data
        console.log("Using mock task data");
        
        // Mock data for testing
        tasks = [
            { task_id: "task1", title: "Implement login screen", status: "inprogress", priority: "high", project_id: "proj1" },
            { task_id: "task2", title: "Fix navigation bug", status: "backlog", priority: "medium", project_id: "proj1" },
            { task_id: "task3", title: "Update documentation", status: "done", priority: "low", project_id: "proj2" },
            { task_id: "task4", title: "Refactor database layer", status: "backlog", priority: "high", project_id: "proj2" },
            { task_id: "task5", title: "Add unit tests", status: "inprogress", priority: "medium", project_id: "proj1" }
        ];
        
        projects = [
            { project_id: "proj1", name: "Frontend App" },
            { project_id: "proj2", name: "Backend API" }
        ];
        
        // Make available globally
        window.tasks = tasks;
        window.projects = projects;
        
        // Update selects module with projects
        selectsUtils.setProjects(projects);
        
        renderTasks();
    } catch (error) {
        console.error('Unexpected error in fetchTasks:', error);
        
        // Fall back to simple mock data if everything else fails
        tasks = [{ task_id: "error1", title: "Error fetching tasks", status: "backlog", priority: "high", project_id: "error" }];
        projects = [{ project_id: "error", name: "Error" }];
        
        window.tasks = tasks;
        window.projects = projects;
        selectsUtils.setProjects(projects);
        renderTasks();
    }
}

// Render tasks in UI
function renderTasks() {
    const tasksContainer = document.getElementById('tasks-container');
    if (!tasksContainer) return;
    
    // Clear existing tasks
    tasksContainer.innerHTML = '';
    
    // Get the selection state
    const { selectedProject, selectedStatus } = selectsUtils.getSelectionState();
    
    // Filter tasks
    const filteredTasks = tasks.filter(task => {
        // Handle project filtering with both project_id and project_name
        let projectMatch = selectedProject === 'all';
        if (!projectMatch) {
            if (task.project_name) {
                // Try to match by project name if it exists on the task
                const project = projects.find(p => p.name === task.project_name);
                if (project) {
                    projectMatch = project.project_id === selectedProject;
                }
            }
            // If we still don't have a match, try the project_id directly
            if (!projectMatch) {
                projectMatch = task.project_id === selectedProject;
            }
        }
        
        const statusMatch = selectedStatus === 'all' || selectedStatus === task.status;
        return projectMatch && statusMatch;
    });
    
    // Sort tasks - priority first, then by status
    filteredTasks.sort((a, b) => {
        // First sort by priority
        const priorityOrder = { high: 1, medium: 2, low: 3 };
        const priorityA = priorityOrder[a.priority] || 4;
        const priorityB = priorityOrder[b.priority] || 4;
        
        if (priorityA !== priorityB) {
            return priorityA - priorityB;
        }
        
        // Then sort by status
        const statusOrder = { inprogress: 1, backlog: 2, done: 3 };
        const statusA = statusOrder[a.status] || 4;
        const statusB = statusOrder[b.status] || 4;
        
        return statusA - statusB;
    });
    
    // Render each task
    filteredTasks.forEach(task => {
        const taskItem = document.createElement('div');
        taskItem.className = `task-item ${task.status}`;
        taskItem.dataset.id = task.task_id;
        
        const taskStatus = document.createElement('div');
        taskStatus.className = `task-status-indicator ${task.status}`;
        
        const taskTitle = document.createElement('div');
        taskTitle.className = 'task-title';
        // Use description as title for API data, or title for mock data
        taskTitle.textContent = task.description || task.title || "Untitled Task";
        
        const taskProject = document.createElement('div');
        taskProject.className = 'task-project';
        
        // First try to use project_name if it exists directly on the task
        if (task.project_name) {
            taskProject.textContent = task.project_name;
        } else {
            // Fall back to looking up by project_id
            const project = projects.find(p => p.project_id === task.project_id);
            taskProject.textContent = project ? project.name : (task.project_id || "Unknown Project");
        }
        
        taskItem.appendChild(taskStatus);
        taskItem.appendChild(taskTitle);
        taskItem.appendChild(taskProject);
        
        // Add click handler to show task details
        taskItem.addEventListener('click', () => {
            commandUtils.executeCommand(`/details ${task.task_id}`);
        });
        
        tasksContainer.appendChild(taskItem);
    });
    
    // Show a message if no tasks found
    if (filteredTasks.length === 0) {
        const noTasksMsg = document.createElement('div');
        noTasksMsg.className = 'no-items-message';
        noTasksMsg.textContent = 'No tasks match the current filters';
        tasksContainer.appendChild(noTasksMsg);
    }
}

// Fetch events from API
async function fetchEvents() {
    console.log("Fetching events data...");
    try {
        // Determine the API base URL - use current origin
        const baseUrl = `${window.location.protocol}//${window.location.host}`;
        
        // Get the current session ID - reuse the one from socket connection if available
        const sessionId = state.sessionId || localStorage.getItem('radbot_session_id') || generateUUID();
        
        // Based on custom_web_ui.md - we need to use the session API endpoint
        const apiUrl = `${baseUrl}/api/events/${sessionId}`;
        console.log(`Attempting to fetch events data from ${apiUrl}`);
        
        try {
            // Make the API request
            const response = await fetch(apiUrl, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Parse the response
                const data = await response.json();
                console.log("Successfully fetched events data:", data);
                
                if (data && Array.isArray(data)) {
                    // Direct array of events
                    events = data;
                } else if (data && data.events && Array.isArray(data.events)) {
                    // Object with events array property
                    events = data.events;
                } else {
                    console.warn("Unexpected events data format:", data);
                    events = [];
                }
                
                // Make events available globally
                window.events = events;
                
                // Render the events in the UI
                renderEvents();
                return;
            } else {
                // Handle error response
                console.warn(`API returned error status: ${response.status}`);
                
                // Try to get more details from error response
                try {
                    const errorData = await response.json();
                    console.warn("Error details:", errorData);
                } catch (parseError) {
                    console.warn("Could not parse error response");
                }
                
                // Use fallback data if API fails
                if (response.status === 404) {
                    console.log("No events found for this session or endpoint not found");
                    
                    // Create a demo event to show the system is working
                    events = [{
                        type: "model_response",
                        timestamp: new Date().toISOString(),
                        category: "model_response",
                        summary: "Welcome Message",
                        text: "Welcome to RadBot! I'm ready to assist you. Try asking me a question or giving me a task to work on.",
                        is_final: true,
                        details: {
                            "model": "gemini-pro",
                            "session_id": sessionId
                        }
                    }];
                } else {
                    // Create an error event
                    events = [{
                        type: "other",
                        timestamp: new Date().toISOString(),
                        category: "error",
                        summary: `API Error: ${response.status} ${response.statusText}`,
                        details: {
                            error_message: `The events API returned status code ${response.status}`,
                            service: "Events API",
                            endpoint: apiUrl,
                            status_code: response.status,
                            status_text: response.statusText
                        }
                    }];
                }
                
                window.events = events;
                renderEvents();
            }
        } catch (apiError) {
            // Handle API connection errors (CORS, connection refused, etc.)
            console.error("API error fetching events:", apiError);
            
            // Create a connection error event
            events = [{
                type: "other",
                timestamp: new Date().toISOString(),
                category: "error",
                summary: "API Connection Error",
                details: {
                    error_message: `Failed to connect to Events API: ${apiError.message}`,
                    service: "Events API",
                    endpoint: apiUrl,
                    error_type: apiError.name,
                    error_stack: apiError.stack
                }
            }];
            
            window.events = events;
            renderEvents();
        }
    } catch (error) {
        // Handle any unexpected errors
        console.error('Unexpected error in fetchEvents:', error);
        
        events = [{
            type: "other",
            timestamp: new Date().toISOString(),
            category: "error",
            summary: "Unexpected Error",
            details: {
                error_message: `An unexpected error occurred: ${error.message}`,
                error_type: error.name,
                error_stack: error.stack
            }
        }];
        
        window.events = events;
        renderEvents();
    }
}

// Render events in UI
function renderEvents() {
    console.log('Rendering events panel');
    
    const eventsContainer = document.getElementById('events-container');
    if (!eventsContainer) {
        console.warn('Events container not found, cannot render events');
        return;
    }
    
    // Clear existing events - first remove event listeners to prevent memory leaks
    const oldEventItems = eventsContainer.querySelectorAll('.event-item');
    oldEventItems.forEach(item => {
        const newItem = item.cloneNode(true);
        if (item.parentNode) {
            item.parentNode.replaceChild(newItem, item);
        }
    });
    eventsContainer.innerHTML = '';
    
    // Get event type filter value
    const eventTypeFilter = document.getElementById('event-type-filter');
    const selectedType = eventTypeFilter ? eventTypeFilter.value : 'all';
    console.log(`Filtering events by type: ${selectedType}`);
    
    // Check if we have any events
    if (!events || events.length === 0) {
        console.log('No events available to display');
        const noEventsMsg = document.createElement('div');
        noEventsMsg.className = 'event-empty-state';
        noEventsMsg.textContent = 'No events recorded yet.';
        eventsContainer.appendChild(noEventsMsg);
        return;
    }
    
    console.log(`Found ${events.length} total events`);
    
    // Map known event types to normalized categories for filtering
    const mapEventTypeToCategory = (type) => {
        if (!type) return 'other';
        
        const typeStr = type.toString().toLowerCase().trim();
        
        // Tool call categories - ADK 0.4.0 may have several variations
        if (['tool_call', 'toolcall', 'tool call', 'tool-call', 'function_call', 'functioncall'].includes(typeStr) || 
            typeStr.includes('tool') || typeStr.includes('function')) {
            return 'tool_call';
        }
        
        // Model response categories
        if (['model_response', 'modelresponse', 'model response', 'response', 'content'].includes(typeStr) ||
            typeStr.includes('model') || typeStr.includes('response')) {
            return 'model_response';
        }
        
        // Agent transfer categories
        if (['agent_transfer', 'agenttransfer', 'agent transfer', 'agent-transfer', 'transfer'].includes(typeStr) ||
            typeStr.includes('agent') || typeStr.includes('transfer')) {
            return 'agent_transfer';
        }
        
        // Planner categories
        if (['planner', 'planning', 'plan'].includes(typeStr) ||
            typeStr.includes('plan') || typeStr.includes('step')) {
            return 'planner';
        }
        
        // Other categories
        if (['other', 'system', 'misc', 'unknown'].includes(typeStr)) {
            return 'other';
        }
        
        // No event reference available here, removed incorrect code
        
        return 'other'; // Default category
    };
    
    // Filter events by type with improved type matching
    const filteredEvents = events.filter(event => {
        if (selectedType === 'all') return true;
        
        // Check primary category from type
        const eventCategory = mapEventTypeToCategory(event.type);
        if (eventCategory === selectedType) return true;
        
        // Also check category if it exists (may be different from type)
        if (event.category && mapEventTypeToCategory(event.category) === selectedType) return true;
        
        // Also check summary for keywords 
        if (event.summary) {
            const summaryLower = event.summary.toLowerCase();
            if (selectedType === 'tool_call' && (summaryLower.includes('tool') || summaryLower.includes('function'))) 
                return true;
            if (selectedType === 'model_response' && (summaryLower.includes('response') || summaryLower.includes('message'))) 
                return true;
            if (selectedType === 'agent_transfer' && (summaryLower.includes('transfer') || summaryLower.includes('agent'))) 
                return true;
        }
        
        // Check for tool_name which indicates a tool call
        if (selectedType === 'tool_call' && event.tool_name) return true;
        
        // Otherwise, it doesn't match the filter
        return false;
    });
    
    console.log(`After filtering: ${filteredEvents.length} events match the current filter`);
    
    // Sort events by timestamp (descending - newest first), 
    // handling both timestamp and start_time fields
    filteredEvents.sort((a, b) => {
        const timeA = new Date(a.timestamp || a.start_time);
        const timeB = new Date(b.timestamp || b.start_time);
        return timeB - timeA;
    });
    
    // Render each event
    filteredEvents.forEach(event => {
        // Check for model information in event details
        if (event.details && event.details.model && 
            (event.type === 'model_response' || event.category === 'model_response')) {
            // Update model status if it's a model response event with model info
            window.statusUtils.updateModelStatus(event.details.model);
        }
        
        // Check for agent transfer events and update the agent name
        if (event.type === 'agent_transfer' || event.category === 'agent_transfer') {
            // Update the current agent name when rendering a transfer event
            if (event.to_agent) {
                const newAgent = event.to_agent;
                console.log(`Agent transfer detected in event rendering: ${newAgent}`);
                // Update agent status using the dedicated function
                window.statusUtils.updateAgentStatus(newAgent);
            }
        }
        
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
        } else if (type === 'model_response' || category === 'model_response') {
            eventCategory = 'model-response';
        }
        
        eventItem.className = `event-item ${eventCategory}`;
        
        // Use an ID if available, or create a unique one based on timestamp and type
        const eventId = event.event_id || `${event.type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        eventItem.dataset.id = eventId;
        
        // Format date/time (handle both timestamp and start_time formats)
        const startTime = new Date(event.timestamp || event.start_time);
        const timeStr = startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const dateStr = startTime.toLocaleDateString([], { month: 'short', day: 'numeric' });
        
        const eventType = document.createElement('div');
        eventType.className = 'event-type';
        eventType.textContent = formatEventType(event.type);
        
        const eventTimestamp = document.createElement('div');
        eventTimestamp.className = 'event-timestamp';
        eventTimestamp.textContent = `${dateStr} ${timeStr}`;
        
        const eventSummary = document.createElement('div');
        eventSummary.className = 'event-summary';
        // Use the most descriptive field available (summary, title, or tool_name)
        eventSummary.textContent = event.summary || event.title || (event.tool_name ? `Tool: ${event.tool_name}` : `Event: ${event.type}`);
        
        eventItem.appendChild(eventType);
        eventItem.appendChild(eventTimestamp);
        eventItem.appendChild(eventSummary);
        
        // Add click handler to show event details
        eventItem.addEventListener('click', () => {
            // Set this event as active and show details
            const allEvents = eventsContainer.querySelectorAll('.event-item');
            allEvents.forEach(e => e.classList.remove('active'));
            eventItem.classList.add('active');
            
            // Show event details
            showEventDetails(event);
        });
        
        eventsContainer.appendChild(eventItem);
    });
    
    // Show a message if no events found
    if (filteredEvents.length === 0) {
        const noEventsMsg = document.createElement('div');
        noEventsMsg.className = 'no-items-message';
        noEventsMsg.textContent = 'No events match the current filter';
        eventsContainer.appendChild(noEventsMsg);
    }
}

// Format event type for display
function formatEventType(type) {
    // Handle null or undefined types
    if (!type) return 'UNKNOWN';
    
    // Handle common variations
    const typeStr = type.toString().toLowerCase().trim();
    
    switch (typeStr) {
        case 'tool_call':
        case 'toolcall':
        case 'tool call':
        case 'tool-call':
            return 'TOOL CALL';
            
        case 'agent_transfer':
        case 'agenttransfer':
        case 'agent transfer':
        case 'agent-transfer':
            return 'AGENT TRANSFER';
            
        case 'planner':
        case 'planning':
        case 'plan':
            return 'PLANNER';
            
        case 'other':
        case 'system':
        case 'misc':
        case 'unknown':
            return 'SYSTEM';
            
        default:
            // Convert to uppercase for consistency
            return typeStr.toUpperCase();
    }
}

// Show event details
function showEventDetails(event) {
    console.log('Showing event details:', event);
    
    // First, ensure the events tile is visible - this is using the tiling system
    let eventsPanel = document.querySelector('[data-content="events"]');
    if (!eventsPanel) {
        console.warn('Events panel not found in DOM, attempting to open it');
        // Try to trigger events panel command
        document.dispatchEvent(new CustomEvent('command:events'));
        
        // Wait a moment and try again
        setTimeout(() => {
            eventsPanel = document.querySelector('[data-content="events"]');
            if (eventsPanel) {
                console.log('Events panel now found, attempting to show details again');
                // Try again after panel is opened
                showEventDetails(event);
            } else {
                console.error('Could not find events panel after attempting to open it');
            }
        }, 300);
        return;
    }
    
    // Now check for the details container
    const detailsContainer = document.getElementById('event-details-content');
    if (!detailsContainer) {
        console.warn('Event details container not found in DOM - attempting to create it');
        
        // Look for detail panel where we can put the content
        const detailPanel = document.querySelector('.detail-panel');
        if (detailPanel) {
            console.log('Found detail-panel, creating event details content');
            
            // Create event details content container
            const detailsContent = document.createElement('div');
            detailsContent.className = 'event-details-content';
            detailsContent.id = 'event-details-content';
            
            // Find existing tile-content if it exists or create one
            let tileContent = detailPanel.querySelector('.tile-content');
            if (!tileContent) {
                tileContent = document.createElement('div');
                tileContent.className = 'tile-content event-details';
                detailPanel.appendChild(tileContent);
            }
            
            // Add details content to the tile content
            tileContent.innerHTML = ''; // Clear existing content
            tileContent.appendChild(detailsContent);
            console.log('Created event-details-content container');
            
            // Now try to use the newly created container
            setTimeout(() => showEventDetails(event), 100);
            return;
        }
        
        console.error('Could not find detail panel to add event details content');
        return;
    }
    
    console.log('Found event-details-content, rendering details');
    
    // Clear existing content
    detailsContainer.innerHTML = '';
    
    // Main details
    const headerSection = document.createElement('div');
    headerSection.className = 'detail-section';
    
    const title = document.createElement('h4');
    // Use the most descriptive field available for the title
    const titleText = event.summary || event.title || (event.tool_name ? `Tool Call: ${event.tool_name}` : `Event: ${event.type}`);
    title.innerHTML = `<span>${titleText}</span>`;
    
    const timestamp = document.createElement('div');
    timestamp.className = 'detail-timestamp';
    timestamp.textContent = new Date(event.timestamp || event.start_time).toLocaleString();
    
    headerSection.appendChild(title);
    headerSection.appendChild(timestamp);
    
    // Event ID - hidden by default but can be shown for debugging
    const idSection = document.createElement('div');
    idSection.className = 'detail-section detail-small';
    
    const idValue = document.createElement('div');
    idValue.className = 'detail-id';
    const eventId = event.event_id || 'N/A';
    idValue.textContent = `Event ID: ${eventId}`;
    idSection.appendChild(idValue);
    
    // Type section with styled badge
    const typeSection = document.createElement('div');
    typeSection.className = 'detail-section';
    
    const typeTitle = document.createElement('h4');
    typeTitle.textContent = 'Event Type: ';
    const typeValue = document.createElement('span');
    typeValue.className = `event-type-badge ${event.type}`;
    typeValue.textContent = formatEventType(event.type);
    typeTitle.appendChild(typeValue);
    
    typeSection.appendChild(typeTitle);
    
    // Add main sections to container
    detailsContainer.appendChild(headerSection);
    detailsContainer.appendChild(typeSection);
    
    // Process specific fields based on event type
    if (event.type === 'tool_call' || event.category === 'tool_call' || 
        event.function_call || event.function_response || 
        event.tool_calls || event.tool_results) {
        
        // Tool call sections
        if (event.tool_name) {
            const toolSection = document.createElement('div');
            toolSection.className = 'detail-section';
            
            const toolTitle = document.createElement('h4');
            toolTitle.textContent = 'Tool:';
            toolSection.appendChild(toolTitle);
            
            const toolName = document.createElement('div');
            toolName.className = 'detail-value';
            toolName.textContent = event.tool_name;
            toolSection.appendChild(toolName);
            
            detailsContainer.appendChild(toolSection);
        }
        
        // Function call details
        if (event.function_call) {
            // Function call specific rendering
            const functionCallSection = document.createElement('div');
            functionCallSection.className = 'detail-section';
            
            const functionTitle = document.createElement('h4');
            functionTitle.textContent = 'Function Call:';
            functionCallSection.appendChild(functionTitle);
            
            if (event.function_call.name) {
                const funcName = document.createElement('div');
                funcName.className = 'detail-value';
                funcName.textContent = event.function_call.name;
                functionCallSection.appendChild(funcName);
            }
            
            if (event.function_call.args) {
                const argsValue = document.createElement('pre');
                argsValue.className = 'detail-json';
                argsValue.innerHTML = formatJsonSyntax(event.function_call.args);
                functionCallSection.appendChild(argsValue);
            }
            
            detailsContainer.appendChild(functionCallSection);
        }
        
        // Function response details
        if (event.function_response) {
            const functionResponseSection = document.createElement('div');
            functionResponseSection.className = 'detail-section';
            
            const responseTitle = document.createElement('h4');
            responseTitle.textContent = 'Function Response:';
            functionResponseSection.appendChild(responseTitle);
            
            if (event.function_response.name) {
                const funcName = document.createElement('div');
                funcName.className = 'detail-value';
                funcName.textContent = event.function_response.name;
                functionResponseSection.appendChild(funcName);
            }
            
            if (event.function_response.response) {
                const responseValue = document.createElement('pre');
                responseValue.className = 'detail-json';
                responseValue.innerHTML = formatJsonSyntax(event.function_response.response);
                functionResponseSection.appendChild(responseValue);
            }
            
            detailsContainer.appendChild(functionResponseSection);
        }
        
        // Input section (regular tool call)
        if (event.input) {
            const inputSection = document.createElement('div');
            inputSection.className = 'detail-section';
            
            const inputTitle = document.createElement('h4');
            inputTitle.textContent = 'Input:';
            inputSection.appendChild(inputTitle);
            
            const inputValue = document.createElement('pre');
            inputValue.className = 'detail-json';
            inputValue.innerHTML = formatJsonSyntax(event.input);
            inputSection.appendChild(inputValue);
            
            detailsContainer.appendChild(inputSection);
        }
        
        // Output section (regular tool call)
        if (event.output) {
            const outputSection = document.createElement('div');
            outputSection.className = 'detail-section';
            
            const outputTitle = document.createElement('h4');
            outputTitle.textContent = 'Output:';
            outputSection.appendChild(outputTitle);
            
            const outputValue = document.createElement('pre');
            outputValue.className = 'detail-json';
            outputValue.innerHTML = formatJsonSyntax(event.output);
            outputSection.appendChild(outputValue);
            
            detailsContainer.appendChild(outputSection);
        }
    } else if (event.type === 'agent_transfer') {
        // Agent transfer details
        const transferSection = document.createElement('div');
        transferSection.className = 'detail-section';
        
        const transferTitle = document.createElement('h4');
        transferTitle.textContent = 'Transfer Details:';
        transferSection.appendChild(transferTitle);
        
        const transferDetails = document.createElement('div');
        transferDetails.className = 'transfer-details';
        
        if (event.from_agent) {
            const fromAgent = document.createElement('div');
            fromAgent.className = 'detail-item';
            fromAgent.innerHTML = `<strong>From:</strong> ${event.from_agent}`;
            transferDetails.appendChild(fromAgent);
        }
        
        if (event.to_agent) {
            const toAgent = document.createElement('div');
            toAgent.className = 'detail-item';
            toAgent.innerHTML = `<strong>To:</strong> ${event.to_agent}`;
            transferDetails.appendChild(toAgent);
        }
        
        transferSection.appendChild(transferDetails);
        detailsContainer.appendChild(transferSection);
    } else if (event.type === 'planner') {
        // Planner details
        if (event.plan) {
            const planSection = document.createElement('div');
            planSection.className = 'detail-section';
            
            const planTitle = document.createElement('h4');
            planTitle.textContent = 'Plan:';
            planSection.appendChild(planTitle);
            
            const planDetails = document.createElement('div');
            planDetails.className = 'plan-details';
            
            // Handle plan query if available
            if (event.plan.query) {
                const query = document.createElement('div');
                query.className = 'detail-item';
                query.innerHTML = `<strong>Query:</strong> ${event.plan.query}`;
                planDetails.appendChild(query);
            }
            
            // Handle plan steps if available
            if (event.plan.steps && Array.isArray(event.plan.steps)) {
                const stepsContainer = document.createElement('div');
                stepsContainer.className = 'detail-item';
                
                const stepsTitle = document.createElement('strong');
                stepsTitle.textContent = 'Steps:';
                stepsContainer.appendChild(stepsTitle);
                
                const stepsList = document.createElement('ol');
                stepsList.className = 'steps-list';
                
                event.plan.steps.forEach(step => {
                    const stepItem = document.createElement('li');
                    stepItem.textContent = step;
                    stepsList.appendChild(stepItem);
                });
                
                stepsContainer.appendChild(stepsList);
                planDetails.appendChild(stepsContainer);
            }
            
            planSection.appendChild(planDetails);
            detailsContainer.appendChild(planSection);
        }
    } else if (event.type === 'model_response') {
        // Model response content
        if (event.text) {
            const textSection = document.createElement('div');
            textSection.className = 'detail-section';
            
            const textTitle = document.createElement('h4');
            textTitle.textContent = 'Response:';
            textSection.appendChild(textTitle);
            
            const textContent = document.createElement('pre');
            textContent.className = 'response-content';
            textContent.textContent = event.text;
            textSection.appendChild(textContent);
            
            detailsContainer.appendChild(textSection);
        }
    }
    
    // Add technical details section for all event types
    if (event.details && Object.keys(event.details).length > 0) {
        const detailsSection = document.createElement('div');
        detailsSection.className = 'detail-section technical-details';
        
        const detailsTitle = document.createElement('h4');
        detailsTitle.textContent = 'Technical Details:';
        detailsSection.appendChild(detailsTitle);
        
        const detailsContent = document.createElement('div');
        detailsContent.className = 'details-content';
        
        // Format technical details as a single JSON object instead of individual fields
        const technicalJsonContainer = document.createElement('div');
        technicalJsonContainer.className = 'json-container';
        technicalJsonContainer.style.maxHeight = '200px';
        technicalJsonContainer.style.overflowY = 'auto';
        
        const technicalJson = document.createElement('pre');
        technicalJson.className = 'detail-json';
        technicalJson.innerHTML = formatJsonSyntax(event.details);
        
        technicalJsonContainer.appendChild(technicalJson);
        detailsContent.appendChild(technicalJsonContainer);
        
        detailsSection.appendChild(detailsContent);
        detailsContainer.appendChild(detailsSection);
    }
    
    // Add event ID at the bottom for reference
    detailsContainer.appendChild(idSection);
    
    // Add category if it exists and different from type
    if (event.category && event.category !== event.type) {
        const categorySection = document.createElement('div');
        categorySection.className = 'detail-section detail-small';
        
        const categoryValue = document.createElement('div');
        categoryValue.className = 'detail-category';
        categoryValue.textContent = `Category: ${event.category}`;
        categorySection.appendChild(categoryValue);
        
        detailsContainer.appendChild(categorySection);
    }
    
    // Add a Raw JSON section to show the full event payload
    const rawSection = document.createElement('div');
    rawSection.className = 'detail-section raw-json-section';
    
    const rawHeader = document.createElement('div');
    rawHeader.className = 'raw-json-header';
    rawHeader.innerHTML = '<h4>Raw Event Data</h4><button class="toggle-raw-json">Show</button>';
    rawSection.appendChild(rawHeader);
    
    const rawContent = document.createElement('div');
    rawContent.className = 'raw-json-content hidden';
    rawContent.style.maxHeight = '300px';
    rawContent.style.overflow = 'hidden';
    
    // Create a scrollable container for the JSON
    const rawJsonContainer = document.createElement('div');
    rawJsonContainer.className = 'raw-json-container';
    rawJsonContainer.style.maxHeight = '300px';
    rawJsonContainer.style.overflowY = 'auto';
    
    // Create a pretty-printed JSON display
    const rawJson = document.createElement('pre');
    rawJson.className = 'raw-json';
    rawJson.style.maxHeight = 'none';
    rawJson.style.overflow = 'visible';
    
    // Remove circular references before stringifying
    const cleanedEvent = JSON.parse(JSON.stringify(event, (key, value) => {
        // Skip parent/circular references that can't be stringified
        if (key === 'parent' || key === '_parent') return undefined;
        return value;
    }));
    
    // Format the JSON with proper indentation and structure
    const formattedJson = JSON.stringify(cleanedEvent, null, 2);
    
    // For better readability, we'll syntax highlight the JSON
    rawJson.innerHTML = formatJsonSyntax(formattedJson);
    
    rawJsonContainer.appendChild(rawJson);
    rawContent.appendChild(rawJsonContainer);
    rawSection.appendChild(rawContent);
    
    // Add toggle behavior
    const toggleButton = rawHeader.querySelector('.toggle-raw-json');
    toggleButton.addEventListener('click', function() {
        rawContent.classList.toggle('hidden');
        this.textContent = rawContent.classList.contains('hidden') ? 'Show' : 'Hide';
    });
    
    detailsContainer.appendChild(rawSection);
}

// Format JSON with syntax highlighting
function formatJsonSyntax(json) {
    if (!json) return '';
    
    // Handle the case where json is already an object
    if (typeof json !== 'string') {
        json = JSON.stringify(json, null, 2);
    }
    
    // Replace potentially harmful characters
    json = json.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;');
    
    // Format different parts of JSON with specific colors
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function(match) {
        let cls = 'json-number'; // default is number
        
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'json-key'; // keys
            } else {
                cls = 'json-string'; // strings
            }
        } else if (/true|false/.test(match)) {
            cls = 'json-boolean'; // booleans
        } else if (/null/.test(match)) {
            cls = 'json-null'; // null
        }
        
        return '<span class="' + cls + '">' + match + '</span>';
    });
}

// Get initial agent and model information
function fetchAgentInfo() {
    console.log("Fetching agent and model information");
    
    try {
        // Make a request to get the agent info from the server
        fetch('/api/agent-info')
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    console.warn("Agent info API returned error:", response.status);
                    return null;
                }
            })
            .then(data => {
                if (data) {
                    console.log("Agent info loaded from API:", data);
                    
                    // Store the agent models in window.state for later reference
                    window.state.agentModels = data.agent_models || {};
                    
                    // Add debug output of available models
                    if (data.agent_models) {
                        console.log("Available agent models:");
                        for (const [agent, model] of Object.entries(data.agent_models)) {
                            console.log(`  ${agent}: ${model}`);
                        }
                    }
                    
                    // Update agent name if available
                    if (data.agent_name) {
                        window.statusUtils.updateAgentStatus(data.agent_name);
                    }
                    
                    // Get the appropriate model for the current agent
                    const currentAgent = window.state.currentAgentName.toLowerCase();
                    let modelToUse = data.model; // Default to main model
                    
                    // Try all possible ways to find the right model
                    if (data.agent_models) {
                        // Look for an exact match first
                        if (data.agent_models[currentAgent]) {
                            modelToUse = data.agent_models[currentAgent];
                            console.log(`Found exact model match for ${currentAgent}: ${modelToUse}`);
                        } 
                        // Then try special case for scout
                        else if (currentAgent === 'scout' && data.agent_models.scout_agent) {
                            modelToUse = data.agent_models.scout_agent;
                            console.log(`Using scout_agent model for ${currentAgent}: ${modelToUse}`);
                        }
                        // Try with _agent suffix
                        else if (data.agent_models[currentAgent + '_agent']) {
                            modelToUse = data.agent_models[currentAgent + '_agent'];
                            console.log(`Using ${currentAgent}_agent model: ${modelToUse}`);
                        }
                        // Try without _agent suffix
                        else if (currentAgent.endsWith('_agent') && data.agent_models[currentAgent.replace('_agent', '')]) {
                            modelToUse = data.agent_models[currentAgent.replace('_agent', '')];
                            console.log(`Using ${currentAgent.replace('_agent', '')} model: ${modelToUse}`);
                        }
                        // For any partial match (case insensitive)
                        else {
                            for (const [agentKey, modelValue] of Object.entries(data.agent_models)) {
                                if (currentAgent.includes(agentKey.toLowerCase()) || 
                                    agentKey.toLowerCase().includes(currentAgent)) {
                                    modelToUse = modelValue;
                                    console.log(`Using partial match ${agentKey} model for ${currentAgent}: ${modelToUse}`);
                                    break;
                                }
                            }
                        }
                    }
                    
                    console.log(`Selected model for ${currentAgent}: ${modelToUse}`);
                    
                    // Update model name
                    if (modelToUse) {
                        window.statusUtils.updateModelStatus(modelToUse);
                    } else {
                        // Fallback to updateModelForCurrentAgent
                        updateModelForCurrentAgent();
                    }
                    
                    // Force a visual refresh of the status bar
                    if (typeof updateStatusBar === 'function') {
                        updateStatusBar();
                    } else if (window.statusUtils && window.statusUtils.updateStatusBar) {
                        window.statusUtils.updateStatusBar();
                    }
                } else {
                    // Fallback to updateModelForCurrentAgent
                    updateModelForCurrentAgent();
                }
            })
            .catch(error => {
                console.warn("Failed to fetch agent info:", error);
                
                // If API fails, still update the displayed model based on current agent
                updateModelForCurrentAgent();
            });
    } catch (error) {
        console.warn("Error in fetchAgentInfo:", error);
        
        // If API fails, still update the displayed model based on current agent
        updateModelForCurrentAgent();
    }
}

// Update model display based on the current agent name
function updateModelForCurrentAgent() {
    const agentName = window.state.currentAgentName.toLowerCase();
    let modelName;
    
    // Log the current agent for debugging
    console.log(`Updating model for agent: ${agentName}`);
    
    // Try to find the model in agentModels first (from API)
    if (window.state.agentModels) {
        // Check all possible variations of the agent name
        const possibleNames = [
            agentName,
            agentName + '_agent',
            agentName.replace('_agent', '')
        ];
        
        // Try each possible name
        for (const name of possibleNames) {
            if (window.state.agentModels[name]) {
                modelName = window.state.agentModels[name];
                console.log(`Found model in agentModels for "${name}": ${modelName}`);
                break;
            }
        }
    }
    
    // If we still don't have a model, use hardcoded values matching config.yaml
    if (!modelName) {
        console.log(`No model found in agentModels, using hardcoded values`);
        
        // Check the agent name with more flexibility - EXACTLY match config.yaml values
        if (agentName.includes('scout')) {
            modelName = "gemini-2.5-pro-preview-05-06";  // Match config.yaml scout_agent
        } else if (agentName.includes('code') || agentName === "code_execution_agent") {
            modelName = "gemini-2.5-flash-preview-04-17";  // Match config.yaml code_execution_agent
        } else if (agentName.includes('search')) {
            modelName = "gemini-2.5-flash-preview-04-17";  // Match config.yaml search_agent
        } else if (agentName.includes('todo')) {
            modelName = "gemini-2.5-flash-preview-04-17";  // Match config.yaml todo_agent
        } else {
            // Default for beto/main agent - match config.yaml main_model
            modelName = "gemini-2.5-flash-preview-04-17";
        }
    }
    
    window.statusUtils.updateModelStatus(modelName);
    console.log(`Updated model based on agent ${agentName}: ${modelName}`);
    
    // Force a visual refresh of the status bar
    if (typeof updateStatusBar === 'function') {
        updateStatusBar();
    } else if (window.statusUtils && window.statusUtils.updateStatusBar) {
        window.statusUtils.updateStatusBar();
    }
}

// Generate a UUID for session ID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);