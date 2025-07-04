"use client";

import { useState } from "react";

interface ChatRequest {
  developerMessage: string;
  userMessage: string;
  model: string;
  apiKey: string;
}

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export function useChat() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendChat = async (data: ChatRequest) => {
    setMessage("");
    setError(null);
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          developer_message: data.developerMessage,
          user_message: data.userMessage,
          model: data.model,
          api_key: data.apiKey,
        }),
      });
      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let fullText = "";
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value);
          fullText += chunk;
          setMessage(prev => prev + chunk);
        }
      }
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