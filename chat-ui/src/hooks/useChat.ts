import { useState, useCallback } from 'react';
import axios from 'axios';
import { ChatMessage, ChatRequest, ChatResponse } from '../types/chat';

const CHAT_API_URL = import.meta.env.VITE_CHAT_API_URL || '/api';

export const useChat = (sessionId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const request: ChatRequest = {
        session_id: sessionId,
        message: content.trim(),
      };

      const response = await axios.post<ChatResponse>(`${CHAT_API_URL}/chat`, request, {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30 second timeout
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.answer,
        timestamp: new Date(),
        sources: response.data.sources,
        tool_calls: response.data.tool_calls,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat API Error:', err);
      let errorMessage = 'Failed to send message. Please try again.';
      
      if (axios.isAxiosError(err)) {
        if (err.code === 'ECONNABORTED') {
          errorMessage = 'Request timed out. Please try again.';
        } else if (err.response?.status === 500) {
          errorMessage = 'Server error. Please try again later.';
        } else if (err.response?.data?.detail) {
          errorMessage = `Error: ${err.response.data.detail}`;
        }
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  };
};