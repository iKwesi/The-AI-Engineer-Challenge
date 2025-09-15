import {
  initiateChatStream,
  readStreamChunk,
  processStreamingChat,
  sendChatRequest,
  type ChatRequest,
} from '../chatService';

// Mock fetch globally
global.fetch = jest.fn();

// Mock TextDecoder
global.TextDecoder = jest.fn().mockImplementation(() => ({
  decode: jest.fn().mockReturnValue('test chunk'),
}));

// Mock ReadableStream and Reader
const mockReader = {
  read: jest.fn(),
  releaseLock: jest.fn(),
};

const mockResponse = {
  ok: true,
  status: 200,
  body: {
    getReader: jest.fn().mockReturnValue(mockReader),
  },
};

describe('chatService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockResolvedValue(mockResponse);
  });

  describe('initiateChatStream', () => {
    const validChatRequest: ChatRequest = {
      developerMessage: 'You are a helpful assistant',
      userMessage: 'Hello, world!',
      model: 'gpt-3.5-turbo',
      apiKey: 'test-api-key',
    };

    it('should successfully initiate a chat stream with valid data', async () => {
      const result = await initiateChatStream(validChatRequest);

      expect(fetch).toHaveBeenCalledWith('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          developer_message: 'You are a helpful assistant',
          user_message: 'Hello, world!',
          model: 'gpt-3.5-turbo',
          api_key: 'test-api-key',
        }),
      });

      expect(result).toHaveProperty('reader');
      expect(result).toHaveProperty('decoder');
      expect(mockResponse.body.getReader).toHaveBeenCalled();
    });

    it('should throw error when API key is missing', async () => {
      const invalidRequest = { ...validChatRequest, apiKey: '' };

      await expect(initiateChatStream(invalidRequest)).rejects.toThrow(
        'API key is required'
      );
    });

    it('should throw error when user message is missing', async () => {
      const invalidRequest = { ...validChatRequest, userMessage: '' };

      await expect(initiateChatStream(invalidRequest)).rejects.toThrow(
        'User message is required'
      );
    });

    it('should throw error when model is missing', async () => {
      const invalidRequest = { ...validChatRequest, model: '' };

      await expect(initiateChatStream(invalidRequest)).rejects.toThrow(
        'Model is required'
      );
    });

    it('should handle HTTP error responses', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        body: null,
      });

      await expect(initiateChatStream(validChatRequest)).rejects.toThrow(
        'Chat API request failed: HTTP error! status: 401'
      );
    });

    it('should handle missing response body', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        status: 200,
        body: null,
      });

      await expect(initiateChatStream(validChatRequest)).rejects.toThrow(
        'Chat API request failed: No response body received from server'
      );
    });

    it('should handle network errors', async () => {
      (fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      await expect(initiateChatStream(validChatRequest)).rejects.toThrow(
        'Chat API request failed: Network error'
      );
    });

    it('should handle unknown errors', async () => {
      (fetch as jest.Mock).mockRejectedValue('Unknown error');

      await expect(initiateChatStream(validChatRequest)).rejects.toThrow(
        'Unknown error occurred during chat API request'
      );
    });
  });

  describe('readStreamChunk', () => {
    const mockDecoder = {
      decode: jest.fn(),
    } as unknown as TextDecoder;

    it('should read and decode a chunk successfully', async () => {
      const mockValue = new Uint8Array([72, 101, 108, 108, 111]); // "Hello"
      mockReader.read.mockResolvedValue({ value: mockValue, done: false });
      (mockDecoder.decode as jest.Mock).mockReturnValue('Hello');

      const result = await readStreamChunk(mockReader as unknown as ReadableStreamDefaultReader<Uint8Array>, mockDecoder);

      expect(result).toEqual({ chunk: 'Hello', done: false });
      expect(mockReader.read).toHaveBeenCalled();
      expect(mockDecoder.decode).toHaveBeenCalledWith(mockValue);
    });

    it('should handle stream completion', async () => {
      mockReader.read.mockResolvedValue({ value: undefined, done: true });

      const result = await readStreamChunk(mockReader as unknown as ReadableStreamDefaultReader<Uint8Array>, mockDecoder);

      expect(result).toEqual({ chunk: '', done: true });
    });

    it('should handle empty chunks', async () => {
      mockReader.read.mockResolvedValue({ value: null, done: false });

      const result = await readStreamChunk(mockReader as unknown as ReadableStreamDefaultReader<Uint8Array>, mockDecoder);

      expect(result).toEqual({ chunk: '', done: false });
    });

    it('should handle stream reading errors', async () => {
      mockReader.read.mockRejectedValue(new Error('Stream error'));

      await expect(readStreamChunk(mockReader as unknown as ReadableStreamDefaultReader<Uint8Array>, mockDecoder)).rejects.toThrow(
        'Stream reading failed: Stream error'
      );
    });

    it('should handle unknown stream errors', async () => {
      mockReader.read.mockRejectedValue('Unknown stream error');

      await expect(readStreamChunk(mockReader as unknown as ReadableStreamDefaultReader<Uint8Array>, mockDecoder)).rejects.toThrow(
        'Unknown error occurred while reading stream'
      );
    });
  });

  describe('processStreamingChat', () => {
    const validChatRequest: ChatRequest = {
      developerMessage: 'You are a helpful assistant',
      userMessage: 'Hello, world!',
      model: 'gpt-3.5-turbo',
      apiKey: 'test-api-key',
    };

    it('should process streaming chat successfully', async () => {
      // Mock the stream to return chunks and then complete
      mockReader.read
        .mockResolvedValueOnce({ value: new Uint8Array([72, 101]), done: false }) // "He"
        .mockResolvedValueOnce({ value: new Uint8Array([108, 108, 111]), done: false }) // "llo"
        .mockResolvedValueOnce({ value: undefined, done: true });

      const mockDecoder = {
        decode: jest.fn()
          .mockReturnValueOnce('He')
          .mockReturnValueOnce('llo'),
      };

      // Mock TextDecoder constructor
      (global.TextDecoder as jest.Mock).mockImplementation(() => mockDecoder);

      const onChunkMock = jest.fn();
      const result = await processStreamingChat(validChatRequest, onChunkMock);

      expect(result).toBe('Hello');
      expect(onChunkMock).toHaveBeenCalledTimes(2);
      expect(onChunkMock).toHaveBeenNthCalledWith(1, 'He');
      expect(onChunkMock).toHaveBeenNthCalledWith(2, 'llo');
    });

    it('should work without onChunk callback', async () => {
      mockReader.read
        .mockResolvedValueOnce({ value: new Uint8Array([72, 105]), done: false }) // "Hi"
        .mockResolvedValueOnce({ value: undefined, done: true });

      const mockDecoder = {
        decode: jest.fn().mockReturnValue('Hi'),
      };

      (global.TextDecoder as jest.Mock).mockImplementation(() => mockDecoder);

      const result = await processStreamingChat(validChatRequest);

      expect(result).toBe('Hi');
    });

    it('should handle streaming errors and release reader lock', async () => {
      mockReader.read.mockRejectedValue(new Error('Stream error'));

      await expect(processStreamingChat(validChatRequest)).rejects.toThrow(
        'Stream reading failed: Stream error'
      );

      expect(mockReader.releaseLock).toHaveBeenCalled();
    });
  });

  describe('sendChatRequest', () => {
    const validChatRequest: ChatRequest = {
      developerMessage: 'You are a helpful assistant',
      userMessage: 'Hello, world!',
      model: 'gpt-3.5-turbo',
      apiKey: 'test-api-key',
    };

    it('should return successful response', async () => {
      // Mock successful streaming
      mockReader.read
        .mockResolvedValueOnce({ value: new Uint8Array([72, 105]), done: false })
        .mockResolvedValueOnce({ value: undefined, done: true });

      const mockDecoder = {
        decode: jest.fn().mockReturnValue('Hi'),
      };

      (global.TextDecoder as jest.Mock).mockImplementation(() => mockDecoder);

      const result = await sendChatRequest(validChatRequest);

      expect(result).toEqual({
        success: true,
        data: 'Hi',
      });
    });

    it('should return error response on failure', async () => {
      (fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const result = await sendChatRequest(validChatRequest);

      expect(result).toEqual({
        success: false,
        error: 'Chat API request failed: Network error',
      });
    });

    it('should handle unknown errors', async () => {
      (fetch as jest.Mock).mockRejectedValue('Unknown error');

      const result = await sendChatRequest(validChatRequest);

      expect(result).toEqual({
        success: false,
        error: 'Unknown error occurred during chat API request',
      });
    });
  });

  describe('API key validation', () => {
    const baseChatRequest: ChatRequest = {
      developerMessage: 'You are a helpful assistant',
      userMessage: 'Hello, world!',
      model: 'gpt-3.5-turbo',
      apiKey: 'test-api-key',
    };

    it('should reject whitespace-only API key', async () => {
      const invalidRequest = { ...baseChatRequest, apiKey: '   ' };

      await expect(initiateChatStream(invalidRequest)).rejects.toThrow(
        'API key is required'
      );
    });

    it('should reject whitespace-only user message', async () => {
      const invalidRequest = { ...baseChatRequest, userMessage: '   ' };

      await expect(initiateChatStream(invalidRequest)).rejects.toThrow(
        'User message is required'
      );
    });

    it('should reject whitespace-only model', async () => {
      const invalidRequest = { ...baseChatRequest, model: '   ' };

      await expect(initiateChatStream(invalidRequest)).rejects.toThrow(
        'Model is required'
      );
    });
  });

  describe('Environment configuration', () => {
    it('should use environment base URL when available', async () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;
      process.env.NEXT_PUBLIC_API_BASE_URL = 'https://api.example.com';

      const validChatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Hello, world!',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      await initiateChatStream(validChatRequest);

      expect(fetch).toHaveBeenCalledWith('https://api.example.com/api/chat', expect.any(Object));

      // Restore original environment
      process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
    });

    it('should use empty base URL when environment variable is not set', async () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;
      delete process.env.NEXT_PUBLIC_API_BASE_URL;

      const validChatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Hello, world!',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      await initiateChatStream(validChatRequest);

      expect(fetch).toHaveBeenCalledWith('/api/chat', expect.any(Object));

      // Restore original environment
      process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
    });
  });
});
