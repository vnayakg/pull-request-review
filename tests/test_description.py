import pytest
from unittest.mock import Mock, patch
from pr_review_agent.prompt_templates import render_description_prompt


def extract_user_block(prompt):
    # Helper to extract the [USER] block for easier assertions
    if "[USER]" in prompt:
        return prompt.split("[USER]", 1)[1]
    return prompt


def extract_system_block(prompt):
    if "[SYSTEM]" in prompt and "[USER]" in prompt:
        return prompt.split("[SYSTEM]", 1)[1].split("[USER]", 1)[0]
    return prompt


def test_render_description_prompt_basic():
    """Test basic description prompt rendering."""
    pr_meta = {
        "title": "Add user authentication",
        "user": {"login": "testuser"},
        "body": "This PR adds user authentication to the app.",
    }
    files = [{"filename": "auth.py", "status": "added", "additions": 50, "deletions": 0}]
    diff_summary = (
        "diff --git a/auth.py b/auth.py\nnew file mode 100644\n+def authenticate_user():\n+    pass"
    )

    prompt = render_description_prompt(pr_meta, files, diff_summary)
    user_block = extract_user_block(prompt)
    # Check SYSTEM/USER structure
    assert "[SYSTEM]" in prompt
    assert "[USER]" in prompt
    # Check that PR title, description, and diff are present in the USER block
    assert "Add user authentication" in user_block
    assert "This PR adds user authentication to the app." in user_block
    assert "auth.py" in user_block
    assert "authenticate_user" in user_block


def test_render_description_prompt_with_context():
    """Test description prompt rendering with repository context."""
    pr_meta = {"title": "Fix login bug", "user": {"login": "developer"}, "body": ""}
    files = [{"filename": "login.py", "status": "modified", "additions": 10, "deletions": 5}]
    diff_summary = (
        "diff --git a/login.py b/login.py\n@@ -10,7 +10,7 @@\n-    return False\n+    return True"
    )
    repository_context = "This is the existing authentication system context."

    prompt = render_description_prompt(pr_meta, files, diff_summary, repository_context)
    user_block = extract_user_block(prompt)
    assert "Fix login bug" in user_block
    assert "login.py" in user_block
    assert "This is the existing authentication system context." in prompt
    # Accept any variant containing 'REPOSITORY CONTEXT'
    assert "REPOSITORY CONTEXT" in prompt or "REPOSITORY CONTEXT" in user_block


def test_render_description_prompt_different_styles():
    """Test description prompt rendering with different styles."""
    pr_meta = {
        "title": "Update dependencies",
        "user": {"login": "maintainer"},
        "body": "Updates package dependencies",
    }
    files = [{"filename": "requirements.txt", "status": "modified", "additions": 5, "deletions": 3}]
    diff_summary = "diff --git a/requirements.txt b/requirements.txt\n@@ -1,3 +1,5 @@\n-flask==2.0.1\n+flask==2.3.0\n+requests==2.31.0"

    # Test brief style
    brief_prompt = render_description_prompt(pr_meta, files, diff_summary, style="brief")
    system_block = extract_system_block(brief_prompt)
    assert "brief" in system_block or "concise" in system_block or "one-paragraph" in system_block

    # Test technical style
    technical_prompt = render_description_prompt(pr_meta, files, diff_summary, style="technical")
    system_block = extract_system_block(technical_prompt)
    assert "technical" in system_block or "implementation details" in system_block

    # Test detailed style (default)
    detailed_prompt = render_description_prompt(pr_meta, files, diff_summary, style="detailed")
    system_block = extract_system_block(detailed_prompt)
    # Check for a key phrase always present in the default system block
    assert "Your task is to provide a full description" in system_block


def test_render_description_prompt_with_existing_description():
    """Test description prompt rendering when PR already has a description."""
    pr_meta = {
        "title": "Add new feature",
        "user": {"login": "featuredev"},
        "body": "This is an existing description that should be considered when generating a new one.",
    }
    files = [{"filename": "feature.py", "status": "added", "additions": 100, "deletions": 0}]
    diff_summary = (
        "diff --git a/feature.py b/feature.py\nnew file mode 100644\n+def new_feature():\n+    pass"
    )

    prompt = render_description_prompt(pr_meta, files, diff_summary)
    user_block = extract_user_block(prompt)
    assert (
        "This is an existing description that should be considered" in user_block
        or "This is an existing description that should be considered" in prompt
    )
    assert "Previous description:" in user_block or "Previous description:" in prompt
    assert "feature.py" in user_block
    assert "new_feature" in user_block or "new_feature" in prompt
