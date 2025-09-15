"use client";

import React from 'react';
import ProfessionalChatInterface from '@/components/features/chat/ProfessionalChatInterface';
import { useChat } from '@/hooks/useChat';

export default function Home() {
  const {
    messages,
    loading,
    error,
    inputValue,
    setInputValue,
    handleSubmit,
    apiKey,
    setApiKey,
  } = useChat();

  return (
    <main>
      <ProfessionalChatInterface
        messages={messages}
        loading={loading}
        error={error}
        inputValue={inputValue}
        setInputValue={setInputValue}
        handleSubmit={handleSubmit}
        apiKey={apiKey}
        setApiKey={setApiKey}
      />
    </main>
  );
}
