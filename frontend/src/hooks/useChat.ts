"use client";

import { useState } from "react";
import { processStreamingChat, type ChatRequest } from "../services/chatService";

export function useChat() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendChat = async (data: ChatRequest) => {
    setMessage("");
    setError(null);
    setLoading(true);
    
    try {
      const fullText = await processStreamingChat(data, (chunk: string) => {
        setMessage(prev => prev + chunk);
      });
      setLoading(false);
      return fullText;
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unknown error");
      }
      setLoading(false);
    }
  };

  return { message, loading, error, sendChat };
}
