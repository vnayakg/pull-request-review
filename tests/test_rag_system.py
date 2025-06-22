import pytest
import tempfile
import os
import numpy as np
from unittest.mock import Mock, patch
from pr_review_agent.rag_system import RAGSystem
from pr_review_agent.rag_text_splitter import RAGTextSplitter, TextChunk
from pr_review_agent.rag_embedder import RAGEmbedder
from pr_review_agent.rag_retriever import RAGRetriever


@pytest.fixture
def sample_config():
    return {
        "rag": {
            "enabled": True,
            "embedder": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "batch_size": 32,
                "max_length": 512,
            },
            "retriever": {"top_k": 10, "similarity_threshold": 0.7},
            "text_splitter": {"chunk_size": 500, "chunk_overlap": 100, "split_by": "token"},
            "storage": {"type": "faiss", "cache_dir": "./.test_rag_cache"},
            "context": {
                "include_file_structure": True,
                "include_readme": True,
                "include_documentation": True,
                "max_files_to_index": 1000,
                "exclude_patterns": ["*.lock", "*.min.js", "node_modules/*", ".git/*"],
            },
        }
    }


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


class TestRAGTextSplitter:
    def test_text_splitter_initialization(self):
        splitter = RAGTextSplitter(chunk_size=500, chunk_overlap=100, split_by="character")
        assert splitter.chunk_size == 500
        assert splitter.chunk_overlap == 100
        assert splitter.split_by == "character"

    def test_split_by_characters(self):
        splitter = RAGTextSplitter(chunk_size=10, chunk_overlap=2, split_by="character")
        text = "This is a test text for splitting."
        chunks = splitter.split_text(text, "test.txt", 1)

        assert len(chunks) > 0
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)
        assert chunks[0].file_path == "test.txt"
        assert chunks[0].start_line == 1


class TestRAGEmbedder:
    @patch("pr_review_agent.rag_embedder.SentenceTransformer")
    def test_embedder_initialization(self, mock_transformer):
        mock_model = Mock()
        mock_transformer.return_value = mock_model
        mock_model.get_sentence_embedding_dimension.return_value = 384

        embedder = RAGEmbedder(model_name="test-model")
        assert embedder.model_name == "test-model"
        assert embedder.batch_size == 32

    @patch("pr_review_agent.rag_embedder.SentenceTransformer")
    def test_embed_texts(self, mock_transformer):
        mock_model = Mock()
        mock_transformer.return_value = mock_model
        # Return a proper numpy array instead of a list
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])

        embedder = RAGEmbedder()
        texts = ["Hello world", "Test text"]
        embeddings = embedder.embed_texts(texts)

        assert embeddings.shape == (2, 3)
        mock_model.encode.assert_called_once()


class TestRAGRetriever:
    def test_retriever_initialization(self):
        retriever = RAGRetriever(top_k=5, similarity_threshold=0.8)
        assert retriever.top_k == 5
        assert retriever.similarity_threshold == 0.8
        assert retriever.index is None

    def test_build_index(self):
        retriever = RAGRetriever()
        chunks = [
            TextChunk("test text 1", "file1.txt", 1, 5, "chunk1"),
            TextChunk("test text 2", "file2.txt", 1, 5, "chunk2"),
        ]
        embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])

        retriever.build_index(chunks, embeddings)
        assert retriever.index is not None
        assert len(retriever.chunks) == 2


class TestRAGSystem:
    @patch("pr_review_agent.rag_system.RAGEmbedder")
    @patch("pr_review_agent.rag_system.RAGRetriever")
    def test_rag_system_initialization(self, mock_retriever, mock_embedder, sample_config):
        mock_embedder_instance = Mock()
        mock_embedder.return_value = mock_embedder_instance
        mock_retriever_instance = Mock()
        mock_retriever.return_value = mock_retriever_instance

        rag_system = RAGSystem(sample_config)

        assert rag_system.config == sample_config
        assert rag_system.rag_config == sample_config["rag"]
        mock_embedder.assert_called_once()
        mock_retriever.assert_called_once()

    def test_get_repo_hash(self, sample_config):
        rag_system = RAGSystem(sample_config)
        hash1 = rag_system._get_repo_hash("https://github.com/test/repo", "main")
        hash2 = rag_system._get_repo_hash("https://github.com/test/repo", "main")
        hash3 = rag_system._get_repo_hash("https://github.com/test/repo", "develop")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 32  # MD5 hash length

    def test_get_cache_path(self, sample_config):
        rag_system = RAGSystem(sample_config)
        repo_hash = "test_hash"
        cache_path = rag_system._get_cache_path(repo_hash)

        expected_path = os.path.join(rag_system.cache_dir, repo_hash)
        assert cache_path == expected_path

    @patch("pr_review_agent.rag_system.subprocess.run")
    def test_clone_or_update_repo_new_repo(self, mock_run, sample_config, temp_dir):
        rag_system = RAGSystem(sample_config)
        repo_url = "https://github.com/test/repo"
        repo_path = os.path.join(temp_dir, "test_repo")

        # Mock successful clone
        mock_run.return_value = Mock()
        mock_run.return_value.returncode = 0

        result = rag_system._clone_or_update_repo(repo_url, repo_path, "main")

        assert result is True
        mock_run.assert_called()

    def test_extract_diff_summary(self, sample_config):
        rag_system = RAGSystem(sample_config)
        diff_content = """
diff --git a/file.txt b/file.txt
index 1234567..abcdefg 100644
--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,4 @@
 old line
+new line
 another line
"""

        summary = rag_system._extract_diff_summary(diff_content)
        assert "new line" in summary
        assert "old line" not in summary  # Only added lines should be included
