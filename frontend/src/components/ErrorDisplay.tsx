"use client";

import React from "react";

interface ErrorDisplayProps {
  error: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error }) => (
  <div className="w-full max-w-xl bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-lg p-4 my-2 shadow">
    <span className="font-semibold">Error:</span> {error}
  </div>
); 