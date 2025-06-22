import pytest
from pr_review_agent.output_formatter import (
    filter_duplicate_issues, 
    format_console, 
    format_json, 
    format_markdown,
    format_fallback_text
)
import yaml

def test_filter_duplicate_issues():
    issues = [
        {'relevant_file': 'test.py', 'issue_header': 'Test', 'issue_content': 'Content 1 with more text', 'start_line': 1, 'end_line': 2},
        {'relevant_file': 'test.py', 'issue_header': 'Test', 'issue_content': 'Content 1 with more text', 'start_line': 1, 'end_line': 2},  # Duplicate
        {'relevant_file': 'test.py', 'issue_header': 'Test 2', 'issue_content': 'Content 2 with more text', 'start_line': 3, 'end_line': 4},
    ]
    filtered = filter_duplicate_issues(issues)
    assert len(filtered) == 2

def test_format_json():
    review = {
        'summary': 'Test summary',
        'key_issues_to_review': [
            {'relevant_file': 'test.py', 'issue_header': 'Test', 'issue_content': 'Content with sufficient length', 'start_line': 1, 'end_line': 2}
        ]
    }
    result = format_json(review)
    assert 'Test summary' in result
    assert 'test.py' in result

def test_format_markdown():
    review = {
        'summary': 'Test summary',
        'key_issues_to_review': [
            {
                'relevant_file': 'test.py', 
                'issue_header': 'Test Issue', 
                'issue_content': 'Test content with sufficient length for the filter', 
                'start_line': 1, 
                'end_line': 2,
                'severity': 'high'
            }
        ],
        'technical_analysis': {
            'code_quality': 'Good',
            'security_considerations': 'None'
        },
        'architectural_consistency': {
            'pattern_alignment': 'Well aligned'
        },
        'overall_assessment': {
            'key_findings': 'No major issues',
            'approval_recommendation': 'approve'
        }
    }
    result = format_markdown(review)
    
    # Check that all sections are present
    assert '# PR Review' in result
    assert '## Summary' in result
    assert '## Key Issues to Review' in result
    assert '## Technical Analysis' in result
    assert '## Architectural Consistency' in result
    assert '## Overall Assessment' in result
    assert '🔴 Issue #1: Test Issue' in result
    assert 'APPROVE' in result

def test_format_markdown_with_legacy_fields():
    review = {
        'security_concerns': 'Potential SQL injection',
        'performance_concerns': 'None',
        'style_concerns': 'Missing docstrings',
        'suggestions_for_improvement': 'Add input validation'
    }
    result = format_markdown(review)
    
    assert '## Security Concerns' in result
    assert '## Performance Concerns' in result
    assert '## Style Concerns' in result
    assert '## Suggestions for Improvement' in result
    assert 'Potential SQL injection' in result

def test_format_fallback_text():
    # Test with structured text
    raw_text = """
SUMMARY:
This is a test summary.

SECURITY CONCERNS:
No security issues found.

PERFORMANCE:
Code looks good.
"""
    # This should not raise an exception
    format_fallback_text(raw_text)

def test_format_fallback_text_unstructured():
    # Test with unstructured text
    raw_text = "This is just some random text without clear sections."
    # This should not raise an exception
    format_fallback_text(raw_text) 