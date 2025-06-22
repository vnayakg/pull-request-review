import json
import re
from rich.console import Console
from rich.panel import Panel
from rich.box import ROUNDED


def filter_duplicate_issues(issues):
    seen = set()
    filtered = []
    for issue in issues:
        key = (
            issue.get("relevant_file"),
            issue.get("issue_header"),
            issue.get("start_line"),
            issue.get("end_line"),
        )
        if key not in seen and issue.get("issue_content") and len(issue.get("issue_content")) > 10:
            seen.add(key)
            filtered.append(issue)
    return filtered


def calculate_confidence(review):
    return review.get("confidence", None)


def format_console(review, show_confidence=False):
    console = Console()

    # Print summary if available
    if review.get("summary"):
        console.print(Panel(review["summary"], title="📋 Summary", box=ROUNDED, style="bold blue"))

    # Print key issues
    issues = filter_duplicate_issues(review.get("key_issues_to_review", []))
    if issues:
        console.print(
            Panel(
                f"Found {len(issues)} issues to review",
                title="🔍 Issues Found",
                style="bold yellow",
            )
        )

        for i, issue in enumerate(issues, 1):
            severity = issue.get("severity", "medium")
            severity_color = {"high": "red", "medium": "yellow", "low": "green"}.get(
                severity, "white"
            )

            issue_text = f"[bold]{issue.get('issue_header', 'No title')}[/bold]\n"
            issue_text += f"File: [cyan]{issue.get('relevant_file', 'Unknown')}[/cyan]\n"
            if issue.get("start_line") and issue.get("end_line"):
                issue_text += (
                    f"Lines: [dim]{issue.get('start_line')}-{issue.get('end_line')}[/dim]\n"
                )
            issue_text += f"\n{issue.get('issue_content', 'No content')}"

            console.print(
                Panel(
                    issue_text,
                    title=f"#{i} [{severity_color}]{severity.upper()}[/{severity_color}]",
                    box=ROUNDED,
                    style=severity_color,
                )
            )

    # Print technical analysis if available
    if review.get("technical_analysis"):
        tech = review["technical_analysis"]
        tech_text = ""
        if tech.get("code_quality"):
            tech_text += f"Code Quality: {tech['code_quality']}\n\n"
        if tech.get("security_considerations") and tech["security_considerations"] != "None":
            tech_text += f"Security: {tech['security_considerations']}\n\n"
        if tech.get("performance_implications") and tech["performance_implications"] != "None":
            tech_text += f"Performance: {tech['performance_implications']}\n\n"
        if tech.get("error_handling"):
            tech_text += f"Error Handling: {tech['error_handling']}"

        if tech_text:
            console.print(
                Panel(tech_text, title="🔧 Technical Analysis", box=ROUNDED, style="bold cyan")
            )

    # Print architectural consistency if available
    if review.get("architectural_consistency"):
        arch = review["architectural_consistency"]
        arch_text = ""
        if arch.get("pattern_alignment"):
            arch_text += f"Pattern Alignment: {arch['pattern_alignment']}\n\n"
        if arch.get("codebase_conventions"):
            arch_text += f"Codebase Conventions: {arch['codebase_conventions']}\n\n"
        if arch.get("integration_assessment"):
            arch_text += f"Integration: {arch['integration_assessment']}"

        if arch_text:
            console.print(
                Panel(
                    arch_text,
                    title="🏗️ Architectural Consistency",
                    box=ROUNDED,
                    style="bold magenta",
                )
            )

    # Print legacy fields for backward compatibility
    if review.get("security_concerns") and review["security_concerns"] != "N/A":
        console.print(
            Panel(
                review["security_concerns"],
                title="🔒 Security Concerns",
                box=ROUNDED,
                style="bold red",
            )
        )

    if review.get("performance_concerns") and review["performance_concerns"] != "N/A":
        console.print(
            Panel(
                review["performance_concerns"],
                title="⚡ Performance Concerns",
                box=ROUNDED,
                style="bold yellow",
            )
        )

    if review.get("style_concerns") and review["style_concerns"] != "N/A":
        console.print(
            Panel(
                review["style_concerns"], title="🎨 Style Concerns", box=ROUNDED, style="bold blue"
            )
        )

    if review.get("suggestions_for_improvement"):
        console.print(
            Panel(
                review["suggestions_for_improvement"],
                title="💡 Suggestions for Improvement",
                box=ROUNDED,
                style="bold green",
            )
        )

    # Print overall assessment
    if review.get("overall_assessment"):
        assessment = review["overall_assessment"]
        if isinstance(assessment, dict):
            assessment_text = ""
            if assessment.get("key_findings"):
                assessment_text += f"Key Findings: {assessment['key_findings']}\n\n"
            if assessment.get("risk_assessment"):
                assessment_text += f"Risk Assessment: {assessment['risk_assessment']}\n\n"
            if assessment.get("approval_recommendation"):
                rec = assessment["approval_recommendation"]
                rec_color = {"approve": "green", "request_changes": "red", "comment": "yellow"}.get(
                    rec, "white"
                )
                assessment_text += f"Recommendation: [{rec_color}]{rec.upper()}[/{rec_color}]"

            if assessment_text:
                console.print(
                    Panel(assessment_text, title="📊 Overall Assessment", box=ROUNDED, style="bold")
                )
        else:
            console.print(
                Panel(str(assessment), title="📊 Overall Assessment", box=ROUNDED, style="bold")
            )

    # Print confidence if available
    confidence = calculate_confidence(review)
    if show_confidence and confidence:
        console.print(
            Panel(f"Confidence: {confidence}", title="🎯 Confidence", box=ROUNDED, style="bold")
        )


