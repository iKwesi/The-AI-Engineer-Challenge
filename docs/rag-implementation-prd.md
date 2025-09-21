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
- [x] Create `aimakerspace/models.py` with domain models
- [x] Create `aimakerspace/document_utils/` directory structure
- [x] Create `aimakerspace/processing_utils/` directory structure

### Phase 2: Document Processing Utilities
- [x] **aimakerspace/document_utils/base.py**
  - [x] Create abstract `DocumentLoader` base class
  - [x] Define common interface for all document loaders
  
- [x] **aimakerspace/document_utils/text_utils.py**
  - [x] Move `TextFileLoader` from `text_utils.py`
  - [x] Enhance with better encoding handling
  - [x] Add comprehensive error handling
  
- [x] **aimakerspace/document_utils/pdf_utils.py**
  - [x] Move `PDFLoader` from `text_utils.py`
  - [x] Enhance with metadata extraction
  - [x] Add password-protected PDF handling
  
- [x] **aimakerspace/document_utils/word_utils.py**
  - [x] Create `WordDocumentLoader` for .docx/.doc files
  - [x] Handle paragraphs, tables, and formatting
  - [x] Extract metadata (author, creation date, etc.)
  
- [x] **aimakerspace/document_utils/excel_utils.py**
  - [x] Create `ExcelLoader` for .xlsx/.xls/.csv files
  - [x] Handle multiple sheets
  - [x] Convert data to readable text format
  
- [x] **aimakerspace/document_utils/youtube_utils.py**
  - [x] Create `YouTubeLoader` for video transcripts
  - [x] Extract video metadata (title, duration, channel)
  - [x] Handle transcript formatting and timestamps
  
- [x] **aimakerspace/document_utils/factory.py**
  - [x] Create `DocumentLoaderFactory` for auto-selection
  - [x] Support file extension and URL pattern matching
  - [x] Provide clear error messages for unsupported formats

### Phase 3: Text Processing Utilities
- [x] **aimakerspace/processing_utils/text_splitter.py**
  - [x] Move `CharacterTextSplitter` from `text_utils.py`
  - [x] Enhance with sentence-aware splitting
  - [x] Add support for different splitting strategies
  
- [x] **aimakerspace/processing_utils/rag_service.py**
  - [x] Create `RAGService` class for orchestration
  - [x] Integrate with existing `VectorDatabase`
  - [x] Integrate with existing `EmbeddingModel`
  - [x] Integrate with existing `ChatOpenAI`
  - [x] Implement context retrieval and response generation

### Phase 4: API Layer Enhancement
- [x] **api/models.py**
  - [x] Create Pydantic models for document upload requests
  - [x] Create models for RAG chat requests
  - [x] Create response models with proper validation
  
- [x] **api/app.py - New Endpoints**
  - [x] `POST /api/upload-document` - File upload endpoint
  - [x] `POST /api/process-youtube` - YouTube URL processing
  - [x] `POST /api/rag-chat` - RAG-powered chat endpoint
  - [x] `GET /api/documents` - List processed documents
  - [x] `DELETE /api/documents/{id}` - Remove documents from vector DB
  - [x] `GET /api/rag-stats` - Service statistics endpoint

### Phase 5: YouTube Integration
- [x] **YouTube URL Detection**
  - [x] Implement regex pattern for YouTube URL detection
  - [x] Support both youtube.com and youtu.be formats
  - [x] Handle URL parameters and timestamps
  
- [x] **Transcript Processing**
  - [x] Integrate `youtube-transcript-api`
  - [x] Handle videos without transcripts gracefully
  - [x] Support multiple languages
  - [x] Extract and store video metadata

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
