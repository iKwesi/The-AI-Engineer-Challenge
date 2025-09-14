# AI Engineer Challenge Frontend Architecture

## Section 1: Template and Framework Selection

### 1.1 Analysis of Existing Project
The frontend architecture will be an enhancement and modernization of the existing application. Based on a review of the `frontend/` directory, the project is founded on the following core technologies:

* **Framework**: **Next.js (App Router)**, as indicated by the project structure (`src/app/`) and dependencies (`package.json`).
* **Language**: **TypeScript**, confirmed by `tsconfig.json` and file extensions.
* **Styling**: **Tailwind CSS**, as configured in `tailwind.config.js` and `postcss.config.mjs`.

All architectural decisions will build upon this existing Next.js foundation, ensuring consistency and leveraging its built-in optimizations for performance and development experience. No new starter template will be introduced.

### 1.2 Change Log

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2025-09-11 | 1.0 | Initial draft of the Frontend Architecture document. | Winston (Architect) |
| 2025-09-13 | 1.1 | Added critical sections to address PO validation report: Testing Infrastructure Setup, Deployment Strategy, and Rollback Procedures. | Winston (Architect) |
| 2025-09-14 | 1.2 | **CRITICAL FIXES**: Updated story sequencing to align with PRD v1.2 - chatService (Story 1.3) now precedes ProfessionalChatInterface (Story 1.4). Added explicit dependency gates, form validation standards, and user documentation requirements. Enhanced testing infrastructure requirements to prevent regression risks. All changes address PO validation blocking issues. | Winston (Architect) |

---
## Section 2: Frontend Tech Stack

This table is the single source of truth for all frontend development.

| Category | Technology | Version | Purpose & Rationale |
| :--- | :--- | :--- | :--- |
| **Framework** | Next.js | `15.3.5` | The core application framework, providing routing, and server-side features. |
| **UI Library** | React | `19.0.0` | The library for building user interface components. |
| **Language** | TypeScript | `^5` | Ensures type safety and improves code quality and maintainability. |
| **Styling** | Tailwind CSS | `^4` | A utility-first CSS framework for rapid and consistent styling. |
| **State Management**| React Hooks | `19.0.0` | For managing component-level and simple app-level state (`useState`, `useContext`). |
| **Testing** | React Testing Library + Jest | `^14.0.0` / `^29.0.0` | Industry-standard for testing React components and ensuring functionality preservation. |
| **Icons** | Heroicons | *(TBD)* | For a consistent, high-quality set of SVG icons, as defined in the UX Spec. |
| **Linting** | ESLint | `^9` | For enforcing code quality and style consistency. |
| **Package Manager**| npm | *(Project)*| For managing project dependencies. |

---
## Section 3: Project Structure

This refined structure provides a clear separation between general-purpose UI elements (`ui`) and feature-specific compositions (`features`), setting a strong foundation for future growth.

```plaintext
frontend/src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
│
├── components/
│   ├── features/
│   │   └── chat/
│   │       └── ProfessionalChatInterface.tsx  # The main, feature-specific component
│   │
│   └── ui/
│       ├── Button.tsx                       # Reusable, styled button
│       ├── Input.tsx                        # Reusable, styled input
│       └── Card.tsx                         # Reusable container component
│
├── hooks/
│   └── useChat.ts
│
├── services/
│   └── chatService.ts
│
├── types/
│   └── index.ts
│
└── utils/
    └── index.ts                           # Utility functions (e.g., classname helpers)
```

---
## Section 4: Component Standards

### 4.1 Component Template
All new React components should follow this basic structure, using TypeScript for props and defining a functional component.

**Example (`Button.tsx`):**
```typescript
import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
}) => {
  const baseClasses = 'px-4 py-2 rounded-lg font-semibold transition-colors';
  const variantClasses = variant === 'primary'
    ? 'bg-accent text-accent-text hover:bg-accent-hover'
    : 'bg-transparent border border-border text-text-primary hover:bg-gray-100';
  const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : '';

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses} ${disabledClasses}`}
    >
      {children}
    </button>
  );
};

export default Button;
```

### 4.2 Naming Conventions
| Element Type | Convention | Example |
| :--- | :--- | :--- |
| **Component Files** | PascalCase | `ProfessionalChatInterface.tsx` |
| **Component Name** | PascalCase | `ProfessionalChatInterface` |
| **Props Interface** | PascalCase, `Props` suffix | `ButtonProps` |
| **Custom Hooks** | camelCase, `use` prefix | `useChat.ts` |
| **Service Files** | camelCase, `Service` suffix | `chatService.ts` |

---
## Section 5: State Management

### 5.1 State Management Approach
We will use a **Custom Hook pattern** centered around `useChat.ts`. This approach is lightweight and keeps all related chat logic colocated. The `page.tsx` component will call the hook and pass state and handlers down as props to presentational components.

### 5.2 State Management Template (`useChat.ts`)
```typescript
import { useState, useCallback } from 'react';
import { chatService } from '@/services/chatService';
import { Message } from '@/types';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const sendChat = useCallback(async (userMessage: string, apiKey: string) => {
    // ... logic to call chatService.streamChat and update state
  }, []);

  return {
    messages,
    loading,
    error,
    sendChat,
  };
};
```

---
## Section 6: API Integration

### 6.1 API Service Layer
All communication with the backend API will be handled by functions within the `src/services/` directory, decoupling UI logic from data fetching.

### 6.2 Service Template (`chatService.ts`)
```typescript
import { ChatApiRequestBody } from '@/types';

export const chatService = {
  streamChat: async (request: ChatApiRequestBody): Promise<ReadableStreamDefaultReader<Uint8Array>> => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok || !response.body) {
      const errorBody = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorBody}`);
    }

    return response.body.getReader();
  },
};
```

---
## Section 7: Routing

### 7.1 Route Configuration
The application is a single-page interface. Routing is handled by the Next.js App Router file system.
* **Root Route (`/`)**: Served from `src/app/page.tsx`. This is the only user-facing route.
* **Protected Routes**: Not applicable, as functionality is controlled by the user-provided API key.

---
## Section 8: Styling Guidelines

### 8.1 Styling Approach
The project will use **Tailwind CSS** exclusively. A utility-first methodology will be applied, with all custom theme values defined in `tailwind.config.js`.

### 8.2 Global Theme Configuration (`tailwind.config.js`)
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [ "./src/**/*.{js,ts,jsx,tsx,mdx}" ],
  theme: {
    extend: {
      colors: {
        'background': '#F8F9FA',
        'text-primary': '#212529',
        'accent': {
          DEFAULT: '#00796B', // Teal
          'hover': '#00695C',
          'text': '#FFFFFF',
        },
        'container': '#FFFFFF',
        'border': '#E9ECEF',
        'assistant-bubble': '#F1F3F5',
      },
      boxShadow: {
        'soft': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      }
    },
  },
  plugins: [ require('@tailwindcss/forms') ],
};
```

---


---
## Section 9: Testing Requirements

The testing framework will be **React Testing Library** with **Jest**.

### 9.1 Component Test Template
```typescript
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Button from './Button';

describe('Button Component', () => {
  it('calls the onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```


### 9.3 Testing Best Practices
* **Arrange, Act, Assert**: Structure tests in this clear pattern.
* **Test Behavior**: Focus tests on what the user experiences.
* **Mock Dependencies**: Isolate components by mocking API services.
* **Regression Testing**: Test existing functionality before and after each story implementation.



---


---
