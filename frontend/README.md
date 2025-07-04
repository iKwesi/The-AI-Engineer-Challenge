# OpenAI Chat Playground Frontend

This is a Next.js (App Router) frontend for the OpenAI Chat API backend in `/api`.

## 🚀 Getting Started

### 1. Install dependencies

```
cd frontend
npm install
```

### 2. Run the development server

```
npm run dev
```

- The app will be available at [http://localhost:3000](http://localhost:3000)
- Uses Turbopack for fast local development

### 3. Connect to the backend

- The frontend expects the backend API to be running and accessible at `/api/chat` and `/api/health`.
- If running locally, ensure the backend FastAPI server is started (see `/api/README.md` for backend instructions).

## 📝 Features
- Enter developer and user messages, select model, and provide OpenAI API key (masked input)
- Streams AI responses from the backend in real time
- Clear loading, error, and responsive states
- Modern, accessible, and visually polished UI

## 🛠️ Project Structure
- `src/components/` — Reusable UI components
- `src/hooks/` — Custom React hooks (e.g., for chat streaming)
- `src/app/` — Main app pages and layout

## 🧑‍💻 Development
- Uses TypeScript, Tailwind CSS, and Next.js best practices
- Modular, scalable, and easy to extend

## 🌐 Deployment
- Ready for deployment on Vercel (recommended)
- For local testing, just run `npm run dev`

## 📋 Environment Variables
- No environment variables are required for the frontend. The OpenAI API key is entered by the user at runtime.

---

For any issues, see the main project FAQ or contact the maintainer.
