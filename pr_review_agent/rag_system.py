import os
import hashlib
import tempfile
import subprocess
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from .rag_embedder import RAGEmbedder
from .rag_retriever import RAGRetriever
from .rag_repository_processor import RAGRepositoryProcessor
from .rag_text_splitter import TextChunk

logger = logging.getLogger(__name__)

class RAGSystem:
    """Main RAG system for contextual pull request reviews."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rag_config = config.get('rag', {})
        
        # Initialize components
        self.embedder = RAGEmbedder(
            model_name=self.rag_config.get('embedder', {}).get('model', 'sentence-transformers/all-MiniLM-L6-v2'),
            batch_size=self.rag_config.get('embedder', {}).get('batch_size', 32),
            max_length=self.rag_config.get('embedder', {}).get('max_length', 512)
        )
        
        self.retriever = RAGRetriever(
            top_k=self.rag_config.get('retriever', {}).get('top_k', 10),
            similarity_threshold=self.rag_config.get('retriever', {}).get('similarity_threshold', 0.7)
        )
        
        self.repository_processor = RAGRepositoryProcessor(
            self.rag_config.get('text_splitter', {})
        )
        
        self.cache_dir = self.rag_config.get('storage', {}).get('cache_dir', './.rag_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_repo_hash(self, repo_url: str, branch: str = "main") -> str:
        """Generate a hash for the repository URL and branch."""
        return hashlib.md5(f"{repo_url}:{branch}".encode()).hexdigest()
    
    def _get_cache_path(self, repo_hash: str) -> str:
        """Get cache path for a repository."""
        return os.path.join(self.cache_dir, repo_hash)
    
    def _clone_or_update_repo(self, repo_url: str, repo_path: str, branch: str = "main") -> bool:
        """Clone or update a repository."""
        try:
            if os.path.exists(repo_path):
                # Update existing repo
                logger.info(f"Updating existing repository: {repo_path}")
                subprocess.run(['git', 'fetch'], cwd=repo_path, check=True)
                subprocess.run(['git', 'checkout', branch], cwd=repo_path, check=True)
                subprocess.run(['git', 'pull', 'origin', branch], cwd=repo_path, check=True)
            else:
                # Clone new repo
                logger.info(f"Cloning repository: {repo_url} to {repo_path}")
                subprocess.run(['git', 'clone', '-b', branch, repo_url, repo_path], check=True)
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone/update repository: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during repository operation: {e}")
            return False
    
    def _build_index(self, repo_path: str, cache_path: str) -> bool:
        """Build the RAG index for a repository."""
        try:
            logger.info("Processing repository files...")
            chunks = self.repository_processor.process_repository(repo_path)
            
            if not chunks:
                logger.warning("No chunks generated from repository")
                return False
            
            logger.info(f"Generated {len(chunks)} chunks, creating embeddings...")
            
            # Create embeddings
            texts = [chunk.text for chunk in chunks]
            embeddings = self.embedder.embed_texts(texts)
            
            # Build index
            self.retriever.build_index(chunks, embeddings)
            
            # Save to cache
            self.retriever.save_index(cache_path)
            
            logger.info("RAG index built and cached successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build RAG index: {e}")
            return False
    
    def prepare_repository_context(self, repo_url: str, branch: str = "main") -> bool:
        """Prepare RAG context for a repository."""
        if not self.rag_config.get('enabled', True):
            logger.info("RAG is disabled in configuration")
            return False
        
        repo_hash = self._get_repo_hash(repo_url, branch)
        cache_path = self._get_cache_path(repo_hash)
        
        # Check if index already exists
        if os.path.exists(f"{cache_path}.faiss") and os.path.exists(f"{cache_path}.chunks"):
            logger.info("Loading existing RAG index from cache")
            try:
                self.retriever.load_index(cache_path)
                return True
            except Exception as e:
                logger.warning(f"Failed to load cached index: {e}")
        
        # Clone/update repository
        repo_path = os.path.join(self.cache_dir, f"repo_{repo_hash}")
        if not self._clone_or_update_repo(repo_url, repo_path, branch):
            return False
        
        # Build index
        return self._build_index(repo_path, cache_path)
    
    def get_context_for_diff(self, diff_content: str, repo_url: str, branch: str = "main") -> str:
        """Get relevant context for a specific diff."""
        if not self.rag_config.get('enabled', True):
            return ""
        
        repo_hash = self._get_repo_hash(repo_url, branch)
        cache_path = self._get_cache_path(repo_hash)
        repo_path = os.path.join(self.cache_dir, f"repo_{repo_hash}")
        
        # Ensure index is loaded
        if not hasattr(self.retriever, 'index') or self.retriever.index is None:
            if os.path.exists(f"{cache_path}.faiss"):
                self.retriever.load_index(cache_path)
            else:
                logger.warning("RAG index not found. Call prepare_repository_context() first.")
                return ""
        
        # Extract relevant files from diff
        relevant_files = self.repository_processor.get_relevant_files_for_diff(diff_content, repo_path)
        
        if not relevant_files:
            return ""
        
        # Get context for relevant files
        context_chunks = self.repository_processor.get_context_for_files(relevant_files, repo_path)
        
        if not context_chunks:
            return ""
        
        # Create embeddings for context chunks
        context_texts = [chunk.text for chunk in context_chunks]
        context_embeddings = self.embedder.embed_texts(context_texts)
        
        # Create temporary retriever for context
        temp_retriever = RAGRetriever(
            top_k=self.rag_config.get('retriever', {}).get('top_k', 10),
            similarity_threshold=self.rag_config.get('retriever', {}).get('similarity_threshold', 0.7)
        )
        temp_retriever.build_index(context_chunks, context_embeddings)
        
        # Get relevant context for the diff
        diff_summary = self._extract_diff_summary(diff_content)
        relevant_context = temp_retriever.get_relevant_context(diff_summary, self.embedder)
        
        return relevant_context
    
    def _extract_diff_summary(self, diff_content: str) -> str:
        """Extract a summary of the diff for context retrieval."""
        lines = diff_content.split('\n')
        summary_lines = []
        
        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                # Added lines
                summary_lines.append(line[1:].strip())
            elif line.startswith('-') and not line.startswith('---'):
                # Removed lines
                summary_lines.append(line[1:].strip())
            elif line.startswith('@@'):
                # Hunk headers
                summary_lines.append(line.strip())
        
        return " ".join(summary_lines[:50])  # Limit to first 50 lines
    
    def get_context_for_query(self, query: str, repo_url: str, branch: str = "main") -> str:
        """Get relevant context for a specific query."""
        if not self.rag_config.get('enabled', True):
            return ""
        
        repo_hash = self._get_repo_hash(repo_url, branch)
        cache_path = self._get_cache_path(repo_hash)
        
        # Ensure index is loaded
        if not hasattr(self.retriever, 'index') or self.retriever.index is None:
            if os.path.exists(f"{cache_path}.faiss"):
                self.retriever.load_index(cache_path)
            else:
                logger.warning("RAG index not found. Call prepare_repository_context() first.")
                return ""
        
        return self.retriever.get_relevant_context(query, self.embedder)
    
    def clear_cache(self, repo_url: str = None, branch: str = "main"):
        """Clear RAG cache for a specific repository or all repositories."""
        if repo_url:
            repo_hash = self._get_repo_hash(repo_url, branch)
            cache_path = self._get_cache_path(repo_hash)
            repo_path = os.path.join(self.cache_dir, f"repo_{repo_hash}")
            
            # Remove cache files
            for ext in ['.faiss', '.chunks']:
                if os.path.exists(f"{cache_path}{ext}"):
                    os.remove(f"{cache_path}{ext}")
            
            # Remove repo directory
            if os.path.exists(repo_path):
                import shutil
                shutil.rmtree(repo_path)
            
            logger.info(f"Cleared cache for {repo_url}")
        else:
            # Clear all cache
            import shutil
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
            logger.info("Cleared all RAG cache") 