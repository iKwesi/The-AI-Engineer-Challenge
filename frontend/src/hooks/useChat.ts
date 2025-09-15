"use client";

import { useState } from "react";
import { processStreamingChat, type ChatRequest } from "../services/chatService";

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [apiKey, setApiKey] = useState('');

  const sendChat = async (userMessage: string) => {
    if (!userMessage.trim()) return;

    // Add user message to messages
    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setInputValue('');
    setLoading(true);
    setError(null);

    // Prepare chat request
    const chatRequest: ChatRequest = {
      userMessage: userMessage,
      model: "gpt-4.1-mini",
      apiKey: apiKey
    };

    try {
      let assistantMessage = "";
      
      // Add empty assistant message that will be updated with streaming content
      setMessages(prev => [...prev, { role: 'assistant', content: "" }]);
      
      const fullText = await processStreamingChat(chatRequest, (chunk: string) => {
        assistantMessage += chunk;
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: assistantMessage };
          return updated;
        });
      });
      
      setLoading(false);
      return fullText;
    } catch (err) {
      // Remove the empty assistant message on error
      setMessages(prev => prev.slice(0, -1));
      
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
    setApiKey,
    sendChat 
  };
}
