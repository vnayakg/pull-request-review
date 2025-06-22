import os
import fnmatch
from typing import List, Dict, Any, Optional
import logging
from .rag_text_splitter import RAGTextSplitter, TextChunk

logger = logging.getLogger(__name__)


class RAGRepositoryProcessor:
    """Handles repository file processing for RAG system."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.text_splitter = RAGTextSplitter(
            chunk_size=config.get("chunk_size", 500),
            chunk_overlap=config.get("chunk_overlap", 100),
            split_by=config.get("split_by", "token"),
        )
        self.exclude_patterns = config.get("exclude_patterns", [])
        self.max_files = config.get("max_files_to_index", 1000)
        self.include_file_structure = config.get("include_file_structure", True)
        self.include_readme = config.get("include_readme", True)
        self.include_documentation = config.get("include_documentation", True)

    def should_exclude_file(self, file_path: str) -> bool:
        """Check if a file should be excluded based on patterns."""
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
            if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
        return False

    def get_readable_files(self, repo_path: str) -> List[str]:
        """Get list of readable files from repository."""
        readable_extensions = {
            # Code files
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".swift",
            ".kt",
            ".scala",
            ".clj",
            # Web files
            ".html",
            ".css",
            ".scss",
            ".sass",
            ".xml",
            ".json",
            ".yaml",
            ".yml",
            # Documentation
            ".md",
            ".txt",
            ".rst",
            ".adoc",
            ".tex",
            # Config files
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".properties",
            # Shell scripts
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            # Docker and deployment
            "Dockerfile",
            ".dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            # Package managers
            "requirements.txt",
            "package.json",
            "pom.xml",
            "build.gradle",
            "Cargo.toml",
            "go.mod",
            "composer.json",
            "Gemfile",
            "pubspec.yaml",
        }

        files = []
        file_count = 0

        for root, dirs, filenames in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not self.should_exclude_file(os.path.join(root, d))]

            for filename in filenames:
                if file_count >= self.max_files:
                    break

                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, repo_path)

                if self.should_exclude_file(rel_path):
                    continue

                # Check if file has readable extension or is a known config file
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in readable_extensions or filename in readable_extensions:
                    files.append(file_path)
                    file_count += 1

        return files

    def read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content with proper encoding handling."""
        try:
            # Try UTF-8 first
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Try with error handling
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                return None
        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            return None

    def get_file_structure(self, repo_path: str) -> str:
        """Get repository file structure as text."""
        if not self.include_file_structure:
            return ""

        structure_lines = ["Repository Structure:"]

        for root, dirs, files in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not self.should_exclude_file(os.path.join(root, d))]

            level = root.replace(repo_path, "").count(os.sep)
            indent = "  " * level
            rel_path = os.path.relpath(root, repo_path)

            if rel_path != ".":
                structure_lines.append(f"{indent}{os.path.basename(root)}/")

            subindent = "  " * (level + 1)
            for file in files:
                if not self.should_exclude_file(os.path.join(rel_path, file)):
                    structure_lines.append(f"{subindent}{file}")

        return "\n".join(structure_lines)

    def process_repository(self, repo_path: str) -> List[TextChunk]:
        """Process repository and return text chunks."""
        logger.info(f"Processing repository: {repo_path}")

        chunks = []

        # Add file structure if enabled
        if self.include_file_structure:
            structure_text = self.get_file_structure(repo_path)
            if structure_text:
                structure_chunks = self.text_splitter.split_text(
                    structure_text, "repository_structure.txt", 1
                )
                chunks.extend(structure_chunks)

        # Process individual files
        files = self.get_readable_files(repo_path)
        logger.info(f"Found {len(files)} files to process")

        for file_path in files:
            content = self.read_file_content(file_path)
            if content is None:
                continue

            rel_path = os.path.relpath(file_path, repo_path)

            # Add file header
            file_header = f"File: {rel_path}\n"
            full_content = file_header + content

            file_chunks = self.text_splitter.split_text(full_content, rel_path, 1)
            chunks.extend(file_chunks)

            logger.debug(f"Processed {rel_path}: {len(file_chunks)} chunks")

        logger.info(f"Total chunks generated: {len(chunks)}")
        return chunks

    def get_relevant_files_for_diff(self, diff_content: str, repo_path: str) -> List[str]:
        """Get list of files mentioned in the diff."""
        import re

        # Extract file paths from diff
        file_pattern = r"^diff --git a/(.+) b/(.+)$"
        files = set()

        for line in diff_content.split("\n"):
            match = re.match(file_pattern, line)
            if match:
                file_path = match.group(1)
                if not self.should_exclude_file(file_path):
                    files.add(file_path)

        return list(files)

    def get_context_for_files(self, file_paths: List[str], repo_path: str) -> List[TextChunk]:
        """Get context chunks for specific files."""
        chunks = []

        for file_path in file_paths:
            full_path = os.path.join(repo_path, file_path)
            if not os.path.exists(full_path):
                continue

            content = self.read_file_content(full_path)
            if content is None:
                continue

            file_header = f"File: {file_path}\n"
            full_content = file_header + content

            file_chunks = self.text_splitter.split_text(full_content, file_path, 1)
            chunks.extend(file_chunks)

        return chunks
