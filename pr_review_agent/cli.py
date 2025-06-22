import click
from rich import print
from .config import Config
from .github_client import GitHubClient
from .diff_parser import DiffParser
from .prompt_templates import render_review_prompt, render_contextual_review_prompt
from .output_formatter import format_console, format_output, format_fallback_text
from .llm_client import get_llm_client
from .rag import RAGSystem # Updated import
import yaml

@click.command()
@click.argument('pr_url')
@click.option('--config', '-c', 'config_path', default=None, help='Path to configuration YAML file')
@click.option('--model', default=None, help='LLM model to use (overrides config)')
@click.option('--output', default=None, help='Output file path')
@click.option('--format', 'output_format', default=None, type=click.Choice(['console', 'json', 'markdown']), help='Output format')
@click.option('--rag/--no-rag', default=None, help='Enable/disable RAG for repository context')
@click.option('--branch', default='main', help='Repository branch to use for RAG context')
@click.option('--clear-cache', is_flag=True, help='Clear RAG cache before processing')
@click.option('--contextual', is_flag=True, help='Use enhanced contextual review prompt')
def main(pr_url, config_path, model, output, output_format, rag, branch, clear_cache, contextual):
    """Review a GitHub pull request using a local or remote LLM with optional RAG context."""
    config = Config(config_path)
    if model:
        # Override model for all LLMs
        for section in ['ollama', 'openai', 'gemini']:
            if section in config.config:
                config.config[section]['model'] = model
    if output:
        config.config['output']['file'] = output
    if output_format:
        config.config['output']['format'] = output_format
    if rag is not None:
        config.config['rag']['enabled'] = rag
    
    print('[bold green]Loaded configuration:[/bold green]')
    print(config.config)
    print(f'PR URL: {pr_url}')

    github_token = config.get('github.token')
    github_api_url = config.get('github.api_url')
    client = GitHubClient(github_token, github_api_url)
    
    # Initialize RAG system if enabled
    rag_system = None
    if config.get('rag.enabled', False):
        print('[bold blue]Initializing RAG system for repository context...[/bold blue]')
        rag_system = RAGSystem(config.config)
        
        if clear_cache:
            print('[bold yellow]Clearing RAG cache...[/bold yellow]')
            rag_system.clear_cache()
    
    try:
        owner, repo, number = client.parse_pr_url(pr_url)
        print(f'[bold]Repo:[/bold] {owner}/{repo}  [bold]PR#[/bold] {number}')
        
        # Get repository URL for RAG
        repo_url = f"https://github.com/{owner}/{repo}"
        
        pr_meta = client.get_pr_metadata(owner, repo, number)
        print(f"[bold]Title:[/bold] {pr_meta.get('title')}")
        print(f"[bold]Author:[/bold] {pr_meta.get('user', {}).get('login')}")
        print(f"[bold]Description:[/bold] {pr_meta.get('body', '')[:200]}{'...' if pr_meta.get('body') and len(pr_meta.get('body')) > 200 else ''}")
        
        files = client.get_pr_files(owner, repo, number)
        print(f"[bold]Changed files:[/bold] {len(files)}")
        for f in files[:5]:
            print(f"- {f['filename']} ({f['status']}, +{f['additions']}/-{f['deletions']})")
        if len(files) > 5:
            print(f"...and {len(files)-5} more files.")
        
        diff = client.get_pr_diff(owner, repo, number)
        print(f"[bold]Diff size:[/bold] {len(diff)} bytes")
        
        parser = DiffParser(diff)
        summary = parser.get_summary()
        print(f"[bold]Parsed diff files:[/bold] {len(summary)}")
        for s in summary[:5]:
            print(f"- {s['file']} ({s['hunks']} hunks)")
        if len(summary) > 5:
            print(f"...and {len(summary)-5} more files.")
        
        # Prepare RAG context if enabled
        repository_context = ""
        if rag_system:
            print('[bold blue]Preparing repository context...[/bold blue]')
            if rag_system.prepare_repository_context(repo_url, branch):
                print('[bold green]Repository context prepared successfully[/bold green]')
                repository_context = rag_system.get_context_for_diff(diff, repo_url, branch)
                if repository_context:
                    print(f'[bold green]Retrieved {len(repository_context)} characters of relevant context[/bold green]')
                else:
                    print('[bold yellow]No relevant context found for this diff[/bold yellow]')
            else:
                print('[bold red]Failed to prepare repository context[/bold red]')
        
        # Prepare prompt for LLM
        llm_client = get_llm_client(config)
        diff_summary = '\n'.join(diff.splitlines()[:1000])
        
        if contextual and repository_context:
            prompt = render_contextual_review_prompt(pr_meta, files, diff_summary, repository_context)
        else:
            prompt = render_review_prompt(pr_meta, files, diff_summary, repository_context)
        
        print(f'[bold yellow]Sending prompt to LLM ({config.get("llm.type")})...[/bold yellow]')
        review_yaml = llm_client.generate_review(prompt)
        
        # Parse YAML output from LLM
        try:
            review_obj = yaml.safe_load(review_yaml)
            review = review_obj['review'] if 'review' in review_obj else review_obj
            print('[bold green]Successfully parsed structured review[/bold green]')
        except Exception as e:
            print(f"[bold yellow]Failed to parse LLM output as YAML: {e}[/bold yellow]")
            print('[bold blue]Falling back to text formatting...[/bold blue]')
            
            # Use fallback formatting for raw text
            fmt = config.get('output.format', 'console')
            if fmt == 'console':
                format_fallback_text(review_yaml)
            else:
                # For non-console formats, just output the raw text
                if output:
                    with open(output, 'w') as f:
                        f.write(review_yaml)
                    print(f"[bold green]Raw review written to {output}[/bold green]")
                else:
                    print(review_yaml)
            return
        
        fmt = config.get('output.format', 'console')
        out_file = config.get('output.file')
        show_confidence = config.get('output.show_confidence', True)
        include_summary = config.get('output.include_summary', True)
        
        if fmt == 'console':
            format_console(review, show_confidence=show_confidence)
        else:
            formatted = format_output(review, fmt, show_confidence=show_confidence)
            if out_file:
                with open(out_file, 'w') as f:
                    f.write(formatted)
                print(f"[bold green]Review written to {out_file}[/bold green]")
            else:
                print(formatted)
                
    except Exception as e:
        print(f"[bold red]Error:[/bold red] {e}")

if __name__ == '__main__':
    main() 