def format_json(review):
    review = review.copy()
    review["key_issues_to_review"] = filter_duplicate_issues(review.get("key_issues_to_review", []))
    return json.dumps(review, indent=2)


def format_markdown(review):
    md = ["# PR Review\n"]

    # Summary
    if review.get("summary"):
        md.append(f"## Summary\n{review['summary']}\n")

    # Key issues
    issues = filter_duplicate_issues(review.get("key_issues_to_review", []))
    if issues:
        md.append("## Key Issues to Review\n")
        for i, issue in enumerate(issues, 1):
            severity = issue.get("severity", "medium")
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")

            md.append(f"### {severity_emoji} Issue #{i}: {issue.get('issue_header', 'No title')}")
            md.append(f"- **File:** `{issue.get('relevant_file', 'Unknown')}`")
            if issue.get("start_line") and issue.get("end_line"):
                md.append(f"- **Lines:** {issue.get('start_line')}-{issue.get('end_line')}")
            md.append(f"- **Severity:** {severity.upper()}")
            md.append(f"- **Description:** {issue.get('issue_content', 'No content')}\n")

    # Technical analysis
    if review.get("technical_analysis"):
        tech = review["technical_analysis"]
        md.append("## Technical Analysis\n")
        if tech.get("code_quality"):
            md.append(f"### Code Quality\n{tech['code_quality']}\n")
        if tech.get("security_considerations") and tech["security_considerations"] != "None":
            md.append(f"### Security Considerations\n{tech['security_considerations']}\n")
        if tech.get("performance_implications") and tech["performance_implications"] != "None":
            md.append(f"### Performance Implications\n{tech['performance_implications']}\n")
        if tech.get("error_handling"):
            md.append(f"### Error Handling\n{tech['error_handling']}\n")

    # Architectural consistency
    if review.get("architectural_consistency"):
        arch = review["architectural_consistency"]
        md.append("## Architectural Consistency\n")
        if arch.get("pattern_alignment"):
            md.append(f"### Pattern Alignment\n{arch['pattern_alignment']}\n")
        if arch.get("codebase_conventions"):
            md.append(f"### Codebase Conventions\n{arch['codebase_conventions']}\n")
        if arch.get("integration_assessment"):
            md.append(f"### Integration Assessment\n{arch['integration_assessment']}\n")

    # Legacy fields
    if review.get("security_concerns") and review["security_concerns"] != "N/A":
        md.append(f"## Security Concerns\n{review['security_concerns']}\n")

    if review.get("performance_concerns") and review["performance_concerns"] != "N/A":
        md.append(f"## Performance Concerns\n{review['performance_concerns']}\n")

    if review.get("style_concerns") and review["style_concerns"] != "N/A":
        md.append(f"## Style Concerns\n{review['style_concerns']}\n")

    if review.get("suggestions_for_improvement"):
        md.append(f"## Suggestions for Improvement\n{review['suggestions_for_improvement']}\n")

    # Overall assessment
    if review.get("overall_assessment"):
        assessment = review["overall_assessment"]
        md.append("## Overall Assessment\n")
        if isinstance(assessment, dict):
            if assessment.get("key_findings"):
                md.append(f"### Key Findings\n{assessment['key_findings']}\n")
            if assessment.get("risk_assessment"):
                md.append(f"### Risk Assessment\n{assessment['risk_assessment']}\n")
            if assessment.get("approval_recommendation"):
                md.append(f"### Recommendation\n{assessment['approval_recommendation'].upper()}\n")
        else:
            md.append(f"{assessment}\n")

    # Confidence
    confidence = calculate_confidence(review)
    if confidence:
        md.append(f"## Confidence\n{confidence}\n")

    # Summary
    md.append(f"## Summary\nTotal Issues: {len(issues)}")

    return "\n".join(md)


def format_fallback_text(raw_text):
    """Format raw text when YAML parsing fails."""
    console = Console()

    # Try to extract sections using common patterns
    sections = []

    # Look for common section headers
    patterns = [
        r"(?:^|\n)([A-Z][A-Z\s]+:?)(?:\n|$)",
        r"(?:^|\n)([A-Z][a-z\s]+:?)(?:\n|$)",
        r"(?:^|\n)(\d+\.\s*[A-Z][^:]+)(?:\n|$)",
        r"(?:^|\n)([A-Z][^:]+:?)(?:\n|$)",
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, raw_text, re.MULTILINE)
        for match in matches:
            section_title = match.group(1).strip()
            start_pos = match.end()

            # Find the next section or end of text
            next_match = re.search(pattern, raw_text[start_pos:], re.MULTILINE)
            if next_match:
                end_pos = start_pos + next_match.start()
            else:
                end_pos = len(raw_text)

            content = raw_text[start_pos:end_pos].strip()
            if content and len(content) > 10:
                sections.append((section_title, content))

    # If no sections found, just format the whole text
    if not sections:
        console.print(Panel(raw_text, title="📝 Review", box=ROUNDED, style="bold"))
        return

    # Print sections
    for title, content in sections:
        console.print(Panel(content, title=title, box=ROUNDED, style="bold"))


def format_output(review, fmt, show_confidence=False):
    if fmt == "json":
        return format_json(review)
    elif fmt == "markdown":
        return format_markdown(review)
    else:
        # Console output is handled directly
        return None
