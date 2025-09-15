import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ProfessionalChatInterface from '../ProfessionalChatInterface';
import { useChat } from '../../../../hooks/useChat';

// Mock the useChat hook
jest.mock('../../../../hooks/useChat');
const mockUseChat = useChat as jest.MockedFunction<typeof useChat>;

describe('ProfessionalChatInterface', () => {
  const mockSendChat = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseChat.mockReturnValue({
      message: '',
      loading: false,
      error: null,
      sendChat: mockSendChat,
    });
  });

  describe('Component Rendering', () => {
    it('renders the component with all main sections', () => {
      render(<ProfessionalChatInterface />);
      
      expect(screen.getByText('Configuration')).toBeInTheDocument();
      expect(screen.getByText('Show Settings')).toBeInTheDocument();
      expect(screen.getByLabelText(/your message/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
    });

    it('renders with custom className', () => {
      const { container } = render(<ProfessionalChatInterface className="custom-class" />);
      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('configuration section is collapsed by default', () => {
      render(<ProfessionalChatInterface />);
      
      expect(screen.queryByLabelText(/api key/i)).not.toBeInTheDocument();
      expect(screen.queryByLabelText(/model/i)).not.toBeInTheDocument();
    });
  });

  describe('Configuration Section', () => {
    it('toggles configuration section visibility', async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      const toggleButton = screen.getByText('Show Settings');
      
      // Initially hidden
      expect(screen.queryByLabelText(/api key/i)).not.toBeInTheDocument();
      
      // Show configuration
      await user.click(toggleButton);
      expect(screen.getByLabelText(/api key/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/model/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/developer message/i)).toBeInTheDocument();
      expect(screen.getByText('Hide Settings')).toBeInTheDocument();
      
      // Hide configuration
      await user.click(screen.getByText('Hide Settings'));
      expect(screen.queryByLabelText(/api key/i)).not.toBeInTheDocument();
      expect(screen.getByText('Show Settings')).toBeInTheDocument();
    });

    it('has proper ARIA attributes for accessibility', async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      const toggleButton = screen.getByText('Show Settings');
      expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
      expect(toggleButton).toHaveAttribute('aria-controls', 'config-section');
      
      await user.click(toggleButton);
      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
      expect(screen.getByTestId('config-section')).toHaveAttribute('id', 'config-section');
    });
  });

  describe('Form Validation', () => {
    beforeEach(async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      // Open configuration section
      await user.click(screen.getByText('Show Settings'));
    });

    it('validates required API key', async () => {
      const user = userEvent.setup();
      
      // Try to submit without API key
      await user.type(screen.getByLabelText(/your message/i), 'Test message');
      await user.click(screen.getByRole('button', { name: /send message/i }));
      
      expect(screen.getByText('API key is required')).toBeInTheDocument();
      expect(mockSendChat).not.toHaveBeenCalled();
    });

    it('validates API key format', async () => {
      const user = userEvent.setup();
      
      // Enter invalid API key
      await user.type(screen.getByLabelText(/api key/i), 'invalid-key');
      await user.type(screen.getByLabelText(/your message/i), 'Test message');
      await user.click(screen.getByRole('button', { name: /send message/i }));
      
      expect(screen.getByText('API key must start with "sk-" and be at least 20 characters')).toBeInTheDocument();
      expect(mockSendChat).not.toHaveBeenCalled();
    });

    it('validates required model', async () => {
      const user = userEvent.setup();
      
      // Clear model field
      const modelInput = screen.getByLabelText(/model/i);
      await user.clear(modelInput);
      
      await user.type(screen.getByLabelText(/api key/i), 'sk-1234567890123456789012345678901234567890');
      await user.type(screen.getByLabelText(/your message/i), 'Test message');
      await user.click(screen.getByRole('button', { name: /send message/i }));
      
      expect(screen.getByText('Model is required')).toBeInTheDocument();
      expect(mockSendChat).not.toHaveBeenCalled();
    });

    it('validates required user message', async () => {
      const user = userEvent.setup();
      
      await user.type(screen.getByLabelText(/api key/i), 'sk-1234567890123456789012345678901234567890');
      await user.click(screen.getByRole('button', { name: /send message/i }));
      
      expect(screen.getByText('Please enter a message')).toBeInTheDocument();
      expect(mockSendChat).not.toHaveBeenCalled();
    });

    it('validates message length limit', async () => {
      const user = userEvent.setup();
      
      const longMessage = 'a'.repeat(4001);
      await user.type(screen.getByLabelText(/api key/i), 'sk-1234567890123456789012345678901234567890');
      await user.type(screen.getByLabelText(/your message/i), longMessage);
      await user.click(screen.getByRole('button', { name: /send message/i }));
      
      expect(screen.getByText('Message exceeds maximum length of 4000 characters')).toBeInTheDocument();
      expect(mockSendChat).not.toHaveBeenCalled();
    });

    it('clears field errors when user starts typing', async () => {
      const user = userEvent.setup();
      
      // Trigger API key error
      await user.type(screen.getByLabelText(/your message/i), 'Test message');
      await user.click(screen.getByRole('button', { name: /send message/i }));
      expect(screen.getByText('API key is required')).toBeInTheDocument();
      
      // Start typing in API key field
      await user.type(screen.getByLabelText(/api key/i), 's');
      expect(screen.queryByText('API key is required')).not.toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    beforeEach(async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      // Open configuration and fill valid data
      await user.click(screen.getByText('Show Settings'));
      await user.type(screen.getByLabelText(/api key/i), 'sk-1234567890123456789012345678901234567890');
      await user.type(screen.getByLabelText(/developer message/i), 'Test developer message');
    });

    it('submits form with valid data', async () => {
      const user = userEvent.setup();
      
      await user.type(screen.getByLabelText(/your message/i), 'Test user message');
      await user.click(screen.getByRole('button', { name: /send message/i }));
      
      expect(mockSendChat).toHaveBeenCalledWith({
        apiKey: 'sk-1234567890123456789012345678901234567890',
        model: 'gpt-4',
        developerMessage: 'Test developer message',
        userMessage: 'Test user message',
      });
    });

    it('clears user message after successful submission', async () => {
      const user = userEvent.setup();
      mockSendChat.mockResolvedValue('Success');
      
      const messageInput = screen.getByLabelText(/your message/i);
      await user.type(messageInput, 'Test user message');
      await user.click(screen.getByRole('button', { name: /send message/i }));
      
      await waitFor(() => {
        expect(messageInput).toHaveValue('');
      });
    });

    it('supports keyboard shortcut (Cmd+Enter)', async () => {
      const user = userEvent.setup();
      
      const messageInput = screen.getByLabelText(/your message/i);
      await user.type(messageInput, 'Test user message');
      await user.keyboard('{Meta>}{Enter}{/Meta}');
      
      expect(mockSendChat).toHaveBeenCalled();
    });

    it('supports keyboard shortcut (Ctrl+Enter)', async () => {
      const user = userEvent.setup();
      
      const messageInput = screen.getByLabelText(/your message/i);
      await user.type(messageInput, 'Test user message');
      await user.keyboard('{Control>}{Enter}{/Control}');
      
      expect(mockSendChat).toHaveBeenCalled();
    });
  });

  describe('Loading States', () => {
    it('shows loading state during submission', () => {
      mockUseChat.mockReturnValue({
        message: '',
        loading: true,
        error: null,
        sendChat: mockSendChat,
      });
      
      render(<ProfessionalChatInterface />);
      
      expect(screen.getByText('Sending...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sending/i })).toBeDisabled();
      expect(screen.getByText('AI is thinking...')).toBeInTheDocument();
      expect(screen.getByLabelText(/your message/i)).toBeDisabled();
    });

    it('disables submit button when message is empty', () => {
      render(<ProfessionalChatInterface />);
      
      const submitButton = screen.getByRole('button', { name: /send message/i });
      expect(submitButton).toBeDisabled();
    });

    it('enables submit button when message has content', async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      const submitButton = screen.getByRole('button', { name: /send message/i });
      const messageInput = screen.getByLabelText(/your message/i);
      
      await user.type(messageInput, 'Test message');
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('displays error messages', () => {
      mockUseChat.mockReturnValue({
        message: '',
        loading: false,
        error: 'Test error message',
        sendChat: mockSendChat,
      });
      
      render(<ProfessionalChatInterface />);
      
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });

    it('transforms API key errors', () => {
      mockUseChat.mockReturnValue({
        message: '',
        loading: false,
        error: 'Invalid API key provided',
        sendChat: mockSendChat,
      });
      
      render(<ProfessionalChatInterface />);
      
      expect(screen.getByText('Invalid API key. Please check your key and try again')).toBeInTheDocument();
    });

    it('transforms timeout errors', () => {
      mockUseChat.mockReturnValue({
        message: '',
        loading: false,
        error: 'Request timed out after 30 seconds',
        sendChat: mockSendChat,
      });
      
      render(<ProfessionalChatInterface />);
      
      expect(screen.getByText('Request timed out. Please check your connection and try again')).toBeInTheDocument();
    });

    it('transforms rate limit errors', () => {
      mockUseChat.mockReturnValue({
        message: '',
        loading: false,
        error: 'Rate limit exceeded',
        sendChat: mockSendChat,
      });
      
      render(<ProfessionalChatInterface />);
      
      expect(screen.getByText('Rate limit exceeded. Please wait a moment and try again')).toBeInTheDocument();
    });

    it('transforms server errors', () => {
      mockUseChat.mockReturnValue({
        message: '',
        loading: false,
        error: 'HTTP error! status: 500',
        sendChat: mockSendChat,
      });
      
      render(<ProfessionalChatInterface />);
      
      expect(screen.getByText('Server error occurred. Please try again later')).toBeInTheDocument();
    });

    it('transforms response format errors', () => {
      mockUseChat.mockReturnValue({
        message: '',
        loading: false,
        error: 'No response body received from server',
        sendChat: mockSendChat,
      });
      
      render(<ProfessionalChatInterface />);
      
      expect(screen.getByText('Unexpected response format. Please try again')).toBeInTheDocument();
    });
  });

  describe('Response Display', () => {
    it('displays streaming response', () => {
      mockUseChat.mockReturnValue({
        message: 'This is a test response from the AI',
        loading: false,
        error: null,
        sendChat: mockSendChat,
      });
      
      render(<ProfessionalChatInterface />);
      
      expect(screen.getByText('Response')).toBeInTheDocument();
      expect(screen.getByText('This is a test response from the AI')).toBeInTheDocument();
    });

    it('preserves whitespace in response', () => {
      mockUseChat.mockReturnValue({
        message: 'Line 1\n\nLine 3 with  spaces',
        loading: false,
        error: null,
        sendChat: mockSendChat,
      });
      
      render(<ProfessionalChatInterface />);
      
      // Check that the response section exists and has the whitespace class
      const responseSection = screen.getByText('Response').closest('div');
      const responseContent = responseSection?.querySelector('.whitespace-pre-wrap');
      expect(responseContent).toBeInTheDocument();
      expect(responseContent).toHaveTextContent('Line 1\n\nLine 3 with  spaces');
    });
  });

  describe('Textarea Auto-resize', () => {
    it('auto-resizes textarea based on content', async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      const textarea = screen.getByLabelText(/your message/i) as HTMLTextAreaElement;
      
      // Mock scrollHeight to simulate content growth
      Object.defineProperty(textarea, 'scrollHeight', {
        configurable: true,
        get: function() { return 150; }
      });
      
      await user.type(textarea, 'This is a long message that should cause the textarea to resize');
      
      // The useEffect should have set the height
      expect(textarea.style.height).toBe('150px');
    });
  });

  describe('Character Counter', () => {
    it('displays character count', async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      const textarea = screen.getByLabelText(/your message/i);
      await user.type(textarea, 'Hello');
      
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('/4000')).toBeInTheDocument();
    });

    it('updates character count as user types', async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      const textarea = screen.getByLabelText(/your message/i);
      
      await user.type(textarea, 'Hello World');
      expect(screen.getByText('11')).toBeInTheDocument();
      expect(screen.getByText('/4000')).toBeInTheDocument();
      
      await user.type(textarea, '!');
      expect(screen.getByText('12')).toBeInTheDocument();
      expect(screen.getByText('/4000')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels and ARIA attributes', () => {
      render(<ProfessionalChatInterface />);
      
      const messageTextarea = screen.getByLabelText(/your message/i);
      expect(messageTextarea).toHaveAttribute('required');
      expect(messageTextarea).toHaveAttribute('aria-invalid', 'false');
    });

    it('announces errors to screen readers', async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      // Open config and trigger validation error
      await user.click(screen.getByText('Show Settings'));
      await user.type(screen.getByLabelText(/your message/i), 'Test');
      await user.click(screen.getByRole('button', { name: /send message/i }));
      
      const errorMessage = screen.getByText('API key is required');
      expect(errorMessage).toHaveAttribute('role', 'alert');
    });

    it('has proper focus management', async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      // Tab through interactive elements
      await user.tab();
      expect(screen.getByText('Show Settings')).toHaveFocus();
      
      await user.tab();
      expect(screen.getByLabelText(/your message/i)).toHaveFocus();
      
      await user.tab();
      expect(screen.getByRole('button', { name: /send message/i })).toHaveFocus();
    });
  });

  describe('Responsive Design', () => {
    it('applies responsive grid classes', async () => {
      const user = userEvent.setup();
      render(<ProfessionalChatInterface />);
      
      await user.click(screen.getByText('Show Settings'));
      
      const gridContainer = screen.getByLabelText(/api key/i).closest('.grid');
      expect(gridContainer).toHaveClass('grid-cols-1', 'md:grid-cols-2');
    });
  });
});
