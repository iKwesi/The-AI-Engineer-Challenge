"use client";

import React, { useEffect, useRef } from 'react';
import { ArrowUp, Loader, AlertCircle, Bot, User, Settings, KeyRound } from 'lucide-react';
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/Accordion";
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
}

const MessageBubble: React.FC<{ message: Message, isOnlyMessage?: boolean }> = ({ message, isOnlyMessage }) => {
  const isUser = message.role === 'user';
  return (
    <div className={cn("flex items-start gap-3 w-full", isUser ? "justify-end" : "justify-start", isOnlyMessage ? "justify-center" : "")}>
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
            : "bg-secondary text-secondary-foreground",
          isOnlyMessage ? "text-center" : ""
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
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

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

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="border-b bg-card p-4 shadow-sm">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-semibold">AI Chat</h1>
          <Accordion type="single" collapsible className="w-full mt-2">
            <AccordionItem value="item-1" className="border-none">
              <AccordionTrigger className="text-sm py-2 hover:no-underline [&[data-state=open]>svg]:text-primary">
                <div className="flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  Configuration
                </div>
              </AccordionTrigger>
              <AccordionContent className="pt-4 space-y-4 px-1">
                <div className="space-y-2">
                  <Label htmlFor="api-key">API Key</Label>
                  <div className="flex items-center gap-2">
                     <KeyRound className="w-4 h-4 text-muted-foreground" />
                    <Input
                      id="api-key"
                      type="password"
                      placeholder="Enter your API key"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="rounded-full"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                   <Label htmlFor="model">Model</Label>
                  <Input id="model" type="text" value="Default Model" disabled className="rounded-full" />
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </header>

      <div ref={scrollAreaRef} className="flex-grow overflow-y-auto p-4 md:p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((msg, index) => (
            <MessageBubble key={index} message={msg} isOnlyMessage={messages.length === 1} />
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
            className="flex items-end gap-2"
          >
            <div className="relative flex-grow border border-input rounded-full focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 flex items-center pr-3">
              <textarea
                ref={textareaRef}
                rows={1}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything"
                className="w-full resize-none bg-transparent shadow-none focus-visible:outline-none p-2.5 text-base md:text-sm"
                aria-label="Chat input"
              />
            </div>
            <Button 
              type="submit" 
              size="icon" 
              disabled={loading || !inputValue.trim()} 
              aria-label="Send message"
              className="h-10 w-10 flex-shrink-0 rounded-full"
            >
              <ArrowUp className="w-5 h-5" />
            </Button>
          </form>
        </div>
      </footer>
    </div>
  );
};

export default ProfessionalChatInterface;
