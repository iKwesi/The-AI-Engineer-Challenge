# Section 5: State Management

## 5.1 State Management Approach
We will use a **Custom Hook pattern** centered around `useChat.ts`. This approach is lightweight and keeps all related chat logic colocated. The `page.tsx` component will call the hook and pass state and handlers down as props to presentational components.

## 5.2 State Management Template (`useChat.ts`)
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