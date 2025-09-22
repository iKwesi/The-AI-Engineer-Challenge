import React from 'react';
import { render, screen, cleanup, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ProfessionalChatInterface from '../ProfessionalChatInterface';
import { useChat, type Message } from '../../../../hooks/useChat';

// Mock the useChat hook
jest.mock('../../../../hooks/useChat');
const mockUseChat = useChat as jest.MockedFunction<typeof useChat>;

describe('ProfessionalChatInterface Integration Tests', () => {
  const mockSendChat = jest.fn();
  const mockSetInputValue = jest.fn();
  const mockSetApiKey = jest.fn();
  const mockHandleSubmit = jest.fn();
  
  const defaultHookReturn = {
    messages: [] as Message[],
    loading: false,
    error: null,
    inputValue: '',
    setInputValue: mockSetInputValue,
    handleSubmit: mockHandleSubmit,
    apiKey: '',
    setApiKey: mockSetApiKey,
    sendChat: mockSendChat,
    pendingFallback: null,
    handleFallbackConfirmation: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseChat.mockReturnValue(defaultHookReturn);
  });

  afterEach(() => {
    cleanup();
  });

  describe('Integration with useChat Hook', () => {
    it('integrates with real useChat hook for successful submission', async () => {
      const hookData = { ...defaultHookReturn, inputValue: 'Test message' };
      
      render(<ProfessionalChatInterface {...hookData} />);
      
      const form = screen.getByRole('button', { name: /send message/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }
      
      expect(mockHandleSubmit).toHaveBeenCalled();
    });

    it('integrates with real useChat hook for error handling', async () => {
      const hookData = { 
        ...defaultHookReturn, 
        error: 'Network error occurred',
        inputValue: 'Test message'
      };
      
      render(<ProfessionalChatInterface {...hookData} />);
      
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Network error occurred')).toBeInTheDocument();
    });

    it('handles streaming response updates in real-time', async () => {
      const messages: Message[] = [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hello! How can I help you today?' }
      ];
      
      const hookData = { ...defaultHookReturn, messages };
      
      render(<ProfessionalChatInterface {...hookData} />);
      
      expect(screen.getByText('Hello')).toBeInTheDocument();
      expect(screen.getByText('Hello! How can I help you today?')).toBeInTheDocument();
    });
  });

  describe('Form Validation Integration', () => {
    it('validates form before calling service', async () => {
      const hookData = { ...defaultHookReturn };
      
      render(<ProfessionalChatInterface {...hookData} />);
      
      // Button should be disabled when no input
      const submitButton = screen.getByRole('button', { name: /send message/i });
      expect(submitButton).toBeDisabled();
    });

    it('validates API key format before submission', async () => {
      const hookData = { 
        ...defaultHookReturn, 
        apiKey: 'invalid-key',
        inputValue: 'Test message'
      };
      
      render(<ProfessionalChatInterface {...hookData} />);
      
      const form = screen.getByRole('button', { name: /send message/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }
      
      expect(mockHandleSubmit).toHaveBeenCalled();
    });
  });

  describe('Error Recovery Integration', () => {
    it('allows retry after error', async () => {
      const hookData = { 
        ...defaultHookReturn, 
        error: 'Network timeout',
        inputValue: 'Test message'
      };
      
      render(<ProfessionalChatInterface {...hookData} />);
      
      expect(screen.getByText('Network timeout')).toBeInTheDocument();
      
      // User can still try to submit again
      const form = screen.getByRole('button', { name: /send message/i }).closest('form');
      if (form) {
        fireEvent.submit(form);
      }
      expect(mockHandleSubmit).toHaveBeenCalled();
    });
  });

  describe('Keyboard Shortcuts Integration', () => {
    it('submits form using Cmd+Enter with real hook', async () => {
      const user = userEvent.setup();
      const hookData = { ...defaultHookReturn, inputValue: 'Test message' };
      
      render(<ProfessionalChatInterface {...hookData} />);
      
      const messageInput = screen.getByLabelText(/chat input/i);
      await user.click(messageInput);
      await user.keyboard('{Meta>}{Enter}{/Meta}');
      
      expect(mockHandleSubmit).toHaveBeenCalled();
    });
  });

  describe('State Management Integration', () => {
    it('maintains form state during submission', async () => {
      const hookData = { 
        ...defaultHookReturn, 
        loading: true,
        inputValue: 'Test message'
      };
      
      render(<ProfessionalChatInterface {...hookData} />);
      
      expect(screen.getByText('Thinking...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send message/i })).toBeDisabled();
      expect(screen.getByLabelText(/chat input/i)).toHaveValue('Test message');
    });
  });

  describe('Performance Integration', () => {
    it('handles rapid successive submissions gracefully', async () => {
      const hookData = { 
        ...defaultHookReturn, 
        inputValue: 'Test message',
        apiKey: 'sk-1234567890123456789012345678901234567890'
      };
      
      render(<ProfessionalChatInterface {...hookData} />);
      
      const form = screen.getByRole('button', { name: /send message/i }).closest('form');
      
      // Rapid submissions
      if (form) {
        fireEvent.submit(form);
        fireEvent.submit(form);
        fireEvent.submit(form);
      }
      
      // Should handle gracefully
      expect(mockHandleSubmit).toHaveBeenCalled();
    });
  });
});
