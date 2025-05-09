// Simplified Tiling Window Manager Implementation
class TilingManager {
  constructor() {
    console.log('Initializing TilingManager');
    this.container = document.getElementById('app-container');
    
    // Track panel states
    this.panelStates = {
      sessionsOpen: false,
      tasksOpen: false,
      eventsOpen: false
    };
    
    this.templates = {
      chat: document.getElementById('chat-template'),
      sessions: document.getElementById('sessions-template'),
      tasks: document.getElementById('tasks-template'),
      events: document.getElementById('events-template'),
      taskDetails: document.getElementById('task-details-template'),
      eventDetails: document.getElementById('event-details-template'),
      sessionDetails: document.getElementById('session-details-template')
    };
    
    // Initialize by rendering the main chat container
    this.renderInitialLayout();
    
    // Listen for command events
    document.addEventListener('command:sessions', () => this.togglePanel('sessions'));
    document.addEventListener('command:tasks', () => this.togglePanel('tasks'));
    document.addEventListener('command:events', () => this.togglePanel('events'));
  }
  
  // Initial layout for chat only
  renderInitialLayout() {
    console.log('Rendering initial layout');
    this.container.innerHTML = '';
    
    // Create chat tile
    const chatTile = document.createElement('div');
    chatTile.className = 'tile';
    chatTile.setAttribute('data-content', 'chat');
    chatTile.style.flex = '1 1 auto';
    
    // Add chat content from template
    const chatContent = document.createElement('div');
    chatContent.className = 'tile-content chat';
    const chatTemplate = this.templates.chat.content.cloneNode(true);
    chatContent.appendChild(chatTemplate);
    chatTile.appendChild(chatContent);
    
    // Add to container
    this.container.appendChild(chatTile);
    
    // Initialize UI event handlers
    this.initializeEventHandlers();
    
    // Signal that the UI is ready
    document.dispatchEvent(new CustomEvent('tiling:ready'));
  }
  
  // Toggle a panel (sessions, tasks, or events)
  togglePanel(panelType) {
    console.log(`Toggling ${panelType} panel`);
    
    // Save chat content and input value before modifying layout
    const savedMessages = this.saveChatMessages();
    const savedInputValue = this.saveChatInput();
    
    // Toggle panel state
    if (panelType === 'sessions') {
      this.panelStates.sessionsOpen = !this.panelStates.sessionsOpen;
      
      // If opening sessions panel, close other panels
      if (this.panelStates.sessionsOpen) {
        this.panelStates.tasksOpen = false;
        this.panelStates.eventsOpen = false;
      }
    } else if (panelType === 'tasks') {
      this.panelStates.tasksOpen = !this.panelStates.tasksOpen;
      
      // If opening tasks panel, close other panels
      if (this.panelStates.tasksOpen) {
        this.panelStates.sessionsOpen = false;
        this.panelStates.eventsOpen = false;
      }
    } else if (panelType === 'events') {
      this.panelStates.eventsOpen = !this.panelStates.eventsOpen;
      
      // If opening events panel, close other panels
      if (this.panelStates.eventsOpen) {
        this.panelStates.sessionsOpen = false;
        this.panelStates.tasksOpen = false;
      }
    }
    
    // Render the new layout
    this.renderLayoutWithPanels(savedMessages, savedInputValue);
  }
  
