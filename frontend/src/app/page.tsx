"use client";

import React, { useCallback } from 'react';
import SidebarLayout from '@/components/layout/SidebarLayout';
import SimpleChatInterface from '@/components/features/chat/SimpleChatInterface';
import RAGChatInterface from '@/components/features/chat/RAGChatInterface';
import { useChat } from '@/hooks/useChat';
import { DocumentProvider, useDocumentContext } from '@/contexts/DocumentContext';

function ChatInterfaceSelector({ 
  apiKey, 
  setApiKey, 
  messages, 
  loading, 
  error, 
  inputValue, 
  setInputValue, 
  handleSubmit, 
  pendingFallback, 
  handleFallbackConfirmation 
}: { 
  apiKey: string; 
  setApiKey: (key: string) => void;
  messages: any[];
  loading: boolean;
  error: string | null;
  inputValue: string;
  setInputValue: (value: string) => void;
  handleSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  pendingFallback: any;
  handleFallbackConfirmation: any;
}) {
  const { documents, isDocumentMode, refreshDocuments } = useDocumentContext();

  // Simple logic: if we have documents and are in document mode, show RAG interface
  // Otherwise, show simple chat interface
  const hasDocuments = documents.length > 0;
  const shouldShowRAGInterface = hasDocuments && isDocumentMode;

  console.log('Chat interface selection:', { 
    hasDocuments, 
    isDocumentMode, 
    shouldShowRAGInterface,
    documentsCount: documents.length
  });

  // Refresh documents when apiKey changes
  React.useEffect(() => {
    if (apiKey?.trim()) {
      refreshDocuments();
    }
  }, [apiKey, refreshDocuments]);

  if (shouldShowRAGInterface) {
    console.log('Showing RAG interface - documents available and in document mode');
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

  console.log('Showing simple chat interface - no documents or in general mode');
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
    <main className="h-full">
      <DocumentProvider apiKey={apiKey}>
        <SidebarLayout
          apiKey={apiKey}
          onDocumentModeEntered={handleDocumentModeEntered}
          onError={handleUploadError}
        >
          <ChatInterfaceSelector 
            apiKey={apiKey} 
            setApiKey={setApiKey}
            messages={messages}
            loading={loading}
            error={error}
            inputValue={inputValue}
            setInputValue={setInputValue}
            handleSubmit={handleSubmit}
            pendingFallback={pendingFallback}
            handleFallbackConfirmation={handleFallbackConfirmation}
          />
        </SidebarLayout>
      </DocumentProvider>
    </main>
  );
}
