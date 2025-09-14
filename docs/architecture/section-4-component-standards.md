# Section 4: Component Standards

## 4.1 Component Template
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

## 4.2 Naming Conventions
| Element Type | Convention | Example |
| :--- | :--- | :--- |
| **Component Files** | PascalCase | `ProfessionalChatInterface.tsx` |
| **Component Name** | PascalCase | `ProfessionalChatInterface` |
| **Props Interface** | PascalCase, `Props` suffix | `ButtonProps` |
| **Custom Hooks** | camelCase, `use` prefix | `useChat.ts` |
| **Service Files** | camelCase, `Service` suffix | `chatService.ts` |

---