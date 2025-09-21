# RAG Implementation Guide

## Overview

This guide documents the complete RAG (Retrieval-Augmented Generation) implementation for The AI Engineer Challenge. The system extends the existing chat application with document processing and context-aware responses.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.13+** with `uv` package manager
2. **OpenAI API Key** - Set as environment variable: `export OPENAI_API_KEY=your_key_here`
3. **Node.js 18+** for the frontend

### Installation

```bash
# Clone and navigate to the project
git clone <repository-url>
cd The-AI-Engineer-Challenge

# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Testing the Implementation

```bash
# Test the RAG implementation (requires OpenAI API key)
python test_rag_implementation.py

# Start the API server
cd api
python app.py

# Start the frontend (in another terminal)
cd frontend
npm run dev
```

## 🏗️ Architecture

### Core Components

```
aimakerspace/
├── document_utils/         # Document processing utilities
│   ├── base.py            # Abstract DocumentLoader base class
│   ├── text_utils.py      # Text file processing (.txt)
│   ├── pdf_utils.py       # PDF processing (.pdf)
│   ├── word_utils.py      # Word documents (.docx, .doc)
│   ├── excel_utils.py     # Excel/CSV (.xlsx, .xls, .csv)
│   ├── youtube_utils.py   # YouTube transcript processing
│   └── factory.py         # Auto-selection of appropriate loader
├── processing_utils/       # Text processing utilities
│   ├── text_splitter.py   # Text chunking with sentence awareness
│   ├── rag_service.py     # Main RAG orchestration service
│   └── page_aware_chunker.py # Advanced PDF chunking
├── models.py              # Domain models and data structures
├── openai_utils/          # OpenAI integrations (unchanged)
└── vectordatabase.py      # Vector storage (unchanged)
```

### Key Features

- **Multi-format Document Support**: PDF, TXT, DOCX, DOC, XLSX, XLS, CSV
- **YouTube Integration**: Automatic transcript extraction and processing
- **Smart Chunking**: Page-aware chunking for PDFs, sentence-aware for text
- **RAG Service**: Complete orchestration of document processing and chat
- **RESTful API**: Full set of endpoints for document management and chat

## 📚 API Endpoints

### Document Management

#### Upload Document
```http
POST /api/upload-document
Content-Type: multipart/form-data

file: <file>
api_key: <your_openai_api_key>
```

**Response:**
```json
{
  "status": "success",
  "message": "Document 'example.pdf' processed successfully",
  "chunks_processed": 15,
  "filename": "example.pdf"
}
```

#### Process YouTube Video
```http
POST /api/process-youtube
Content-Type: application/json

{
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "api_key": "your_openai_api_key"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "YouTube video processed successfully",
  "video_title": "Example Video Title",
  "chunks_processed": 8
}
```

#### List Documents
```http
GET /api/documents?api_key=your_openai_api_key
```

**Response:**
```json
{
  "documents": [
    {
      "document_id": "example.pdf",
      "filename": "example.pdf",
      "document_type": "pdf",
      "chunk_count": 15,
      "word_count": 2500,
      "processing_metadata": {...},
      "status": "completed"
    }
  ]
}
```

#### Remove Document
```http
DELETE /api/documents/example.pdf?api_key=your_openai_api_key
```

### Chat Endpoints

#### RAG-Powered Chat
```http
POST /api/rag-chat
Content-Type: application/json

{
  "user_message": "What is quantum machine learning?",
  "model": "gpt-4o-mini",
  "api_key": "your_openai_api_key",
  "use_context": true
}
```

**Response:**
```json
{
  "response": "Based on the uploaded documents, quantum machine learning...",
  "used_context": true
}
```

#### Regular Chat (Fallback)
```http
POST /api/chat
Content-Type: application/json

{
  "user_message": "Hello, how are you?",
  "model": "gpt-4o-mini",
  "api_key": "your_openai_api_key"
}
```

### System Endpoints

#### Service Statistics
```http
GET /api/rag-stats?api_key=your_openai_api_key
```

**Response:**
```json
{
  "stats": {
    "documents_processed": 3,
    "chunks_created": 45,
    "embeddings_generated": 45,
    "queries_processed": 12,
    "active_documents": 3,
    "vector_db_size": 45,
    "last_activity": "2024-01-15T10:30:00"
  }
}
```

#### Health Check
```http
GET /api/health
```

## 🔧 Usage Examples

### Python SDK Usage

```python
import asyncio
from aimakerspace.processing_utils.rag_service import RAGService
from aimakerspace.models import ChunkingConfig, ProcessingLimits

async def example_usage():
    # Initialize RAG service
    rag_service = RAGService(
        api_key="your_openai_api_key",
        chunking_config=ChunkingConfig(chunk_size=1000, overlap=200),
        processing_limits=ProcessingLimits(max_file_size_mb=50)
    )
    
    # Process a document
    processed_doc = await rag_service.process_document(
        source="path/to/document.pdf",
        document_id="my_document",
        use_page_aware_chunking=True
    )
    
    # Chat with context
    response = await rag_service.chat_with_context(
        user_message="What are the key findings?",
        max_context_chunks=5
    )
    
    print(f"Response: {response}")

