"use client";

import React from "react";

export const LoadingIndicator: React.FC = () => (
  <div className="flex items-center justify-center gap-2 text-blue-600 animate-pulse">
    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
    <span>Loading...</span>
  </div>
); 