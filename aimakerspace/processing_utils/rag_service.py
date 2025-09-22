"""
RAG (Retrieval-Augmented Generation) service for orchestrating document processing and chat.

This module provides the main RAGService class that coordinates document loading,
chunking, embedding, storage, and retrieval for context-aware chat responses.
"""

from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import asyncio
from datetime import datetime

from ..models import (
    Document, 
    Chunk, 
    ProcessedDocument, 
    SearchQuery, 
    SearchResult,
    ChunkingConfig,
    ProcessingLimits,
    DocumentProcessingError,
    VectorDatabaseError
)
from ..document_utils.factory import DocumentLoaderFactory
from ..processing_utils.text_splitter import CharacterTextSplitter
from ..processing_utils.page_aware_chunker import PageAwareChunker
from ..processing_utils.conversation_mode_manager import (
    ConversationModeManager, 
    ConversationMode, 
    FallbackRequest, 
    ConflictDetection,
    DocumentModeSession
)
from ..vectordatabase import VectorDatabase
from ..openai_utils.embedding import EmbeddingModel
from ..openai_utils.chatmodel import ChatOpenAI


class RAGService:
    """
    Main service class for RAG operations.
    
    This service orchestrates the entire RAG pipeline:
    1. Document loading and processing
    2. Text chunking with metadata
    3. Embedding generation
    4. Vector storage and retrieval
    5. Context-aware response generation
    """
    
    def __init__(
        self,
        api_key: str,
        chunking_config: Optional[ChunkingConfig] = None,
        processing_limits: Optional[ProcessingLimits] = None,
        embedding_model_name: str = "text-embedding-3-small",
        chat_model_name: str = "gpt-4o-mini"
    ):
        """
        Initialize the RAG service.
        
        Args:
            api_key: OpenAI API key
            chunking_config: Configuration for text chunking
            processing_limits: Limits for document processing
            embedding_model_name: Name of the embedding model to use
            chat_model_name: Name of the chat model to use
        """
        self.api_key = api_key
        self.chunking_config = chunking_config or ChunkingConfig()
        self.processing_limits = processing_limits or ProcessingLimits()
        
        # Initialize components
        self.document_factory = DocumentLoaderFactory(self.processing_limits)
        self.text_splitter = CharacterTextSplitter.from_config(self.chunking_config)
        self.page_aware_chunker = PageAwareChunker(self.chunking_config)
        
        # Initialize OpenAI components
        self.embedding_model = EmbeddingModel(embeddings_model_name=embedding_model_name, api_key=api_key)
        self.chat_model = ChatOpenAI(model_name=chat_model_name, api_key=api_key)
        
        # Initialize vector database with embedding model
        self.vector_db = VectorDatabase(embedding_model=self.embedding_model)
        
        # Initialize conversation mode manager
        self.conversation_manager = ConversationModeManager()
        
        # Track processed documents
        self.processed_documents: Dict[str, ProcessedDocument] = {}
        
        # Service statistics
        self.stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'queries_processed': 0,
            'last_activity': None
        }
    
    async def process_document(
        self, 
        source: Union[Path, str], 
        document_id: Optional[str] = None,
        use_page_aware_chunking: bool = True,
        **loader_kwargs
    ) -> ProcessedDocument:
        """
        Process a document through the complete RAG pipeline.
        
        Args:
            source: File path or URL to process
            document_id: Optional custom document ID
            use_page_aware_chunking: Whether to use page-aware chunking for PDFs
            **loader_kwargs: Additional arguments for document loader
            
        Returns:
            ProcessedDocument with chunks and metadata
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        try:
            # Step 1: Load document
            documents = self.document_factory.load_documents(source, **loader_kwargs)
            if not documents:
                raise DocumentProcessingError(f"No documents loaded from {source}")
            
            # For now, handle single document (can be extended for multiple)
            document = documents[0]
            if document_id:
                document.document_id = document_id
            
            # Step 2: Chunk document
            if use_page_aware_chunking and hasattr(document, 'structure'):
                # Use page-aware chunking for structured documents
                chunks = self.page_aware_chunker.chunk_document_structure(
                    document, 
                    document.structure
                )
            else:
                # Use regular text splitting
                chunks = self._chunk_document_regular(document)
            
            # Step 3: Generate embeddings
            await self._generate_embeddings(chunks)
            
            # Step 4: Store in vector database
            self._store_chunks(chunks)
            
            # Step 5: Create processed document
            processed_doc = ProcessedDocument(
                original_document=document,
                chunks=chunks,
                processing_metadata={
                    'chunking_method': 'page_aware' if use_page_aware_chunking else 'regular',
                    'chunk_count': len(chunks),
                    'processing_time': datetime.now().isoformat(),
                    'chunking_config': {
                        'chunk_size': self.chunking_config.chunk_size,
                        'overlap': self.chunking_config.overlap,
                        'preserve_sentences': self.chunking_config.preserve_sentences
                    }
                }
            )
            
            # Store processed document
            self.processed_documents[document.document_id] = processed_doc
            
            # Update statistics
            self.stats['documents_processed'] += 1
            self.stats['chunks_created'] += len(chunks)
            self.stats['embeddings_generated'] += len(chunks)
            self.stats['last_activity'] = datetime.now().isoformat()
            
            return processed_doc
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to process document {source}: {e}")
    
    def _chunk_document_regular(self, document: Document) -> List[Chunk]:
        """
        Chunk a document using regular text splitting.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of Chunk objects
        """
        text_chunks = self.text_splitter.split_text(document.content)
        chunks = []
        
        for i, chunk_text in enumerate(text_chunks):
            chunk = Chunk(
                content=chunk_text,
                chunk_index=i,
                source_document_id=document.document_id,
                chunk_id=f"{document.document_id}-chunk-{i:03d}",
                metadata={
                    'filename': document.metadata.get('filename', 'unknown'),
                    'document_type': document.document_type.value,
                    'chunk_method': 'regular_text_splitting',
                    'processing_timestamp': datetime.now().isoformat()
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _generate_embeddings(self, chunks: List[Chunk]) -> None:
        """
        Generate embeddings for a list of chunks.
        
        Args:
            chunks: List of chunks to embed
        """
        try:
            # Extract text content
            texts = [chunk.content for chunk in chunks]
            
            # Generate embeddings (synchronous call)
            embeddings = self.embedding_model.get_embeddings(texts)
            
            # Assign embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                
        except Exception as e:
            raise VectorDatabaseError(f"Failed to generate embeddings: {e}")
    
    def _store_chunks(self, chunks: List[Chunk]) -> None:
        """
        Store chunks in the vector database.
        
        Args:
            chunks: List of chunks to store
        """
        try:
            for chunk in chunks:
                if chunk.embedding is None:
                    raise VectorDatabaseError(f"Chunk {chunk.chunk_id} has no embedding")
                
                # Store in vector database
                self.vector_db.add(
                    vector=chunk.embedding,
                    metadata={
                        'chunk_id': chunk.chunk_id,
                        'content': chunk.content,
                        'source_document_id': chunk.source_document_id,
                        'chunk_index': chunk.chunk_index,
                        **chunk.metadata
                    }
                )
                
        except Exception as e:
            raise VectorDatabaseError(f"Failed to store chunks: {e}")
    
    async def search(
        self, 
        query: str, 
        k: int = 5, 
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> SearchResult:
        """
        Search for relevant chunks based on a query.
        
        Args:
            query: Search query text
            k: Number of results to return
            min_score: Minimum similarity score
            filters: Optional metadata filters
            
        Returns:
            SearchResult with relevant chunks and scores
        """
        try:
            # Generate query embedding (synchronous call)
            query_embedding = self.embedding_model.get_embedding(query)
            
            # Search vector database
            results = self.vector_db.search(
                query_vector=query_embedding,
                k=k
            )
            
            # Convert results to chunks
            chunks = []
            scores = []
            
            for result in results:
                if result['score'] >= min_score:
                    # Apply filters if provided
                    if filters and not self._matches_filters(result['metadata'], filters):
                        continue
                    
                    # Reconstruct chunk from metadata
                    chunk = self._reconstruct_chunk_from_metadata(result['metadata'])
                    chunks.append(chunk)
                    scores.append(result['score'])
            
            # Create search query object
            search_query = SearchQuery(
                query_text=query,
                k=k,
                min_score=min_score,
                filters=filters or {}
            )
            
            # Update statistics
            self.stats['queries_processed'] += 1
            self.stats['last_activity'] = datetime.now().isoformat()
            
            return SearchResult(
                chunks=chunks,
                scores=scores,
                query=search_query
            )
            
        except Exception as e:
            raise VectorDatabaseError(f"Search failed: {e}")
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if metadata matches the provided filters.
        
        Args:
            metadata: Chunk metadata
            filters: Filter criteria
            
        Returns:
            True if metadata matches filters
        """
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def _reconstruct_chunk_from_metadata(self, metadata: Dict[str, Any]) -> Chunk:
        """
        Reconstruct a Chunk object from stored metadata.
        
        Args:
            metadata: Stored chunk metadata
            
        Returns:
            Reconstructed Chunk object
        """
        return Chunk(
            content=metadata.get('content', ''),
            chunk_index=metadata.get('chunk_index', 0),
            source_document_id=metadata.get('source_document_id', ''),
            chunk_id=metadata.get('chunk_id', ''),
            page_start=metadata.get('page_start'),
            page_end=metadata.get('page_end'),
            section_title=metadata.get('section_title'),
            section_level=metadata.get('section_level'),
            metadata=metadata
        )
    
    async def chat_with_context(
        self,
        user_message: str,
        context_query: Optional[str] = None,
        max_context_chunks: int = 5,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a chat response using retrieved context.
        
        Args:
            user_message: User's message
            context_query: Optional custom query for context retrieval (defaults to user_message)
            max_context_chunks: Maximum number of context chunks to use
            system_prompt: Optional custom system prompt
            
        Returns:
            Generated response with context
        """
        try:
            # Use user message as context query if not provided
            query = context_query or user_message
            
            # Retrieve relevant context
            search_result = await self.search(query, k=max_context_chunks)
            
            # Build context string
            context_parts = []
            for i, chunk in enumerate(search_result.chunks):
                citation = chunk.get_citation_text() if hasattr(chunk, 'get_citation_text') else f"Document {i+1}"
                context_parts.append(f"[{citation}]\n{chunk.content}")
            
            context = "\n\n".join(context_parts)
            
            # Build system prompt
            if system_prompt is None:
                system_prompt = self._build_default_system_prompt(context)
            else:
                system_prompt = system_prompt.replace("{context}", context)
            
            # Generate response (synchronous call)
            response = self.chat_model.run(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response
            
        except Exception as e:
            # Fallback to response without context (synchronous call)
            return self.chat_model.run(
                messages=[{"role": "user", "content": user_message}]
            )
    
    def _build_default_system_prompt(self, context: str) -> str:
        """
        Build the default system prompt with context.
        
        Args:
            context: Retrieved context text
            
        Returns:
            System prompt with embedded context
        """
        return f"""You are a helpful AI assistant. Use only the provided context to answer the user's question.  
            If the context does not contain relevant information, say:  
            "I couldn’t find information in the provided sources."  

            Context:
            {context}

            Instructions:
            - Base answers strictly on the context above  
            - Always cite the specific source(s) you used, including page numbers if they are available in the context  
            - Format: [Title, p. X] or [Title, pp. X–Y]  
            - If page numbers are not available in the context, cite the source without them  
            - Never invent or guess page numbers or citations  
            - Be concise and accurate
        """
    
    def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a processed document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Document information or None if not found
        """
        if document_id not in self.processed_documents:
            return None
        
        processed_doc = self.processed_documents[document_id]
        
        return {
            'document_id': document_id,
            'filename': processed_doc.original_document.metadata.get('filename', 'unknown'),
            'document_type': processed_doc.original_document.document_type.value,
            'chunk_count': len(processed_doc.chunks),
            'word_count': processed_doc.original_document.get_word_count(),
            'processing_metadata': processed_doc.processing_metadata,
            'status': processed_doc.status.value
        }
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all processed documents.
        
        Returns:
            List of document information dictionaries
        """
        return [
            self.get_document_info(doc_id) 
            for doc_id in self.processed_documents.keys()
        ]
    
    def remove_document(self, document_id: str) -> bool:
        """
        Remove a document and its chunks from the system.
        
        Args:
            document_id: ID of the document to remove
            
        Returns:
            True if document was removed, False if not found
        """
        if document_id not in self.processed_documents:
            return False
        
        try:
            # Remove chunks from vector database
            processed_doc = self.processed_documents[document_id]
            for chunk in processed_doc.chunks:
                # Note: VectorDatabase would need a remove method
                # This is a placeholder for the interface
                if hasattr(self.vector_db, 'remove'):
                    self.vector_db.remove(chunk.chunk_id)
            
            # Remove from processed documents
            del self.processed_documents[document_id]
            
            # Update statistics
            self.stats['documents_processed'] -= 1
            self.stats['chunks_created'] -= len(processed_doc.chunks)
            self.stats['last_activity'] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            print(f"Warning: Failed to fully remove document {document_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.
        
        Returns:
            Dictionary with service statistics
        """
        return {
            **self.stats,
            'active_documents': len(self.processed_documents),
            'vector_db_size': len(self.vector_db.vectors) if hasattr(self.vector_db, 'vectors') else 0
        }
    
    def clear_all_documents(self) -> None:
        """
        Clear all processed documents and reset the system.
        """
        self.processed_documents.clear()
        
        # Clear vector database
        if hasattr(self.vector_db, 'clear'):
            self.vector_db.clear()
        else:
            # Reinitialize if no clear method
            self.vector_db = VectorDatabase()
        
        # Reset statistics
        self.stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'queries_processed': 0,
            'last_activity': datetime.now().isoformat()
        }
    
    # Conversation Mode Management Methods
    
    def enter_document_mode(self, documents: List[Document]) -> DocumentModeSession:
        """
        Enter document mode with the provided documents.
        
        Args:
            documents: List of documents to activate
            
        Returns:
            Updated session
        """
        return self.conversation_manager.enter_document_mode(documents)
    
    def exit_document_mode(self) -> DocumentModeSession:
        """
        Exit document mode and return to general mode.
        
        Returns:
            Updated session
        """
        return self.conversation_manager.exit_document_mode()
    
    async def query_with_fallback(
        self,
        query: str,
        max_context_chunks: int = 5,
        context_aware_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Query with intelligent fallback detection.
        
        Args:
            query: User's query
            max_context_chunks: Maximum number of context chunks
            context_aware_threshold: Optional custom threshold
            
        Returns:
            Dictionary with response, fallback info, and citations
        """
        # Perform search
        search_result = await self.search(query, k=max_context_chunks)
        
        # Check for fallback need
        needs_fallback, fallback_request = self.conversation_manager.query_with_fallback(
            query, search_result, context_aware_threshold
        )
        
        if needs_fallback and fallback_request:
            return {
                'needs_fallback': True,
                'fallback_request': {
                    'query': fallback_request.query,
                    'confidence_score': fallback_request.confidence_score,
                    'explanation': fallback_request.explanation,
                    'timestamp': fallback_request.timestamp
                },
                'retrieved_chunks': [
                    {
                        'content': chunk.content,
                        'source_document_id': chunk.source_document_id,
                        'chunk_id': chunk.chunk_id,
                        'metadata': chunk.metadata
                    }
                    for chunk in fallback_request.retrieved_chunks
                ]
            }
        
        # Generate response with context
        response = await self.chat_with_context(
            query, 
            max_context_chunks=max_context_chunks
        )
        
        # Build citations
        citations = []
        for chunk in search_result.chunks:
            doc_info = self.get_document_info(chunk.source_document_id)
            citations.append({
                'chunk_id': chunk.chunk_id,
                'document_name': doc_info['filename'] if doc_info else 'Unknown',
                'document_id': chunk.source_document_id,
                'content_preview': chunk.content[:200] + '...' if len(chunk.content) > 200 else chunk.content
            })
        
        return {
            'needs_fallback': False,
            'response': response,
            'citations': citations,
            'confidence_score': self.conversation_manager.current_session.conversation_context.get('last_confidence_score', 0.0) if self.conversation_manager.current_session else 0.0
        }
    
    async def detect_multi_document_conflicts(
        self,
        query: str,
        max_context_chunks: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Detect conflicts between multiple documents for a query.
        
        Args:
            query: User's query
            max_context_chunks: Maximum chunks per document
            
        Returns:
            Conflict information if detected, None otherwise
        """
        if not self.conversation_manager.current_session:
            return None
        
        # Get search results for each document
        search_results_by_document = {}
        
        for doc_id in self.conversation_manager.current_session.documents.keys():
            # Search with document filter
            search_result = await self.search(
                query, 
                k=max_context_chunks,
                filters={'source_document_id': doc_id}
            )
            if search_result.chunks:
                search_results_by_document[doc_id] = search_result
        
        # Detect conflicts
        conflict = self.conversation_manager.detect_multi_document_conflicts(
            query, search_results_by_document
        )
        
        if conflict:
            return {
                'query': conflict.query,
                'explanation': conflict.explanation,
                'conflicting_documents': [
                    {
                        'document_id': doc_id,
                        'document_name': self._get_document_name(doc_id),
                        'confidence_score': conflict.confidence_scores.get(doc_id, 0.0),
                        'relevant_chunks': [
                            {
                                'content': chunk.content[:200] + '...' if len(chunk.content) > 200 else chunk.content,
                                'chunk_id': chunk.chunk_id
                            }
                            for chunk in chunks[:2]  # Show top 2 chunks
                        ]
                    }
                    for doc_id, chunks in conflict.conflicting_documents.items()
                ]
            }
        
        return None
    
    def resolve_conflict(
        self,
        query: str,
        selected_document_id: str,
        confidence_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Record user's resolution of a multi-document conflict.
        
        Args:
            query: The query that caused the conflict
            selected_document_id: Document ID the user selected
            confidence_scores: Confidence scores for all documents
            
        Returns:
            Resolution record
        """
        resolution = self.conversation_manager.resolve_conflict(
            query, selected_document_id, confidence_scores
        )
        
        return {
            'query': resolution.query,
            'selected_document': resolution.selected_document,
            'selected_document_name': self._get_document_name(resolution.selected_document),
            'timestamp': resolution.timestamp,
            'confidence_scores': resolution.confidence_scores
        }
    
    def get_conversation_status(self) -> Dict[str, Any]:
        """
        Get current conversation mode status.
        
        Returns:
            Status information
        """
        return self.conversation_manager.get_session_status()
    
    def load_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Load a conversation session from stored data.
        
        Args:
            session_data: Session data dictionary
            
        Returns:
            True if loaded successfully
        """
        return self.conversation_manager.load_session(session_data)
    
    def get_session_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current session data for storage.
        
        Returns:
            Session data dictionary or None
        """
        if self.conversation_manager.current_session:
            return self.conversation_manager.current_session.to_dict()
        return None
    
    def _get_document_name(self, document_id: str) -> str:
        """
        Get display name for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document display name
        """
        doc_info = self.get_document_info(document_id)
        if doc_info:
            return doc_info['filename']
        return f"Document {document_id[:8]}..."
    
    def update_document_chunks_in_session(self, document_id: str) -> None:
        """
        Update document chunk information in the conversation session.
        
        Args:
            document_id: Document ID to update
        """
        if document_id in self.processed_documents:
            processed_doc = self.processed_documents[document_id]
            vector_ids = [chunk.chunk_id for chunk in processed_doc.chunks]
            
            self.conversation_manager.update_document_chunks(
                document_id, 
                len(processed_doc.chunks), 
                vector_ids
            )


# Convenience functions for quick RAG operations
async def process_and_chat(
    source: Union[Path, str],
    user_message: str,
    api_key: str,
    **kwargs
) -> str:
    """
    Convenience function to process a document and immediately chat with it.
    
    Args:
        source: Document source to process
        user_message: User's question
        api_key: OpenAI API key
        **kwargs: Additional arguments for processing
        
    Returns:
        Chat response with context from the document
    """
    rag_service = RAGService(api_key=api_key)
    await rag_service.process_document(source, **kwargs)
    return await rag_service.chat_with_context(user_message)


async def quick_search(
    source: Union[Path, str],
    query: str,
    api_key: str,
    k: int = 5
) -> List[str]:
    """
    Convenience function to quickly search a document.
    
    Args:
        source: Document source to search
        query: Search query
        api_key: OpenAI API key
        k: Number of results to return
        
    Returns:
        List of relevant text chunks
    """
    rag_service = RAGService(api_key=api_key)
    await rag_service.process_document(source)
    search_result = await rag_service.search(query, k=k)
    return [chunk.content for chunk in search_result.chunks]
