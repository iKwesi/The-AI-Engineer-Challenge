"use client";

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { ArrowUp, Loader, AlertCircle, Bot, User, Settings, KeyRound, ChevronDown, Upload, Youtube, FileText, X } from 'lucide-react';
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { Avatar, AvatarFallback } from "@/components/ui/Avatar";
import { Label } from "@/components/ui/Label";
import { cn } from '@/lib/utils';
import { type Message } from '@/hooks/useChat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import DocumentManager from '@/components/features/upload/DocumentManager';
import { hasYouTubeUrls, detectYouTubeUrls, processYouTubeUrl } from '@/services/documentService';

export interface RAGChatInterfaceProps {
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
}

const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
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
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[[rehypeKatex, { strict: false, throwOnError: false }]]}
              components={{
                // H3 headings with proper spacing and typography
                h3: ({ children }) => (
                  <h3 className="text-base font-semibold mt-4 mb-2 first:mt-0 text-foreground">
                    {children}
                  </h3>
                ),
                
                // H2 headings (in case they're used)
                h2: ({ children }) => (
                  <h2 className="text-lg font-semibold mt-4 mb-2 first:mt-0 text-foreground">
                    {children}
                  </h2>
                ),
                
                // H1 headings (in case they're used)
                h1: ({ children }) => (
                  <h1 className="text-xl font-bold mt-4 mb-3 first:mt-0 text-foreground">
                    {children}
                  </h1>
                ),
                
                // Paragraphs with proper spacing
                p: ({ children }) => (
                  <p className="mb-4 last:mb-0 leading-relaxed text-foreground">
                    {children}
                  </p>
                ),
                
                // Unordered lists with proper indentation and spacing
                ul: ({ children }) => (
                  <ul className="ml-6 mb-4 last:mb-0 space-y-1 list-disc">
                    {children}
                  </ul>
                ),
                
                // Ordered lists with proper indentation and spacing
                ol: ({ children }) => (
                  <ol className="ml-6 mb-4 last:mb-0 space-y-1 list-decimal">
                    {children}
                  </ol>
                ),
                
                // List items with proper spacing
                li: ({ children }) => (
                  <li className="mb-1 leading-relaxed text-foreground">
                    {children}
                  </li>
                ),
                
                // Inline code with background and padding
                code: ({ children, ...props }) => {
                  const isInline = !props.className?.includes('language-');
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
                
                // Pre blocks for code blocks
                pre: ({ children }) => (
                  <pre className="bg-muted/80 p-3 rounded-md text-xs font-mono overflow-x-auto mb-4 last:mb-0 border">
                    {children}
                  </pre>
                ),
                
                // Strong/bold text
                strong: ({ children }) => (
                  <strong className="font-semibold text-foreground">
                    {children}
                  </strong>
                ),
                
                // Emphasis/italic text
                em: ({ children }) => (
                  <em className="italic text-foreground">
                    {children}
                  </em>
                ),
                
                // Blockquotes
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-muted-foreground/30 pl-4 my-4 italic text-muted-foreground">
                    {children}
                  </blockquote>
                ),
                
                // Horizontal rules
                hr: () => (
                  <hr className="my-6 border-muted-foreground/20" />
                ),
                
                // Tables
                table: ({ children }) => (
                  <div className="overflow-x-auto my-4">
                    <table className="min-w-full border-collapse border border-muted-foreground/20">
                      {children}
                    </table>
                  </div>
                ),
                
                th: ({ children }) => (
                  <th className="border border-muted-foreground/20 px-3 py-2 bg-muted/50 font-semibold text-left">
                    {children}
                  </th>
                ),
                
                td: ({ children }) => (
                  <td className="border border-muted-foreground/20 px-3 py-2">
                    {children}
                  </td>
                ),
              }}
            >
              {preprocessMathContent(message.content)}
            </ReactMarkdown>
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

