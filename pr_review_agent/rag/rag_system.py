import os
import hashlib
import tempfile
import subprocess
import re # Added for _extract_diff_summary
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from .embedder import RAGEmbedder
from .retriever import RAGRetriever
from .repository_processor import RAGRepositoryProcessor
from .text_splitter import TextChunk

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
        
        retriever_config = self.rag_config.get('retriever', {})
        self.retriever = RAGRetriever(
            top_k=retriever_config.get('top_k', 10),
            similarity_threshold=retriever_config.get('similarity_threshold', 0.7),
            max_context_length=retriever_config.get('max_context_length', 2000)
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
        
        # Ensure the main repository index is loaded and available in self.retriever
        if not hasattr(self.retriever, 'index') or self.retriever.index is None:
            # Attempt to load it if cache path seems valid
            if os.path.exists(f"{cache_path}.faiss"):
                logger.info(f"Main index not loaded for {repo_url}, attempting to load from {cache_path}")
                try:
                    self.retriever.load_index(cache_path)
                except Exception as e:
                    logger.error(f"Failed to load index for {repo_url} from {cache_path}: {e}")
                    return "" # Or handle error appropriately
            else:
                logger.warning(f"RAG index not found for {repo_url} at {cache_path}. Call prepare_repository_context() first.")
                return ""

        # Extract a summary from the diff content to use as a query
        diff_summary_query = self._extract_diff_summary(diff_content)

        if not diff_summary_query:
            logger.info("Empty diff summary, cannot retrieve context.")
            return ""

        logger.info(f"Querying main index with diff summary for {repo_url}")
        # Use the main retriever (self.retriever) to get context
        # The max_context_length can be made configurable later (as per plan step 3)
        relevant_context = self.retriever.get_relevant_context(
            query=diff_summary_query,
            embedder=self.embedder
            # max_context_length can be passed here if configured
        )
        
        if relevant_context:
            logger.info(f"Retrieved {len(relevant_context)} characters of context for the diff.")
        else:
            logger.info("No relevant context found for the diff summary in the main index.")

        return relevant_context
    
    def _extract_diff_summary(self, diff_content: str, max_summary_length: int = 1000) -> str:
        """
        Extract a more meaningful summary of the diff for context retrieval.
        Focuses on changed lines and their immediate context, including function/class definitions.
        """
        summary_parts = []
        current_file = None
        hunk_lines_collected = 0 # Counter for lines collected within the current hunk

        # Regex to identify potential function/class definition lines
        definition_re = re.compile(r'^\s*(def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)')
        file_header_re = re.compile(r'^diff --git a/(.+?) b/(.+)$')
        hunk_header_re = re.compile(r'^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@(.*)$') # Capture content after

        lines = diff_content.splitlines()
        
        # First pass: collect file names mentioned in the diff
        changed_files_info = []
        for line in lines:
            file_match = file_header_re.match(line)
            if file_match:
                changed_files_info.append(f"File changed: {file_match.group(2)}")

        if changed_files_info:
            summary_parts.append("Changes in files: " + ", ".join(changed_files_info))

        context_window = 2  # Number of context lines to include around a change

        for i, line in enumerate(lines):
            if len(" ".join(summary_parts)) > max_summary_length:
                break

            hunk_match = hunk_header_re.match(line)
            if hunk_match:
                hunk_context = hunk_match.group(1).strip()
                if hunk_context:
                    summary_parts.append(f"Change context: {hunk_context}")
                hunk_lines_collected = 0 # Reset for new hunk
                # Look for definitions before the hunk
                for j in range(max(0, i - 5), i):
                    def_match = definition_re.match(lines[j])
                    if def_match:
                        summary_parts.append(f"In {def_match.group(1)} {def_match.group(2)}:")
                        break
                continue

            # Prioritize added/removed lines and their immediate context
            if line.startswith('+') and not line.startswith('+++'):
                if hunk_lines_collected < 15 : # Limit lines per hunk
                    # Add context before
                    for k in range(max(0, i - context_window), i):
                        if lines[k].startswith(' ') and lines[k] not in summary_parts[-context_window:]: # Avoid duplicate context
                            summary_parts.append(lines[k].strip())
                    summary_parts.append(f"Added: {line[1:].strip()}")
                    hunk_lines_collected +=1
            elif line.startswith('-') and not line.startswith('---'):
                if hunk_lines_collected < 15 : # Limit lines per hunk
                     # Add context before
                    for k in range(max(0, i - context_window), i):
                         if lines[k].startswith(' ') and lines[k] not in summary_parts[-context_window:]: # Avoid duplicate context
                            summary_parts.append(lines[k].strip())
                    summary_parts.append(f"Removed: {line[1:].strip()}")
                    hunk_lines_collected +=1
            elif line.startswith(' '): # Context line
                # Check if this context line is near a change that was just added
                is_near_added_change = any(p.startswith("Added:") for p in summary_parts[-2:])
                is_near_removed_change = any(p.startswith("Removed:") for p in summary_parts[-2:])
                if (is_near_added_change or is_near_removed_change) and hunk_lines_collected < 15 and line.strip() not in summary_parts[-context_window:]:
                    summary_parts.append(line.strip())
                    # hunk_lines_collected +=1 # Context lines don't count as much towards the hunk limit

            # Capture definitions if they appear
            def_match = definition_re.match(line)
            if def_match and hunk_lines_collected < 15:
                summary_parts.append(f"Context: {def_match.group(1)} {def_match.group(2)}")


        final_summary = " ".join(summary_parts)
        if len(final_summary) > max_summary_length:
            # A simple way to truncate, might cut mid-word.
            # More sophisticated truncation (e.g., by tokens) could be added if needed.
            cutoff_index = final_summary.rfind(' ', 0, max_summary_length)
            if cutoff_index == -1: # no space found
                return final_summary[:max_summary_length]
            return final_summary[:cutoff_index]

        return final_summary

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
    
    def clear_cache(self, repo_url: Optional[str] = None, branch: str = "main") -> None:
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