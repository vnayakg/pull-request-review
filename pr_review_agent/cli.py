import click
from rich import print
from .config import Config
from .github_client import GitHubClient
from .diff_parser import DiffParser
from .ollama_client import OllamaClient
from .prompt_templates import render_review_prompt
from .output_formatter import format_console, format_output
import yaml

@click.command()
@click.argument('pr_url')
@click.option('--config', '-c', 'config_path', default=None, help='Path to configuration YAML file')
@click.option('--model', default=None, help='Ollama model to use')
@click.option('--output', default=None, help='Output file path')
@click.option('--format', 'output_format', default=None, type=click.Choice(['console', 'json', 'markdown']), help='Output format')
def main(pr_url, config_path, model, output, output_format):
    """Review a GitHub pull request using a local LLM via Ollama."""
    config = Config(config_path)
    # Override config with CLI options if provided
    if model:
        config.config['ollama']['model'] = model
    if output:
        config.config['output']['file'] = output
    if output_format:
        config.config['output']['format'] = output_format
    print('[bold green]Loaded configuration:[/bold green]')
    print(config.config)
    print(f'PR URL: {pr_url}')

    github_token = config.get('github.token')
    github_api_url = config.get('github.api_url')
    client = GitHubClient(github_token, github_api_url)
    try:
        owner, repo, number = client.parse_pr_url(pr_url)
        print(f'[bold]Repo:[/bold] {owner}/{repo}  [bold]PR#[/bold] {number}')
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
        # Prepare prompt for LLM
        ollama_cfg = config.get('ollama')
        ollama_client = OllamaClient(
            endpoint=ollama_cfg['endpoint'],
            model=ollama_cfg['model'],
            temperature=ollama_cfg.get('temperature', 0.1),
            max_tokens=ollama_cfg.get('max_tokens', 2048)
        )
        # For MVP, use the first N files' diffs as context
        diff_summary = '\n'.join(diff.splitlines()[:1000])
        prompt = render_review_prompt(pr_meta, files, diff_summary)
        print('[bold yellow]Sending prompt to LLM...[/bold yellow]')
        review_yaml = ollama_client.generate_review(prompt)
        # Parse YAML output from LLM
        try:
            review_obj = yaml.safe_load(review_yaml)
            review = review_obj['review'] if 'review' in review_obj else review_obj
        except Exception as e:
            print(f"[bold red]Failed to parse LLM output as YAML:[/bold red] {e}")
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