const RAGChatInterface: React.FC<RAGChatInterfaceProps> = ({
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
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [showDocumentManager, setShowDocumentManager] = useState(false);
  const [youtubeDetection, setYoutubeDetection] = useState<{
    urls: string[];
    show: boolean;
  }>({ urls: [], show: false });
  const [isProcessingYouTube, setIsProcessingYouTube] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const documentManagerRef = useRef<HTMLDivElement>(null);
  const [documentManagerHeight, setDocumentManagerHeight] = useState(0);

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

  // Measure document manager height when it's shown/hidden
  useEffect(() => {
    if (documentManagerRef.current && showDocumentManager) {
      const resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          setDocumentManagerHeight(entry.contentRect.height);
        }
      });
      
      resizeObserver.observe(documentManagerRef.current);
      
      return () => {
        resizeObserver.disconnect();
      };
    } else {
      setDocumentManagerHeight(0);
    }
  }, [showDocumentManager]);

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

  // Handle document mode entered
  const handleDocumentModeEntered = useCallback(() => {
    // Optionally refresh conversation mode status or show notification
    console.log('Document mode entered');
  }, []);

  // Handle upload error
  const handleUploadError = useCallback((error: string) => {
    console.error('Upload error:', error);
  }, []);

  // Check if we should show the welcome screen (no messages yet)
  const showWelcomeScreen = !messages || messages.length === 0;

  if (showWelcomeScreen) {
    // Welcome screen layout - centered like ChatGPT with document upload
    return (
      <div className="flex flex-col h-screen bg-background text-foreground">
        <header className="border-b bg-card p-4 shadow-sm">
          <div className="w-full flex items-center justify-between px-4">
            <h1 className="text-xl font-semibold">RAG AI Chat</h1>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                onClick={() => setShowDocumentManager(!showDocumentManager)}
                className="flex items-center gap-2 text-sm"
              >
                <Upload className="w-4 h-4" />
                Documents
              </Button>
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
          </div>
        </header>

        {/* Document Manager */}
        {showDocumentManager && (
          <div className="border-b bg-muted/20 p-4">
            <div className="max-w-4xl mx-auto">
              <DocumentManager
                apiKey={apiKey}
                onDocumentModeEntered={handleDocumentModeEntered}
                onError={handleUploadError}
              />
            </div>
          </div>
        )}

        {/* Centered welcome content */}
        <div className="flex-grow flex flex-col items-center justify-center p-4">
          <div className="max-w-2xl w-full text-center space-y-8">
            <h2 className="text-3xl font-semibold text-foreground">
              Chat with your documents and YouTube videos
            </h2>
            
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
                  placeholder="Ask me anything or paste a YouTube URL"
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

  // Chat conversation layout - current layout when messages exist
  return (
    <div className="flex flex-col h-screen bg-background text-foreground overflow-hidden">
      <header className="border-b bg-card p-4 shadow-sm">
        <div className="w-full flex items-center justify-between px-4">
          <h1 className="text-xl font-semibold">RAG AI Chat</h1>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              onClick={() => setShowDocumentManager(!showDocumentManager)}
              className="flex items-center gap-2 text-sm"
            >
              <Upload className="w-4 h-4" />
              Documents
            </Button>
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
        </div>
      </header>

      {/* Document Manager */}
      {showDocumentManager && (
        <div ref={documentManagerRef} className="border-b bg-muted/20 p-4 max-h-96 overflow-y-auto">
          <div className="max-w-4xl mx-auto">
            <DocumentManager
              apiKey={apiKey}
              onDocumentModeEntered={handleDocumentModeEntered}
              onError={handleUploadError}
            />
          </div>
        </div>
      )}

      <div 
        ref={scrollAreaRef} 
        className="overflow-y-auto fixed bottom-24 left-0 right-0"
        style={{
          top: showDocumentManager 
            ? `${80 + documentManagerHeight}px` // 80px for header
            : '80px' // Just header height
        }}
      >
        <div className="max-w-4xl mx-auto p-4 space-y-6">
          {messages.map((msg, index) => (
            <MessageBubble key={index} message={msg} />
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

      <footer className="fixed bottom-0 left-0 right-0 bg-card border-t p-4">
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
                placeholder="Ask me anything or paste a YouTube URL"
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

export default RAGChatInterface;
