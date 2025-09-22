/**
 * Document Service - Handles all API communication for document upload functionality
 * Supports both single and batch file uploads
 */

export interface DocumentUploadRequest {
  files: File[];
  apiKey: string;
}

export interface DocumentUploadResult {
  filename: string;
  status: 'success' | 'failed';
  message: string;
  chunks_processed: number;
  file_size: number;
}

export interface DocumentUploadResponse {
  status: 'success' | 'partial_success' | 'failed';
  message: string;
  total_files: number;
  successful_files: number;
  failed_files: number;
  results: DocumentUploadResult[];
  entered_document_mode: boolean;
}

export interface YouTubeProcessRequest {
  url: string;
  apiKey: string;
}

export interface YouTubeProcessResponse {
  status: 'success' | 'failed';
  message: string;
  video_title?: string;
  chunks_processed?: number;
  entered_document_mode?: boolean;
}

export interface DocumentListResponse {
  documents: Array<{
    id: string;
    name: string;
    type: string;
    size: number;
    chunks: number;
    uploaded_at: string;
  }>;
}

export interface ConversationModeStatus {
  mode: 'general' | 'document';
  session_id?: string;
  documents: Array<{
    id: string;
    name: string;
    chunks: number;
  }>;
}

/**
 * Configuration for the document service
 */
const getBaseUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_BASE_URL || "";
};

/**
 * Validates the document upload request
 */
const validateUploadRequest = (data: DocumentUploadRequest): void => {
  if (!data.apiKey?.trim()) {
    throw new Error("API key is required");
  }
  if (!data.files || data.files.length === 0) {
    throw new Error("At least one file is required");
  }
};

/**
 * Uploads a single document to the API
 * @param file - The file to upload
 * @param apiKey - The API key for authentication
 * @returns Promise<DocumentUploadResponse> - The upload response
 */
export const uploadSingleDocument = async (
  file: File,
  apiKey: string
): Promise<DocumentUploadResponse> => {
  validateUploadRequest({ files: [file], apiKey });

  const baseUrl = getBaseUrl();
  const formData = new FormData();
  formData.append('file', file);
  formData.append('api_key', apiKey);

  try {
    const response = await fetch(`${baseUrl}/api/upload-document`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Transform single upload response to match batch response format
    return {
      status: data.status === 'success' ? 'success' : 'failed',
      message: data.message,
      total_files: 1,
      successful_files: data.status === 'success' ? 1 : 0,
      failed_files: data.status === 'success' ? 0 : 1,
      results: [{
        filename: file.name,
        status: data.status,
        message: data.message,
        chunks_processed: data.chunks_processed || 0,
        file_size: file.size
      }],
      entered_document_mode: data.entered_document_mode || false
    };
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Document upload failed: ${error.message}`);
    }
    throw new Error("Unknown error occurred during document upload");
  }
};

/**
 * Uploads multiple documents to the API (batch upload)
 * @param files - The files to upload
 * @param apiKey - The API key for authentication
 * @returns Promise<DocumentUploadResponse> - The batch upload response
 */
export const uploadMultipleDocuments = async (
  files: File[],
  apiKey: string
): Promise<DocumentUploadResponse> => {
  validateUploadRequest({ files, apiKey });

  const baseUrl = getBaseUrl();
  const formData = new FormData();
  
  files.forEach(file => {
    formData.append('files', file);
  });
  formData.append('api_key', apiKey);

  try {
    const response = await fetch(`${baseUrl}/api/upload-documents`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Batch upload failed: ${error.message}`);
    }
    throw new Error("Unknown error occurred during batch upload");
  }
};

/**
 * Processes a YouTube URL
 * @param url - The YouTube URL to process
 * @param apiKey - The API key for authentication
 * @returns Promise<YouTubeProcessResponse> - The processing response
 */
export const processYouTubeUrl = async (
  url: string,
  apiKey: string
): Promise<YouTubeProcessResponse> => {
  if (!apiKey?.trim()) {
    throw new Error("API key is required");
  }
  if (!url?.trim()) {
    throw new Error("YouTube URL is required");
  }

  const baseUrl = getBaseUrl();

  try {
    const response = await fetch(`${baseUrl}/api/process-youtube`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url: url.trim(),
        api_key: apiKey,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`YouTube processing failed: ${error.message}`);
    }
    throw new Error("Unknown error occurred during YouTube processing");
  }
};