  // Render layout based on current panel states
  renderLayoutWithPanels(savedMessages, savedInputValue) {
    console.log('Rendering layout with panels', this.panelStates);
    
    // Clear container
    this.container.innerHTML = '';
    
    if (!this.panelStates.sessionsOpen && !this.panelStates.tasksOpen && !this.panelStates.eventsOpen) {
      // Just render chat panel
      const chatTile = document.createElement('div');
      chatTile.className = 'tile';
      chatTile.setAttribute('data-content', 'chat');
      chatTile.style.flex = '1 1 auto';
      
      const chatContent = document.createElement('div');
      chatContent.className = 'tile-content chat';
      const chatTemplate = this.templates.chat.content.cloneNode(true);
      chatContent.appendChild(chatTemplate);
      chatTile.appendChild(chatContent);
      
      this.container.appendChild(chatTile);
      this.container.classList.remove('with-panel');
    } else {
      // Create horizontal container for split view
      const container = document.createElement('div');
      container.className = 'tile-container horizontal';
      this.container.appendChild(container);
      this.container.classList.add('with-panel');
      
      // Add chat tile
      const chatTile = document.createElement('div');
      chatTile.className = 'tile';
      chatTile.setAttribute('data-content', 'chat');
      chatTile.style.flex = '70 1 0%';
      
      const chatContent = document.createElement('div');
      chatContent.className = 'tile-content chat';
      const chatTemplate = this.templates.chat.content.cloneNode(true);
      chatContent.appendChild(chatTemplate);
      chatTile.appendChild(chatContent);
      
      container.appendChild(chatTile);
      
      // Add resize handle
      const resizeHandle = document.createElement('div');
      resizeHandle.className = 'resize-handle resize-handle-horizontal';
      container.appendChild(resizeHandle);
      
      // Add second panel (sessions, tasks, or events)
      const secondPanelTile = document.createElement('div');
      secondPanelTile.className = 'tile split-in-horizontal';
      secondPanelTile.style.flex = '30 1 0%';
      
      // Determine which panel to show
      let panelType;
      if (this.panelStates.sessionsOpen) {
        panelType = 'sessions';
      } else if (this.panelStates.tasksOpen) {
        panelType = 'tasks';
      } else {
        panelType = 'events';
      }
      secondPanelTile.setAttribute('data-content', panelType);
      
      // Add header
      const header = document.createElement('div');
      header.className = 'tile-header';
      
      const title = document.createElement('div');
      title.className = 'tile-title';
      
      // Set appropriate title based on panel type
      if (panelType === 'sessions') {
        title.textContent = 'Sessions';
      } else if (panelType === 'tasks') {
        title.textContent = 'Tasks';
      } else {
        title.textContent = 'Events';
      }
      
      const controls = document.createElement('div');
      controls.className = 'tile-controls';
      
      const closeButton = document.createElement('button');
      closeButton.className = 'tile-control tile-close';
      closeButton.innerHTML = '×';
      closeButton.addEventListener('click', (e) => {
        e.stopPropagation();
        this.togglePanel(panelType);
      });
      
      controls.appendChild(closeButton);
      header.appendChild(title);
      header.appendChild(controls);
      
      secondPanelTile.appendChild(header);
      
      // If events panel, create a split view for list and details
      if (panelType === 'events') {
        // Create a vertical container for the split
        const verticalContainer = document.createElement('div');
        verticalContainer.className = 'tile-container vertical';
        
        // Add events content tile
        const eventsContentTile = document.createElement('div');
        eventsContentTile.className = 'tile';
        eventsContentTile.style.flex = '60 1 0%';
        
        // Add events content
        const eventsContent = document.createElement('div');
        eventsContent.className = 'tile-content events';
        
        // Add mountain background
        const mountainBg = document.createElement('div');
        mountainBg.className = 'mountain-bg';
        eventsContent.appendChild(mountainBg);
        
        // Add content from template
        const eventsTemplate = this.templates.events.content.cloneNode(true);
        eventsContent.appendChild(eventsTemplate);
        eventsContentTile.appendChild(eventsContent);
        
        // Add details tile
        const detailsContentTile = document.createElement('div');
        detailsContentTile.className = 'tile detail-panel';
        detailsContentTile.style.flex = '40 1 0%';
        
        // Add event details content
        const detailsContent = document.createElement('div');
        detailsContent.className = 'tile-content event-details';
        
        // Add content from template
        const detailsTemplate = this.templates.eventDetails.content.cloneNode(true);
        detailsContent.appendChild(detailsTemplate);
        detailsContentTile.appendChild(detailsContent);
        
        // Add both to vertical container
        verticalContainer.appendChild(eventsContentTile);
        
        // Add resize handle
        const verticalResizeHandle = document.createElement('div');
        verticalResizeHandle.className = 'resize-handle resize-handle-vertical';
        verticalContainer.appendChild(verticalResizeHandle);
        
        verticalContainer.appendChild(detailsContentTile);
        
        // Add vertical container to the second panel tile
        secondPanelTile.appendChild(verticalContainer);
        
        // Setup vertical resize handle
        this.setupVerticalResizeHandle(verticalResizeHandle, eventsContentTile, detailsContentTile);
      } else if (panelType === 'sessions') {
        // Similar split view for sessions panel
        const verticalContainer = document.createElement('div');
        verticalContainer.className = 'tile-container vertical';
        
        // Add sessions content tile
        const sessionsContentTile = document.createElement('div');
        sessionsContentTile.className = 'tile';
        sessionsContentTile.style.flex = '70 1 0%';
        
        // Add sessions content
        const sessionsContent = document.createElement('div');
        sessionsContent.className = 'tile-content sessions';
        
        // Add mountain background
        const mountainBg = document.createElement('div');
        mountainBg.className = 'mountain-bg';
        sessionsContent.appendChild(mountainBg);
        
        // Add content from template
        const sessionsTemplate = this.templates.sessions.content.cloneNode(true);
        sessionsContent.appendChild(sessionsTemplate);
        sessionsContentTile.appendChild(sessionsContent);
        
        // Add details tile
        const detailsContentTile = document.createElement('div');
        detailsContentTile.className = 'tile detail-panel';
        detailsContentTile.style.flex = '30 1 0%';
        
        // Add session details content
        const detailsContent = document.createElement('div');
        detailsContent.className = 'tile-content session-details';
        
        // Add content from template
        const detailsTemplate = this.templates.sessionDetails.content.cloneNode(true);
        detailsContent.appendChild(detailsTemplate);
        detailsContentTile.appendChild(detailsContent);
        
        // Add both to vertical container
        verticalContainer.appendChild(sessionsContentTile);
        
        // Add resize handle
        const verticalResizeHandle = document.createElement('div');
        verticalResizeHandle.className = 'resize-handle resize-handle-vertical';
        verticalContainer.appendChild(verticalResizeHandle);
        
        verticalContainer.appendChild(detailsContentTile);
        
        // Add vertical container to the second panel tile
        secondPanelTile.appendChild(verticalContainer);
        
        // Setup vertical resize handle
        this.setupVerticalResizeHandle(verticalResizeHandle, sessionsContentTile, detailsContentTile);
      } else {
        // For other panels (tasks), use the simple layout
        const panelContent = document.createElement('div');
        panelContent.className = `tile-content ${panelType}`;
        
        // Add mountain background
        const mountainBg = document.createElement('div');
        mountainBg.className = 'mountain-bg';
        panelContent.appendChild(mountainBg);
        
        // Add content from template
        const template = this.templates[panelType].content.cloneNode(true);
        panelContent.appendChild(template);
        
        secondPanelTile.appendChild(panelContent);
      }
      container.appendChild(secondPanelTile);
      
      // Set up resize handle
      this.setupResizeHandle(resizeHandle, chatTile, secondPanelTile);
    }
    
    // Restore chat messages and input value
    this.restoreChatMessages(savedMessages);
    this.restoreChatInput(savedInputValue);
    
    // Initialize event handlers
    this.initializeEventHandlers();
    
    // Refresh app.js event listeners
    this.reinitializeAppJs();
    
    // Trigger content rendering for the visible panel with better timing
    if (this.panelStates.sessionsOpen && window.sessionManager && typeof window.sessionManager.renderSessionsList === 'function') {
      console.log('Scheduling renderSessionsList after panel toggle');
      // Use longer delays with multiple attempts to ensure DOM is fully ready
      setTimeout(() => {
        console.log('First attempt to render sessions list');
        window.sessionManager.renderSessionsList(0);
        
        // Schedule a second attempt as a fallback
        setTimeout(() => {
          console.log('Second attempt to render sessions list (fallback)');
          if (window.sessionManager.sessionsContainer === null) {
            window.sessionManager.renderSessionsList(1);
          }
        }, 300);
      }, 200);
    } else if (this.panelStates.tasksOpen && typeof window.renderTasks === 'function') {
      console.log('Calling renderTasks after panel toggle');
      setTimeout(() => window.renderTasks(), 200);
    } else if (this.panelStates.eventsOpen && typeof window.renderEvents === 'function') {
      console.log('Calling renderEvents after panel toggle');
      setTimeout(() => window.renderEvents(), 200);
    }
  }
  
