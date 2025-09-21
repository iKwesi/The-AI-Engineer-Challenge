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
        self.embedding_model = EmbeddingModel(api_key=api_key, model=embedding_model_name)
        self.chat_model = ChatOpenAI(api_key=api_key, model=chat_model_name)
        
        # Initialize vector database
        self.vector_db = VectorDatabase()
        
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
            response = self.chat_model.agenerate_response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response
            
        except Exception as e:
            # Fallback to response without context (synchronous call)
            return self.chat_model.agenerate_response(
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
        return f"""You are a helpful AI assistant. Use the following context to answer the user's question. 
If the context doesn't contain relevant information, say so and provide a general response.

Context:
{context}

Instructions:
- Answer based on the provided context when relevant
- Cite sources when possible (e.g., "According to the document...")
- If context is insufficient, acknowledge this and provide general guidance
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
