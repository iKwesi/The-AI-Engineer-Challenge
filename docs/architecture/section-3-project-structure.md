# Section 3: Project Structure

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