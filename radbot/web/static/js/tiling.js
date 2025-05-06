// Simplified Tiling Window Manager Implementation
class TilingManager {
  constructor() {
    console.log('Initializing TilingManager');
    this.container = document.getElementById('app-container');
    
    // Track panel states
    this.panelStates = {
      tasksOpen: false,
      eventsOpen: false
    };
    
    this.templates = {
      chat: document.getElementById('chat-template'),
      tasks: document.getElementById('tasks-template'),
      events: document.getElementById('events-template'),
      taskDetails: document.getElementById('task-details-template'),
      eventDetails: document.getElementById('event-details-template')
    };
    
    // Initialize by rendering the main chat container
    this.renderInitialLayout();
    
    // Listen for command events
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
  
  // Toggle a panel (tasks or events)
  togglePanel(panelType) {
    console.log(`Toggling ${panelType} panel`);
    
    // Save chat content and input value before modifying layout
    const savedMessages = this.saveChatMessages();
    const savedInputValue = this.saveChatInput();
    
    // Toggle panel state
    if (panelType === 'tasks') {
      this.panelStates.tasksOpen = !this.panelStates.tasksOpen;
      
      // If opening tasks panel, close events panel
      if (this.panelStates.tasksOpen) {
        this.panelStates.eventsOpen = false;
      }
    } else if (panelType === 'events') {
      this.panelStates.eventsOpen = !this.panelStates.eventsOpen;
      
      // If opening events panel, close tasks panel
      if (this.panelStates.eventsOpen) {
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
    
    if (!this.panelStates.tasksOpen && !this.panelStates.eventsOpen) {
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
      
      // Add second panel (tasks or events)
      const secondPanelTile = document.createElement('div');
      secondPanelTile.className = 'tile split-in-horizontal';
      secondPanelTile.style.flex = '30 1 0%';
      
      const panelType = this.panelStates.tasksOpen ? 'tasks' : 'events';
      secondPanelTile.setAttribute('data-content', panelType);
      
      // Add header
      const header = document.createElement('div');
      header.className = 'tile-header';
      
      const title = document.createElement('div');
      title.className = 'tile-title';
      title.textContent = panelType === 'tasks' ? 'Tasks' : 'Events';
      
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
      
      // Add panel content
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
    
    // Trigger content rendering for the visible panel
    if (this.panelStates.tasksOpen && typeof window.renderTasks === 'function') {
      console.log('Calling renderTasks after panel toggle');
      setTimeout(() => window.renderTasks(), 100);
    } else if (this.panelStates.eventsOpen && typeof window.renderEvents === 'function') {
      console.log('Calling renderEvents after panel toggle');
      setTimeout(() => window.renderEvents(), 100);
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
  
  // Set up resize handle functionality
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