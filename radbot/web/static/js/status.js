/**
 * Status functionality module for RadBot UI
 */

// Status bar elements
let agentStatus;
let modelStatus;
let timeStatus;
let connectionStatus;

// Initialize status functionality
export function initStatus() {
    console.log('Initializing status module');
    
    // Status Bar Elements
    agentStatus = document.getElementById('agent-status');
    modelStatus = document.getElementById('model-status');
    timeStatus = document.getElementById('time-status');
    connectionStatus = document.getElementById('connection-status');
    
    // Initialize status bar
    updateStatusBar();
    
    // Start clock
    updateClock();
    setInterval(updateClock, 1000);
    
    return true;
}

// Update status bar elements
export function updateStatusBar() {
    if (agentStatus) {
        agentStatus.textContent = `AGENT: ${window.state.currentAgentName.toUpperCase()}`;
    }
    
    if (modelStatus) {
        modelStatus.textContent = `MODEL: ${window.state.currentModel}`;
    }
    
    updateClock();
    setStatus('ready');
}

// Update the clock display
export function updateClock() {
    if (!timeStatus) return;
    
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    timeStatus.textContent = `TIME: ${hours}:${minutes}:${seconds}`;
}

// Set the UI status indicator
export function setStatus(status) {
    // Update the connection status in the main status bar
    if (connectionStatus) {
        switch (status) {
            case 'ready':
                connectionStatus.textContent = 'CONNECTION: ACTIVE';
                if (window.chatModule) {
                    const chatElements = window.chatModule.getChatElements();
                    if (chatElements.sendButton) chatElements.sendButton.disabled = false;
                    if (chatElements.input) chatElements.input.disabled = false;
                }
                break;
            case 'thinking':
                connectionStatus.textContent = 'CONNECTION: PROCESSING...';
                if (window.chatModule && window.chatModule.getChatElements().sendButton) {
                    window.chatModule.getChatElements().sendButton.disabled = true;
                }
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
                    if (window.chatModule) {
                        const chatElements = window.chatModule.getChatElements();
                        if (chatElements.sendButton) chatElements.sendButton.disabled = false;
                        if (chatElements.input) chatElements.input.disabled = false;
                    }
                } else {
                    connectionStatus.textContent = `CONNECTION: ${status.toUpperCase()}`;
                }
        }
    }
    
    // Make sure the agent status is up to date, except for disconnected state
    if (status !== 'disconnected' && agentStatus) {
        const displayName = window.state.currentAgentName.toUpperCase();
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

// Update agent status
export function updateAgentStatus(agentName) {
    if (!agentName) return;
    
    // Update global state - ensure uppercase for consistency
    const formattedName = agentName.toUpperCase();
    window.state.currentAgentName = formattedName;
    
    // Update status bar
    if (agentStatus) {
        agentStatus.textContent = `AGENT: ${formattedName}`;
        
        // Visual feedback to ensure update is visible
        agentStatus.style.color = 'var(--term-blue)';
        setTimeout(() => {
            agentStatus.style.color = 'var(--term-amber)';
        }, 100);
        
        console.log(`Agent status updated: ${formattedName}`);
        
        // Update CSS variable for any styling that might use it
        document.documentElement.style.setProperty('--agent-name', `"${formattedName}"`);
    }
}

// Update model status
export function updateModelStatus(modelName) {
    if (!modelName) return;
    
    // Update global state
    window.state.currentModel = modelName;
    
    // Update status bar
    if (modelStatus) {
        modelStatus.textContent = `MODEL: ${modelName}`;
        
        // Visual feedback to ensure update is visible
        modelStatus.style.color = 'var(--term-blue)';
        setTimeout(() => {
            modelStatus.style.color = 'var(--text-primary)';
        }, 100);
        
        console.log(`Model status updated: ${modelName}`);
    }
}

// Handle status updates from server
export function handleStatusUpdate(status) {
    setStatus(status);
    
    // Ensure agent name is always visible in the status bar
    if (agentStatus) {
        agentStatus.textContent = `AGENT: ${window.state.currentAgentName.toUpperCase()}`;
    }
    
    // Ensure model name is always visible in the status bar
    if (modelStatus) {
        modelStatus.textContent = `MODEL: ${window.state.currentModel}`;
    }
}