/**
 * Gets the list of uploaded documents
 * @param apiKey - The API key for authentication
 * @returns Promise<DocumentListResponse> - The list of documents
 */
export const getDocumentList = async (apiKey: string): Promise<DocumentListResponse> => {
  if (!apiKey?.trim()) {
    throw new Error("API key is required");
  }

  const baseUrl = getBaseUrl();

  try {
    const response = await fetch(`${baseUrl}/api/documents?api_key=${encodeURIComponent(apiKey)}`, {
      method: "GET",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to get document list: ${error.message}`);
    }
    throw new Error("Unknown error occurred while getting document list");
  }
};

/**
 * Removes a document from the system
 * @param documentId - The ID of the document to remove
 * @param apiKey - The API key for authentication
 * @returns Promise<{status: string, message: string}> - The removal response
 */
export const removeDocument = async (
  documentId: string,
  apiKey: string
): Promise<{status: string, message: string}> => {
  if (!apiKey?.trim()) {
    throw new Error("API key is required");
  }
  if (!documentId?.trim()) {
    throw new Error("Document ID is required");
  }

  const baseUrl = getBaseUrl();

  try {
    const response = await fetch(`${baseUrl}/api/documents/${encodeURIComponent(documentId)}?api_key=${encodeURIComponent(apiKey)}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to remove document: ${error.message}`);
    }
    throw new Error("Unknown error occurred while removing document");
  }
};

/**
 * Gets the current conversation mode status
 * @param apiKey - The API key for authentication
 * @returns Promise<ConversationModeStatus> - The current mode status
 */
export const getConversationModeStatus = async (apiKey: string): Promise<ConversationModeStatus> => {
  if (!apiKey?.trim()) {
    throw new Error("API key is required");
  }

  const baseUrl = getBaseUrl();

  try {
    const response = await fetch(`${baseUrl}/api/conversation/status?api_key=${encodeURIComponent(apiKey)}`, {
      method: "GET",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    // The API returns {status: "success", conversation_status: {...}}
    // We need to return just the conversation_status part
    return data.conversation_status || data;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to get conversation mode status: ${error.message}`);
    }
    throw new Error("Unknown error occurred while getting conversation mode status");
  }
};

/**
 * Enters document mode
 * @param apiKey - The API key for authentication
 * @returns Promise<{status: string, message: string}> - The enter response
 */
export const enterDocumentMode = async (apiKey: string): Promise<{status: string, message: string}> => {
  if (!apiKey?.trim()) {
    throw new Error("API key is required");
  }

  const baseUrl = getBaseUrl();

  try {
    const response = await fetch(`${baseUrl}/api/conversation/enter-document-mode`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        api_key: apiKey,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to enter document mode: ${error.message}`);
    }
    throw new Error("Unknown error occurred while entering document mode");
  }
};

/**
 * Exits document mode
 * @param apiKey - The API key for authentication
 * @returns Promise<{status: string, message: string}> - The exit response
 */
export const exitDocumentMode = async (apiKey: string): Promise<{status: string, message: string}> => {
  if (!apiKey?.trim()) {
    throw new Error("API key is required");
  }

  const baseUrl = getBaseUrl();

  try {
    const response = await fetch(`${baseUrl}/api/conversation/exit-document-mode`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        api_key: apiKey,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to exit document mode: ${error.message}`);
    }
    throw new Error("Unknown error occurred while exiting document mode");
  }
};

/**
 * Detects YouTube URLs in text
 * @param text - The text to search for YouTube URLs
 * @returns string[] - Array of detected YouTube URLs
 */
export const detectYouTubeUrls = (text: string): string[] => {
  const youtubeRegex = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/g;
  const matches = text.match(youtubeRegex);
  return matches || [];
};

/**
 * Checks if a string contains YouTube URLs
 * @param text - The text to check
 * @returns boolean - True if YouTube URLs are found
 */
export const hasYouTubeUrls = (text: string): boolean => {
  return detectYouTubeUrls(text).length > 0;
};
