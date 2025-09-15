import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ProfessionalChatInterface from '../ProfessionalChatInterface';
import * as chatService from '../../../../services/chatService';

// Mock the chat service
jest.mock('../../../../services/chatService');
const mockChatService = chatService as jest.Mocked<typeof chatService>;

describe('ProfessionalChatInterface Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Integration with useChat Hook', () => {
    it('integrates with real useChat hook for successful submission', async () => {
      const user = userEvent.setup();
      
      // Mock successful streaming response
      mockChatService.processStreamingChat.mockImplementation(
        async (_, onChunk) => {
          // Simulate streaming chunks
          if (onChunk) {
            onChunk('Hello ');
            await new Promise(resolve => setTimeout(resolve, 10));
            onChunk('world!');
          }
          return 'Hello world!';
        }
      );

      render(<ProfessionalChatInterface />);

      // Open configuration and fill form
      await user.click(screen.getByText('Show Settings'));
      await user.type(screen.getByLabelText(/api key/i), 'sk-1234567890123456789012345678901234567890');
      await user.type(screen.getByLabelText(/model/i), 'gpt-4');
      await user.type(screen.getByLabelText(/developer message/i), 'Test context');
      await user.type(screen.getByLabelText(/your message/i), 'Hello AI');

      // Submit form
      await user.click(screen.getByRole('button', { name: /send message/i }));

      // Verify loading state appears
      expect(screen.getByText('Sending...')).toBeInTheDocument();
      expect(screen.getByText('AI is thinking...')).toBeInTheDocument();

      // Wait for response to complete
      await waitFor(() => {
        expect(screen.getByText('Hello world!')).toBeInTheDocument();
      });

      // Verify service was called with correct data
      expect(mockChatService.processStreamingChat).toHaveBeenCalledWith(
        {
          apiKey: 'sk-1234567890123456789012345678901234567890',
          model: 'gpt-4',
          developerMessage: 'Test context',
          userMessage: 'Hello AI',
        },
        expect.any(Function)
      );

      // Verify user message was cleared
      expect(screen.getByLabelText(/your message/i)).toHaveValue('');
    });

    it('integrates with real useChat hook for error handling', async () => {
      const user = userEvent.setup();
      
      // Mock service error
      mockChatService.processStreamingChat.mockRejectedValue(
        new Error('API key is invalid')
      );

      render(<ProfessionalChatInterface />);

      // Open configuration and fill form
      await user.click(screen.getByText('Show Settings'));
      await user.type(screen.getByLabelText(/api key/i), 'sk-invalid');
      await user.type(screen.getByLabelText(/your message/i), 'Test message');

      // Submit form
      await user.click(screen.getByRole('button', { name: /send message/i }));

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
        expect(screen.getByText('API key is invalid')).toBeInTheDocument();
      });

      // Verify loading state is cleared
      expect(screen.queryByText('Sending...')).not.toBeInTheDocument();
      expect(screen.queryByText('AI is thinking...')).not.toBeInTheDocument();
    });

    it('handles streaming response updates in real-time', async () => {
      const user = userEvent.setup();
      
      // Mock streaming response with multiple chunks
      mockChatService.processStreamingChat.mockImplementation(
        async (_, onChunk) => {
          if (onChunk) {
            onChunk('The ');
            await new Promise(resolve => setTimeout(resolve, 10));
            onChunk('quick ');
            await new Promise(resolve => setTimeout(resolve, 10));
            onChunk('brown ');
            await new Promise(resolve => setTimeout(resolve, 10));
            onChunk('fox');
          }
          return 'The quick brown fox';
        }
      );

      render(<ProfessionalChatInterface />);

      // Setup and submit
      await user.click(screen.getByText('Show Settings'));
      await user.type(screen.getByLabelText(/api key/i), 'sk-1234567890123456789012345678901234567890');
      await user.type(screen.getByLabelText(/your message/i), 'Tell me a story');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      // Wait for final response
      await waitFor(() => {
        expect(screen.getByText('The quick brown fox')).toBeInTheDocument();
      }, { timeout: 1000 });
    });
  });

  describe('Form Validation Integration', () => {
    it('validates form before calling service', async () => {
      const user = userEvent.setup();
      
      render(<ProfessionalChatInterface />);

      // Try to submit with empty form
      await user.click(screen.getByRole('button', { name: /send message/i }));

      // Verify validation errors appear
      expect(screen.getByText('Please enter a message')).toBeInTheDocument();
      
      // Verify service was not called
      expect(mockChatService.processStreamingChat).not.toHaveBeenCalled();
    });

    it('validates API key format before submission', async () => {
      const user = userEvent.setup();
      
      render(<ProfessionalChatInterface />);

      // Open config and enter invalid API key
      await user.click(screen.getByText('Show Settings'));
      await user.type(screen.getByLabelText(/api key/i), 'invalid');
      await user.type(screen.getByLabelText(/your message/i), 'Test');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      // Verify validation error
      expect(screen.getByText('API key must start with "sk-" and be at least 20 characters')).toBeInTheDocument();
      
      // Verify service was not called
      expect(mockChatService.processStreamingChat).not.toHaveBeenCalled();
    });
  });

  describe('Error Recovery Integration', () => {
    it('allows retry after error', async () => {
      const user = userEvent.setup();
      
      // First call fails, second succeeds
      mockChatService.processStreamingChat
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce('Success response');

      render(<ProfessionalChatInterface />);

      // Setup form
      await user.click(screen.getByText('Show Settings'));
      await user.type(screen.getByLabelText(/api key/i), 'sk-1234567890123456789012345678901234567890');
      await user.type(screen.getByLabelText(/your message/i), 'Test message');

      // First submission fails
      await user.click(screen.getByRole('button', { name: /send message/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      // Retry submission
      await user.type(screen.getByLabelText(/your message/i), 'Retry message');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      // Second submission succeeds
      await waitFor(() => {
        expect(screen.getByText('Success response')).toBeInTheDocument();
      });

      // Error should be cleared
      expect(screen.queryByText('Network error')).not.toBeInTheDocument();
    });
  });

  describe('Keyboard Shortcuts Integration', () => {
    it('submits form using Cmd+Enter with real hook', async () => {
      const user = userEvent.setup();
      
      mockChatService.processStreamingChat.mockResolvedValue('Keyboard shortcut response');

      render(<ProfessionalChatInterface />);

      // Setup form
      await user.click(screen.getByText('Show Settings'));
      await user.type(screen.getByLabelText(/api key/i), 'sk-1234567890123456789012345678901234567890');
      
      const messageInput = screen.getByLabelText(/your message/i);
      await user.type(messageInput, 'Test keyboard shortcut');
      
      // Use keyboard shortcut
      await user.keyboard('{Meta>}{Enter}{/Meta}');

      // Verify submission
      await waitFor(() => {
        expect(screen.getByText('Keyboard shortcut response')).toBeInTheDocument();
      });

      expect(mockChatService.processStreamingChat).toHaveBeenCalledWith(
        expect.objectContaining({
          userMessage: 'Test keyboard shortcut',
        }),
        expect.any(Function)
      );
    });
  });

  describe('State Management Integration', () => {
    it('maintains form state during submission', async () => {
      const user = userEvent.setup();
      
      // Mock slow response
      mockChatService.processStreamingChat.mockImplementation(
        async () => {
          await new Promise(resolve => setTimeout(resolve, 100));
          return 'Slow response';
        }
      );

      render(<ProfessionalChatInterface />);

      // Setup form
      await user.click(screen.getByText('Show Settings'));
      await user.type(screen.getByLabelText(/api key/i), 'sk-1234567890123456789012345678901234567890');
      await user.type(screen.getByLabelText(/developer message/i), 'Context message');
      await user.type(screen.getByLabelText(/your message/i), 'Test message');

      // Submit form
      await user.click(screen.getByRole('button', { name: /send message/i }));

      // During submission, verify form state
      expect(screen.getByDisplayValue('sk-1234567890123456789012345678901234567890')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Context message')).toBeInTheDocument();
      expect(screen.getByLabelText(/your message/i)).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.getByText('Slow response')).toBeInTheDocument();
      });

      // Verify API key and developer message are preserved
      expect(screen.getByDisplayValue('sk-1234567890123456789012345678901234567890')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Context message')).toBeInTheDocument();
      
      // User message should be cleared
      expect(screen.getByLabelText(/your message/i)).toHaveValue('');
    });
  });

  describe('Performance Integration', () => {
    it('handles rapid successive submissions gracefully', async () => {
      const user = userEvent.setup();
      
      // Mock responses
      mockChatService.processStreamingChat
        .mockResolvedValueOnce('Response 1')
        .mockResolvedValueOnce('Response 2');

      render(<ProfessionalChatInterface />);

      // Setup form
      await user.click(screen.getByText('Show Settings'));
      await user.type(screen.getByLabelText(/api key/i), 'sk-1234567890123456789012345678901234567890');

      // First submission
      await user.type(screen.getByLabelText(/your message/i), 'Message 1');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      // Wait for first response
      await waitFor(() => {
        expect(screen.getByText('Response 1')).toBeInTheDocument();
      });

      // Second submission
      await user.type(screen.getByLabelText(/your message/i), 'Message 2');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      // Wait for second response
      await waitFor(() => {
        expect(screen.getByText('Response 2')).toBeInTheDocument();
      });

      // Verify both service calls were made
      expect(mockChatService.processStreamingChat).toHaveBeenCalledTimes(2);
    });
  });
});
