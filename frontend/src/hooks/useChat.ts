"use client";

import { useState, useCallback } from "react";
import { 
  processStreamingChat, 
  sendSmartChatRequest, 
  confirmFallback,
  getConversationStatus,
  type ChatRequest,
  type RAGChatResponse 
} from "../services/chatService";

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{
    chunk_id: string;
    document_name: string;
    document_id: string;
    content_preview: string;
  }>;
  usedContext?: boolean;
  confidenceScore?: number;
}

export interface FallbackRequest {
  query: string;
  explanation: string;
  confidence_score: number;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [apiKey, setApiKey] = useState(() => {
    // Initialize API key from localStorage if available
    if (typeof window !== 'undefined') {
      return localStorage.getItem('rag-chat-api-key') || '';
    }
    return '';
  });
  const [pendingFallback, setPendingFallback] = useState<FallbackRequest | null>(null);

  // Persist API key to localStorage when it changes
  const handleSetApiKey = useCallback((key: string) => {
    setApiKey(key);
    if (typeof window !== 'undefined') {
      if (key.trim()) {
        localStorage.setItem('rag-chat-api-key', key);
      } else {
        localStorage.removeItem('rag-chat-api-key');
      }
    }
  }, []);

  const sendChat = async (userMessage: string) => {
    if (!userMessage.trim()) return;

    // Add user message to messages
    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setInputValue('');
    setLoading(true);
    setError(null);
    setPendingFallback(null);

    // Prepare chat request
    const chatRequest: ChatRequest = {
      userMessage: userMessage,
      model: "gpt-4.1-mini",
      apiKey: apiKey
    };

    try {
      // Use smart chat that automatically chooses RAG or regular chat
      const response: RAGChatResponse = await sendSmartChatRequest(chatRequest);
      
      if (!response.success) {
        throw new Error(response.error || "Chat request failed");
      }

      if (response.needsFallback && response.fallbackRequest) {
        // Handle fallback scenario
        setPendingFallback({
          query: response.fallbackRequest.query,
          explanation: response.fallbackRequest.explanation,
          confidence_score: response.fallbackRequest.confidence_score
        });
        
        // Add a message indicating fallback is needed
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `I couldn't find relevant information in your uploaded documents to answer: "${userMessage}"\n\n**Confidence Score:** ${(response.fallbackRequest.confidence_score * 100).toFixed(1)}%\n\n**Explanation:** ${response.fallbackRequest.explanation}\n\nWould you like me to answer using my general knowledge instead?`,
          usedContext: false,
          confidenceScore: response.fallbackRequest.confidence_score
        }]);
      } else {
        // Add successful response
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: response.response || "No response received",
          citations: response.citations,
          usedContext: response.usedContext,
          confidenceScore: response.confidenceScore
        }]);
      }
      
      setLoading(false);
      return response.response;
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unknown error");
      }
      setLoading(false);
    }
  };

  const handleFallbackConfirmation = async (useGeneralKnowledge: boolean) => {
    if (!pendingFallback) return;

    setLoading(true);
    setError(null);

    try {
      const response = await confirmFallback(
        pendingFallback.query, 
        useGeneralKnowledge, 
        apiKey
      );

      if (!response.success) {
        throw new Error(response.error || "Fallback request failed");
      }

      if (useGeneralKnowledge && response.response) {
        // Replace the fallback message with the general knowledge response
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: 'assistant',
            content: response.response || "No response received",
            usedContext: false,
            citations: []
          };
          return updated;
        });
      } else {
        // User declined, check if documents still exist before staying in document mode
        try {
          const status = await getConversationStatus(apiKey);
          const hasDocuments = status.documents && Array.isArray(status.documents) && status.documents.length > 0;
          
          if (!hasDocuments) {
            // No documents available, inform user and suggest they upload documents
            setMessages(prev => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                role: 'assistant',
                content: "I notice you don't have any documents uploaded. To use document mode, please upload some documents first. For now, I can answer using my general knowledge if you'd like.",
                usedContext: false,
                citations: []
              };
              return updated;
            });
          } else {
            // Documents exist, stay in document mode
            setMessages(prev => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                role: 'assistant',
                content: "I'll stay focused on your uploaded documents. Please try rephrasing your question or ask about content that's in your documents.",
                usedContext: false,
                citations: []
              };
              return updated;
            });
          }
        } catch (statusError) {
          // If we can't check status, default to the original message
          console.warn('Failed to check document status after fallback:', statusError);
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: 'assistant',
              content: "I'll stay focused on your uploaded documents. Please try rephrasing your question or ask about content that's in your documents.",
              usedContext: false,
              citations: []
            };
            return updated;
          });
        }
      }

      setPendingFallback(null);
      setLoading(false);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unknown error");
      }
      setLoading(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!inputValue.trim()) return;
    await sendChat(inputValue);
  };

  return { 
    messages, 
    loading, 
    error, 
    inputValue, 
    setInputValue, 
    handleSubmit, 
    apiKey, 
    setApiKey: handleSetApiKey,
    sendChat,
    pendingFallback,
    handleFallbackConfirmation
  };
}
