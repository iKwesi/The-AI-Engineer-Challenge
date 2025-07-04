"use client";

import React from "react";

interface MessageStreamProps {
  message: string;
  loading: boolean;
}

export const MessageStream: React.FC<MessageStreamProps> = ({ message, loading }) => (
  <div className="w-full max-w-xl min-h-[120px] bg-gray-50 dark:bg-gray-800 rounded-lg shadow-inner p-4 font-mono text-gray-900 dark:text-gray-100 whitespace-pre-wrap break-words">
    {loading && <span className="text-blue-500 animate-pulse">Streaming...</span>}
    {message}
  </div>
); 