/**
 * Chat Service - Handles all API communication for chat functionality
 * Framework-agnostic service for chat API interactions
 */

export interface ChatRequest {
  userMessage: string;
  model: string;
  apiKey: string;
  forceGeneralMode?: boolean;
  forceDocumentMode?: boolean;
}

export interface RAGChatRequest {
  userMessage: string;
  model: string;
  apiKey: string;
  useContext?: boolean;
}

export interface ChatResponse {
  success: boolean;
  data?: string;
  error?: string;
}

export interface RAGChatResponse {
  success: boolean;
  response?: string;
  usedContext?: boolean;
  needsFallback?: boolean;
  fallbackRequest?: any;
  citations?: Array<{
    chunk_id: string;
    document_name: string;
    document_id: string;
    content_preview: string;
  }>;
  confidenceScore?: number;
  error?: string;
}

export interface StreamingChatResponse {
  reader: ReadableStreamDefaultReader<Uint8Array>;
  decoder: TextDecoder;
}

export interface ConversationStatus {
  mode: 'general' | 'document';
  session_active: boolean;
  documents: Array<{
    id: string;
    name: string;
    size: number;
    upload_time: number;
    chunk_count: number;
  }>;
}

/**
 * Configuration for the chat service
 */
const getBaseUrl = (): string => {
  // If environment variable is set, use it (for production/custom deployments)
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }
  
  // Auto-detect based on environment
  if (typeof window !== 'undefined') {
    // Client-side: use current origin for production, localhost for development
    const { protocol, hostname } = window.location;
    
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      // Development: backend runs on port 8000
      return 'http://localhost:8000';
    } else {
      // Production: assume API is on same domain (Vercel deployment)
      return `${protocol}//${hostname}`;
    }
  }
  
  // Server-side fallback (during SSR)
  return '';
};

/**
 * Validates the chat request data
 */
const validateChatRequest = (data: ChatRequest): void => {
  if (!data.apiKey?.trim()) {
    throw new Error("API key is required");
  }
  if (!data.userMessage?.trim()) {
    throw new Error("User message is required");
  }
  if (!data.model?.trim()) {
    throw new Error("Model is required");
  }
};

/**
 * Transforms the request data to match the API contract
 */
const transformRequestData = (data: ChatRequest) => {
  return {
    user_message: data.userMessage,
    model: data.model,
    api_key: data.apiKey,
  };
};

/**
 * Initiates a streaming chat request to the API
 * @param data - The chat request data
 * @returns Promise<StreamingChatResponse> - The streaming response setup
 * @throws Error if the request fails or validation fails
 */
export const initiateChatStream = async (data: ChatRequest): Promise<StreamingChatResponse> => {
  // Validate input data
  validateChatRequest(data);

  const baseUrl = getBaseUrl();
  
  try {
    const response = await fetch(`${baseUrl}/api/chat`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json" 
      },
      body: JSON.stringify(transformRequestData(data)),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error("No response body received from server");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    return {
      reader,
      decoder,
    };
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Chat API request failed: ${error.message}`);
    }
    throw new Error("Unknown error occurred during chat API request");
  }
};

/**
 * Reads a chunk from the streaming response
 * @param reader - The stream reader
 * @param decoder - The text decoder
 * @returns Promise<{chunk: string, done: boolean}> - The decoded chunk and completion status
 */
export const readStreamChunk = async (
  reader: ReadableStreamDefaultReader<Uint8Array>,
  decoder: TextDecoder
): Promise<{ chunk: string; done: boolean }> => {
  try {
    const { value, done } = await reader.read();
    
    if (done) {
      return { chunk: "", done: true };
    }

    if (value) {
      const chunk = decoder.decode(value);
      return { chunk, done: false };
    }

    return { chunk: "", done: false };
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Stream reading failed: ${error.message}`);
    }
    throw new Error("Unknown error occurred while reading stream");
  }
};

/**
 * Processes a complete streaming chat request
 * @param data - The chat request data
 * @param onChunk - Callback function called for each chunk received
 * @returns Promise<string> - The complete response text
 */
export const processStreamingChat = async (
  data: ChatRequest,
  onChunk?: (chunk: string) => void
): Promise<string> => {
  const { reader, decoder } = await initiateChatStream(data);
  
  let fullText = "";
  let done = false;

  try {
    while (!done) {
      const { chunk, done: chunkDone } = await readStreamChunk(reader, decoder);
      done = chunkDone;
      
      if (chunk) {
        fullText += chunk;
        if (onChunk) {
          onChunk(chunk);
        }
      }
    }

    return fullText;
  } catch (error) {
    // Ensure reader is released on error
    try {
      reader.releaseLock();
    } catch {
      // Ignore release errors
    }
    throw error;
  }
};

/**
 * Simple non-streaming chat request (for testing or simple use cases)
 * @param data - The chat request data
 * @returns Promise<ChatResponse> - The complete response
 */
