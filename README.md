# Pull Request Review Agent with RAG

A powerful CLI tool for reviewing GitHub pull requests using local or remote LLMs with **Retrieval-Augmented Generation (RAG)** for contextual code reviews.

## Features

- 🤖 **Multiple LLM Support**: Ollama (local), OpenAI, and Google Gemini
- 🔍 **RAG Context**: Understands repository structure and existing code patterns
- 📊 **Smart Analysis**: Provides contextual feedback based on codebase conventions
- 🎯 **Flexible Output**: Console, JSON, or Markdown formats
- ⚡ **Caching**: Efficient repository indexing with persistent cache
- 🔧 **Configurable**: YAML-based configuration with environment variable support

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pull-request-llm.git
cd pull-request-llm

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Quick Start

### Basic Usage

```bash
# Review a pull request
pr-review-agent https://github.com/owner/repo/pull/123

# With RAG context enabled
pr-review-agent https://github.com/owner/repo/pull/123 --rag

# Enhanced contextual review
pr-review-agent https://github.com/owner/repo/pull/123 --rag --contextual
```

### RAG Management

```bash
# Index a repository for RAG context
pr-rag index https://github.com/owner/repo

# Query repository context
pr-rag query https://github.com/owner/repo "How is authentication handled?"

# Clear cache
pr-rag clear-cache

# Check RAG status
pr-rag status
```

## Development with Makefile

This project includes a comprehensive Makefile for common development tasks:

```bash
# Show all available commands
make help

# Set up development environment
make full-setup

# Run tests
make test

# Run tests with coverage
make test-coverage

# Format code
make format

# Run linting
make lint

# Run demos
make demo
make demo-output

# Clean up
make clean
make clean-cache

# Build distribution
make build
```

### Quick Development Workflow

```bash
# 1. Set up everything
make full-setup

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run tests
make test

# 4. Try the demo
make demo

# 5. Format and lint before committing
make format
make lint
```

## Configuration

Create a `config.yaml` file or use environment variables:

```yaml
llm:
  type: gemini  # ollama, openai, gemini

github:
  token: ${GITHUB_TOKEN}
  api_url: "https://api.github.com"

# RAG configuration
rag:
  enabled: true
  embedder:
    model: "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: 32
    max_length: 512
  retriever:
    top_k: 10
    similarity_threshold: 0.7
  text_splitter:
    chunk_size: 500
    chunk_overlap: 100
    split_by: "token"
  storage:
    type: "faiss"
    cache_dir: "./.rag_cache"
  context:
    include_file_structure: true
    include_readme: true
    include_documentation: true
    max_files_to_index: 1000
    exclude_patterns:
      - "*.lock"
      - "*.min.js"
      - "node_modules/*"
      - ".git/*"

# LLM-specific configurations
ollama:
  endpoint: "http://localhost:11434"
  model: "codellama:7b"
  temperature: 0.1
  max_tokens: 2048

openai:
  api_key: ${OPENAI_API_KEY}
  model: "gpt-3.5-turbo"
  temperature: 0.1
  max_tokens: 2048

gemini:
  api_key: ${GEMINI_API_KEY}
  model: "gemini-2.0-flash"
  temperature: 0.1
  max_tokens: 2048

review:
  max_files: 50
  max_lines_per_file: 1000
  include_context_lines: 3

output:
  format: "console"  # console, json, markdown
  file: null
  include_summary: true
  show_confidence: true
```

## Environment Variables

Set these environment variables for API access:

```bash
export GITHUB_TOKEN="your_github_token"
export OPENAI_API_KEY="your_openai_key"
export GEMINI_API_KEY="your_gemini_key"
```

## How RAG Works

The RAG system enhances pull request reviews by:

1. **Repository Indexing**: Clones and processes the repository to create embeddings
2. **Context Retrieval**: Finds relevant code sections based on the PR changes
3. **Enhanced Prompts**: Provides the LLM with repository context for better analysis
4. **Pattern Recognition**: Identifies codebase conventions and architectural patterns

### Benefits

- **Contextual Feedback**: Reviews consider existing code patterns and conventions
- **Architectural Consistency**: Ensures changes align with codebase structure
- **Better Integration**: Suggests improvements based on existing implementations
- **Reduced False Positives**: Understands project-specific patterns and requirements

## Advanced Usage

### Custom Configuration

```bash
# Use custom config file
pr-review-agent https://github.com/owner/repo/pull/123 -c my_config.yaml

# Override model
pr-review-agent https://github.com/owner/repo/pull/123 --model gpt-4

# Output to file
pr-review-agent https://github.com/owner/repo/pull/123 --output review.md --format markdown
```

### RAG Options

```bash
# Use specific branch for context
pr-review-agent https://github.com/owner/repo/pull/123 --rag --branch develop

# Force re-indexing
pr-rag index https://github.com/owner/repo --force

# Clear cache before review
pr-review-agent https://github.com/owner/repo/pull/123 --rag --clear-cache
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run with verbose output
make test-verbose
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Check project health
make health
```

### Project Structure

```
pull-request-llm/
├── pr_review_agent/
│   ├── cli.py                 # Main CLI interface
│   ├── rag_cli.py            # RAG management commands
│   ├── rag_system.py         # Main RAG orchestrator
│   ├── rag_embedder.py       # Text embedding
│   ├── rag_retriever.py      # Similarity search
│   ├── rag_text_splitter.py  # Text chunking
│   ├── rag_repository_processor.py  # Repository processing
│   ├── github_client.py      # GitHub API client
│   ├── llm_client.py         # LLM integration
│   ├── prompt_templates.py   # Review prompts
│   └── output_formatter.py   # Output formatting
├── config/
│   └── default_config.yaml   # Default configuration
├── tests/                    # Test suite
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── Makefile                  # Development tasks
└── README.md                 # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Format code: `make format`
6. Run linting: `make lint`
7. Submit a pull request
