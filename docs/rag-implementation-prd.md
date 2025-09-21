# RAG System Implementation - Product Requirements & Checklist

## Overview
This document outlines the implementation of a Retrieval-Augmented Generation (RAG) system for The AI Engineer Challenge, extending the existing chat application with document processing and context-aware responses.

## Project Context
- **Base Application**: Existing Next.js frontend + FastAPI backend chat application
- **Enhancement Goal**: Add document upload, processing, and RAG-powered chat capabilities
- **Assignment Requirements**: Support PDF upload, multi-format documents, and YouTube transcript processing

## Architecture Decisions Made

### 1. Dependency Management
- ✅ **Decision**: Use root-level `pyproject.toml` for monorepo dependency management
- ✅ **Rationale**: Single source of truth, easier `uv sync`, shared dependencies between `aimakerspace` and `api`

### 2. Code Organization (Separation of Concerns)
- ✅ **Decision**: Refactor `text_utils.py` into focused utilities following Single Responsibility Principle
- ✅ **Rationale**: Current `text_utils.py` violates SRP (handles PDF + text + splitting)
- ✅ **Decision**: Keep `openai_utils/` intact (well-designed)
- ✅ **Decision**: Use `utils` naming convention instead of `loaders`

### 3. YouTube Integration
- ✅ **Decision**: Auto-detect YouTube links in chat (not dedicated upload button)
- ✅ **Rationale**: Better UX, natural conversation flow, bypasses OpenAI's external link limitations

## Final Architecture

```
aimakerspace/
├── openai_utils/           # ✅ KEEP INTACT - OpenAI integrations
│   ├── embedding.py        # ✅ Perfect as-is
│   ├── chatmodel.py        # ✅ Perfect as-is
│   └── prompts.py          # ✅ Perfect as-is
├── document_utils/         # 🆕 NEW - Document processing utilities
│   ├── __init__.py
│   ├── base.py             # Abstract DocumentLoader base class
│   ├── text_utils.py       # Text file processing (.txt)
│   ├── pdf_utils.py        # PDF processing (.pdf)
│   ├── word_utils.py       # Word document processing (.docx, .doc)
│   ├── excel_utils.py      # Excel/CSV processing (.xlsx, .xls, .csv)
│   ├── youtube_utils.py    # YouTube transcript processing
│   └── factory.py          # Auto-selection of appropriate utility
├── processing_utils/       # 🆕 NEW - Text processing utilities
│   ├── __init__.py
│   ├── text_splitter.py    # CharacterTextSplitter (moved from text_utils.py)
│   └── rag_service.py      # RAG orchestration
├── models.py               # 🆕 Simple domain models
├── vectordatabase.py       # ✅ KEEP - works well
└── text_utils.py           # ❌ DEPRECATE - functionality moved to document_utils/

api/
├── app.py                  # ✅ ENHANCE - Add new endpoints, keep HTTP concerns only
├── models.py               # 🆕 NEW - Pydantic request/response models
└── (existing files)
```

## Implementation Checklist

### Phase 1: Foundation & Architecture Setup
- [x] Update root `pyproject.toml` with all required dependencies
- [ ] Create `aimakerspace/models.py` with domain models
- [ ] Create `aimakerspace/document_utils/` directory structure
- [ ] Create `aimakerspace/processing_utils/` directory structure

### Phase 2: Document Processing Utilities
- [ ] **aimakerspace/document_utils/base.py**
  - [ ] Create abstract `DocumentLoader` base class
  - [ ] Define common interface for all document loaders
  
- [ ] **aimakerspace/document_utils/text_utils.py**
  - [ ] Move `TextFileLoader` from `text_utils.py`
  - [ ] Enhance with better encoding handling
  - [ ] Add comprehensive error handling
  
- [ ] **aimakerspace/document_utils/pdf_utils.py**
  - [ ] Move `PDFLoader` from `text_utils.py`
  - [ ] Enhance with metadata extraction
  - [ ] Add password-protected PDF handling
  
- [ ] **aimakerspace/document_utils/word_utils.py**
  - [ ] Create `WordDocumentLoader` for .docx/.doc files
  - [ ] Handle paragraphs, tables, and formatting
  - [ ] Extract metadata (author, creation date, etc.)
  
- [ ] **aimakerspace/document_utils/excel_utils.py**
  - [ ] Create `ExcelLoader` for .xlsx/.xls/.csv files
  - [ ] Handle multiple sheets
  - [ ] Convert data to readable text format
  
- [ ] **aimakerspace/document_utils/youtube_utils.py**
  - [ ] Create `YouTubeLoader` for video transcripts
  - [ ] Extract video metadata (title, duration, channel)
  - [ ] Handle transcript formatting and timestamps
  
- [ ] **aimakerspace/document_utils/factory.py**
  - [ ] Create `DocumentUtilsFactory` for auto-selection
  - [ ] Support file extension and URL pattern matching
  - [ ] Provide clear error messages for unsupported formats

### Phase 3: Text Processing Utilities
- [ ] **aimakerspace/processing_utils/text_splitter.py**
  - [ ] Move `CharacterTextSplitter` from `text_utils.py`
  - [ ] Enhance with sentence-aware splitting
  - [ ] Add support for different splitting strategies
  
