"use client";

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { ArrowUp, Loader, AlertCircle, Bot, User, Settings, KeyRound, ChevronDown, Youtube, FileText, X } from 'lucide-react';
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { Avatar, AvatarFallback } from "@/components/ui/Avatar";
import { Label } from "@/components/ui/Label";
import { cn } from '@/lib/utils';
import { type Message, type FallbackRequest } from '@/hooks/useChat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { hasYouTubeUrls, detectYouTubeUrls, processYouTubeUrl } from '@/services/documentService';

// Helper function to detect if citations are from YouTube content
const isYouTubeContent = (citations: any[]): boolean => {
  return citations.some(citation => 
    citation.content_preview?.includes('=== YouTube Video:') ||
    citation.content_preview?.includes('=== Transcript ===') ||
    citation.document_name === 'unknown' && citation.content_preview?.includes('Channel:')
  );
};

export interface SimpleChatInterfaceProps {
  messages: Message[];
  loading: boolean;
  error: string | null;
  inputValue: string;
  setInputValue: (value: string) => void;
  handleSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  apiKey: string;
  setApiKey: (key: string) => void;
  model?: string;
  setModel?: (model: string) => void;
  pendingFallback?: FallbackRequest | null;
  handleFallbackConfirmation?: (useGeneralKnowledge: boolean) => void;
}