export const sendChatRequest = async (data: ChatRequest): Promise<ChatResponse> => {
  try {
    const fullText = await processStreamingChat(data);
    return {
      success: true,
      data: fullText,
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return {
      success: false,
      error: errorMessage,
    };
  }
};

/**
 * Get conversation status to check if we're in document mode
 * @param apiKey - The API key
 * @returns Promise<ConversationStatus> - The conversation status
 */
export const getConversationStatus = async (apiKey: string): Promise<ConversationStatus> => {
  const baseUrl = getBaseUrl();
  
  try {
    const response = await fetch(`${baseUrl}/api/conversation/status?api_key=${encodeURIComponent(apiKey)}`, {
      method: "GET",
      headers: { 
        "Content-Type": "application/json" 
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result.conversation_status;
  } catch (error) {
    // If conversation status fails, assume general mode
    return {
      mode: 'general',
      session_active: false,
      documents: []
    };
  }
};

/**
 * Send a RAG chat request with document context
 * @param data - The RAG chat request data
 * @returns Promise<RAGChatResponse> - The RAG response with citations
 */
export const sendRAGChatRequest = async (data: RAGChatRequest): Promise<RAGChatResponse> => {
  const baseUrl = getBaseUrl();
  
  try {
    const response = await fetch(`${baseUrl}/api/conversation/chat`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json" 
      },
      body: JSON.stringify({
        user_message: data.userMessage,
        model: data.model,
        api_key: data.apiKey,
        use_context: data.useContext !== false
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    return {
      success: true,
      response: result.response,
      usedContext: true,
      needsFallback: result.needs_fallback,
      fallbackRequest: result.fallback_request,
      citations: result.citations,
      confidenceScore: result.confidence_score
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return {
      success: false,
      error: errorMessage,
    };
  }
};

/**
 * Confirm fallback to general knowledge when document context is insufficient
 * @param query - The original query
 * @param useGeneralKnowledge - Whether to use general knowledge
 * @param apiKey - The API key
 * @returns Promise<RAGChatResponse> - The fallback response
 */
export const confirmFallback = async (
  query: string, 
  useGeneralKnowledge: boolean, 
  apiKey: string
): Promise<RAGChatResponse> => {
  const baseUrl = getBaseUrl();
  
  try {
    const response = await fetch(`${baseUrl}/api/conversation/fallback-confirm`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json" 
      },
      body: JSON.stringify({
        query,
        use_general_knowledge: useGeneralKnowledge,
        api_key: apiKey
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    return {
      success: true,
      response: result.response,
      usedContext: !result.used_general_knowledge,
      needsFallback: false,
      citations: []
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return {
      success: false,
      error: errorMessage,
    };
  }
};

/**
 * Smart chat function that automatically chooses between regular chat and RAG
 * @param data - The chat request data
 * @returns Promise<RAGChatResponse> - The appropriate response
 */
export const sendSmartChatRequest = async (data: ChatRequest): Promise<RAGChatResponse> => {
  try {
    // Handle user overrides first
    if (data.forceGeneralMode) {
      console.log('User requested general knowledge mode, using regular chat');
      const response = await sendChatRequest(data);
      return {
        success: response.success,
        response: response.data,
        usedContext: false,
        needsFallback: false,
        citations: [],
        error: response.error
      };
    }

    // First check conversation status
    const status = await getConversationStatus(data.apiKey);
    
    // Check if documents are available (fix: properly check array structure)
    const hasDocuments = status.documents && Array.isArray(status.documents) && status.documents.length > 0;
    const isDocumentMode = status.mode === 'document';
    const isSessionActive = status.session_active;
    
    console.log('Smart chat status check:', { hasDocuments, isDocumentMode, isSessionActive, documentsCount: status.documents?.length });

    // Handle force document mode override
    if (data.forceDocumentMode && !hasDocuments) {
      console.log('User requested document mode but no documents available');
      return {
        success: false,
        error: "Document mode requested but no documents are available. Please upload documents first.",
        response: "",
        usedContext: false,
        needsFallback: false,
        citations: []
      };
    }
    
    // CRITICAL FIX: If we're in document mode but have no documents, exit document mode
    if (isDocumentMode && !hasDocuments) {
      console.log('Document mode active but no documents found, exiting document mode');
      try {
        const exitResponse = await fetch(`${getBaseUrl()}/api/conversation/exit-document-mode`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ api_key: data.apiKey })
        });
        
        if (exitResponse.ok) {
          console.log('Successfully exited document mode');
        } else {
          console.warn('Failed to exit document mode:', exitResponse.status);
        }
      } catch (error) {
        console.warn('Error exiting document mode:', error);
      }
      
      // Use regular chat since we have no documents
      console.log('Using regular chat after exiting document mode');
      const response = await sendChatRequest(data);
      return {
        success: response.success,
        response: response.data,
        usedContext: false,
        needsFallback: false,
        citations: [],
        error: response.error
      };
    }
    
    if (hasDocuments) {
      // Try to enter document mode if not already active
      if (!isDocumentMode || !isSessionActive) {
        console.log('Attempting to enter document mode...');
        try {
          const enterModeResponse = await fetch(`${getBaseUrl()}/api/conversation/enter-document-mode`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: data.apiKey })
          });
          
          if (enterModeResponse.ok) {
            console.log('Successfully entered document mode');
          } else {
            console.warn('Failed to enter document mode:', enterModeResponse.status);
          }
        } catch (error) {
          console.warn('Error entering document mode:', error);
        }
      }
      
      // Use RAG chat when documents are available
      console.log('Using RAG chat with documents');
      const ragResponse = await sendRAGChatRequest({
        userMessage: data.userMessage,
        model: data.model,
        apiKey: data.apiKey,
        useContext: true
      });
      
      // If RAG succeeds, return it
      if (ragResponse.success) {
        console.log('RAG request successful, used context:', ragResponse.usedContext);
        return ragResponse;
      }
      
      // If RAG fails, fall back to regular chat but log the error
      console.warn('RAG request failed, falling back to regular chat:', ragResponse.error);
    } else {
      console.log('No documents available, using regular chat');
    }
    
    // Use regular chat when no documents are available or RAG failed
    const response = await sendChatRequest(data);
    return {
      success: response.success,
      response: response.data,
      usedContext: false,
      needsFallback: false,
      citations: [],
      error: response.error
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    console.error('Smart chat request error:', errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  }
};