- [ ] **aimakerspace/processing_utils/rag_service.py**
  - [ ] Create `RAGService` class for orchestration
  - [ ] Integrate with existing `VectorDatabase`
  - [ ] Integrate with existing `EmbeddingModel`
  - [ ] Integrate with existing `ChatOpenAI`
  - [ ] Implement context retrieval and response generation

### Phase 4: API Layer Enhancement
- [ ] **api/models.py**
  - [ ] Create Pydantic models for document upload requests
  - [ ] Create models for RAG chat requests
  - [ ] Create response models with proper validation
  
- [ ] **api/app.py - New Endpoints**
  - [ ] `POST /api/upload-document` - File upload endpoint
  - [ ] `POST /api/process-youtube` - YouTube URL processing
  - [ ] `POST /api/rag-chat` - RAG-powered chat endpoint
  - [ ] `GET /api/documents` - List processed documents
  - [ ] `DELETE /api/documents/{id}` - Remove documents from vector DB

### Phase 5: YouTube Integration
- [ ] **YouTube URL Detection**
  - [ ] Implement regex pattern for YouTube URL detection
  - [ ] Support both youtube.com and youtu.be formats
  - [ ] Handle URL parameters and timestamps
  
- [ ] **Transcript Processing**
  - [ ] Integrate `youtube-transcript-api`
  - [ ] Handle videos without transcripts gracefully
  - [ ] Support multiple languages
  - [ ] Extract and store video metadata

### Phase 6: Frontend Integration
- [ ] **File Upload Component**
  - [ ] Create drag-and-drop file upload interface
  - [ ] Support multiple file formats
  - [ ] Show upload progress and processing status
  
- [ ] **YouTube Link Detection**
  - [ ] Auto-detect YouTube URLs in chat messages
  - [ ] Show processing indicators for video analysis
  - [ ] Provide user feedback during transcript extraction
  
- [ ] **RAG Chat Enhancement**
  - [ ] Modify existing chat to use RAG when documents are available
  - [ ] Show document sources in responses
  - [ ] Allow users to toggle RAG on/off

### Phase 7: Testing & Quality Assurance
- [ ] **Unit Tests**
  - [ ] Test all document loaders with sample files
  - [ ] Test text splitter with various content types
  - [ ] Test RAG service integration
  - [ ] Test API endpoints with proper mocking
  
- [ ] **Integration Tests**
  - [ ] Test end-to-end document processing pipeline
  - [ ] Test YouTube transcript processing
  - [ ] Test RAG chat with real documents
  
- [ ] **Error Handling Tests**
  - [ ] Test file size limits
  - [ ] Test unsupported file formats
  - [ ] Test network failures for YouTube processing
  - [ ] Test malformed documents

### Phase 8: Documentation & Deployment
- [ ] **Update API README**
  - [ ] Document new endpoints and request/response formats
  - [ ] Provide usage examples
  - [ ] Document supported file formats and limitations
  
- [ ] **Update Project Documentation**
  - [ ] Document new architecture and design decisions
  - [ ] Provide setup and usage instructions
  - [ ] Document environment variables and configuration
  
- [ ] **Deployment Preparation**
  - [ ] Ensure all dependencies are properly specified
  - [ ] Test deployment on Vercel
  - [ ] Verify file upload limits and storage

## Technical Specifications

### File Processing Limits
- **Maximum file size**: 50MB per file
- **Supported formats**: PDF, TXT, DOCX, DOC, XLSX, XLS, CSV
- **YouTube**: Any public video with available transcripts

### Text Chunking Strategy
- **Chunk size**: 1000 characters (configurable)
- **Overlap**: 200 characters (configurable)
- **Strategy**: Character-based with sentence awareness

### Vector Database Configuration
- **Embedding model**: text-embedding-3-small (OpenAI)
- **Vector dimensions**: 1536
- **Similarity search**: Top-k retrieval (k=5 default)

### API Rate Limits
- **File uploads**: 10 files per minute per user
- **YouTube processing**: 5 videos per minute per user
- **Chat requests**: 60 requests per minute per user

## Success Criteria

### Assignment Requirements (Must Have)
- [ ] ✅ PDF upload and processing
- [ ] ✅ RAG system using aimakerspace library
- [ ] ✅ Chat with PDF using simple RAG
- [ ] ✅ Multi-format document support
- [ ] ✅ Deployed to Vercel

### Enhanced Features (Nice to Have)
- [ ] YouTube transcript processing
- [ ] Auto-detection of YouTube links
- [ ] Multiple document management
- [ ] Document source attribution in responses
- [ ] Advanced chunking strategies

### Code Quality Standards
- [ ] Single Responsibility Principle followed
- [ ] Comprehensive test coverage (>80%)
- [ ] Clear separation of concerns
- [ ] Proper error handling and user feedback
- [ ] Clean, documented code

## Risk Mitigation

### Technical Risks
- **Large file processing**: Implement streaming and chunking
- **YouTube API limits**: Implement retry logic and caching
- **Vector database performance**: Optimize embedding and search
- **Memory usage**: Implement proper cleanup and garbage collection

### User Experience Risks
- **Slow processing**: Provide clear progress indicators
- **Failed uploads**: Implement retry mechanisms and clear error messages
- **Poor search results**: Fine-tune chunking and retrieval parameters

## Notes
- This document should be updated as implementation progresses
- Each completed task should be marked with ✅
- Any architectural changes should be documented and justified
- Regular reviews should be conducted to ensure alignment with goals