# Run the example
asyncio.run(example_usage())
```

### Document Factory Usage

```python
from aimakerspace.document_utils import DocumentLoaderFactory

# Create factory
factory = DocumentLoaderFactory()

# Check if a file can be loaded
can_load = factory.can_load("document.pdf")
print(f"Can load PDF: {can_load}")

# Load documents
documents = factory.load_documents("document.pdf")
print(f"Loaded {len(documents)} documents")

# Get supported formats
formats = factory.get_supported_formats()
print(f"Supported formats: {list(formats.keys())}")
```

### Curl Examples

```bash
# Upload a document
curl -X POST "http://localhost:8000/api/upload-document" \
  -F "file=@document.pdf" \
  -F "api_key=your_openai_api_key"

# Process YouTube video
curl -X POST "http://localhost:8000/api/process-youtube" \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "api_key": "your_openai_api_key"
  }'

# RAG chat
curl -X POST "http://localhost:8000/api/rag-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Summarize the key points from the documents",
    "api_key": "your_openai_api_key",
    "use_context": true
  }'
```

## 🔍 Supported File Formats

| Format | Extensions | Description | Features |
|--------|------------|-------------|----------|
| **PDF** | `.pdf` | PDF documents | Page-aware chunking, metadata extraction |
| **Text** | `.txt` | Plain text files | Encoding detection, sentence-aware splitting |
| **Word** | `.docx`, `.doc` | Microsoft Word | Paragraph/table extraction, metadata |
| **Excel** | `.xlsx`, `.xls`, `.csv` | Spreadsheets | Multi-sheet support, data formatting |
| **YouTube** | YouTube URLs | Video transcripts | Auto-detection, metadata extraction |

## ⚙️ Configuration

### Chunking Configuration

```python
from aimakerspace.models import ChunkingConfig

config = ChunkingConfig(
    chunk_size=1000,           # Characters per chunk
    overlap=200,               # Overlap between chunks
    preserve_sentences=True,   # Don't split sentences
    min_chunk_size=100,        # Minimum chunk size
    max_chunk_size=2000        # Maximum chunk size
)
```

### Processing Limits

```python
from aimakerspace.models import ProcessingLimits

limits = ProcessingLimits(
    max_file_size_mb=50,       # Maximum file size
    max_files_per_batch=10,    # Batch processing limit
    timeout_seconds=300        # Processing timeout
)
```

## 🧪 Testing

### Running Tests

```bash
# Run the comprehensive test suite
python test_rag_implementation.py

# Test specific components
python -c "
from aimakerspace.document_utils import DocumentLoaderFactory
factory = DocumentLoaderFactory()
print('Supported formats:', list(factory.get_supported_formats().keys()))
"
```

### Test Coverage

The test suite covers:
- ✅ Document loader factory functionality
- ✅ File format detection and validation
- ✅ RAG service initialization (requires API key)
- ✅ Document processing pipeline (requires API key)
- ✅ Search and retrieval functionality (requires API key)
- ✅ Context-aware chat responses (requires API key)

## 🚀 Deployment

### Environment Variables

```bash
# Required
export OPENAI_API_KEY=your_openai_api_key

# Optional
export MAX_FILE_SIZE_MB=50
export CHUNK_SIZE=1000
export CHUNK_OVERLAP=200
```

### Vercel Deployment

The application is configured for Vercel deployment with:
- `vercel.json` configuration
- Proper Python dependencies in `pyproject.toml`
- API routes in `/api/` directory

### Docker Deployment (Optional)

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000
CMD ["python", "api/app.py"]
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure all dependencies are installed
   uv sync
   
   # Check Python path
   python -c "import sys; print(sys.path)"
   ```

2. **API Key Issues**
   ```bash
   # Verify API key is set
   echo $OPENAI_API_KEY
   
   # Test API key validity
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

3. **File Upload Issues**
   - Check file size limits (50MB default)
   - Verify file format is supported
   - Ensure proper Content-Type headers

4. **Memory Issues**
   - Reduce chunk size for large documents
   - Process documents individually rather than in batches
   - Monitor system memory usage

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for RAG service
rag_service = RAGService(api_key="...", debug=True)
```

## 📈 Performance Optimization

### Chunking Strategy
- **Small documents**: Use smaller chunks (500-800 chars)
- **Large documents**: Use larger chunks (1000-1500 chars)
- **Technical documents**: Preserve sentences and paragraphs

### Vector Database
- **Batch operations**: Process multiple documents together
- **Index optimization**: Regular cleanup of unused vectors
- **Memory management**: Monitor vector database size

### API Performance
- **Caching**: Implement response caching for repeated queries
- **Rate limiting**: Respect OpenAI API rate limits
- **Async processing**: Use async/await for I/O operations

## 🤝 Contributing

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Run linting
black aimakerspace/ api/
isort aimakerspace/ api/
flake8 aimakerspace/ api/

# Run tests
pytest tests/
```

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Add unit tests for new functionality
- Update documentation for API changes

## 📄 License

This project is part of The AI Engineer Challenge. See the main repository for license information.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the test output for specific error messages
3. Ensure all dependencies are properly installed
4. Verify OpenAI API key is valid and has sufficient credits

---

**Last Updated**: September 2024  
**Version**: 1.0.0  
**Status**: Production Ready ✅
