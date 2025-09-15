// Mock for react-markdown
import React from 'react';

const ReactMarkdown = ({ children }) => {
  return React.createElement('div', { 'data-testid': 'markdown' }, children);
};

export default ReactMarkdown;
