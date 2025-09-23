# 🚀 The AI Engineer Challenge: RAG-Powered Chat Playground

> **Where documents meet AI magic!** ✨ Transform your static files into interactive conversations with the power of Retrieval-Augmented Generation (RAG).

## 🎯 What's This All About?

Ever wished you could have a conversation with your documents? Well, now you can! This isn't just another chatbot – it's a sophisticated AI playground that lets you:

- 💬 **Chat with OpenAI models** using your own API key
- 📄 **Upload documents** (PDFs, Word docs, Excel files, text files) and chat with their content
- 🎥 **Process YouTube videos** and discuss their transcripts
- 🧠 **Smart context switching** between general knowledge and document-specific answers
- 🔍 **Advanced RAG capabilities** with adaptive thresholds and conflict resolution

Think of it as giving your documents a voice and your AI a memory!

## 🏗️ Architecture Overview

This bad boy is built with a modern, scalable architecture:

### Frontend (Next.js + React + TypeScript)
- **Professional Chat Interface** with streaming responses
- **Document Management** with drag-and-drop uploads
- **Smart UI Components** built with Radix UI and Tailwind CSS
- **Responsive Design** that looks great on any device

### Backend (FastAPI + Python)
- **Streaming Chat API** for real-time conversations
- **RAG Service** with intelligent document processing
- **Vector Database** for lightning-fast semantic search
- **YouTube Integration** for video transcript processing

### AI Magic (OpenAI + Custom RAG)
- **GPT-4 Integration** with custom system prompts
- **Intelligent Chunking** with page-aware processing
- **Adaptive Thresholds** for relevance scoring
- **Conflict Resolution** for multi-document scenarios

## 🚀 Quick Start Guide

### Prerequisites