  // Save chat messages before layout changes
  saveChatMessages() {
    const messagesContainer = document.getElementById('chat-messages');
    return messagesContainer ? messagesContainer.innerHTML : null;
  }
  
  // Save chat input value before layout changes
  saveChatInput() {
    const inputElement = document.getElementById('chat-input');
    return inputElement ? inputElement.value : '';
  }
  
  // Restore chat messages after layout changes
  restoreChatMessages(savedMessages) {
    if (!savedMessages) return;
    
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
      messagesContainer.innerHTML = savedMessages;
      console.log('Restored chat messages');
    }
  }
  
  // Restore chat input value after layout changes
  restoreChatInput(savedInputValue) {
    if (!savedInputValue) return;
    
    const inputElement = document.getElementById('chat-input');
    if (inputElement) {
      inputElement.value = savedInputValue;
      console.log('Restored input value');
      
      // Trigger input event to resize textarea if needed
      const event = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(event);
    }
  }
  
  // Set up horizontal resize handle functionality
  setupResizeHandle(handle, leftElement, rightElement) {
    let startX;
    let startLeftWidth;
    let startRightWidth;
    
    const start = (e) => {
      e.preventDefault();
      startX = e.clientX;
      
      const leftRect = leftElement.getBoundingClientRect();
      const rightRect = rightElement.getBoundingClientRect();
      
      startLeftWidth = leftRect.width;
      startRightWidth = rightRect.width;
      
      document.addEventListener('mousemove', move);
      document.addEventListener('mouseup', end);
      
      handle.classList.add('active');
    };
    
    const move = (e) => {
      const delta = e.clientX - startX;
      
      // Calculate percentages based on container width
      const containerWidth = leftElement.parentNode.clientWidth - handle.clientWidth;
      const leftPercent = ((startLeftWidth + delta) / containerWidth) * 100;
      const rightPercent = ((startRightWidth - delta) / containerWidth) * 100;
      
      // Apply constraints (minimum 15% width)
      if (leftPercent >= 15 && rightPercent >= 15) {
        leftElement.style.flex = `${leftPercent} 1 0%`;
        rightElement.style.flex = `${rightPercent} 1 0%`;
      }
    };
    
    const end = () => {
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', end);
      handle.classList.remove('active');
    };
    
    handle.addEventListener('mousedown', start);
  }
  
  // Set up vertical resize handle functionality
  setupVerticalResizeHandle(handle, topElement, bottomElement) {
    let startY;
    let startTopHeight;
    let startBottomHeight;
    
    const start = (e) => {
      e.preventDefault();
      startY = e.clientY;
      
      const topRect = topElement.getBoundingClientRect();
      const bottomRect = bottomElement.getBoundingClientRect();
      
      startTopHeight = topRect.height;
      startBottomHeight = bottomRect.height;
      
      document.addEventListener('mousemove', move);
      document.addEventListener('mouseup', end);
      
      handle.classList.add('active');
    };
    
    const move = (e) => {
      const delta = e.clientY - startY;
      
      // Calculate percentages based on container height
      const containerHeight = topElement.parentNode.clientHeight - handle.clientHeight;
      const topPercent = ((startTopHeight + delta) / containerHeight) * 100;
      const bottomPercent = ((startBottomHeight - delta) / containerHeight) * 100;
      
      // Apply constraints (minimum 15% height)
      if (topPercent >= 15 && bottomPercent >= 15) {
        topElement.style.flex = `${topPercent} 1 0%`;
        bottomElement.style.flex = `${bottomPercent} 1 0%`;
      }
    };
    
    const end = () => {
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', end);
      handle.classList.remove('active');
    };
    
    handle.addEventListener('mousedown', start);
  }
  
  // Initialize event handlers for panels
  initializeEventHandlers() {
    // Tasks panel handlers
    const tasksContainer = document.getElementById('tasks-container');
    if (tasksContainer) {
      tasksContainer.addEventListener('click', (e) => {
        const taskItem = e.target.closest('.task-item');
        if (taskItem && taskItem.dataset.taskId) {
          console.log(`Task clicked: ${taskItem.dataset.taskId}`);
          // Show task details (not implemented in simplified version)
        }
      });
    }
    
    // Events panel handlers
    const eventsContainer = document.getElementById('events-container');
    if (eventsContainer) {
      eventsContainer.addEventListener('click', (e) => {
        const eventItem = e.target.closest('.event-item');
        if (eventItem && eventItem.dataset.eventId) {
          console.log(`Event clicked: ${eventItem.dataset.eventId}`);
          // Show event details (not implemented in simplified version)
        }
      });
    }
    
    // Sessions panel handlers
    const sessionsContainer = document.getElementById('sessions-container');
    if (sessionsContainer) {
      console.log('Sessions container found, initializing handlers');
      
      // Initialize sessions UI if session manager exists
      if (window.sessionManager && typeof window.sessionManager.initSessionsUI === 'function') {
        console.log('Initializing sessions UI from tiling manager');
        window.sessionManager.initSessionsUI();
      } else {
        console.log('Session manager not available or initSessionsUI not a function');
      }
      
      // Initialize new session button
      const newSessionButton = document.getElementById('new-session-button');
      if (newSessionButton) {
        console.log('Setting up new session button handler');
        // Remove existing handlers
        const newBtn = newSessionButton.cloneNode(true);
        if (newSessionButton.parentNode) {
          newSessionButton.parentNode.replaceChild(newBtn, newSessionButton);
        }
        
        // Add handler
        newBtn.addEventListener('click', () => {
          console.log('New session button clicked');
          if (window.sessionManager && typeof window.sessionManager.createNewSession === 'function') {
            window.sessionManager.createNewSession();
          }
        });
      }
    }
  }
  
  // Reinitialize app.js event listeners 
  reinitializeAppJs() {
    console.log('Reinitializing app.js event listeners');
    
    // Dispatch event for app.js to re-initialize
    document.dispatchEvent(new CustomEvent('layout:changed'));
    
    // As a fallback, manually trigger initialization
    setTimeout(() => {
      if (typeof window.initializeUI === 'function') {
        window.initializeUI();
      }
    }, 100);
  }
  
  // Show task details (simplified version)
  showTaskDetails(taskId) {
    console.log(`Show task details: ${taskId}`);
    // Simply log the request in this simplified version
  }
  
  // Show event details (simplified version)
  showEventDetails(eventId) {
    console.log(`Show event details: ${eventId}`);
    // Simply log the request in this simplified version
  }
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM loaded, initializing tiling manager');
  window.tilingManager = new TilingManager();
  
  // Signal that the tiling manager is ready
  document.dispatchEvent(new CustomEvent('tiling:ready'));
  console.log('Tiling manager initialized and ready');
});