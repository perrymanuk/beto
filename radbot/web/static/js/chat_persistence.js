/**
 * Chat persistence module for RadBot UI with server synchronization
 * Handles both localStorage-based and server-based message storage
 */

export class ChatPersistence {
  constructor(options = {}) {
    this.maxMessagesPerChat = options.maxMessagesPerChat || 200;
    this.storagePrefix = options.storagePrefix || 'radbot_chat_';
    this.useSessionOnly = options.useSessionOnly || false;
    this.messageCache = {}; // In-memory cache
    this.saveBatchTimeout = null;
    this.serverSyncEnabled = options.serverSyncEnabled !== false; // Enable by default

    // Session metadata - will be initialized by session manager
    this.sessionsIndexKey = 'radbot_sessions_index';

    // Listen for storage events from other tabs
    window.addEventListener('storage', this.handleStorageEvent.bind(this));

    // Track online status for server sync
    this.isOnline = window.navigator.onLine;
    window.addEventListener('online', () => {
      console.log('Browser went online, triggering sync');
      this.isOnline = true;
      this.syncWithServer(window.state?.sessionId);
    });

    window.addEventListener('offline', () => {
      console.log('Browser went offline, disabling sync');
      this.isOnline = false;
    });
  }

  // Get the appropriate storage object
  getStorage() {
    return this.useSessionOnly ? sessionStorage : localStorage;
  }

  // Save messages with debounced writes to improve performance
  saveMessages(chatId, messages) {
    if (!chatId || !Array.isArray(messages)) {
      console.error('Invalid parameters for saveMessages:', { chatId, messageCount: messages ? messages.length : 0 });
      return false;
    }

    // Make sure messages are valid before saving
    const validMessages = this.validateMessages(messages);

    // Update in-memory cache first
    this.messageCache[chatId] = validMessages.slice(-this.maxMessagesPerChat);

    console.log(`Saving ${this.messageCache[chatId].length} messages to localStorage for session ${chatId}`);

    // Function to actually perform the save
    const performSave = () => {
      try {
        const storage = this.getStorage();
        const key = `${this.storagePrefix}${chatId}`;

        // Stringify messages
        const json = JSON.stringify(this.messageCache[chatId]);

        // Verify we have actual data
        if (!json || json === '[]' || json === 'null') {
          console.warn('Attempting to save empty data to localStorage:', json);
        }

        // Save to storage
        storage.setItem(key, json);

        // Verify it was saved correctly
        const savedData = storage.getItem(key);
        if (savedData) {
          console.log(`Successfully saved ${this.messageCache[chatId].length} messages to localStorage. Data size: ${savedData.length} bytes`);

          // Trigger server sync if online and enabled
          if (this.serverSyncEnabled && this.isOnline) {
            this.syncWithServer(chatId);
          }

          return true;
        } else {
          console.error('Failed to save messages - no data found after save');
          return false;
        }
      } catch (e) {
        console.error('Error saving messages:', e);
        return false;
      }
    };

    // Batch save to storage
    clearTimeout(this.saveBatchTimeout);
    this.saveBatchTimeout = setTimeout(() => {
      try {
        if (performSave()) {
          return true;
        }

        // If save failed, try cleanup and retry
        console.log('Initial save failed, trying cleanup...');
        this.cleanupOldData();

        if (performSave()) {
          return true;
        }

        // If still failing, try session storage
        console.log('Save still failing after cleanup, trying session storage...');
        this.useSessionOnly = true;
        return this.saveMessages(chatId, messages);
      } catch (e) {
        console.error('Failed to save chat history:', e);
        return false;
      }
    }, 300);

    return true;
  }

