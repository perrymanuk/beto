/**
 * Test functions for sessions functionality
 * This file contains test functions that can be run in the browser console
 */

// Test creating a new session
function testCreateSession() {
  console.log('Testing session creation');
  if (!window.sessionManager) {
    console.error('Session manager not initialized');
    return;
  }
  
  const newSession = window.sessionManager.createNewSession();
  console.log('Created new session:', newSession);
  return newSession;
}

// Test switching between sessions
function testSwitchSession(sessionId) {
  console.log('Testing session switching to', sessionId);
  if (!window.sessionManager) {
    console.error('Session manager not initialized');
    return;
  }
  
  if (!sessionId) {
    // Get all sessions
    const sessions = window.sessionManager.sessionsIndex.sessions;
    if (sessions.length < 2) {
      console.warn('Not enough sessions to test switching, creating a new one');
      const newSession = window.sessionManager.createNewSession();
      sessionId = newSession.id;
    } else {
      // Get a session that's not the active one
      const activeId = window.sessionManager.sessionsIndex.active_session_id;
      sessionId = sessions.find(s => s.id !== activeId)?.id;
    }
  }
  
  if (!sessionId) {
    console.error('Could not find a session to switch to');
    return;
  }
  
  // Switch to the selected session
  window.sessionManager.switchToSession(sessionId);
  console.log('Switched to session:', sessionId);
  return sessionId;
}

// Test renaming a session
function testRenameSession(sessionId, newName) {
  console.log('Testing session renaming');
  if (!window.sessionManager) {
    console.error('Session manager not initialized');
    return;
  }
  
  if (!sessionId) {
    // Use active session
    sessionId = window.sessionManager.sessionsIndex.active_session_id;
  }
  
  if (!newName) {
    newName = `Test Session ${Date.now()}`;
  }
  
  const result = window.sessionManager.renameSession(sessionId, newName);
  console.log(`Renamed session ${sessionId} to "${newName}": ${result}`);
  return result;
}

// Test deleting a session
function testDeleteSession(sessionId) {
  console.log('Testing session deletion');
  if (!window.sessionManager) {
    console.error('Session manager not initialized');
    return;
  }
  
  if (!sessionId) {
    // Get all sessions
    const sessions = window.sessionManager.sessionsIndex.sessions;
    if (sessions.length < 2) {
      console.warn('Not enough sessions to test deletion, need at least 2');
      return false;
    }
    
    // Get a session that's not the active one
    const activeId = window.sessionManager.sessionsIndex.active_session_id;
    sessionId = sessions.find(s => s.id !== activeId)?.id;
  }
  
  if (!sessionId) {
    console.error('Could not find a session to delete');
    return false;
  }
  
  // Make sure we're not trying to delete the active session
  if (sessionId === window.sessionManager.sessionsIndex.active_session_id) {
    console.error('Cannot delete the active session');
    return false;
  }
  
  const result = window.sessionManager.deleteSession(sessionId);
  console.log(`Deleted session ${sessionId}: ${result}`);
  return result;
}

// Run all tests in sequence
function runAllTests() {
  console.log('Running all session tests');
  
  // Create a new session
  const newSession = testCreateSession();
  
  // Add a message to the new session
  if (window.chatModule) {
    window.chatModule.addMessage('user', 'This is a test message for the new session');
    window.chatModule.addMessage('assistant', 'This is a test response in the new session');
  }
  
  // Switch back to the original session
  const originalSessionId = window.sessionManager.sessionsIndex.sessions[0].id;
  testSwitchSession(originalSessionId);
  
  // Rename the original session
  testRenameSession(originalSessionId, 'Original Session');
  
  // Switch to the new session again
  testSwitchSession(newSession.id);
  
  // Rename the new session
  testRenameSession(newSession.id, 'New Test Session');
  
  // Create a third session for deletion test
  const deleteTestSession = testCreateSession();
  
  // Switch back to the original session
  testSwitchSession(originalSessionId);
  
  // Delete the session created for deletion test
  testDeleteSession(deleteTestSession.id);
  
  console.log('All tests completed');
}

// Expose test functions to the window object
window.testCreateSession = testCreateSession;
window.testSwitchSession = testSwitchSession;
window.testRenameSession = testRenameSession;
window.testDeleteSession = testDeleteSession;
window.runAllTests = runAllTests;

console.log('Sessions test functions loaded. Run window.runAllTests() to test all functionality');