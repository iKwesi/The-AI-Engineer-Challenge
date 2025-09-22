"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { getDocumentList, exitDocumentMode, getConversationModeStatus } from '@/services/documentService';

export interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  chunks: number;
  uploaded_at: string;
}

export interface DocumentContextType {
  documents: Document[];
  isDocumentMode: boolean;
  isLoading: boolean;
  error: string | null;
  refreshDocuments: () => Promise<void>;
  setDocumentMode: (mode: boolean) => void;
  handleDocumentRemoved: () => Promise<void>;
}

const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

export interface DocumentProviderProps {
  children: React.ReactNode;
  apiKey: string;
}

export const DocumentProvider: React.FC<DocumentProviderProps> = ({ children, apiKey }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isDocumentMode, setIsDocumentMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshDocuments = useCallback(async () => {
    if (!apiKey?.trim()) {
      setDocuments([]);
      setIsDocumentMode(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Get both document list and conversation mode status
      const [docResponse, modeResponse] = await Promise.all([
        getDocumentList(apiKey),
        getConversationModeStatus(apiKey)
      ]);

      // Filter out invalid documents and ensure all required properties exist
      const validDocuments = (docResponse.documents || []).filter((doc: any) => 
        doc && 
        typeof doc.id === 'string' && 
        typeof doc.name === 'string' && 
        typeof doc.type === 'string' &&
        typeof doc.size === 'number' &&
        typeof doc.chunks === 'number' &&
        typeof doc.uploaded_at === 'string' &&
        doc.id.trim() !== '' &&
        doc.name.trim() !== ''
      );
      
      console.log('DocumentContext refresh:', {
        validDocumentsCount: validDocuments.length,
        backendMode: modeResponse.mode,
        rawDocuments: docResponse.documents?.length || 0
      });

      // CRITICAL FIX: If no valid documents exist, force exit document mode
      if (validDocuments.length === 0) {
        console.log('No valid documents found, forcing exit from document mode');
        setDocuments([]);
        setIsDocumentMode(false);
        
        // If backend thinks we're in document mode, exit it
        if (modeResponse.mode === 'document') {
          console.log('Backend is in document mode but no documents exist, exiting...');
          try {
            await exitDocumentMode(apiKey);
            console.log('Successfully exited document mode');
          } catch (exitError) {
            console.warn('Failed to exit document mode:', exitError);
          }
        }
      } else {
        // We have valid documents, update state accordingly
        setDocuments(validDocuments);
        setIsDocumentMode(modeResponse.mode === 'document');
        
        // If we have documents but not in document mode, we might want to enter it
        // But let's be conservative and only set the state based on backend response
        console.log(`Found ${validDocuments.length} valid documents, mode: ${modeResponse.mode}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh documents';
      setError(errorMessage);
      console.error('Error refreshing documents:', err);
      
      // On error, assume no documents and general mode
      setDocuments([]);
      setIsDocumentMode(false);
    } finally {
      setIsLoading(false);
    }
  }, [apiKey]);

  const setDocumentMode = useCallback((mode: boolean) => {
    setIsDocumentMode(mode);
  }, []);

  const handleDocumentRemoved = useCallback(async () => {
    // Refresh documents to get current state
    await refreshDocuments();
    
    // Check if we need to exit document mode after refresh
    // Use a small delay to ensure the refresh has completed
    setTimeout(async () => {
      try {
        // Get fresh document list and conversation status
        const [docResponse, modeResponse] = await Promise.all([
          getDocumentList(apiKey),
          getConversationModeStatus(apiKey)
        ]);

        const validDocuments = (docResponse.documents || []).filter((doc: any) => 
          doc && 
          typeof doc.id === 'string' && 
          typeof doc.name === 'string' && 
          typeof doc.type === 'string' &&
          typeof doc.size === 'number' &&
          typeof doc.chunks === 'number' &&
          typeof doc.uploaded_at === 'string' &&
          doc.id.trim() !== '' &&
          doc.name.trim() !== ''
        );

        // If no valid documents remain but we're still in document mode, exit it
        if (validDocuments.length === 0 && modeResponse.mode === 'document' && apiKey?.trim()) {
          console.log('No documents remaining, exiting document mode');
          await exitDocumentMode(apiKey);
          setIsDocumentMode(false);
          setDocuments([]);
          console.log('Successfully exited document mode after document removal');
        } else {
          // Update state with current documents
          setDocuments(validDocuments);
          setIsDocumentMode(modeResponse.mode === 'document');
        }
      } catch (error) {
        console.warn('Failed to handle document removal properly:', error);
        // On error, assume no documents and general mode
        setDocuments([]);
        setIsDocumentMode(false);
      }
    }, 100);
  }, [apiKey]);

  // Initial load and refresh when apiKey changes
  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  const value: DocumentContextType = {
    documents,
    isDocumentMode,
    isLoading,
    error,
    refreshDocuments,
    setDocumentMode,
    handleDocumentRemoved
  };

  return (
    <DocumentContext.Provider value={value}>
      {children}
    </DocumentContext.Provider>
  );
};

export const useDocumentContext = (): DocumentContextType => {
  const context = useContext(DocumentContext);
  if (context === undefined) {
    throw new Error('useDocumentContext must be used within a DocumentProvider');
  }
  return context;
};