Before we dive in, make sure you have:
- **Node.js 18+** (for the frontend)
- **Python 3.8+** (for the backend)
- **OpenAI API Key** (get one at [platform.openai.com](https://platform.openai.com))

### 1. Clone & Setup

```bash
# Clone this awesome repo
git clone https://github.com/iKwesi/The-AI-Engineer-Challenge.git
cd The-AI-Engineer-Challenge

# Install backend dependencies
pip install -r api/requirements.txt

# Install frontend dependencies
cd frontend
npm install
```

### 2. Fire Up the Backend

```bash
# From the root directory
cd api
python app.py
```

Your API will be running at `http://localhost:8000` 🎉

### 3. Launch the Frontend

```bash
# In a new terminal, from the frontend directory
cd frontend
npm run dev
```

Your app will be live at `http://localhost:3000` 🚀

### 4. Start Chatting!

1. Open your browser to `http://localhost:3000`
2. Enter your OpenAI API key in the configuration section
3. Start chatting or upload some documents to get the full experience!

## 🎮 How to Use

### Basic Chat Mode
Just type your question and hit enter! The AI will respond using general knowledge.

### Document Mode (The Cool Stuff!)
1. **Upload Documents**: Drag and drop your files or click to browse
2. **Auto-Magic**: The system automatically enters "document mode"
3. **Smart Conversations**: Ask questions about your documents and get precise, cited answers
4. **Fallback Handling**: If your question isn't in the docs, the AI will offer to use general knowledge

### YouTube Mode
1. Paste a YouTube URL in the chat
2. The system processes the video transcript
3. Chat about the video content like it's a document!

## 🛠️ Development

### Project Structure

```
├── frontend/                 # Next.js React app
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API communication
│   │   └── utils/          # Helper functions
├── api/                     # FastAPI backend
│   ├── app.py              # Main API server
│   └── requirements.txt    # Python dependencies
├── aimakerspace/           # Core AI/RAG functionality
│   ├── document_utils/     # Document processing
│   ├── openai_utils/       # OpenAI integration
│   └── processing_utils/   # RAG and conversation management
└── docs/                   # Comprehensive documentation
```

### Running Tests

```bash
# Frontend tests
cd frontend
npm test

# Backend tests (from root)
python -m pytest tests/
```

### Code Quality

We use:
- **ESLint** for JavaScript/TypeScript linting
- **Prettier** for code formatting
- **TypeScript** for type safety
- **Jest** for testing

## 🌟 Key Features

### 🧠 Smart RAG System
- **Page-Aware Chunking**: Maintains document structure for better context
- **Adaptive Thresholds**: Automatically adjusts relevance scoring
- **Multi-Document Support**: Handle conflicts when documents disagree
- **Citation Tracking**: Always know where answers come from

### 💬 Professional Chat Interface
- **Streaming Responses**: See answers appear in real-time
- **Markdown Support**: Rich formatting with math equations (LaTeX)
- **Message History**: Keep track of your conversations
- **Error Handling**: Graceful fallbacks when things go wrong

### 📁 Document Management
- **Multiple Formats**: PDF, DOCX, XLSX, TXT, and more
- **Batch Upload**: Process multiple files at once
- **Smart Processing**: Automatic format detection and optimization
- **Storage Management**: Easy document removal and cleanup

### 🎥 YouTube Integration
- **Transcript Extraction**: Automatically get video transcripts
- **Content Analysis**: Chat about video content like any document
- **Error Handling**: Graceful handling of videos without transcripts

## 🚀 Deployment

### Vercel (Recommended for Frontend)

The frontend is optimized for Vercel deployment:

```bash
# Deploy to Vercel
cd frontend
npx vercel --prod
```

### Backend Deployment

The FastAPI backend can be deployed to:
- **Railway**
- **Heroku**
- **Google Cloud Run**
- **AWS Lambda** (with Mangum)

Check out the deployment guides in the `docs/` folder!

## 🤝 Contributing

We love contributions! Here's how to get involved:

1. **Fork the repo**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Guidelines

- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

## 📚 Documentation

Dive deeper with our comprehensive docs:

- **[Product Requirements](docs/prd.md)** - What we're building and why
- **[Frontend Architecture](docs/architecture/)** - Technical deep-dive
- **[API Documentation](api/README.md)** - Backend API reference
- **[Testing Guide](docs/TESTING_GUIDE.md)** - How to test everything
- **[RAG Implementation](docs/rag-implementation-prd.md)** - The AI magic explained

## 🐛 Troubleshooting

### Common Issues

**"API key not working"**
- Make sure your OpenAI API key is valid and has credits
- Check that you're using the correct key format (starts with `sk-`)

**"Documents not uploading"**
- Check file size (max 50MB)
- Ensure file format is supported
- Try refreshing the page and uploading again

**"Chat responses are slow"**
- This is normal for large documents
- Try smaller chunks or fewer documents
- Check your internet connection

### Getting Help

- 📖 Check the [FAQ](FAQandCommonIssues.md)
- 🐛 [Open an issue](https://github.com/iKwesi/The-AI-Engineer-Challenge/issues)
- 💬 Start a [discussion](https://github.com/iKwesi/The-AI-Engineer-Challenge/discussions)

## 🎉 What's Next?

This project is actively evolving! Upcoming features include:

- 🔐 **User Authentication** - Save your documents and conversations
- 🌐 **Multi-language Support** - Chat in your preferred language
- 📊 **Analytics Dashboard** - Track your usage and insights
- 🤖 **Custom AI Models** - Bring your own models
- 🔗 **API Integrations** - Connect to more data sources

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for the amazing GPT models
- **Vercel** for seamless deployment
- **The open-source community** for the incredible tools and libraries
- **You** for checking out this project! 🎉

---

**Ready to turn your documents into conversations?** 🚀

[Get Started](#-quick-start-guide) | [View Docs](docs/) | [Report Issues](https://github.com/iKwesi/The-AI-Engineer-Challenge/issues)

---

*Built with ❤️ by developers who believe AI should be accessible, powerful, and fun to use.*
