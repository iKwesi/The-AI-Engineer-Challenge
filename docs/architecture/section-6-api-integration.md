# Section 6: API Integration

## 6.1 API Service Layer
All communication with the backend API will be handled by functions within the `src/services/` directory, decoupling UI logic from data fetching.

## 6.2 Service Template (`chatService.ts`)
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