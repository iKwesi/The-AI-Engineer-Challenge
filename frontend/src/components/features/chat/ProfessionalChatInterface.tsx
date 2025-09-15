"use client";

import React, { useEffect, useRef, useState } from 'react';
import { ArrowUp, Loader, AlertCircle, Bot, User, Settings, KeyRound, ChevronDown } from 'lucide-react';
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { Avatar, AvatarFallback } from "@/components/ui/Avatar";
import { Label } from "@/components/ui/Label";
import { cn } from '@/lib/utils';
import { type Message } from '@/hooks/useChat';

export interface ProfessionalChatInterfaceProps {
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
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
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

const ProfessionalChatInterface: React.FC<ProfessionalChatInterfaceProps> = ({
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
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Track if textarea is multi-line
  const isMultiLine = (inputValue && inputValue.includes('\n')) || (textareaRef.current && textareaRef.current.scrollHeight > textareaRef.current.clientHeight);

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

  // Check if we should show the welcome screen (no messages yet)
  const showWelcomeScreen = !messages || messages.length === 0;

  if (showWelcomeScreen) {
    // Welcome screen layout - centered like ChatGPT
    return (
      <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="border-b bg-card p-4 shadow-sm">
        <div className="w-full flex items-center justify-between px-4">
          <h1 className="text-xl font-semibold">AI Chat</h1>
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
                     <KeyRound className="w-4 h-4 text-muted-foreground" />
                    <Input
                      id="api-key-welcome"
                      type="password"
                      placeholder="Enter your API key"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      onKeyDown={handleConfigKeyDown}
                      className="rounded-md"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                   <Label htmlFor="model-welcome">Model</Label>
                  <Input 
                    id="model-welcome" 
                    type="text" 
                    value={model} 
                    onChange={(e) => setModel(e.target.value)}
                    onKeyDown={handleConfigKeyDown}
                    placeholder="Enter model name"
                    className="rounded-md" 
                  />
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
              What's on the agenda today?
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
                  placeholder="Ask me anything"
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
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="border-b bg-card p-4 shadow-sm">
        <div className="w-full flex items-center justify-between px-4">
          <h1 className="text-xl font-semibold">AI Chat</h1>
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
                     <KeyRound className="w-4 h-4 text-muted-foreground" />
                    <Input
                      id="api-key-chat"
                      type="password"
                      placeholder="Enter your API key"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      onKeyDown={handleConfigKeyDown}
                      className="rounded-md"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                   <Label htmlFor="model-chat">Model</Label>
                  <Input 
                    id="model-chat" 
                    type="text" 
                    value={model} 
                    onChange={(e) => setModel(e.target.value)}
                    onKeyDown={handleConfigKeyDown}
                    placeholder="Enter model name"
                    className="rounded-md" 
                  />
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

      <div ref={scrollAreaRef} className="flex-grow overflow-y-auto">
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

      <footer className="bg-card border-t p-4">
        <div className="max-w-4xl mx-auto">
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
                placeholder="Ask me anything"
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

export default ProfessionalChatInterface;
