def render_review_prompt(pr_meta, files, diff_summary, repository_context=""):
    title = pr_meta.get("title", "")
    author = pr_meta.get("user", {}).get("login", "")
    description = pr_meta.get("body", "")

    # Add repository context if available
    context_section = ""
    if repository_context:
        context_section = f"""

REPOSITORY CONTEXT:
The following is relevant context from the existing codebase to help you understand the codebase structure, patterns, and conventions:

{repository_context}

"""

    prompt = f"""
You are a senior software engineer reviewing a GitHub pull request. You have access to the repository context to provide more informed and contextual feedback.

PR Title: {title}
Author: {author}
Description: {description[:500]}

Below are the code changes (unified diff format):

{diff_summary}{context_section}

Please provide a detailed code review in the following YAML format:

```yaml
review:
  summary: "Brief summary of the overall assessment"
  key_issues_to_review:
    - relevant_file: "path/to/file.py"
      issue_header: "Brief issue title"
      issue_content: "Detailed description of the issue and suggested fix"
      start_line: 10
      end_line: 15
      severity: "high|medium|low"
    - relevant_file: "path/to/another.py"
      issue_header: "Another issue"
      issue_content: "Description"
      start_line: 25
      end_line: 30
      severity: "medium"
  security_concerns: "Any security issues found or 'None' if no concerns"
  performance_concerns: "Any performance issues found or 'None' if no concerns"
  style_concerns: "Any code style issues found or 'None' if no concerns"
  suggestions_for_improvement: "General suggestions for improving the code"
  architectural_consistency: "How well the changes align with existing patterns"
  test_coverage: "Suggestions for test coverage or 'None' if adequate"
  overall_assessment: "Overall recommendation (approve/request_changes/comment)"
  confidence: "high|medium|low"
```

When providing feedback, consider:
1. The existing codebase structure and patterns shown in the repository context
2. How the changes align with or deviate from established conventions
3. Whether the changes follow the same architectural patterns as the rest of the codebase
4. Potential conflicts or improvements based on existing implementations

Focus on actionable, specific feedback with clear recommendations.
"""
    return prompt


def render_contextual_review_prompt(
    pr_meta, files, diff_summary, repository_context, specific_questions=""
):
    """Enhanced prompt for contextual review with specific questions."""
    title = pr_meta.get("title", "")
    author = pr_meta.get("user", {}).get("login", "")
    description = pr_meta.get("body", "")

    questions_section = ""
    if specific_questions:
        questions_section = f"""

SPECIFIC QUESTIONS TO ADDRESS:
{specific_questions}

"""

    prompt = f"""
You are a senior software engineer conducting a comprehensive code review with full repository context.

PR Title: {title}
Author: {author}
Description: {description[:500]}

REPOSITORY CONTEXT:
The following is relevant context from the existing codebase to help you understand the codebase structure, patterns, and conventions:

{repository_context}

CODE CHANGES:
{diff_summary}{questions_section}

Please provide a comprehensive code review in the following YAML format:

```yaml
review:
  summary: "Brief summary of the overall assessment"
  technical_analysis:
    code_quality: "Assessment of code quality and correctness"
    performance_implications: "Performance considerations or 'None'"
    security_considerations: "Security issues found or 'None'"
    error_handling: "Error handling assessment"
  architectural_consistency:
    pattern_alignment: "How well changes align with existing patterns"
    codebase_conventions: "Consistency with established conventions"
    integration_assessment: "Integration with existing systems"
    architectural_improvements: "Suggested architectural improvements or 'None'"
  maintenance_and_readability:
    code_clarity: "Assessment of code clarity and documentation"
    test_coverage: "Test coverage suggestions or 'None' if adequate"
    maintainability: "Maintainability assessment"
    extensibility: "Future extensibility considerations"
  specific_recommendations:
    improvements: "Concrete suggestions for improvement"
    alternative_approaches: "Alternative approaches if applicable or 'None'"
    best_practices: "Best practices recommendations"
    refactoring_opportunities: "Refactoring opportunities or 'None'"
  key_issues_to_review:
    - relevant_file: "path/to/file.py"
      issue_header: "Brief issue title"
      issue_content: "Detailed description of the issue and suggested fix"
      start_line: 10
      end_line: 15
      severity: "high|medium|low"
      category: "security|performance|style|bug|enhancement"
  overall_assessment:
    key_findings: "Summary of key findings"
    risk_assessment: "Risk assessment (low|medium|high)"
    approval_recommendation: "approve|request_changes|comment"
    approval_conditions: "Conditions for approval or 'None'"
    priority_changes: "Priority order of suggested changes"
  confidence: "high|medium|low"
```

Format your response as structured YAML with clear sections and actionable feedback.
"""
    return prompt


