/**
 * Panel Trigger System for RadBot UI
 * 
 * This script connects the UI buttons directly to the tiling manager
 * to ensure panels toggle correctly.
 */

// Wait for DOM content loaded to initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('Panel trigger system initialized');
    
    // Setup task button - needs to directly call tilingManager
    document.addEventListener('command:tasks', function() {
        console.log('Tasks command received - direct call to tiling manager');
        
        // Check if tiling manager exists
        if (window.tilingManager) {
            window.tilingManager.togglePanel('tasks');
        } else {
            console.error('Tiling manager not found');
        }
    });
    
    // Setup events button - needs to directly call tilingManager
    document.addEventListener('command:events', function() {
        console.log('Events command received - direct call to tiling manager');
        
        // Check if tiling manager exists
        if (window.tilingManager) {
            window.tilingManager.togglePanel('events');
        } else {
            console.error('Tiling manager not found');
        }
    });
    
    // Add direct click handlers to buttons
    setupDirectHandlers();
});

// Set up direct handlers for buttons
function setupDirectHandlers() {
    const toggleTasksButton = document.getElementById('toggle-tasks-button');
    const toggleEventsButton = document.getElementById('toggle-events-button');
    
    if (toggleTasksButton) {
        toggleTasksButton.addEventListener('click', function(e) {
            console.log('Tasks button clicked - direct handler');
            e.preventDefault();
            e.stopPropagation();
            
            // Call tiling manager directly
            if (window.tilingManager) {
                window.tilingManager.togglePanel('tasks');
            } else {
                console.error('Tiling manager not available');
            }
        });
    }
    
    if (toggleEventsButton) {
        toggleEventsButton.addEventListener('click', function(e) {
            console.log('Events button clicked - direct handler');
            e.preventDefault();
            e.stopPropagation();
            
            // Call tiling manager directly
            if (window.tilingManager) {
                window.tilingManager.togglePanel('events');
            } else {
                console.error('Tiling manager not available');
            }
        });
    }
}

// Re-attach handlers when layout changes
document.addEventListener('tiling:ready', function() {
    console.log('Tiling ready - setting up direct handlers');
    setTimeout(setupDirectHandlers, 200);
});

document.addEventListener('layout:changed', function() {
    console.log('Layout changed - re-setting up direct handlers');
    setTimeout(setupDirectHandlers, 200);
});