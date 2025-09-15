import React from 'react';
import { renderHook, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useChat } from '../useChat';
import type { ChatRequest } from '../../services/chatService';

// Mock fetch globally
global.fetch = jest.fn();

// Mock TextDecoder
global.TextDecoder = jest.fn().mockImplementation(() => ({
  decode: jest.fn(),
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

describe('useChat Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockResolvedValue(mockResponse);
  });

  describe('Complete chat flow from hook through service', () => {
    it('should handle successful streaming chat end-to-end', async () => {
      // Setup streaming response simulation
      const chunks = ['Hello', ' ', 'world', '!'];
      let chunkIndex = 0;

      mockReader.read.mockImplementation(() => {
        if (chunkIndex < chunks.length) {
          const chunk = chunks[chunkIndex++];
          return Promise.resolve({
            value: new Uint8Array(Array.from(chunk, c => c.charCodeAt(0))),
            done: false,
          });
        }
        return Promise.resolve({ value: undefined, done: true });
      });

      const mockDecoder = {
        decode: jest.fn().mockImplementation((value: Uint8Array) => {
          return String.fromCharCode(...Array.from(value));
        }),
      };

      (global.TextDecoder as jest.Mock).mockImplementation(() => mockDecoder);

      const { result } = renderHook(() => useChat());

      // Initial state verification
      expect(result.current.message).toBe('');
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe(null);

      const chatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Hello, world!',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      let fullResponse: string | undefined;

      // Execute chat request
      await act(async () => {
        fullResponse = await result.current.sendChat(chatRequest);
      });

      // Verify final state
      expect(result.current.message).toBe('Hello world!');
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe(null);
      expect(fullResponse).toBe('Hello world!');

      // Verify API call was made correctly
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
    });

    it('should handle loading state during streaming', async () => {
      // Setup a delayed response to test loading state
      let resolveRead: (value: any) => void;
      const readPromise = new Promise(resolve => {
        resolveRead = resolve;
      });

      mockReader.read.mockReturnValue(readPromise);

      const { result } = renderHook(() => useChat());

      const chatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Test message',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      // Start the chat request
      let chatPromise: Promise<string | undefined>;
      act(() => {
        chatPromise = result.current.sendChat(chatRequest);
      });

      // Verify loading state is active
      expect(result.current.loading).toBe(true);
      expect(result.current.message).toBe('');
      expect(result.current.error).toBe(null);

      // Complete the request
      await act(async () => {
        resolveRead!({ value: undefined, done: true });
        await chatPromise;
      });

      // Verify loading state is cleared
      expect(result.current.loading).toBe(false);
    });

    it('should accumulate message chunks during streaming', async () => {
      const chunks = ['Chunk', ' 1', ', Chunk', ' 2', ', Done'];
      let chunkIndex = 0;

      mockReader.read.mockImplementation(() => {
        if (chunkIndex < chunks.length) {
          const chunk = chunks[chunkIndex++];
          return Promise.resolve({
            value: new Uint8Array(Array.from(chunk, c => c.charCodeAt(0))),
            done: false,
          });
        }
        return Promise.resolve({ value: undefined, done: true });
      });

      const mockDecoder = {
        decode: jest.fn().mockImplementation((value: Uint8Array) => {
          return String.fromCharCode(...Array.from(value));
        }),
      };

      (global.TextDecoder as jest.Mock).mockImplementation(() => mockDecoder);

      const { result } = renderHook(() => useChat());

      const chatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Test streaming',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      await act(async () => {
        await result.current.sendChat(chatRequest);
      });

      expect(result.current.message).toBe('Chunk 1, Chunk 2, Done');
    });
  });

  describe('Error propagation from service to hook', () => {
    it('should handle API validation errors', async () => {
      const { result } = renderHook(() => useChat());

      const invalidRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: '', // Invalid: empty message
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      await act(async () => {
        await result.current.sendChat(invalidRequest);
      });

      expect(result.current.error).toBe('User message is required');
      expect(result.current.loading).toBe(false);
      expect(result.current.message).toBe('');
    });

    it('should handle network errors', async () => {
      (fetch as jest.Mock).mockRejectedValue(new Error('Network connection failed'));

      const { result } = renderHook(() => useChat());

      const chatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Test message',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      await act(async () => {
        await result.current.sendChat(chatRequest);
      });

      expect(result.current.error).toBe('Chat API request failed: Network connection failed');
      expect(result.current.loading).toBe(false);
      expect(result.current.message).toBe('');
    });

    it('should handle HTTP error responses', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 401,
        body: null,
      });

      const { result } = renderHook(() => useChat());

      const chatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Test message',
        model: 'gpt-3.5-turbo',
        apiKey: 'invalid-key',
      };

      await act(async () => {
        await result.current.sendChat(chatRequest);
      });

      expect(result.current.error).toBe('Chat API request failed: HTTP error! status: 401');
      expect(result.current.loading).toBe(false);
      expect(result.current.message).toBe('');
    });

    it('should handle streaming errors', async () => {
      mockReader.read.mockRejectedValue(new Error('Stream interrupted'));

      const { result } = renderHook(() => useChat());

      const chatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Test message',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      await act(async () => {
        await result.current.sendChat(chatRequest);
      });

      expect(result.current.error).toBe('Stream reading failed: Stream interrupted');
      expect(result.current.loading).toBe(false);
      expect(result.current.message).toBe('');
    });

    it('should handle unknown errors gracefully', async () => {
      (fetch as jest.Mock).mockRejectedValue('Unknown error type');

      const { result } = renderHook(() => useChat());

      const chatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Test message',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      await act(async () => {
        await result.current.sendChat(chatRequest);
      });

      expect(result.current.error).toBe('Unknown error occurred during chat API request');
      expect(result.current.loading).toBe(false);
      expect(result.current.message).toBe('');
    });
  });

  describe('State management during multiple requests', () => {
    it('should reset state between requests', async () => {
      // First request setup
      mockReader.read
        .mockResolvedValueOnce({ value: new Uint8Array([72, 105]), done: false }) // "Hi"
        .mockResolvedValueOnce({ value: undefined, done: true });

      const mockDecoder = {
        decode: jest.fn().mockReturnValue('Hi'),
      };

      (global.TextDecoder as jest.Mock).mockImplementation(() => mockDecoder);

      const { result } = renderHook(() => useChat());

      const firstRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'First message',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      // Execute first request
      await act(async () => {
        await result.current.sendChat(firstRequest);
      });

      expect(result.current.message).toBe('Hi');
      expect(result.current.error).toBe(null);

      // Setup second request
      jest.clearAllMocks();
      (fetch as jest.Mock).mockResolvedValue(mockResponse);
      
      mockReader.read
        .mockResolvedValueOnce({ value: new Uint8Array([66, 121, 101]), done: false }) // "Bye"
        .mockResolvedValueOnce({ value: undefined, done: true });

      mockDecoder.decode.mockReturnValue('Bye');

      const secondRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Second message',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      // Execute second request
      await act(async () => {
        await result.current.sendChat(secondRequest);
      });

      // Verify state was reset and new message is displayed
      expect(result.current.message).toBe('Bye');
      expect(result.current.error).toBe(null);
      expect(result.current.loading).toBe(false);
    });

    it('should handle concurrent requests properly', async () => {
      const { result } = renderHook(() => useChat());

      const chatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Test message',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      // Start first request
      let firstPromise: Promise<string | undefined>;
      act(() => {
        firstPromise = result.current.sendChat(chatRequest);
      });

      // Start second request immediately (should reset state)
      let secondPromise: Promise<string | undefined>;
      act(() => {
        secondPromise = result.current.sendChat(chatRequest);
      });

      // Wait for both to complete
      await act(async () => {
        await Promise.all([firstPromise, secondPromise]);
      });

      // Verify final state is consistent
      expect(result.current.loading).toBe(false);
    });
  });

  describe('Environment and configuration integration', () => {
    it('should work with different base URLs', async () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;
      process.env.NEXT_PUBLIC_API_BASE_URL = 'https://custom-api.example.com';

      mockReader.read.mockResolvedValue({ value: undefined, done: true });

      const { result } = renderHook(() => useChat());

      const chatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Test with custom URL',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      await act(async () => {
        await result.current.sendChat(chatRequest);
      });

      expect(fetch).toHaveBeenCalledWith(
        'https://custom-api.example.com/api/chat',
        expect.any(Object)
      );

      // Restore original environment
      process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
    });
  });

  describe('Performance and memory management', () => {
    it('should handle component unmount gracefully', async () => {
      const { result, unmount } = renderHook(() => useChat());

      // Verify initial state
      expect(result.current.message).toBe('');
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe(null);

      // Unmount the hook
      unmount();

      // Test passes if no errors are thrown during unmount
      expect(true).toBe(true);
    });

    it('should handle errors during streaming and release resources', async () => {
      mockReader.read.mockRejectedValue(new Error('Stream error'));

      const { result } = renderHook(() => useChat());

      const chatRequest: ChatRequest = {
        developerMessage: 'You are a helpful assistant',
        userMessage: 'Test error handling',
        model: 'gpt-3.5-turbo',
        apiKey: 'test-api-key',
      };

      await act(async () => {
        await result.current.sendChat(chatRequest);
      });

      // Verify error state
      expect(result.current.error).toBe('Stream reading failed: Stream error');
      expect(result.current.loading).toBe(false);
      
      // Verify reader lock was released on error
      expect(mockReader.releaseLock).toHaveBeenCalled();
    });
  });
});
