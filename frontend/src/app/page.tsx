"use client";

import React, { useCallback } from 'react';
import SidebarLayout from '@/components/layout/SidebarLayout';
import SimpleChatInterface from '@/components/features/chat/SimpleChatInterface';
import { useChat } from '@/hooks/useChat';
import { DocumentProvider } from '@/contexts/DocumentContext';

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
    pendingFallback,
    handleFallbackConfirmation,
  } = useChat();

  // Handle document mode entered
  const handleDocumentModeEntered = useCallback(() => {
    // Optionally refresh conversation mode status or show notification
    console.log('Document mode entered');
  }, []);

  // Handle upload error
  const handleUploadError = useCallback((error: string) => {
    console.error('Upload error:', error);
  }, []);

  return (
    <main className="h-screen">
      <DocumentProvider apiKey={apiKey}>
        <SidebarLayout
          apiKey={apiKey}
          onDocumentModeEntered={handleDocumentModeEntered}
          onError={handleUploadError}
        >
          <SimpleChatInterface
            messages={messages}
            loading={loading}
            error={error}
            inputValue={inputValue}
            setInputValue={setInputValue}
            handleSubmit={handleSubmit}
            apiKey={apiKey}
            setApiKey={setApiKey}
            pendingFallback={pendingFallback}
            handleFallbackConfirmation={handleFallbackConfirmation}
          />
        </SidebarLayout>
      </DocumentProvider>
    </main>
  );
}
