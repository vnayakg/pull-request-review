# Pull Request Review Agent Makefile
# Common development tasks and utilities

.PHONY: help install install-dev test test-verbose lint format clean setup demo demo-rag demo-output build install-pkg uninstall-pkg docs clean-cache

# Default target
help:
	@echo "🚀 Pull Request Review Agent - Available Commands:"
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  setup          - Set up the development environment"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo "  install-pkg    - Install the package in development mode"
	@echo "  uninstall-pkg  - Uninstall the package"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test           - Run tests"
	@echo "  test-verbose   - Run tests with verbose output"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo ""
	@echo "🔧 Code Quality:"
	@echo "  lint           - Run linting checks"
	@echo "  format         - Format code with black"
	@echo ""
	@echo "🎯 Demos:"
	@echo "  demo           - Run the main RAG demo"
	@echo "  demo-rag       - Run RAG functionality demo"
	@echo "  demo-output    - Run output formatting demo"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  clean          - Clean build artifacts and cache"
	@echo "  clean-cache    - Clean RAG cache directories"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  docs           - Generate documentation"
	@echo ""
	@echo "📦 Distribution:"
	@echo "  build          - Build distribution packages"
	@echo "  dist           - Create distribution files"

# Setup development environment
setup:
	@echo "🔧 Setting up development environment..."
	python3 -m venv venv
	@echo "✅ Virtual environment created"
	@echo "📝 To activate: source venv/bin/activate"
	@echo "📦 Then run: make install-dev"

# Install production dependencies
install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt

# Install development dependencies
install-dev: install
	@echo "🔧 Installing development dependencies..."
	pip install -r requirements-dev.txt

# Install package in development mode
install-pkg:
	@echo "📦 Installing package in development mode..."
	pip install -e .

# Uninstall package
uninstall-pkg:
	@echo "🗑️ Uninstalling package..."
	pip uninstall -y pr-review-agent

# Run tests
test:
	@echo "🧪 Running tests..."
	export PYTHONPATH=. && pytest tests/ -v

# Run tests with verbose output
test-verbose:
	@echo "🧪 Running tests with verbose output..."
	export PYTHONPATH=. && pytest tests/ -v -s

# Run tests with coverage
test-coverage:
	@echo "🧪 Running tests with coverage..."
	export PYTHONPATH=. && pytest tests/ --cov=pr_review_agent --cov-report=html --cov-report=term

# Run linting
lint:
	@echo "🔍 Running linting checks..."
	@echo "Checking with flake8..."
	flake8 pr_review_agent/ tests/ --max-line-length=150 --ignore=E203,W503
	@echo "Checking with mypy..."
	mypy pr_review_agent/ --ignore-missing-imports
	@echo "✅ Linting completed"

# Format code
format:
	@echo "🎨 Formatting code with black..."
	black pr_review_agent/ tests/ --line-length=100
	@echo "✅ Code formatting completed"

# Clean build artifacts and cache
clean:
	@echo "🧹 Cleaning build artifacts and cache..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Clean RAG cache directories
clean-cache:
	@echo "🗑️ Cleaning RAG cache directories..."
	rm -rf .rag_cache/
	rm -rf .test_rag_cache/
	@echo "✅ RAG cache cleaned"

# Run main RAG demo
demo:
	@echo "🚀 Running main RAG demo..."
	python demo_rag.py

# Run RAG functionality demo
demo-rag:
	@echo "🔍 Running RAG functionality demo..."
	python -c "from pr_review_agent.rag_system import RAGSystem; from pr_review_agent.config import Config; print('RAG system imported successfully')"

# Run output formatting demo
demo-output:
	@echo "🎨 Running output formatting demo..."
	python demo_output_formatting.py

# Generate documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "Documentation is available in README.md"
	@echo "For API documentation, run: pydoc pr_review_agent"

# Build distribution packages
build:
	@echo "📦 Building distribution packages..."
	python setup.py sdist bdist_wheel
	@echo "✅ Distribution packages built"

# Create distribution files
dist: build
	@echo "📦 Distribution files created in dist/"

# Quick development workflow
dev: install-dev install-pkg
	@echo "🚀 Development environment ready!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make demo' to see the demo"

# Full setup for new developers
full-setup: setup install-dev install-pkg
	@echo "🎉 Full setup completed!"
	@echo "Virtual environment: venv/"
	@echo "Dependencies: installed"
	@echo "Package: installed in development mode"
	@echo ""
	@echo "Next steps:"
	@echo "1. Activate virtual environment: source venv/bin/activate"
	@echo "2. Run tests: make test"
	@echo "3. Try the demo: make demo"

# Check project health
health: test lint
	@echo "✅ Project health check completed"

# Release preparation
release: clean test lint build
	@echo "🎉 Release preparation completed!"
	@echo "Distribution files are ready in dist/"

# Show project info
info:
	@echo "📊 Project Information:"
	@echo "Name: Pull Request Review Agent"
	@echo "Version: $(shell python -c "import pr_review_agent; print(pr_review_agent.__version__)" 2>/dev/null || echo "Unknown")"
	@echo "Python: $(shell python --version)"
	@echo "Location: $(shell pwd)"
	@echo ""
	@echo "📁 Key directories:"
	@echo "Source: pr_review_agent/"
	@echo "Tests: tests/"
	@echo "Config: config/"
	@echo "Cache: .rag_cache/" 