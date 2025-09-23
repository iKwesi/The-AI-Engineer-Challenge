/**
 * Session Manager - Handles browser session ID generation and management
 * Session IDs are generated per browser session and cleared on page refresh
 */

const SESSION_STORAGE_KEY = 'lechat_session_id';

/**
 * Generate a new session ID
 */
function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Get the current session ID, generating one if it doesn't exist
 * Session ID persists only for the current browser session (cleared on refresh)
 */
export function getSessionId(): string {
  // Try to get existing session ID from sessionStorage (cleared on page refresh)
  let sessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);
  
  if (!sessionId) {
    // Generate new session ID if none exists
    sessionId = generateSessionId();
    sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    console.log('Generated new session ID:', sessionId);
  }
  
  return sessionId;
}

/**
 * Clear the current session ID (forces generation of new session on next call)
 */
export function clearSessionId(): void {
  sessionStorage.removeItem(SESSION_STORAGE_KEY);
  console.log('Cleared session ID');
}

/**
 * Check if we have an active session
 */
export function hasActiveSession(): boolean {
  return sessionStorage.getItem(SESSION_STORAGE_KEY) !== null;
}

/**
 * Get session info for debugging
 */
export function getSessionInfo(): { sessionId: string; isNew: boolean } {
  const sessionId = getSessionId();
  const isNew = !hasActiveSession();
  
  return {
    sessionId,
    isNew
  };
}
