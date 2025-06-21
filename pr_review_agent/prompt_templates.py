def render_review_prompt(pr_meta, files, diff_summary):
    title = pr_meta.get('title', '')
    author = pr_meta.get('user', {}).get('login', '')
    description = pr_meta.get('body', '')
    prompt = f"""
You are a senior software engineer reviewing a GitHub pull request.

PR Title: {title}
Author: {author}
Description: {description[:500]}

Below are the code changes (unified diff format):

{diff_summary}

Please provide a detailed code review, including:
- Bugs or issues
- Security, performance, and style feedback
- Suggestions for improvement
- Line-by-line comments if possible
- Summary and overall assessment
"""
    return prompt 