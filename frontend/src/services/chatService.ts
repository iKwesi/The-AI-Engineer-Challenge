/**
 * Chat Service - Handles all API communication for chat functionality
 * Framework-agnostic service for chat API interactions
 */

export interface ChatRequest {
  developerMessage: string;
  userMessage: string;
  model: string;
  apiKey: string;
}

export interface ChatResponse {
  success: boolean;
  data?: string;
  error?: string;
}

export interface StreamingChatResponse {
  reader: ReadableStreamDefaultReader<Uint8Array>;
  decoder: TextDecoder;
}

/**
 * Configuration for the chat service
 */
const getBaseUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_BASE_URL || "";
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
    developer_message: data.developerMessage,
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
