"use client";

import { useState, useCallback } from 'react';
import { 
  uploadSingleDocument, 
  uploadMultipleDocuments, 
  processYouTubeUrl,
  type DocumentUploadResponse,
  type YouTubeProcessResponse 
} from '@/services/documentService';
import type { UploadedFile } from '@/components/features/upload/FileUpload';

export interface UseDocumentUploadOptions {
  apiKey: string;
  onUploadComplete?: (response: DocumentUploadResponse) => void;
  onYouTubeProcessComplete?: (response: YouTubeProcessResponse) => void;
  onError?: (error: string) => void;
}

export function useDocumentUpload({
  apiKey,
  onUploadComplete,
  onYouTubeProcessComplete,
  onError
}: UseDocumentUploadOptions) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Generate unique ID for files
  const generateFileId = useCallback(() => {
    return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Add files to the upload queue
  const addFiles = useCallback((files: File[]) => {
    const newUploadedFiles: UploadedFile[] = files.map(file => ({
      file,
      id: generateFileId(),
      status: 'pending'
    }));

    setUploadedFiles(prev => [...prev, ...newUploadedFiles]);
    setUploadError(null);
  }, [generateFileId]);

  // Remove a file from the upload queue
  const removeFile = useCallback((fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  }, []);

  // Clear all files
  const clearFiles = useCallback(() => {
    setUploadedFiles([]);
    setUploadError(null);
  }, []);

  // Update file status
  const updateFileStatus = useCallback((
    fileId: string, 
    status: UploadedFile['status'], 
    progress?: number, 
    error?: string,
    chunks?: number
  ) => {
    setUploadedFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, status, progress, error, chunks }
        : file
    ));
  }, []);

  // Upload files (single or multiple)
  const uploadFiles = useCallback(async () => {
    if (!apiKey?.trim()) {
      const error = "API key is required for upload";
      setUploadError(error);
      onError?.(error);
      return;
    }

    const pendingFiles = uploadedFiles.filter(f => f.status === 'pending');
    if (pendingFiles.length === 0) {
      const error = "No files to upload";
      setUploadError(error);
      onError?.(error);
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      // Mark all pending files as uploading
      pendingFiles.forEach(file => {
        updateFileStatus(file.id, 'uploading', 0);
      });

      let response: DocumentUploadResponse;

      if (pendingFiles.length === 1) {
        // Single file upload
        const file = pendingFiles[0];
        updateFileStatus(file.id, 'uploading', 50);
        response = await uploadSingleDocument(file.file, apiKey);
      } else {
        // Multiple file upload (batch)
        const files = pendingFiles.map(f => f.file);
        
        // Update progress for all files
        pendingFiles.forEach(file => {
          updateFileStatus(file.id, 'uploading', 50);
        });

        response = await uploadMultipleDocuments(files, apiKey);
      }

      // Update file statuses based on response
      response.results.forEach(result => {
        const uploadedFile = pendingFiles.find(f => f.file.name === result.filename);
        if (uploadedFile) {
          updateFileStatus(
            uploadedFile.id,
            result.status === 'success' ? 'success' : 'error',
            100,
            result.status === 'failed' ? result.message : undefined,
            result.chunks_processed
          );
        }
      });

      onUploadComplete?.(response);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadError(errorMessage);
      
      // Mark all uploading files as error
      pendingFiles.forEach(file => {
        updateFileStatus(file.id, 'error', 0, errorMessage);
      });

      onError?.(errorMessage);
    } finally {
      setIsUploading(false);
    }
  }, [apiKey, uploadedFiles, updateFileStatus, onUploadComplete, onError]);

  // Process YouTube URL
  const processYouTube = useCallback(async (url: string) => {
    if (!apiKey?.trim()) {
      const error = "API key is required for YouTube processing";
      setUploadError(error);
      onError?.(error);
      return;
    }

    if (!url?.trim()) {
      const error = "YouTube URL is required";
      setUploadError(error);
      onError?.(error);
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      const response = await processYouTubeUrl(url, apiKey);
      onYouTubeProcessComplete?.(response);
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'YouTube processing failed';
      setUploadError(errorMessage);
      onError?.(errorMessage);
      throw error;
    } finally {
      setIsUploading(false);
    }
  }, [apiKey, onYouTubeProcessComplete, onError]);

  // Get upload statistics
  const getUploadStats = useCallback(() => {
    const total = uploadedFiles.length;
    const pending = uploadedFiles.filter(f => f.status === 'pending').length;
    const uploading = uploadedFiles.filter(f => f.status === 'uploading').length;
    const success = uploadedFiles.filter(f => f.status === 'success').length;
    const error = uploadedFiles.filter(f => f.status === 'error').length;
    const totalSize = uploadedFiles.reduce((sum, f) => sum + f.file.size, 0);

    return {
      total,
      pending,
      uploading,
      success,
      error,
      totalSize,
      isComplete: pending === 0 && uploading === 0,
      hasErrors: error > 0,
      hasSuccess: success > 0
    };
  }, [uploadedFiles]);

  // Check if ready to upload
  const canUpload = useCallback(() => {
    const stats = getUploadStats();
    return stats.pending > 0 && !isUploading && apiKey?.trim();
  }, [getUploadStats, isUploading, apiKey]);

  return {
    // State
    uploadedFiles,
    isUploading,
    uploadError,
    
    // Actions
    addFiles,
    removeFile,
    clearFiles,
    uploadFiles,
    processYouTube,
    
    // Computed
    getUploadStats,
    canUpload: canUpload(),
    
    // Utilities
    updateFileStatus
  };
}

export default useDocumentUpload;