  // Get messages for a specific chat
  getMessages(chatId) {
    if (!chatId) {
      console.warn('getMessages called with empty chatId');
      return [];
    }

    // Check in-memory cache first
    if (this.messageCache[chatId]) {
      console.log(`Using cached messages for ${chatId}: ${this.messageCache[chatId].length} messages`);
      return [...this.messageCache[chatId]];
    }

    // Try to load from storage
    try {
      const storage = this.getStorage();
      const key = `${this.storagePrefix}${chatId}`;
      console.log(`Attempting to retrieve messages from storage key: ${key}`);

      // First try getting the item directly
      let data = storage.getItem(key);

      // Log all keys for debugging
      const keys = [];
      for (let i = 0; i < storage.length; i++) {
        keys.push(storage.key(i));
      }
      console.log('All keys in storage:', keys);

      // Try to match key by exact match or substring
      if (!data) {
        const matchingKey = keys.find(k => k === key || k.includes(chatId));
        if (matchingKey) {
          console.log(`Found matching key: ${matchingKey}`);
          data = storage.getItem(matchingKey);
        }
      }

      if (data) {
        try {
          console.log(`Raw data from storage: ${data.substring(0, 50)}...`);
          const messages = JSON.parse(data);
          // Validate and cache
          this.messageCache[chatId] = this.validateMessages(messages);
          console.log(`Successfully loaded ${this.messageCache[chatId].length} messages for chat ${chatId}`);
          return [...this.messageCache[chatId]];
        } catch (parseError) {
          console.error('Error parsing chat data:', parseError, 'Raw data:', data);
          return [];
        }
      } else {
        console.log(`No saved chat data found for chat ${chatId}`);

        // Try loading from server if enabled and online
        if (this.serverSyncEnabled && this.isOnline) {
          console.log(`Attempting to load messages from server for chat ${chatId}`);
          // We can't await here, so we'll return an empty array for now
          // and the server sync will update the cache asynchronously
          this.loadMessagesFromServer(chatId)
            .then(success => {
              if (success) {
                console.log(`Successfully loaded messages from server for chat ${chatId}`);
              } else {
                console.log(`No messages found on server for chat ${chatId}`);
              }
            })
            .catch(error => {
              console.error(`Error loading messages from server for chat ${chatId}:`, error);
            });
        }
      }
    } catch (e) {
      console.error('Error loading chat data', e);
    }

    return [];
  }

  // Add a single message to the chat history
  addMessage(chatId, message) {
    // Get existing messages
    const messages = this.getMessages(chatId);

    // Add the new message
    messages.push(message);

    // Save the updated messages locally
    const saveResult = this.saveMessages(chatId, messages);

    // Send to server if server sync is enabled and online
    if (this.serverSyncEnabled && this.isOnline) {
      this.sendMessageToServer(chatId, message)
        .catch(error => console.error('Error sending message to server:', error));
    }

    return saveResult;
  }

  // Clear chat history for a specific chat ID
  clearChat(chatId) {
    if (!chatId) return false;

    // Clear in-memory cache
    if (this.messageCache[chatId]) {
      delete this.messageCache[chatId];
    }

    // Clear from storage
    try {
      const storage = this.getStorage();
      const key = `${this.storagePrefix}${chatId}`;
      storage.removeItem(key);

      // Notify server if enabled and online
      if (this.serverSyncEnabled && this.isOnline) {
        fetch(`/api/sessions/${chatId}/reset`, { method: 'POST' })
          .catch(error => console.error('Error resetting session on server:', error));
      }

      return true;
    } catch (e) {
      console.error('Error clearing chat data', e);
      return false;
    }
  }

  // Handle storage events from other tabs
  handleStorageEvent(event) {
    // Only process our own storage keys
    if (event.key && event.key.startsWith(this.storagePrefix)) {
      const chatId = event.key.replace(this.storagePrefix, '');

      // Clear cache for this chat ID to force a reload from storage
      if (this.messageCache[chatId]) {
        delete this.messageCache[chatId];
      }

      // Dispatch an event that chat data has changed
      window.dispatchEvent(new CustomEvent('chatDataChanged', {
        detail: { chatId, source: 'storage' }
      }));
    }
  }

  // Check if error is due to quota exceeded
  isQuotaExceeded(e) {
    return (
      e instanceof DOMException &&
      (e.code === 22 || // Chrome
       e.code === 1014 || // Firefox
       e.name === 'QuotaExceededError' ||
       e.name === 'NS_ERROR_DOM_QUOTA_REACHED')
    );
  }

