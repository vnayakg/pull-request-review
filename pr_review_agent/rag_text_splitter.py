import re
import tiktoken
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""

    text: str
    file_path: str
    start_line: int
    end_line: int
    chunk_id: str
    metadata: Dict[str, Any] = None


class RAGTextSplitter:
    """Handles text splitting for RAG system."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100, split_by: str = "token"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.split_by = split_by
        self.tokenizer = None
        if split_by == "token":
            self._init_tokenizer()

    def _init_tokenizer(self):
        """Initialize tokenizer for token-based splitting."""
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to initialize tokenizer: {e}")
            self.split_by = "character"

    def split_text(self, text: str, file_path: str, start_line: int = 1) -> List[TextChunk]:
        """Split text into chunks based on the specified method."""
        if self.split_by == "token":
            return self._split_by_tokens(text, file_path, start_line)
        elif self.split_by == "sentence":
            return self._split_by_sentences(text, file_path, start_line)
        else:
            return self._split_by_characters(text, file_path, start_line)

    def _split_by_tokens(self, text: str, file_path: str, start_line: int) -> List[TextChunk]:
        """Split text by tokens."""
        if not self.tokenizer:
            return self._split_by_characters(text, file_path, start_line)

        tokens = self.tokenizer.encode(text)
        chunks = []
        chunk_id = 0

        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk_tokens = tokens[i : i + self.chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)

            # Estimate line numbers
            lines_before = text[: text.find(chunk_text)].count("\n") if chunk_text in text else 0
            chunk_start_line = start_line + lines_before
            chunk_end_line = chunk_start_line + chunk_text.count("\n")

            chunk = TextChunk(
                text=chunk_text,
                file_path=file_path,
                start_line=chunk_start_line,
                end_line=chunk_end_line,
                chunk_id=f"{file_path}_{chunk_id}",
                metadata={"split_method": "token"},
            )
            chunks.append(chunk)
            chunk_id += 1

        return chunks

    def _split_by_sentences(self, text: str, file_path: str, start_line: int) -> List[TextChunk]:
        """Split text by sentences."""
        # Simple sentence splitting - can be improved with more sophisticated NLP
        sentences = re.split(r"[.!?]+", text)
        chunks = []
        chunk_id = 0
        current_chunk = ""
        current_start_line = start_line

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunk = TextChunk(
                        text=current_chunk.strip(),
                        file_path=file_path,
                        start_line=current_start_line,
                        end_line=current_start_line + current_chunk.count("\n"),
                        chunk_id=f"{file_path}_{chunk_id}",
                        metadata={"split_method": "sentence"},
                    )
                    chunks.append(chunk)
                    chunk_id += 1

                current_chunk = sentence
                current_start_line = start_line + text[: text.find(sentence)].count("\n")
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        # Add the last chunk
        if current_chunk:
            chunk = TextChunk(
                text=current_chunk.strip(),
                file_path=file_path,
                start_line=current_start_line,
                end_line=current_start_line + current_chunk.count("\n"),
                chunk_id=f"{file_path}_{chunk_id}",
                metadata={"split_method": "sentence"},
            )
            chunks.append(chunk)

        return chunks

    def _split_by_characters(self, text: str, file_path: str, start_line: int) -> List[TextChunk]:
        """Split text by characters."""
        chunks = []
        chunk_id = 0

        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk_text = text[i : i + self.chunk_size]

            # Calculate line numbers
            text_before = text[:i]
            chunk_start_line = start_line + text_before.count("\n")
            chunk_end_line = chunk_start_line + chunk_text.count("\n")

            chunk = TextChunk(
                text=chunk_text,
                file_path=file_path,
                start_line=chunk_start_line,
                end_line=chunk_end_line,
                chunk_id=f"{file_path}_{chunk_id}",
                metadata={"split_method": "character"},
            )
            chunks.append(chunk)
            chunk_id += 1

        return chunks