const MessageBubble: React.FC<{ 
  message: Message; 
  onFallbackConfirm?: (useGeneralKnowledge: boolean) => void;
  pendingFallback?: boolean;
}> = ({ message, onFallbackConfirm, pendingFallback }) => {
  const isUser = message.role === 'user';
  
  // Preprocess content to convert various math notations to LaTeX
  const preprocessMathContent = (content: string): string => {
    if (isUser) return content;
    
    let processed = content;
    
    // Convert square bracket notation to LaTeX delimiters
    processed = processed.replace(/\[\s*([^[\]]+?)\s*\]/g, (match, mathContent) => {
      const trimmed = mathContent.trim();
      if (/[=+\-*/^_\\]|frac|sqrt|sum|int|alpha|beta|gamma|delta|theta|pi|sigma|omega|cdot|times|div|\d+[a-z]|\w+\s*=/.test(trimmed)) {
        return `$$${trimmed}$$`;
      }
      return match;
    });
    
    // Convert parentheses notation to LaTeX delimiters
    processed = processed.replace(/\(\s*([^()]+?)\s*\)/g, (match, mathContent) => {
      const trimmed = mathContent.trim();
      if (/\\[a-zA-Z]+|[=+\-*/^_]|frac|sqrt|sum|int|alpha|beta|gamma|delta|theta|pi|sigma|omega|cdot|times|div|\d+[a-z]|\w+\s*=/.test(trimmed)) {
        return `$${trimmed}$`;
      }
      return match;
    });
    
    return processed;
  };

  return (
    <div className={cn("flex items-start gap-3 w-full", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <Avatar className="w-8 h-8 border">
          <AvatarFallback><Bot className="w-5 h-5" /></AvatarFallback>
        </Avatar>
      )}
      <div
        className={cn(
          "max-w-xl rounded-lg px-4 py-3 shadow-soft",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-secondary text-secondary-foreground"
        )}
      >
        {isUser ? (
          // User messages: plain text with whitespace preservation
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          // AI responses: markdown rendering with professional formatting
          <div className="text-sm max-w-none">
            {/* Context indicator */}
            {message.usedContext !== undefined && (
              <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
                <FileText className="w-3 h-3" />
                <span>
                  {message.usedContext ? 'Using document context' : 'Using general knowledge'}
                </span>
                {message.confidenceScore !== undefined && (
                  <span className="ml-2 px-1.5 py-0.5 bg-muted rounded text-xs">
                    {(message.confidenceScore * 100).toFixed(1)}% confidence
                  </span>
                )}
              </div>
            )}
            
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[[rehypeKatex, { strict: false, throwOnError: false }]]}
              components={{
                h3: ({ children, ...props }) => (
                  <h3 className="text-base font-semibold mt-4 mb-2 first:mt-0 text-foreground" {...props}>
                    {children}
                  </h3>
                ),
                h2: ({ children, ...props }) => (
                  <h2 className="text-lg font-semibold mt-4 mb-2 first:mt-0 text-foreground" {...props}>
                    {children}
                  </h2>
                ),
                h1: ({ children, ...props }) => (
                  <h1 className="text-xl font-bold mt-4 mb-3 first:mt-0 text-foreground" {...props}>
                    {children}
                  </h1>
                ),
                p: ({ children, ...props }) => (
                  <p className="mb-4 last:mb-0 leading-relaxed text-foreground" {...props}>
                    {children}
                  </p>
                ),
                ul: ({ children, ...props }) => (
                  <ul className="ml-6 mb-4 last:mb-0 space-y-1 list-disc" {...props}>
                    {children}
                  </ul>
                ),
                ol: ({ children, ...props }) => (
                  <ol className="ml-6 mb-4 last:mb-0 space-y-1 list-decimal" {...props}>
                    {children}
                  </ol>
                ),
                li: ({ children, ...props }) => (
                  <li className="mb-1 leading-relaxed text-foreground" {...props}>
                    {children}
                  </li>
                ),
                code: ({ children, className, ...props }) => {
                  const isInline = !className?.includes('language-');
                  return isInline ? (
                    <code className="bg-muted/60 px-1.5 py-0.5 rounded text-xs font-mono text-foreground border" {...props}>
                      {children}
                    </code>
                  ) : (
                    <code className="block bg-muted/80 p-3 rounded-md text-xs font-mono overflow-x-auto text-foreground border" {...props}>
                      {children}
                    </code>
                  );
                },
                pre: ({ children, ...props }) => (
                  <pre className="bg-muted/80 p-3 rounded-md text-xs font-mono overflow-x-auto mb-4 last:mb-0 border" {...props}>
                    {children}
                  </pre>
                ),
                strong: ({ children, ...props }) => (
                  <strong className="font-semibold text-foreground" {...props}>
                    {children}
                  </strong>
                ),
                em: ({ children, ...props }) => (
                  <em className="italic text-foreground" {...props}>
                    {children}
                  </em>
                ),
                blockquote: ({ children, ...props }) => (
                  <blockquote className="border-l-4 border-muted-foreground/30 pl-4 my-4 italic text-muted-foreground" {...props}>
                    {children}
                  </blockquote>
                ),
                hr: (props) => (
                  <hr className="my-6 border-muted-foreground/20" {...props} />
                ),
                table: ({ children, ...props }) => (
                  <div className="overflow-x-auto my-4">
                    <table className="min-w-full border-collapse border border-muted-foreground/20" {...props}>
                      {children}
                    </table>
                  </div>
                ),
                th: ({ children, ...props }) => (
                  <th className="border border-muted-foreground/20 px-3 py-2 bg-muted/50 font-semibold text-left" {...props}>
                    {children}
                  </th>
                ),
                td: ({ children, ...props }) => (
                  <td className="border border-muted-foreground/20 px-3 py-2" {...props}>
                    {children}
                  </td>
                ),
              }}
            >
              {preprocessMathContent(message.content)}
            </ReactMarkdown>

            {/* Citations - Skip for YouTube content */}
            {message.citations && message.citations.length > 0 && !isYouTubeContent(message.citations) && (
              <div className="mt-3 pt-3 border-t border-muted-foreground/20">
                <div className="text-xs text-muted-foreground mb-2">Sources:</div>
                <div className="space-y-1">
                  {message.citations.map((citation, index) => (
                    <div key={index} className="text-xs bg-muted/50 rounded p-2">
                      <div className="font-medium">{citation.document_name}</div>
                      <div className="text-muted-foreground truncate">
                        {citation.content_preview}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Fallback confirmation buttons */}
            {pendingFallback && onFallbackConfirm && (
              <div className="mt-3 pt-3 border-t border-muted-foreground/20">
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => onFallbackConfirm(true)}
                    className="text-xs"
                  >
                    Use General Knowledge
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onFallbackConfirm(false)}
                    className="text-xs"
                  >
                    Stay in Document Mode
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      {isUser && (
        <Avatar className="w-8 h-8 border">
          <AvatarFallback><User className="w-5 h-5" /></AvatarFallback>
        </Avatar>
      )}
    </div>
  );
};

const LoadingIndicator: React.FC = () => (
  <div className="flex justify-center items-center p-4">
    <div className="flex items-center gap-2 text-muted-foreground">
      <Loader className="w-5 h-5 animate-spin" />
      <span>Thinking...</span>
    </div>
  </div>
);

const YouTubeDetectionAlert: React.FC<{ 
  urls: string[], 
  onProcess: (url: string) => void,
  onDismiss: () => void,
  isProcessing: boolean 
}> = ({ urls, onProcess, onDismiss, isProcessing }) => (
  <Alert className="border-blue-200 bg-blue-50 text-blue-800">
    <Youtube className="h-4 w-4 text-blue-600" />
    <AlertTitle>YouTube URL Detected!</AlertTitle>
    <AlertDescription className="space-y-2">
      <p>Found YouTube URL(s) in your message. Would you like to process the video content?</p>
      <div className="flex flex-wrap gap-2">
        {urls.map((url, index) => (
          <Button
            key={index}
            size="sm"
            variant="outline"
            onClick={() => onProcess(url)}
            disabled={isProcessing}
            className="text-blue-700 border-blue-300 hover:bg-blue-100"
          >
            {isProcessing ? (
              <>
                <Loader className="w-3 h-3 animate-spin mr-1" />
                Processing...
              </>
            ) : (
              <>
                <Youtube className="w-3 h-3 mr-1" />
                Process Video
              </>
            )}
          </Button>
        ))}
        <Button
          size="sm"
          variant="ghost"
          onClick={onDismiss}
          disabled={isProcessing}
          className="text-blue-700 hover:bg-blue-100"
        >
          <X className="w-3 h-3 mr-1" />
          Dismiss
        </Button>
      </div>
    </AlertDescription>
  </Alert>
);

const SimpleChatInterface: React.FC<SimpleChatInterfaceProps> = ({
  messages,
  loading,
  error,
  inputValue,
  setInputValue,
  handleSubmit,
  apiKey,
  setApiKey,
  model = "gpt-4.1-mini",
  setModel = () => {},
  pendingFallback,
  handleFallbackConfirmation,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [youtubeDetection, setYoutubeDetection] = useState<{
    urls: string[];
    show: boolean;
  }>({ urls: [], show: false });
  const [isProcessingYouTube, setIsProcessingYouTube] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Track if textarea is multi-line
  const isMultiLine = (inputValue && inputValue.includes('\n')) || (textareaRef.current && textareaRef.current.scrollHeight > textareaRef.current.clientHeight);

  // Detect YouTube URLs in input
  useEffect(() => {
    if (inputValue && hasYouTubeUrls(inputValue)) {
      const urls = detectYouTubeUrls(inputValue);
      setYoutubeDetection({ urls, show: true });
    } else {
      setYoutubeDetection({ urls: [], show: false });
    }
  }, [inputValue]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${scrollHeight}px`;
    }
  }, [inputValue]);
  
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      const form = event.currentTarget.form;
      if (form) {
        const syntheticEvent = {
          preventDefault: () => {},
          currentTarget: form,
        } as React.FormEvent<HTMLFormElement>;
        handleSubmit(syntheticEvent);
      }
    }
  };

  // Handle Enter key in configuration inputs to collapse dropdown
  const handleConfigKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      setIsDropdownOpen(false);
    }
  };

  // Handle Done button click to collapse dropdown
  const handleDoneClick = () => {
    setIsDropdownOpen(false);
  };

  // Handle YouTube processing
  const handleYouTubeProcess = useCallback(async (url: string) => {
    if (!apiKey?.trim()) {
      return;
    }

    setIsProcessingYouTube(true);
    try {
      await processYouTubeUrl(url, apiKey);
      setYoutubeDetection({ urls: [], show: false });
      // Optionally show success message or refresh document mode status
    } catch (error) {
      console.error('YouTube processing failed:', error);
    } finally {
      setIsProcessingYouTube(false);
    }
  }, [apiKey]);

  // Check if we should show the welcome screen (no messages yet)
  const showWelcomeScreen = !messages || messages.length === 0;

  if (showWelcomeScreen) {
    // Welcome screen layout - centered like ChatGPT
    return (
      <div className="flex flex-col h-full bg-background text-foreground">
        <header className="border-b bg-card p-4 shadow-sm">
          <div className="w-full flex items-center justify-between px-4">
            <h1 className="text-xl font-semibold">LeChat AI</h1>
            <div className="relative" ref={dropdownRef}>
              <Button
                variant="ghost"
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center gap-2 text-sm"
              >
                <Settings className="w-4 h-4" />
                Configuration
                <ChevronDown className={cn("w-4 h-4 transition-transform", isDropdownOpen && "rotate-180")} />
              </Button>
              
              {isDropdownOpen && (
                <div className="absolute right-0 top-full mt-2 w-80 bg-card border rounded-lg shadow-lg z-50 p-4 space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="api-key-welcome">API Key</Label>
                    <div className="flex items-center gap-2">
                       <KeyRound className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      <Input
                        id="api-key-welcome"
                        type="password"
                        placeholder="Enter your API key"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        onKeyDown={handleConfigKeyDown}
                        className="rounded-md w-64"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="model-welcome">Model</Label>
                    <div className="flex items-center gap-2">
                      <span className="w-4 h-4 flex-shrink-0"></span>
                      <Input 
                        id="model-welcome" 
                        type="text" 
                        value={model} 
                        onChange={(e) => setModel(e.target.value)}
                        onKeyDown={handleConfigKeyDown}
                        placeholder="Enter model name"
                        className="rounded-md w-64" 
                      />
                    </div>
                  </div>
                  <div className="flex justify-end pt-2">
                    <Button
                      onClick={handleDoneClick}
                      size="sm"
                      className="text-sm"
                    >
                      Done
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Centered welcome content */}
        <div className="flex-grow flex flex-col items-center justify-center p-4">
          <div className="max-w-2xl w-full text-center space-y-8">
            <h2 className="text-3xl font-semibold text-foreground">
              Welcome to LeChat AI
            </h2>
            
            <p className="text-lg text-muted-foreground">
              Please enter your API key in the configuration to chat. You can upload your documents to enable RAG and chat with your documents.
            </p>
            
            {/* Show loading state */}
            {loading && <LoadingIndicator />}
            
            {/* Show error state */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* YouTube Detection Alert */}
            {youtubeDetection.show && (
              <YouTubeDetectionAlert
                urls={youtubeDetection.urls}
                onProcess={handleYouTubeProcess}
                onDismiss={() => setYoutubeDetection({ urls: [], show: false })}
                isProcessing={isProcessingYouTube}
              />
            )}
            
            <form onSubmit={handleSubmit} className="w-full">
              <div className={cn(
                "relative border border-input focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 flex items-center",
                isMultiLine ? "rounded-lg items-end" : "rounded-full"
              )}>
                <textarea
                  ref={textareaRef}
                  rows={1}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="How can I help you today?"
                  className="w-full resize-none bg-transparent shadow-none focus-visible:outline-none p-2.5 pr-12 text-base md:text-sm"
                  aria-label="Chat input"
                />
                <Button 
                  type="submit" 
                  size="icon" 
                  disabled={loading || !inputValue || !inputValue.trim()} 
                  aria-label="Send message"
                  className={cn(
                    "absolute right-2 h-8 w-8 flex-shrink-0 rounded-full",
                    isMultiLine ? "bottom-2" : "top-1/2 -translate-y-1/2",
                    // Override cursor behavior for chat submit button specifically
                    (loading || !inputValue || !inputValue.trim()) ? "cursor-default" : "cursor-pointer"
                  )}
                >
                  <ArrowUp className="w-4 h-4" />
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // Chat conversation layout - using flexbox instead of fixed positioning
  return (
    <div className="flex flex-col h-full bg-background text-foreground">
      {/* Header */}
      <header className="flex-shrink-0 border-b bg-card p-4 shadow-sm">
        <div className="w-full flex items-center justify-between px-4">
          <h1 className="text-xl font-semibold">LeChat AI</h1>
          <div className="relative" ref={dropdownRef}>
            <Button
              variant="ghost"
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center gap-2 text-sm"
            >
              <Settings className="w-4 h-4" />
              Configuration
              <ChevronDown className={cn("w-4 h-4 transition-transform", isDropdownOpen && "rotate-180")} />
            </Button>
            
            {isDropdownOpen && (
              <div className="absolute right-0 top-full mt-2 w-80 bg-card border rounded-lg shadow-lg z-50 p-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="api-key-chat">API Key</Label>
                  <div className="flex items-center gap-2">
                     <KeyRound className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                    <Input
                      id="api-key-chat"
                      type="password"
                      placeholder="Enter your API key"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      onKeyDown={handleConfigKeyDown}
                      className="rounded-md w-64"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="model-chat">Model</Label>
                  <div className="flex items-center gap-2">
                    <span className="w-4 h-4 flex-shrink-0"></span>
                    <Input 
                      id="model-chat" 
                      type="text" 
                      value={model} 
                      onChange={(e) => setModel(e.target.value)}
                      onKeyDown={handleConfigKeyDown}
                      placeholder="Enter model name"
                      className="rounded-md w-64" 
                    />
                  </div>
                </div>
                <div className="flex justify-end pt-2">
                  <Button
                    onClick={handleDoneClick}
                    size="sm"
                    className="text-sm"
                  >
                    Done
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Chat Messages Area - takes remaining space */}
      <div className="flex-1 overflow-y-auto" ref={scrollAreaRef}>
        <div className="max-w-4xl mx-auto p-4 space-y-6">
          {messages.map((msg, index) => (
            <MessageBubble 
              key={index} 
              message={msg} 
              onFallbackConfirm={handleFallbackConfirmation}
              pendingFallback={pendingFallback !== null && index === messages.length - 1}
            />
          ))}
          {loading && <LoadingIndicator />}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>
      </div>

      {/* Footer - Input Area */}
      <footer className="flex-shrink-0 bg-card border-t p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {/* YouTube Detection Alert */}
          {youtubeDetection.show && (
            <YouTubeDetectionAlert
              urls={youtubeDetection.urls}
              onProcess={handleYouTubeProcess}
              onDismiss={() => setYoutubeDetection({ urls: [], show: false })}
              isProcessing={isProcessingYouTube}
            />
          )}

          <form
            onSubmit={handleSubmit}
            className="flex items-end"
          >
            <div className={cn(
              "relative flex-grow border border-input focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 flex items-center",
              isMultiLine ? "rounded-lg items-end" : "rounded-full"
            )}>
              <textarea
                ref={textareaRef}
                rows={1}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="How can I help you today?"
                className="w-full resize-none bg-transparent shadow-none focus-visible:outline-none p-2.5 pr-12 text-base md:text-sm"
                aria-label="Chat input"
              />
              <Button 
                type="submit" 
                size="icon" 
                disabled={loading || !inputValue || !inputValue.trim()} 
                aria-label="Send message"
                className={cn(
                  "absolute right-2 h-8 w-8 flex-shrink-0 rounded-full",
                  isMultiLine ? "bottom-2" : "top-1/2 -translate-y-1/2",
                  // Override cursor behavior for chat submit button specifically
                  (loading || !inputValue || !inputValue.trim()) ? "cursor-default" : "cursor-pointer"
                )}
              >
                <ArrowUp className="w-4 h-4" />
              </Button>
            </div>
          </form>
        </div>
      </footer>
    </div>
  );
};

export default SimpleChatInterface;
