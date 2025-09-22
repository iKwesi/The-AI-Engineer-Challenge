"use client";

import React, { useState, useCallback } from 'react';
import { Upload, FileText, Youtube, X, Settings, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { cn } from '@/lib/utils';
import FileUpload from './FileUpload';
import useDocumentUpload from '@/hooks/useDocumentUpload';
import { hasYouTubeUrls, detectYouTubeUrls } from '@/services/documentService';
import type { DocumentUploadResponse, YouTubeProcessResponse } from '@/services/documentService';

export interface DocumentManagerProps {
  apiKey: string;
  onDocumentModeEntered?: () => void;
  onError?: (error: string) => void;
  className?: string;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({
  apiKey,
  onDocumentModeEntered,
  onError,
  className
}) => {
  const [activeTab, setActiveTab] = useState<'files' | 'youtube'>('files');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [uploadMode, setUploadMode] = useState<'single' | 'multiple'>('single');
  const [showUploadSuccess, setShowUploadSuccess] = useState(false);
  const [showYouTubeSuccess, setShowYouTubeSuccess] = useState(false);
  const [lastUploadResponse, setLastUploadResponse] = useState<DocumentUploadResponse | null>(null);
  const [lastYouTubeResponse, setLastYouTubeResponse] = useState<YouTubeProcessResponse | null>(null);

  const handleUploadComplete = useCallback((response: DocumentUploadResponse) => {
    setLastUploadResponse(response);
    setShowUploadSuccess(true);
    
    if (response.entered_document_mode) {
      onDocumentModeEntered?.();
    }

    // Auto-hide success message after 5 seconds
    setTimeout(() => {
      setShowUploadSuccess(false);
    }, 5000);
  }, [onDocumentModeEntered]);

  const handleYouTubeComplete = useCallback((response: YouTubeProcessResponse) => {
    setLastYouTubeResponse(response);
    setShowYouTubeSuccess(true);
    setYoutubeUrl(''); // Clear the input
    
    if (response.entered_document_mode) {
      onDocumentModeEntered?.();
    }

    // Auto-hide success message after 5 seconds
    setTimeout(() => {
      setShowYouTubeSuccess(false);
    }, 5000);
  }, [onDocumentModeEntered]);

  const handleError = useCallback((error: string) => {
    onError?.(error);
  }, [onError]);

  const {
    uploadedFiles,
    isUploading,
    uploadError,
    addFiles,
    removeFile,
    clearFiles,
    uploadFiles,
    processYouTube,
    getUploadStats,
    canUpload
  } = useDocumentUpload({
    apiKey,
    onUploadComplete: handleUploadComplete,
    onYouTubeProcessComplete: handleYouTubeComplete,
    onError: handleError
  });

  // Auto-upload files when they're added
  const handleFilesSelected = useCallback(async (files: File[]) => {
    addFiles(files);
    // Automatically start upload after files are added to state
    // Use a longer delay to ensure state is updated and canUpload is true
    setTimeout(() => {
      const stats = getUploadStats();
      if (stats.pending > 0 && !isUploading && apiKey?.trim()) {
        uploadFiles();
      }
    }, 200); // Increased delay to ensure state is properly updated
  }, [addFiles, uploadFiles, getUploadStats, isUploading, apiKey]);

  const handleYouTubeSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!youtubeUrl.trim()) {
      handleError("Please enter a YouTube URL");
      return;
    }

    const detectedUrls = detectYouTubeUrls(youtubeUrl);
    if (detectedUrls.length === 0) {
      handleError("Please enter a valid YouTube URL");
      return;
    }

    try {
      await processYouTube(detectedUrls[0]);
    } catch (error) {
      // Error is already handled by the hook
    }
  }, [youtubeUrl, processYouTube, handleError]);

  const stats = getUploadStats();

  return (
    <div className={cn("space-y-6", className)}>
      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-muted p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('files')}
          className={cn(
            "flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
            activeTab === 'files'
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <FileText className="w-4 h-4" />
          Documents
        </button>
        <button
          onClick={() => setActiveTab('youtube')}
          className={cn(
            "flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
            activeTab === 'youtube'
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Youtube className="w-4 h-4" />
          YouTube
        </button>
      </div>

      {/* Success Messages */}
      {showUploadSuccess && lastUploadResponse && (
        <Alert className="border-green-200 bg-green-50 text-green-800">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertTitle>Upload Successful!</AlertTitle>
          <AlertDescription>
            {lastUploadResponse.status === 'success' 
              ? `Successfully uploaded ${lastUploadResponse.successful_files} file(s).`
              : `Uploaded ${lastUploadResponse.successful_files} of ${lastUploadResponse.total_files} files.`
            }
            {lastUploadResponse.entered_document_mode && " Document mode activated."}
            <Button
              variant="ghost"
              size="sm"
              className="ml-2 h-auto p-0 text-green-700 hover:text-green-900"
              onClick={() => setShowUploadSuccess(false)}
            >
              <X className="w-3 h-3" />
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {showYouTubeSuccess && lastYouTubeResponse && (
        <Alert className="border-green-200 bg-green-50 text-green-800">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertTitle>YouTube Processing Successful!</AlertTitle>
          <AlertDescription>
            {lastYouTubeResponse.video_title && `"${lastYouTubeResponse.video_title}" `}
            processed successfully.
            {lastYouTubeResponse.chunks_processed && ` ${lastYouTubeResponse.chunks_processed} chunks created.`}
            {lastYouTubeResponse.entered_document_mode && " Document mode activated."}
            <Button
              variant="ghost"
              size="sm"
              className="ml-2 h-auto p-0 text-green-700 hover:text-green-900"
              onClick={() => setShowYouTubeSuccess(false)}
            >
              <X className="w-3 h-3" />
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* File Upload Tab */}
      {activeTab === 'files' && (
        <Card padding="none">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Document Upload
                </CardTitle>
                <CardDescription>
                  Drag & drop or click to upload documents - they'll be processed automatically
                </CardDescription>
              </div>
              
              {/* Upload Mode Toggle */}
              <div className="flex items-center gap-2">
                <Label htmlFor="upload-mode" className="text-sm">Mode:</Label>
                <select
                  id="upload-mode"
                  value={uploadMode}
                  onChange={(e) => setUploadMode(e.target.value as 'single' | 'multiple')}
                  className="text-sm border rounded px-2 py-1 bg-background"
                  disabled={isUploading || stats.total > 0}
                >
                  <option value="single">Single File</option>
                  <option value="multiple">Multiple Files</option>
                </select>
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* File Upload Component */}
            <FileUpload
              onFilesSelected={handleFilesSelected}
              onFileRemove={removeFile}
              uploadedFiles={uploadedFiles}
              multiple={uploadMode === 'multiple'}
              maxFiles={10}
              maxSizeBytes={50 * 1024 * 1024} // 50MB
              disabled={isUploading}
            />

            {/* Upload Error */}
            {uploadError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{uploadError}</AlertDescription>
              </Alert>
            )}

            {/* Upload Stats */}
            {stats.total > 0 && (
              <div className="text-sm text-muted-foreground space-y-1">
                <p>
                  Files: {stats.total} total
                  {stats.success > 0 && `, ${stats.success} uploaded`}
                  {stats.error > 0 && `, ${stats.error} failed`}
                  {stats.pending > 0 && `, ${stats.pending} pending`}
                </p>
                {stats.totalSize > 0 && (
                  <p>Total size: {(stats.totalSize / (1024 * 1024)).toFixed(2)} MB</p>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button
                onClick={uploadFiles}
                disabled={!canUpload}
                className="flex items-center gap-2"
              >
                {isUploading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload {uploadMode === 'multiple' ? 'Files' : 'File'}
                  </>
                )}
              </Button>

              {stats.total > 0 && (
                <Button
                  variant="outline"
                  onClick={clearFiles}
                  disabled={isUploading}
                >
                  Clear All
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* YouTube Tab */}
      {activeTab === 'youtube' && (
        <Card padding="none">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Youtube className="w-5 h-5" />
              YouTube Video Processing
            </CardTitle>
            <CardDescription>
              Process YouTube video transcripts to chat with video content
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleYouTubeSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="youtube-url">YouTube URL</Label>
                <Input
                  id="youtube-url"
                  type="url"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  disabled={isUploading}
                />
                <p className="text-xs text-muted-foreground">
                  Supports youtube.com and youtu.be URLs
                </p>
              </div>

              <Button
                type="submit"
                disabled={!youtubeUrl.trim() || isUploading || !hasYouTubeUrls(youtubeUrl)}
                className="flex items-center gap-2"
              >
                {isUploading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Youtube className="w-4 h-4" />
                    Process Video
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Help Text */}
      <div className="text-xs text-muted-foreground space-y-1">
        <p>
          <strong>Supported formats:</strong> PDF, TXT, DOCX, DOC, XLSX, XLS, CSV
        </p>
        <p>
          <strong>File limits:</strong> {uploadMode === 'single' ? '50MB per file' : '50MB total for all files'}
        </p>
        <p>
          <strong>Document mode:</strong> Automatically activated after successful upload
        </p>
      </div>
    </div>
  );
};

export default DocumentManager;
