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
  isDocumentMode: boolean; // Keep internal name for compatibility
  isLoading: boolean;
  error: string | null;
  refreshDocuments: () => Promise<void>;
  setDocumentMode: (mode: boolean) => void; // Keep internal name for compatibility
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
      const validDocuments = (docResponse.documents || []).filter((doc: unknown) => {
        if (!doc || typeof doc !== 'object') return false;
        
        const docObj = doc as Record<string, unknown>;
        
        // Log the document structure for debugging
        console.log('Document validation check:', docObj);
        
        // Check for the actual backend field names
        const hasId = (docObj.document_id || docObj.id) && typeof (docObj.document_id || docObj.id) === 'string' && String(docObj.document_id || docObj.id).trim() !== '';
        const hasName = (docObj.filename || docObj.name) && typeof (docObj.filename || docObj.name) === 'string' && String(docObj.filename || docObj.name).trim() !== '';
        
        // More flexible validation for other fields
        const hasValidType = (docObj.document_type || docObj.type) !== undefined;
        const hasValidChunks = (docObj.chunk_count || docObj.chunks) !== undefined && !isNaN(Number(docObj.chunk_count || docObj.chunks));
        
        const isValid = hasId && hasName && hasValidType && hasValidChunks;
        
        if (!isValid) {
          console.log('Document failed validation:', {
            hasId,
            hasName,
            hasValidType,
            hasValidChunks,
            doc: docObj
          });
        }
        
        return isValid;
      }).map((doc: unknown) => {
        const docObj = doc as Record<string, unknown>;
        const processingMetadata = docObj.processing_metadata as Record<string, unknown> | undefined;
        
        return {
          // Normalize the document structure to match frontend expectations
          id: String(docObj.document_id || docObj.id),
          name: String(docObj.filename || docObj.name),
          type: String(docObj.document_type || docObj.type || 'unknown'),
          size: Number(docObj.file_size || docObj.size || docObj.word_count || 0), // Prefer actual file size, fallback to word count
          chunks: Number(docObj.chunk_count || docObj.chunks || 0),
          uploaded_at: String(processingMetadata?.processing_time || docObj.uploaded_at || new Date().toISOString())
        };
      });
      
      console.log('DocumentContext refresh:', {
        validDocumentsCount: validDocuments.length,
        backendMode: modeResponse.mode,
        rawDocuments: docResponse.documents?.length || 0,
        rawDocumentSample: docResponse.documents?.[0] || null
      });

      // Update documents state first
      setDocuments(validDocuments);

      // Simple mode logic: if we have documents, we're in RAG mode
      // If no documents, we're in general mode
      const shouldBeInRAGMode = validDocuments.length > 0;
      const currentBackendMode = modeResponse.mode === 'document';

      if (shouldBeInRAGMode && !currentBackendMode) {
        // We have documents but backend is in general mode - enter RAG mode
        console.log('Documents found, entering RAG mode');
        try {
          await enterDocumentMode(apiKey);
          setIsDocumentMode(true);
          console.log('Successfully entered RAG mode');
        } catch (error) {
          console.warn('Failed to enter RAG mode:', error);
          // Still set frontend to RAG mode since we have documents
          setIsDocumentMode(true);
        }
      } else if (!shouldBeInRAGMode && currentBackendMode) {
        // No documents but backend is in document mode - exit RAG mode
        console.log('No documents found, exiting RAG mode');
        try {
          await exitDocumentMode(apiKey);
          setIsDocumentMode(false);
          console.log('Successfully exited RAG mode');
        } catch (error) {
          console.warn('Failed to exit RAG mode:', error);
          // Still set frontend to general mode since we have no documents
          setIsDocumentMode(false);
        }
      } else {
        // Backend and frontend are in sync
        setIsDocumentMode(shouldBeInRAGMode);
        console.log(`Mode synchronized: ${shouldBeInRAGMode ? 'RAG' : 'general'} mode`);
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
