# PR Review Agent (MVP)

A CLI tool to review GitHub pull requests using a local LLM via Ollama.

## Features
- Fetches PR diffs from GitHub
- Sends code changes to a local LLM (Ollama) for review
- Outputs review comments in console, JSON, or Markdown
- Configurable via YAML file and environment variables

## Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage
```bash
pr-review-agent https://github.com/owner/repo/pull/123
pr-review-agent --model codellama:13b https://github.com/owner/repo/pull/123
pr-review-agent --output reviews.md --format markdown https://github.com/owner/repo/pull/123
pr-review-agent --config my-config.yaml https://github.com/owner/repo/pull/123
```

## Configuration
See `config/default_config.yaml` for all options.

## Requirements
- Python 3.8+
- [Ollama](https://ollama.com/) running locally
- GitHub token (for private repos)

## License
MIT 