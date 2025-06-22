def render_review_prompt(pr_meta, files, diff_summary, repository_context=""):
    title = pr_meta.get('title', '')
    author = pr_meta.get('user', {}).get('login', '')
    description = pr_meta.get('body', '')
    
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

def render_contextual_review_prompt(pr_meta, files, diff_summary, repository_context, specific_questions=""):
    """Enhanced prompt for contextual review with specific questions."""
    title = pr_meta.get('title', '')
    author = pr_meta.get('user', {}).get('login', '')
    description = pr_meta.get('body', '')
    
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