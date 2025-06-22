"""
PR Review Agent package: CLI tool for reviewing GitHub PRs using a local LLM via Ollama.
"""

from .cli import main
from .rag_system import RAGSystem

__version__ = "1.0.0"
