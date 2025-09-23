// Utility function to generate random session ID
export const generateSessionId = (): string => {
  // Generate 5-6 character alphanumeric string
  const randomChars = Math.random().toString(36).substring(2, 8); // 6 characters
  return `user_${randomChars}`;
};

// Utility function to get or create session ID
export const getSessionId = (): string => {
  // Check if session ID exists in sessionStorage
  let sessionId = sessionStorage.getItem('chat_session_id');
  
  if (!sessionId) {
    // Generate new session ID if none exists
    sessionId = generateSessionId();
    sessionStorage.setItem('chat_session_id', sessionId);
  }
  
  return sessionId;
};

// Utility function to reset session ID (for new conversation)
export const resetSessionId = (): string => {
  const newSessionId = generateSessionId();
  sessionStorage.setItem('chat_session_id', newSessionId);
  return newSessionId;
};