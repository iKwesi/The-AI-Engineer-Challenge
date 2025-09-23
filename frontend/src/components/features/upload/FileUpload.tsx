"use client";

import React, { useCallback, useState } from 'react';
import { Upload, File, X, AlertCircle, CheckCircle } from 'lucide-react';
import { Button } from "@/components/ui/Button";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { cn } from '@/lib/utils';

export interface UploadedFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress?: number;
  error?: string;
  chunks?: number;
}

export interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  onFileRemove: (fileId: string) => void;
  uploadedFiles: UploadedFile[];
  multiple?: boolean;
  maxFiles?: number;
  maxSizeBytes?: number;
  acceptedTypes?: string[];
  disabled?: boolean;
  className?: string;
}

const SUPPORTED_TYPES = [
  'application/pdf',
  'text/plain',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'text/csv'
];

const TYPE_EXTENSIONS = {
  'application/pdf': '.pdf',
  'text/plain': '.txt',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'application/msword': '.doc',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
  'application/vnd.ms-excel': '.xls',
  'text/csv': '.csv'
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const getFileIcon = (type: string) => {
  if (type.includes('pdf')) return '📄';
  if (type.includes('word') || type.includes('document')) return '📝';
  if (type.includes('sheet') || type.includes('excel') || type.includes('csv')) return '📊';
  return '📄';
};

export const FileUpload: React.FC<FileUploadProps> = ({
  onFilesSelected,
  onFileRemove,
  uploadedFiles,
  multiple = false,
  maxFiles = 10,
  maxSizeBytes = 50 * 1024 * 1024, // 50MB default
  acceptedTypes = SUPPORTED_TYPES,
  disabled = false,
  className
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateFiles = useCallback((files: File[]): { valid: File[], errors: string[] } => {
    const errors: string[] = [];
    const valid: File[] = [];

    // Check if adding these files would exceed max files
    if (multiple && uploadedFiles.length + files.length > maxFiles) {
      errors.push(`Maximum ${maxFiles} files allowed. Currently have ${uploadedFiles.length} files.`);
      return { valid, errors };
    }

    // For single file mode, only take the first file
    const filesToProcess = multiple ? files : files.slice(0, 1);

    let totalSize = uploadedFiles.reduce((sum, f) => sum + f.file.size, 0);

    for (const file of filesToProcess) {
      // Check file type
      if (!acceptedTypes.includes(file.type)) {
        const supportedExts = acceptedTypes.map(type => TYPE_EXTENSIONS[type as keyof typeof TYPE_EXTENSIONS]).join(', ');
        errors.push(`"${file.name}" is not a supported file type. Supported: ${supportedExts}`);
        continue;
      }

      // Check individual file size (for single uploads)
      if (!multiple && file.size > maxSizeBytes) {
        errors.push(`"${file.name}" is too large. Maximum size: ${formatFileSize(maxSizeBytes)}`);
        continue;
      }

      // Check combined size (for multiple uploads)
      if (multiple && totalSize + file.size > maxSizeBytes) {
        errors.push(`Adding "${file.name}" would exceed the total size limit of ${formatFileSize(maxSizeBytes)}`);
        continue;
      }

      // Check for duplicates
      const isDuplicate = uploadedFiles.some(uf => 
        uf.file.name === file.name && uf.file.size === file.size
      );
      if (isDuplicate) {
        errors.push(`"${file.name}" is already selected`);
        continue;
      }

      valid.push(file);
      totalSize += file.size;
    }

    return { valid, errors };
  }, [acceptedTypes, maxFiles, maxSizeBytes, multiple, uploadedFiles]);

  const handleFileSelection = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);
    const { valid, errors } = validateFiles(fileArray);

    if (errors.length > 0) {
      setValidationError(errors.join(' '));
      return;
    }

    setValidationError(null);
    if (valid.length > 0) {
      onFilesSelected(valid);
    }
  }, [validateFiles, onFilesSelected]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (disabled) return;

    const files = e.dataTransfer.files;
    handleFileSelection(files);
  }, [disabled, handleFileSelection]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelection(e.target.files);
    // Reset input value to allow selecting the same file again
    e.target.value = '';
  }, [handleFileSelection]);

  const totalSize = uploadedFiles.reduce((sum, file) => sum + file.file.size, 0);
  const remainingSize = maxSizeBytes - totalSize;

  return (
    <div className={cn("space-y-4", className)}>
      {/* Upload Area */}
      <div
        className={cn(
          "border-2 border-dashed rounded-lg p-6 text-center transition-colors flex flex-col justify-center",
          isDragOver && !disabled ? "border-primary bg-primary/5" : "border-muted-foreground/25",
          disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:border-primary/50",
          uploadedFiles.length > 0 ? "bg-muted/20" : ""
        )}
        style={{ width: '350px', height: '249.55px' }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => {
          if (!disabled) {
            document.getElementById('file-input')?.click();
          }
        }}
      >
        <input
          id="file-input"
          type="file"
          multiple={multiple}
          accept={acceptedTypes.join(',')}
          onChange={handleInputChange}
          disabled={disabled}
          className="hidden"
        />
        
        <Upload className={cn(
          "w-8 h-8 mx-auto mb-2",
          isDragOver ? "text-primary" : "text-muted-foreground"
        )} />
        
        <p className="text-sm font-medium mb-1">
          {isDragOver ? "Drop files here" : `Drag and drop files here or click to upload`}
        </p>
        
        <p className="text-xs text-muted-foreground">
          {multiple ? `Up to ${maxFiles} files, ` : "Single file, "}
          {multiple ? `${formatFileSize(maxSizeBytes)} total` : `max ${formatFileSize(maxSizeBytes)}`}
        </p>
        
        <p className="text-xs text-muted-foreground mt-1">
          Supported: PDF, TXT, DOCX, DOC, XLSX, XLS, CSV
        </p>
        
        {multiple && totalSize > 0 && (
          <p className="text-xs text-muted-foreground mt-2">
            Used: {formatFileSize(totalSize)} / {formatFileSize(maxSizeBytes)}
            {remainingSize > 0 && ` (${formatFileSize(remainingSize)} remaining)`}
          </p>
        )}
      </div>

      {/* Validation Error */}
      {validationError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{validationError}</AlertDescription>
        </Alert>
      )}

      {/* File List */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">
            {multiple ? `Selected Files (${uploadedFiles.length})` : "Selected File"}
          </h4>
          
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {uploadedFiles.map((uploadedFile) => (
              <div
                key={uploadedFile.id}
                className="flex items-center gap-3 p-3 border rounded-lg bg-card"
              >
                <span className="text-lg">{getFileIcon(uploadedFile.file.type)}</span>
                
                <div className="flex-grow min-w-0">
                  <p className="text-sm font-medium truncate">{uploadedFile.file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatFileSize(uploadedFile.file.size)}
                    {uploadedFile.chunks && ` • ${uploadedFile.chunks} chunks`}
                  </p>
                  
                  {/* Progress bar for uploading files */}
                  {uploadedFile.status === 'uploading' && uploadedFile.progress !== undefined && (
                    <div className="w-full bg-muted rounded-full h-1.5 mt-1">
                      <div 
                        className="bg-primary h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${uploadedFile.progress}%` }}
                      />
                    </div>
                  )}
                  
                  {/* Error message */}
                  {uploadedFile.status === 'error' && uploadedFile.error && (
                    <p className="text-xs text-destructive mt-1">{uploadedFile.error}</p>
                  )}
                </div>
                
                {/* Status Icon */}
                <div className="flex items-center gap-2">
                  {uploadedFile.status === 'success' && (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  )}
                  {uploadedFile.status === 'error' && (
                    <AlertCircle className="w-4 h-4 text-destructive" />
                  )}
                  {uploadedFile.status === 'uploading' && (
                    <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  )}
                  
                  {/* Remove button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="w-6 h-6"
                    onClick={(e) => {
                      e.stopPropagation();
                      onFileRemove(uploadedFile.id);
                    }}
                    disabled={uploadedFile.status === 'uploading'}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
