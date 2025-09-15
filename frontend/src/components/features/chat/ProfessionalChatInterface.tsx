import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../../../hooks/useChat';
import { ChatRequest } from '../../../services/chatService';
import Button from '../../ui/Button';
import Input from '../../ui/Input';
import Card from '../../ui/Card';

export interface ProfessionalChatInterfaceProps {
  className?: string;
}

interface FormData {
  apiKey: string;
  model: string;
  developerMessage: string;
  userMessage: string;
}

interface FormErrors {
  apiKey?: string;
  model?: string;
  developerMessage?: string;
  userMessage?: string;
}

export const ProfessionalChatInterface: React.FC<ProfessionalChatInterfaceProps> = ({
  className = '',
}) => {
  const { message, loading, error, sendChat } = useChat();
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    apiKey: '',
    model: 'gpt-4',
    developerMessage: '',
    userMessage: '',
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [formData.userMessage]);

  const validateForm = (): boolean => {
    const errors: FormErrors = {};

    // API Key validation
    if (!formData.apiKey.trim()) {
      errors.apiKey = 'API key is required';
    } else if (!formData.apiKey.startsWith('sk-') || formData.apiKey.length < 20) {
      errors.apiKey = 'API key must start with "sk-" and be at least 20 characters';
    }

    // Model validation
    if (!formData.model.trim()) {
      errors.model = 'Model is required';
    }

    // User message validation
    if (!formData.userMessage.trim()) {
      errors.userMessage = 'Please enter a message';
    } else if (formData.userMessage.length > 4000) {
      errors.userMessage = 'Message exceeds maximum length of 4000 characters';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (field: keyof FormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value,
    }));
    
    // Clear error for this field when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      const chatRequest: ChatRequest = {
        apiKey: formData.apiKey,
        model: formData.model,
        developerMessage: formData.developerMessage,
        userMessage: formData.userMessage,
      };

      await sendChat(chatRequest);
      
      // Clear user message after successful submission
      setFormData(prev => ({
        ...prev,
        userMessage: '',
      }));
    } catch {
      // Error is handled by useChat hook
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit(e as React.FormEvent);
    }
  };

  const getErrorMessage = (error: string): string => {
    if (error.includes('Invalid API key')) {
      return 'Invalid API key. Please check your key and try again';
    }
    if (error.includes('timeout') || error.includes('timed out')) {
      return 'Request timed out. Please check your connection and try again';
    }
    if (error.includes('rate limit')) {
      return 'Rate limit exceeded. Please wait a moment and try again';
    }
    if (error.includes('HTTP error! status: 5')) {
      return 'Server error occurred. Please try again later';
    }
    if (error.includes('No response body')) {
      return 'Unexpected response format. Please try again';
    }
    return error;
  };

  const containerClasses = [
    'max-w-4xl mx-auto p-4 space-y-6',
    className,
  ].join(' ').trim();

  return (
    <div className={containerClasses}>
      {/* Configuration Section */}
      <Card className="transition-all duration-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text-primary">Configuration</h2>
          <Button
            variant="secondary"
            onClick={() => setIsConfigOpen(!isConfigOpen)}
            className="text-sm"
            aria-expanded={isConfigOpen}
            aria-controls="config-section"
          >
            {isConfigOpen ? 'Hide' : 'Show'} Settings
          </Button>
        </div>
        
        {isConfigOpen && (
          <div id="config-section" data-testid="config-section" className="space-y-4 border-t border-border pt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                type="password"
                label="API Key"
                placeholder="sk-..."
                value={formData.apiKey}
                onChange={handleInputChange('apiKey')}
                error={!!formErrors.apiKey}
                errorMessage={formErrors.apiKey}
                required
                name="apiKey"
              />
              <Input
                type="text"
                label="Model"
                placeholder="gpt-4"
                value={formData.model}
                onChange={handleInputChange('model')}
                error={!!formErrors.model}
                errorMessage={formErrors.model}
                required
                name="model"
              />
            </div>
            <div>
              <Input
                type="text"
                label="Developer Message (Optional)"
                placeholder="Additional context for the AI..."
                value={formData.developerMessage}
                onChange={handleInputChange('developerMessage')}
                name="developerMessage"
              />
            </div>
          </div>
        )}
      </Card>

      {/* Chat Interface */}
      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label 
              htmlFor="user-message"
              className="block text-sm font-medium text-text-primary mb-2"
            >
              Your Message
              <span className="text-red-500 ml-1">*</span>
            </label>
            <textarea
              ref={textareaRef}
              id="user-message"
              name="userMessage"
              placeholder="Type your message here... (Cmd/Ctrl + Enter to send)"
              value={formData.userMessage}
              onChange={handleInputChange('userMessage')}
              onKeyDown={handleKeyDown}
              disabled={loading || isSubmitting}
              required
              className={`w-full px-3 py-2 border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-1 resize-none min-h-[100px] max-h-[300px] ${
                formErrors.userMessage 
                  ? 'border-red-500 bg-red-50 text-text-primary focus:border-red-500 focus:ring-red-500'
                  : 'border-border bg-container text-text-primary focus:border-accent'
              } ${
                (loading || isSubmitting) ? 'opacity-50 cursor-not-allowed bg-gray-100' : ''
              }`}
              aria-invalid={!!formErrors.userMessage}
              aria-describedby={formErrors.userMessage ? 'user-message-error' : undefined}
            />
            {formErrors.userMessage && (
              <p 
                id="user-message-error"
                className="mt-1 text-sm text-red-600"
                role="alert"
              >
                {formErrors.userMessage}
              </p>
            )}
            <div className="mt-1 text-xs text-gray-500 flex justify-between">
              <span>Cmd/Ctrl + Enter to send</span>
              <span>{formData.userMessage.length}/4000</span>
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              type="submit"
              onClick={() => {}} // Required by Button component, but form submission is handled by onSubmit
              disabled={loading || isSubmitting || !formData.userMessage.trim()}
              className="min-w-[120px]"
            >
              {loading || isSubmitting ? 'Sending...' : 'Send Message'}
            </Button>
          </div>
        </form>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg 
                className="h-5 w-5 text-red-400" 
                viewBox="0 0 20 20" 
                fill="currentColor"
                aria-hidden="true"
              >
                <path 
                  fillRule="evenodd" 
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" 
                  clipRule="evenodd" 
                />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="mt-1 text-sm text-red-700">{getErrorMessage(error)}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Response Display */}
      {(message || loading) && (
        <Card>
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-text-primary">Response</h3>
            
            {loading && (
              <div className="flex items-center space-x-2 text-gray-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent"></div>
                <span className="text-sm">AI is thinking...</span>
              </div>
            )}
            
            {message && (
              <div className="bg-assistant-bubble rounded-lg p-4">
                <div className="whitespace-pre-wrap text-text-primary leading-relaxed">
                  {message}
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default ProfessionalChatInterface;
