"use client";

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

export default function TestLatexPage() {
  const testContent = `
# LaTeX Rendering Test

## Inline Math
Here is some inline math: $\\frac{12}{4} = 3$

## Block Math
$$\\frac{a}{b} = c$$

## More Examples
- Simple fraction: $\\frac{1}{2}$
- Square root: $\\sqrt{16} = 4$
- Quadratic formula: $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$

## Block Math Examples
$$\\sum_{i=1}^{n} x_i = x_1 + x_2 + \\cdots + x_n$$

$$\\int_{a}^{b} f(x) dx$$
  `;

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">LaTeX Rendering Test Page</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <ReactMarkdown
          remarkPlugins={[remarkMath]}
          rehypePlugins={[rehypeKatex]}
        >
          {testContent}
        </ReactMarkdown>
      </div>
      
      <div className="mt-8 p-4 bg-gray-100 rounded">
        <h2 className="text-lg font-semibold mb-2">Debug Info</h2>
        <p>If you see properly rendered mathematical expressions above, LaTeX is working correctly.</p>
        <p>If you see raw LaTeX code (like \frac{12}{4}), there's still an issue with the setup.</p>
      </div>
    </div>
  );
}
