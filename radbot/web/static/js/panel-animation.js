/**
 * Enhanced Panel Animation from Left
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const appContainer = document.getElementById('app-container');
    const chatContainerWrapper = document.getElementById('chat-container-wrapper');
    const eventsPanel = document.getElementById('events-panel');
    const tasksPanel = document.getElementById('tasks-panel');
    const toggleEventsButton = document.getElementById('toggle-events-button');
    const toggleTasksButton = document.getElementById('toggle-tasks-button');
    
    // Note: We don't initialize panels as hidden here
    // because app.js already handles this
    
    // Toggle events panel
    toggleEventsButton.addEventListener('click', function() {
        const isVisible = !eventsPanel.classList.contains('hidden');
        
        // If currently visible, hide it
        if (isVisible) {
            eventsPanel.classList.add('hidden');
            appContainer.classList.remove('panel-visible');
        } else {
            // Hide tasks panel if it's visible
            tasksPanel.classList.add('hidden');
            
            // Show events panel
            eventsPanel.classList.remove('hidden');
            appContainer.classList.add('panel-visible');
        }
    });
    
    // Toggle tasks panel
    toggleTasksButton.addEventListener('click', function() {
        const isVisible = !tasksPanel.classList.contains('hidden');
        
        // If currently visible, hide it
        if (isVisible) {
            tasksPanel.classList.add('hidden');
            appContainer.classList.remove('panel-visible');
        } else {
            // Hide events panel if it's visible
            eventsPanel.classList.add('hidden');
            
            // Show tasks panel
            tasksPanel.classList.remove('hidden');
            appContainer.classList.add('panel-visible');
        }
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        // Adjust panels based on window size
        const windowWidth = window.innerWidth;
        
        // For very small screens, close panels automatically
        if (windowWidth < 768 && 
            ((!eventsPanel.classList.contains('hidden')) || 
             (!tasksPanel.classList.contains('hidden')))) {
            
            eventsPanel.classList.add('hidden');
            tasksPanel.classList.add('hidden');
            appContainer.classList.remove('panel-visible');
        }
    });
});