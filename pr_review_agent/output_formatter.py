import json
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

def filter_duplicate_issues(issues):
    seen = set()
    filtered = []
    for issue in issues:
        key = (issue.get('relevant_file'), issue.get('issue_header'), issue.get('start_line'), issue.get('end_line'))
        if key not in seen and issue.get('issue_content') and len(issue.get('issue_content')) > 10:
            seen.add(key)
            filtered.append(issue)
    return filtered

def calculate_confidence(review):
    # Placeholder: In the future, use LLM output or heuristics for confidence
    # For now, return None or a static value if needed
    return review.get('confidence', None)

def format_console(review, show_confidence=False):
    console = Console()
    issues = filter_duplicate_issues(review.get('key_issues_to_review', []))
    table = Table(title="Key Issues to Review", show_lines=True)
    table.add_column("File")
    table.add_column("Header")
    table.add_column("Content")
    table.add_column("Lines")
    for issue in issues:
        table.add_row(
            issue.get('relevant_file', ''),
            issue.get('issue_header', ''),
            issue.get('issue_content', ''),
            f"{issue.get('start_line', '')}-{issue.get('end_line', '')}"
        )
    console.print(table)
    console.print(Panel(f"Security Concerns: {review.get('security_concerns', 'N/A')}", title="Security"))
    console.print(Panel(f"Relevant Tests: {review.get('relevant_tests', 'N/A')}", title="Tests"))
    confidence = calculate_confidence(review)
    if show_confidence and confidence is not None:
        console.print(Panel(f"Confidence: {confidence}", title="Confidence"))
    console.print(Panel(f"Total Issues: {len(issues)}", title="Summary"))

def format_json(review):
    review = review.copy()
    review['key_issues_to_review'] = filter_duplicate_issues(review.get('key_issues_to_review', []))
    return json.dumps(review, indent=2)

def format_markdown(review):
    issues = filter_duplicate_issues(review.get('key_issues_to_review', []))
    md = ["# PR Review\n"]
    md.append("## Key Issues to Review\n")
    for issue in issues:
        md.append(f"- **File:** `{issue.get('relevant_file', '')}`\n  - **Header:** {issue.get('issue_header', '')}\n  - **Content:** {issue.get('issue_content', '')}\n  - **Lines:** {issue.get('start_line', '')}-{issue.get('end_line', '')}")
    md.append(f"\n## Security Concerns\n{review.get('security_concerns', 'N/A')}")
    md.append(f"\n## Relevant Tests\n{review.get('relevant_tests', 'N/A')}")
    confidence = calculate_confidence(review)
    if confidence is not None:
        md.append(f"\n## Confidence\n{confidence}")
    md.append(f"\n## Summary\nTotal Issues: {len(issues)}")
    return '\n'.join(md)

def format_output(review, fmt, show_confidence=False):
    if fmt == 'json':
        return format_json(review)
    elif fmt == 'markdown':
        return format_markdown(review)
    else:
        # Console output is handled directly
        return None 