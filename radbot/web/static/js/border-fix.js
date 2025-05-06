// Script to fix border alignment issues
document.addEventListener('DOMContentLoaded', function() {
    // Function to enforce full width and proper border alignment
    function fixUILayout() {
        // Force the container to be full width of the viewport
        const appContainer = document.getElementById('app-container');
        const windowWidth = window.innerWidth;
        
        // Set exact dimensions to prevent browser quirks
        document.body.style.width = `${windowWidth}px`;
        appContainer.style.width = `${windowWidth}px`;
        appContainer.style.maxWidth = `${windowWidth}px`;
        
        // Ensure the right edge is visible by setting width to 100vw
        document.documentElement.style.width = '100vw';
        document.documentElement.style.overflowX = 'hidden';
        
        // Hide the status bar overflow which may be causing the issue
        const statusBar = document.getElementById('status-bar');
        if (statusBar) {
            statusBar.style.width = '100%';
            statusBar.style.boxSizing = 'border-box';
        }
        
        // Ensure no scrollbars appear and break layout
        document.body.style.overflow = 'hidden';
        
        // Force a redraw by toggling a class
        appContainer.classList.toggle('force-redraw');
        setTimeout(() => {
            appContainer.classList.toggle('force-redraw');
        }, 10);
    }
    
    // Run on page load and resize
    fixUILayout();
    window.addEventListener('load', fixUILayout);
    window.addEventListener('resize', fixUILayout);
    
    // Fix layout when panels are toggled
    const toggleButtons = [
        document.getElementById('toggle-events-button'),
        document.getElementById('toggle-tasks-button'),
        document.getElementById('reset-button')
    ];
    
    toggleButtons.forEach(button => {
        if (button) {
            button.addEventListener('click', () => {
                setTimeout(fixUILayout, 10);
            });
        }
    });
});