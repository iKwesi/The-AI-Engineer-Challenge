"use client";

import React, { useCallback } from 'react';
import SidebarLayout from '@/components/layout/SidebarLayout';
import SimpleChatInterface from '@/components/features/chat/SimpleChatInterface';
import RAGChatInterface from '@/components/features/chat/RAGChatInterface';
import { useChat } from '@/hooks/useChat';
import { DocumentProvider, useDocumentContext } from '@/contexts/DocumentContext';

function ChatInterfaceSelector() {
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

  const { documents, isDocumentMode } = useDocumentContext();

  // Determine which interface to show based on document availability
  const hasDocuments = documents.length > 0;
  const shouldShowRAGInterface = hasDocuments && isDocumentMode;

  console.log('Chat interface selection:', { hasDocuments, isDocumentMode, shouldShowRAGInterface });

  if (shouldShowRAGInterface) {
    return (
      <RAGChatInterface
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
    );
  }

  return (
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
  );
}

export default function Home() {
  const {
    apiKey,
    setApiKey,
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
          <ChatInterfaceSelector />
        </SidebarLayout>
      </DocumentProvider>
    </main>
  );
}
