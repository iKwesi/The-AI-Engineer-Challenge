"use client";

import React, { useState } from "react";

interface ChatFormProps {
  onSubmit: (data: {
    developerMessage: string;
    userMessage: string;
    model: string;
    apiKey: string;
  }) => void;
  loading: boolean;
}

export const ChatForm: React.FC<ChatFormProps> = ({ onSubmit, loading }) => {
  const [developerMessage, setDeveloperMessage] = useState("");
  const [userMessage, setUserMessage] = useState("");
  const [model, setModel] = useState("gpt-4.1-mini");
  const [apiKey, setApiKey] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ developerMessage, userMessage, model, apiKey });
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-xl bg-white dark:bg-gray-900 rounded-lg shadow-md p-6 flex flex-col gap-4">
      <label className="flex flex-col gap-1">
        <span className="font-semibold">Developer Message</span>
        <textarea
          className="border rounded p-2 min-h-[48px] resize-y bg-gray-50 dark:bg-gray-800"
          value={developerMessage}
          onChange={e => setDeveloperMessage(e.target.value)}
          required
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="font-semibold">User Message</span>
        <textarea
          className="border rounded p-2 min-h-[48px] resize-y bg-gray-50 dark:bg-gray-800"
          value={userMessage}
          onChange={e => setUserMessage(e.target.value)}
          required
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="font-semibold">Model</span>
        <input
          className="border rounded p-2 bg-gray-50 dark:bg-gray-800"
          value={model}
          onChange={e => setModel(e.target.value)}
          placeholder="gpt-4.1-mini"
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="font-semibold">OpenAI API Key</span>
        <input
          className="border rounded p-2 bg-gray-50 dark:bg-gray-800"
          type="password"
          value={apiKey}
          onChange={e => setApiKey(e.target.value)}
          required
        />
      </label>
      <button
        type="submit"
        className="bg-blue-600 text-white font-semibold py-2 px-4 rounded hover:bg-blue-700 transition disabled:opacity-60"
        disabled={loading}
      >
        {loading ? "Sending..." : "Send"}
      </button>
    </form>
  );
}; 