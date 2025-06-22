import os
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple, Optional
from .text_splitter import TextChunk
from .embedder import RAGEmbedder # Import for type hinting
import logging

logger = logging.getLogger(__name__)

class RAGRetriever:
    """Handles similarity search for RAG system using FAISS."""
    
    def __init__(self, top_k: int = 10, similarity_threshold: float = 0.7, max_context_length: int = 2000):
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.max_context_length = max_context_length
        self.index = None
        self.chunks = []
        self.embeddings = None
        self.dimension = None
    
    def build_index(self, chunks: List[TextChunk], embeddings: np.ndarray):
        """Build FAISS index from chunks and their embeddings."""
        if not chunks or len(chunks) == 0:
            logger.warning("No chunks provided for index building")
            return
        
        if embeddings.shape[0] != len(chunks):
            raise ValueError(f"Number of embeddings ({embeddings.shape[0]}) doesn't match number of chunks ({len(chunks)})")
        
        self.chunks = chunks
        self.embeddings = embeddings
        self.dimension = embeddings.shape[1]
        
        # Create FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.index.add(embeddings.astype('float32'))
        
        logger.info(f"Built FAISS index with {len(chunks)} chunks and dimension {self.dimension}")
    
    def search(self, query_embedding: np.ndarray) -> List[Tuple[TextChunk, float]]:
        """Search for similar chunks given a query embedding."""
        if self.index is None:
            logger.warning("Index not built. Call build_index() first.")
            return []
        
        # Ensure query embedding is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), self.top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks) and score >= self.similarity_threshold:
                results.append((self.chunks[idx], float(score)))
        
        return results
    
    def search_by_text(self, query_text: str, embedder: RAGEmbedder) -> List[Tuple[TextChunk, float]]:
        """Search for similar chunks given a query text."""
        query_embedding = embedder.embed_single_text(query_text)
        return self.search(query_embedding)
    
    def save_index(self, filepath: str):
        """Save the index and chunks to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{filepath}.faiss")
        
        # Save chunks and metadata
        with open(f"{filepath}.chunks", 'wb') as f:
            pickle.dump(self.chunks, f)
        
        logger.info(f"Saved index to {filepath}")
    
    def load_index(self, filepath: str):
        """Load the index and chunks from disk."""
        try:
            # Load FAISS index
            self.index = faiss.read_index(f"{filepath}.faiss")
            
            # Load chunks
            with open(f"{filepath}.chunks", 'rb') as f:
                self.chunks = pickle.load(f)
            
            self.dimension = self.index.d
            logger.info(f"Loaded index from {filepath} with {len(self.chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to load index from {filepath}: {e}")
            raise
    
    def get_relevant_context(self, query: str, embedder: RAGEmbedder) -> str:
        """Get relevant context as a formatted string for the query, using instance's max_context_length."""
        results = self.search_by_text(query, embedder)
        
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for chunk, score in results:
            chunk_text = f"File: {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line})\n{chunk.text}\n"
            
            if current_length + len(chunk_text) > self.max_context_length:
                break
            
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        return "\n".join(context_parts) 