  // Cleanup old data to free space
  cleanupOldData() {
    const storage = this.getStorage();

    // Get all keys related to our app
    const chatKeys = [];
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i);
      if (key && key.startsWith(this.storagePrefix)) {
        const chatId = key.replace(this.storagePrefix, '');
        chatKeys.push({
          key,
          chatId,
          size: (storage.getItem(key) || '').length
        });
      }
    }

    // Sort by size (largest first) and remove some
    chatKeys.sort((a, b) => b.size - a.size);

    // Remove the largest items to free space
    for (let i = 0; i < Math.min(chatKeys.length, 3); i++) {
      try {
        storage.removeItem(chatKeys[i].key);
        console.log(`Removed large chat history: ${chatKeys[i].chatId} (${chatKeys[i].size} bytes)`);
      } catch (e) {
        console.error('Error removing item during cleanup', e);
      }
    }
  }

  // Validate messages array - ensure it has the right structure
  validateMessages(messages) {
    if (!Array.isArray(messages)) {
      console.warn('validateMessages: messages is not an array:', messages);
      return [];
    }

    // Filter out invalid messages
    const filteredMessages = messages.filter(msg => {
      const isValid = (
        msg &&
        typeof msg === 'object' &&
        (msg.role === 'user' || msg.role === 'assistant' || msg.role === 'system') &&
        typeof msg.content === 'string'
      );

      if (!isValid) {
        console.warn('Filtering out invalid message:', msg);
      }

      return isValid;
    });

    console.log(`validateMessages: ${filteredMessages.length}/${messages.length} messages passed validation`);
    return filteredMessages;
  }

  // Get list of all saved chats
  getAllChats() {
    const storage = this.getStorage();
    const chats = [];

    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i);
      if (key && key.startsWith(this.storagePrefix)) {
        const chatId = key.replace(this.storagePrefix, '');
        chats.push(chatId);
      }
    }

    return chats;
  }

  // Get the last message for a chat
  getLastMessage(chatId) {
    if (!chatId) return null;

    // Check cache first
    if (this.messageCache[chatId] && this.messageCache[chatId].length > 0) {
      return this.messageCache[chatId][this.messageCache[chatId].length - 1];
    }

    // Try to get from storage
    const messages = this.getMessages(chatId);
    if (messages && messages.length > 0) {
      return messages[messages.length - 1];
    }

    return null;
  }

  // --- Server Synchronization Methods ---

  // Sync messages with server
  async syncWithServer(sessionId) {
    if (!this.serverSyncEnabled || !this.isOnline || !sessionId) {
      return false;
    }

    console.log(`Syncing messages with server for session ${sessionId}`);

    try {
      // Get all local messages
      const messages = this.getMessages(sessionId);

      if (!messages || messages.length === 0) {
        // Try loading from server if no local messages
        return await this.loadMessagesFromServer(sessionId);
      }

      // TEMPORARY FIX: Skip batch sync on first page load to prevent duplicate messages
      if (window.initialLoadInProgress) {
        console.log("Skipping batch sync during initial load to prevent duplicates");
        return true;
      }

      // Check if we've already synced these messages
      const syncedMessageKey = `${this.storagePrefix}${sessionId}_synced`;
      const storage = this.getStorage();
      const lastSyncedCount = parseInt(storage.getItem(syncedMessageKey) || '0');
      
      // Only sync if we have new messages or haven't synced before
      if (messages.length <= lastSyncedCount && lastSyncedCount > 0) {
        console.log(`Skipping sync - already synced ${lastSyncedCount} messages, current count: ${messages.length}`);
        return true;
      }

      // Send to server in batches, but only send messages we haven't synced yet
      const batchSize = 50;
      let syncCount = 0;

      // First, check if this is a duplicate session that we've just loaded
      if (messages.length > 100) {
        // If we have more than 100 messages, only do initial sync, not full batch sync
        console.log(`Large message count (${messages.length}), limiting initial sync to avoid duplicates`);
        syncCount = messages.length;
        storage.setItem(syncedMessageKey, syncCount.toString());
        return true;
      }
      
      // Normal sync for small message counts
      for (let i = 0; i < messages.length; i += batchSize) {
        const batch = messages.slice(i, i + batchSize);
        await this.sendMessagesToServer(sessionId, batch);
        syncCount += batch.length;
      }

      // Store the number of messages we've synced
      storage.setItem(syncedMessageKey, syncCount.toString());

      console.log(`Successfully synced ${syncCount} messages with server for session ${sessionId}`);
      return true;
    } catch (e) {
      console.error(`Error syncing with server for session ${sessionId}:`, e);
      return false;
    }
  }

  // Send a batch of messages to server
  async sendMessagesToServer(sessionId, messages) {
    if (!sessionId || !messages || !this.isOnline || messages.length === 0) {
      return false;
    }

    try {
      // Convert messages to API format
      const apiMessages = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        agent_name: msg.agent,
        metadata: {
          client_id: msg.id,
          client_timestamp: msg.timestamp
        }
      }));

      // Send batch request
      const response = await fetch(`/api/messages/${sessionId}/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: apiMessages })
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log(`Successfully sent ${data.count} messages to server for session ${sessionId}`);
      return true;
    } catch (e) {
      console.error(`Error sending messages to server for session ${sessionId}:`, e);
      return false;
    }
  }

  // Send a single message to server
  async sendMessageToServer(sessionId, message) {
    if (!sessionId || !message || !this.isOnline) {
      return false;
    }

    try {
      // Convert message to API format
      const apiMessage = {
        role: message.role,
        content: message.content,
        agent_name: message.agent,
        metadata: {
          client_id: message.id,
          client_timestamp: message.timestamp
        }
      };

      // Send request
      const response = await fetch(`/api/messages/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiMessage)
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      console.log(`Successfully sent message to server for session ${sessionId}`);
      return true;
    } catch (e) {
      console.error(`Error sending message to server for session ${sessionId}:`, e);
      return false;
    }
  }

  // Load messages from server
  async loadMessagesFromServer(sessionId) {
    if (!sessionId || !this.isOnline) {
      return false;
    }

    try {
      // Get messages from server
      const response = await fetch(`/api/messages/${sessionId}`);

      // Handle 404 or other errors gracefully
      if (!response.ok) {
        if (response.status === 404) {
          console.log(`No messages found on server for session ${sessionId}`);
          return false;
        }
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.messages || data.messages.length === 0) {
        console.log(`No messages found on server for session ${sessionId}`);
        return false;
      }

      // Convert server messages to client format
      const serverMessages = data.messages.map(msg => ({
        id: msg.metadata?.client_id || msg.message_id,
        role: msg.role,
        content: msg.content,
        agent: msg.agent_name,
        timestamp: msg.metadata?.client_timestamp || Date.parse(msg.timestamp)
      }));

      console.log(`Loaded ${serverMessages.length} messages from server for session ${sessionId}`);

      // Get any existing local messages
      const localMessages = this.getMessages(sessionId);

      // Merge messages without duplicates (keeping client IDs where possible)
      const mergedMessages = mergeMessages(localMessages, serverMessages);

      // Update cache and localStorage
      this.messageCache[sessionId] = mergedMessages;
      this.saveMessages(sessionId, mergedMessages);

      return true;
    } catch (e) {
      console.error(`Error loading messages from server for session ${sessionId}:`, e);
      return false;
    }
  }
}

// Create and merge message objects from different sources
export function mergeMessages(localMessages, serverMessages) {
  // Create a map of existing messages by ID
  const messageMap = new Map();

  // Add local messages to the map
  localMessages.forEach(msg => {
    if (msg.id) {
      messageMap.set(msg.id, msg);
    }
  });

  // Add/update with server messages
  serverMessages.forEach(msg => {
    if (msg.id) {
      // Server message takes precedence if it exists in both
      messageMap.set(msg.id, msg);
    }
  });

  // Convert back to array and sort by timestamp
  return Array.from(messageMap.values())
    .sort((a, b) => {
      const timeA = a.timestamp || 0;
      const timeB = b.timestamp || 0;
      return timeA - timeB;
    });
}

// Create a message object with consistent structure
export function createMessageObject(role, content, agentName = null) {
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : generateUUID(),
    role: role,
    content: content,
    timestamp: Date.now(),
    agent: agentName
  };
}

// Generate a UUID for message IDs if crypto.randomUUID is not available
export function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}