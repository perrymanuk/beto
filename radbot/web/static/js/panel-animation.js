/**
 * Panel Animation Support for Tiling Interface
 * 
 * This script simply forwards commands to the tiling system.
 * The actual panel rendering is handled by the tiling.js file.
 */

// Initialize panel animation listeners
function initPanelAnimation() {
    console.log('Initializing panel animation support (forwarding to tiling system)');
    
    // Setup panel toggle buttons - just forward the events to the tiling system
    const toggleEventsButton = document.getElementById('toggle-events-button');
    const toggleTasksButton = document.getElementById('toggle-tasks-button');
    
    if (toggleEventsButton) {
        toggleEventsButton.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Events toggle button clicked');
            document.dispatchEvent(new CustomEvent('command:events'));
        });
    }
    
    if (toggleTasksButton) {
        toggleTasksButton.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Tasks toggle button clicked');
            document.dispatchEvent(new CustomEvent('command:tasks'));
        });
    }
}

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize with a slight delay to ensure DOM is fully ready
    setTimeout(initPanelAnimation, 300);
});

// Re-initialize when tiling system reports ready
document.addEventListener('tiling:ready', function() {
    console.log('Tiling system ready, setting up panel animation support');
    initPanelAnimation();
});

// Also re-initialize on layout changes
document.addEventListener('layout:changed', function() {
    console.log('Layout changed, re-initializing panel animation support');
    initPanelAnimation();
});