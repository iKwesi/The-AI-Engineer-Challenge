"use client";

import React, { useState, useCallback } from 'react';
import { FileText, Trash2, AlertCircle, Loader } from 'lucide-react';
import { Button } from "@/components/ui/Button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { cn } from '@/lib/utils';
import { useDocumentContext } from '@/contexts/DocumentContext';
import { removeDocument } from '@/services/documentService';

export interface DocumentListProps {
  apiKey: string;
  onError?: (error: string) => void;
  className?: string;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  apiKey,
  onError,
  className
}) => {
  const { documents, isLoading, error, handleDocumentRemoved } = useDocumentContext();
  const [removingDocuments, setRemovingDocuments] = useState<Set<string>>(new Set());
  const [removeError, setRemoveError] = useState<string | null>(null);

  const handleRemoveDocument = useCallback(async (documentId: string, documentName: string) => {
    if (!apiKey?.trim()) {
      const error = "API key is required to remove documents";
      setRemoveError(error);
      onError?.(error);
      return;
    }

    // Confirm removal
    if (!window.confirm(`Are you sure you want to remove "${documentName}"? This action cannot be undone.`)) {
      return;
    }

    setRemovingDocuments(prev => new Set(prev).add(documentId));
    setRemoveError(null);

    try {
      await removeDocument(documentId, apiKey);
      
      // Refresh documents and handle removal side effects
      await handleDocumentRemoved();
      
      console.log(`Document "${documentName}" removed successfully`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to remove document';
      setRemoveError(errorMessage);
      onError?.(errorMessage);
      console.error('Error removing document:', error);
    } finally {
      setRemovingDocuments(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });
    }
  }, [apiKey, onError, handleDocumentRemoved]);

  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  const formatUploadDate = useCallback((dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return 'Unknown date';
    }
  }, []);

  if (isLoading) {
    return (
      <Card className={cn("", className)}>
        <CardContent className="flex items-center justify-center py-8">
          <Loader className="w-6 h-6 animate-spin mr-2" />
          <span>Loading documents...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn("", className)}>
        <CardContent className="py-4">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error Loading Documents</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Uploaded Documents
          {documents.length > 0 && (
            <span className="text-sm font-normal text-muted-foreground">
              ({documents.length} document{documents.length !== 1 ? 's' : ''})
            </span>
          )}
        </CardTitle>
        <CardDescription>
          Manage your uploaded documents and remove them if needed
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Remove Error */}
        {removeError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{removeError}</AlertDescription>
          </Alert>
        )}

        {/* Document List */}
        {documents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">No documents uploaded</p>
            <p className="text-sm">Upload documents to start chatting with your content</p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((document) => {
              const isRemoving = removingDocuments.has(document.id);
              
              return (
                <div
                  key={document.id}
                  className={cn(
                    "flex items-center justify-between p-4 border rounded-lg transition-colors",
                    isRemoving ? "bg-muted opacity-50" : "bg-background hover:bg-muted/50"
                  )}
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="flex-shrink-0">
                      <FileText className="w-5 h-5 text-blue-600" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-sm truncate" title={document.name}>
                          {document.name}
                        </h4>
                        <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                          {document.type.toUpperCase()}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>{formatFileSize(document.size)}</span>
                        <span>{document.chunks} chunk{document.chunks !== 1 ? 's' : ''}</span>
                        <span>Uploaded {formatUploadDate(document.uploaded_at)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex-shrink-0 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveDocument(document.id, document.name)}
                      disabled={isRemoving}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      {isRemoving ? (
                        <Loader className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Summary */}
        {documents.length > 0 && (
          <div className="pt-4 border-t">
            <div className="text-xs text-muted-foreground space-y-1">
              <p>
                <strong>Total documents:</strong> {documents.length}
              </p>
              <p>
                <strong>Total chunks:</strong> {documents.reduce((sum, doc) => sum + doc.chunks, 0)}
              </p>
              <p>
                <strong>Total size:</strong> {formatFileSize(documents.reduce((sum, doc) => sum + doc.size, 0))}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DocumentList;
