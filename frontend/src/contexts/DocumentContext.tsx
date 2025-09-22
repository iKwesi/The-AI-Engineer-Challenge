"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { getDocumentList, exitDocumentMode, getConversationModeStatus, enterDocumentMode } from '@/services/documentService';

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
      // More lenient validation to handle different backend response formats
      const validDocuments = (docResponse.documents || []).filter((doc: any) => {
        if (!doc) return false;
        
        // Log the document structure for debugging
        console.log('Document validation check:', doc);
        
        // Basic validation - only require essential fields
        const hasId = doc.id && typeof doc.id === 'string' && doc.id.trim() !== '';
        const hasName = doc.name && typeof doc.name === 'string' && doc.name.trim() !== '';
        
        // More flexible validation for other fields
        const hasValidType = doc.type !== undefined;
        const hasValidSize = doc.size !== undefined && !isNaN(Number(doc.size));
        const hasValidChunks = doc.chunks !== undefined && !isNaN(Number(doc.chunks));
        const hasValidDate = doc.uploaded_at !== undefined;
        
        const isValid = hasId && hasName && hasValidType && hasValidSize && hasValidChunks && hasValidDate;
        
        if (!isValid) {
          console.log('Document failed validation:', {
            hasId,
            hasName,
            hasValidType,
            hasValidSize,
            hasValidChunks,
            hasValidDate,
            doc
          });
        }
        
        return isValid;
      }).map((doc: any) => ({
        // Normalize the document structure
        id: String(doc.id),
        name: String(doc.name),
        type: String(doc.type || 'unknown'),
        size: Number(doc.size) || 0,
        chunks: Number(doc.chunks) || 0,
        uploaded_at: String(doc.uploaded_at)
      }));
      
      console.log('DocumentContext refresh:', {
        validDocumentsCount: validDocuments.length,
        backendMode: modeResponse.mode,
        rawDocuments: docResponse.documents?.length || 0,
        rawDocumentSample: docResponse.documents?.[0] || null
      });

      // Update documents state first
      setDocuments(validDocuments);

      // Simple mode logic: if we have documents, we're in document mode
      // If no documents, we're in general mode
      const shouldBeInDocumentMode = validDocuments.length > 0;
      const currentBackendMode = modeResponse.mode === 'document';

      if (shouldBeInDocumentMode && !currentBackendMode) {
        // We have documents but backend is in general mode - enter document mode
        console.log('Documents found, entering document mode');
        try {
          await enterDocumentMode(apiKey);
          setIsDocumentMode(true);
          console.log('Successfully entered document mode');
        } catch (error) {
          console.warn('Failed to enter document mode:', error);
          // Still set frontend to document mode since we have documents
          setIsDocumentMode(true);
        }
      } else if (!shouldBeInDocumentMode && currentBackendMode) {
        // No documents but backend is in document mode - exit document mode
        console.log('No documents found, exiting document mode');
        try {
          await exitDocumentMode(apiKey);
          setIsDocumentMode(false);
          console.log('Successfully exited document mode');
        } catch (error) {
          console.warn('Failed to exit document mode:', error);
          // Still set frontend to general mode since we have no documents
          setIsDocumentMode(false);
        }
      } else {
        // Backend and frontend are in sync
        setIsDocumentMode(shouldBeInDocumentMode);
        console.log(`Mode synchronized: ${shouldBeInDocumentMode ? 'document' : 'general'} mode`);
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
    // Simply refresh documents - the refresh logic will handle mode switching
    await refreshDocuments();
  }, [refreshDocuments]);

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
