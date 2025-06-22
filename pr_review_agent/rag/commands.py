import click
from rich import print
from ..config import Config # Corrected import for parent directory
from . import RAGSystem # Corrected import to use rag package's __init__.py

@click.group()
def rag():
    """RAG (Retrieval-Augmented Generation) management commands."""
    pass

@rag.command()
@click.argument('repo_url')
@click.option('--config', '-c', 'config_path', default=None, help='Path to configuration YAML file')
@click.option('--branch', default='main', help='Repository branch to index')
@click.option('--force', is_flag=True, help='Force re-indexing even if cache exists')
def index(repo_url, config_path, branch, force):
    """Index a repository for RAG context."""
    config = Config(config_path)
    
    if not config.get('rag.enabled', False):
        print('[bold red]RAG is disabled in configuration[/bold red]')
        return
    
    print(f'[bold blue]Indexing repository: {repo_url}[/bold blue]')
    print(f'[bold]Branch:[/bold] {branch}')
    
    rag_system = RAGSystem(config.config)
    
    if force:
        print('[bold yellow]Clearing existing cache...[/bold yellow]')
        rag_system.clear_cache(repo_url, branch)
    
    if rag_system.prepare_repository_context(repo_url, branch):
        print('[bold green]Repository indexed successfully![/bold green]')
    else:
        print('[bold red]Failed to index repository[/bold red]')

@rag.command()
@click.option('--config', '-c', 'config_path', default=None, help='Path to configuration YAML file')
@click.option('--repo-url', help='Clear cache for specific repository')
@click.option('--branch', default='main', help='Repository branch (if repo-url is specified)')
def clear_cache(config_path, repo_url, branch):
    """Clear RAG cache."""
    config = Config(config_path)
    rag_system = RAGSystem(config.config)
    
    if repo_url:
        print(f'[bold yellow]Clearing cache for: {repo_url}[/bold yellow]')
        rag_system.clear_cache(repo_url, branch)
    else:
        print('[bold yellow]Clearing all RAG cache...[/bold yellow]')
        rag_system.clear_cache()
    
    print('[bold green]Cache cleared successfully![/bold green]')

@rag.command()
@click.argument('repo_url')
@click.argument('query')
@click.option('--config', '-c', 'config_path', default=None, help='Path to configuration YAML file')
@click.option('--branch', default='main', help='Repository branch')
def query(repo_url, query, config_path, branch):
    """Query repository context with a specific question."""
    config = Config(config_path)
    
    if not config.get('rag.enabled', False):
        print('[bold red]RAG is disabled in configuration[/bold red]')
        return
    
    print(f'[bold blue]Querying repository: {repo_url}[/bold blue]')
    print(f'[bold]Query:[/bold] {query}')
    
    rag_system = RAGSystem(config.config)
    
    if rag_system.prepare_repository_context(repo_url, branch):
        context = rag_system.get_context_for_query(query, repo_url, branch)
        if context:
            print('[bold green]Relevant context found:[/bold green]')
            print(context)
        else:
            print('[bold yellow]No relevant context found for this query[/bold yellow]')
    else:
        print('[bold red]Failed to prepare repository context[/bold red]')

@rag.command()
@click.option('--config', '-c', 'config_path', default=None, help='Path to configuration YAML file')
def status(config_path):
    """Show RAG system status and configuration."""
    config = Config(config_path)
    
    print('[bold blue]RAG System Status:[/bold blue]')
    print(f'[bold]Enabled:[/bold] {config.get("rag.enabled", False)}')
    
    if config.get('rag.enabled', False):
        rag_config = config.get('rag', {})
        print(f'[bold]Embedder Model:[/bold] {rag_config.get("embedder", {}).get("model", "N/A")}')
        print(f'[bold]Top K:[/bold] {rag_config.get("retriever", {}).get("top_k", "N/A")}')
        print(f'[bold]Chunk Size:[/bold] {rag_config.get("text_splitter", {}).get("chunk_size", "N/A")}')
        print(f'[bold]Cache Directory:[/bold] {rag_config.get("storage", {}).get("cache_dir", "N/A")}')
        
        # Check cache directory
        import os
        cache_dir = rag_config.get('storage', {}).get('cache_dir', './.rag_cache')
        if os.path.exists(cache_dir):
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.faiss')]
            print(f'[bold]Cached Repositories:[/bold] {len(cache_files)}')
        else:
            print('[bold]Cache Directory:[/bold] Not found')
    else:
        print('[bold yellow]RAG is disabled in configuration[/bold yellow]')

if __name__ == '__main__':
    rag() 