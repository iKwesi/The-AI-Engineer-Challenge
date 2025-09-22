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

  const { documents, isDocumentMode, refreshDocuments } = useDocumentContext();

  // Determine which interface to show based on document availability
  const hasDocuments = documents.length > 0;
  
  // CRITICAL FIX: Only show RAG interface if we actually have documents
  // If no documents exist, always show SimpleChatInterface regardless of backend mode
  const shouldShowRAGInterface = hasDocuments && isDocumentMode;

  console.log('Chat interface selection:', { 
    hasDocuments, 
    isDocumentMode, 
    shouldShowRAGInterface,
    documentsCount: documents.length,
    documentIds: documents.map(d => d.id)
  });

  // Force refresh documents when apiKey changes to ensure we have current state
  React.useEffect(() => {
    if (apiKey?.trim()) {
      refreshDocuments();
    }
  }, [apiKey, refreshDocuments]);

  // DEFENSIVE: If no documents exist, always show SimpleChatInterface
  if (!hasDocuments) {
    console.log('No documents found, forcing SimpleChatInterface');
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

  // Only show RAG interface if we have documents AND are in document mode
  if (shouldShowRAGInterface) {
    console.log('Documents found and in document mode, showing RAGChatInterface');
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

  // Fallback to SimpleChatInterface
  console.log('Fallback to SimpleChatInterface');
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