def render_description_prompt(
    pr_meta,
    files,
    diff_summary,
    repository_context="",
    style="detailed",
    extra_instructions=None,
    related_tickets=None,
    branch="main",
    commit_messages_str=None,
    enable_custom_labels=False,
    custom_labels_class=None,
    enable_semantic_files_types=True,
    include_file_summary_changes=True,
    enable_pr_diagram=False,
    duplicate_prompt_examples=None,
):
    """
    Generate a prompt for creating PR descriptions, following a structured YAML output and detailed instructions.
    """
    # System prompt
    system = """You are PR-Reviewer, a language model designed to review a Git Pull Request (PR).
Your task is to provide a full description for the PR content: type, description, title, and files walkthrough.
- Focus on the new PR code (lines starting with '+' in the 'PR Git Diff' section).
- Keep in mind that the 'Previous title', 'Previous description' and 'Commit messages' sections may be partial, simplistic, non-informative or out of date. Hence, compare them to the PR diff code, and use them only as a reference.
- The generated title and description should prioritize the most significant changes.
- If needed, each YAML output should be in block scalar indicator ('|')
- When quoting variables, names or file paths from the code, use backticks (`) instead of single quote (').
- When needed, use '- ' as bullets
"""
    # Add style-specific instructions
    if style == "brief":
        system += (
            "\n- Write the description in a single concise paragraph. Be brief and to the point."
        )
    elif style == "technical":
        system += "\n- Focus on technical and implementation details in the description. Include implementation details, code structure, and rationale for changes."
    # (detailed is default, so no extra instructions needed)
    if extra_instructions:
        system += f"""
\nExtra instructions from the user:
=====
{extra_instructions}
=====
"""
    system += """

The output must be a YAML object equivalent to type $PRDescription, according to the following Pydantic definitions:
=====
class PRType(str, Enum):
    bug_fix = "Bug fix"
    tests = "Tests"
    enhancement = "Enhancement"
    documentation = "Documentation"
    other = "Other"
"""
    if enable_custom_labels and custom_labels_class:
        system += f"\n{custom_labels_class}\n"
    if enable_semantic_files_types:
        system += """

class FileDescription(BaseModel):
    filename: str = Field(description="The full file path of the relevant file")
"""
        if include_file_summary_changes:
            system += '    changes_summary: str = Field(description="concise summary of the changes in the relevant file, in bullet points (1-4 bullet points).")\n'
        system += "    changes_title: str = Field(description=\"one-line summary (5-10 words) capturing the main theme of changes in the file\")\n    label: str = Field(description=\"a single semantic label that represents a type of code changes that occurred in the File. Possible values (partial list): 'bug fix', 'tests', 'enhancement', 'documentation', 'error handling', 'configuration changes', 'dependencies', 'formatting', 'miscellaneous', ...\")\n"
    system += """

class PRDescription(BaseModel):
    type: List[PRType] = Field(description="one or more types that describe the PR content. Return the label member value (e.g. 'Bug fix', not 'bug_fix')")
    description: str = Field(description="summarize the PR changes in up to four bullet points, each up to 8 words. For large PRs, add sub-bullets if needed. Order bullets by importance, with each bullet highlighting a key change group.")
    title: str = Field(description="a concise and descriptive title that captures the PR's main theme")
"""
    if enable_pr_diagram:
        system += '    changes_diagram: str = Field(description="a horizontal diagram that represents the main PR changes, in the format of a valid mermaid LR flowchart. The diagram should be concise and easy to read. Leave empty if no diagram is relevant. To create robust Mermaid diagrams, follow this two-step process: (1) Declare the nodes: nodeID["node description"]. (2) Then define the links: nodeID1 -- "link text" --> nodeID2 ")\n'
    if enable_semantic_files_types:
        system += '    pr_files: List[FileDescription] = Field(max_items=20, description="a list of all the files that were changed in the PR, and summary of their changes. Each file must be analyzed regardless of change size.")\n'
    system += "====="

    # User prompt
    user = ""
    if related_tickets:
        user += "Related Ticket Info:\n"
        for ticket in related_tickets:
            user += f"=====\nTicket Title: `{ticket.get('title', '')}`\n"
            if ticket.get("labels"):
                user += f"Ticket Labels: {ticket['labels']}\n"
            if ticket.get("body"):
                user += f"Ticket Description:\n#####\n{ticket['body']}\n#####\n"
            user += "=====\n"
    user += "\nPR Info:\n\n"
    user += f"Previous title: `{pr_meta.get('title', '')}`\n\n"
    if pr_meta.get("body"):
        user += f"Previous description:\n=====\n{pr_meta.get('body').strip()}\n=====\n"
    user += f"\nBranch: `{branch}`\n\n"
    if commit_messages_str:
        user += f"Commit messages:\n=====\n{commit_messages_str.strip()}\n=====\n"
    # Insert repository context if provided
    if repository_context:
        user += f"\nREPOSITORY CONTEXT (for LLM reference):\n====="
        user += f"\n{repository_context.strip()}\n====="
    user += "\n\nThe PR Git Diff:\n=====" + "\n" + diff_summary.strip() + "\n====="
    user += "\nNote that lines in the diff body are prefixed with a symbol that represents the type of change: '-' for deletions, '+' for additions, and ' ' (a space) for unchanged lines.\n"
    if duplicate_prompt_examples:
        user += "\n\nExample output:\n```yaml\n" + duplicate_prompt_examples + "\n```"
        user += "\n(replace '...' with the actual values)\n"
    user += "\n\nResponse (should be a valid YAML, and nothing else):\n```yaml\n"

    # Compose the final prompt
    prompt = f"[SYSTEM]\n{system}\n\n[USER]\n{user}"
    return prompt
