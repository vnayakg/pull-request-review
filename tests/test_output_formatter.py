from pr_review_agent.output_formatter import filter_duplicate_issues, format_json, format_markdown
import yaml

def test_filter_duplicate_issues():
    issues = [
        {'relevant_file': 'a.py', 'issue_header': 'Bug', 'issue_content': 'Something wrong here', 'start_line': 1, 'end_line': 2},
        {'relevant_file': 'a.py', 'issue_header': 'Bug', 'issue_content': 'Something wrong here', 'start_line': 1, 'end_line': 2},
        {'relevant_file': 'a.py', 'issue_header': 'Bug', 'issue_content': 'Short', 'start_line': 1, 'end_line': 2},
        {'relevant_file': 'b.py', 'issue_header': 'Style', 'issue_content': 'Needs refactor', 'start_line': 3, 'end_line': 4},
    ]
    filtered = filter_duplicate_issues(issues)
    assert len(filtered) == 2
    assert any(i['relevant_file'] == 'a.py' for i in filtered)
    assert any(i['relevant_file'] == 'b.py' for i in filtered)

def test_format_json_and_markdown():
    review = {
        'key_issues_to_review': [
            {'relevant_file': 'a.py', 'issue_header': 'Bug', 'issue_content': 'Something wrong here', 'start_line': 1, 'end_line': 2},
        ],
        'security_concerns': 'No',
        'relevant_tests': 'Yes',
        'confidence': 0.95
    }
    json_out = format_json(review)
    assert 'a.py' in json_out and 'Bug' in json_out
    md_out = format_markdown(review)
    assert '**File:** `a.py`' in md_out and '## Confidence' in md_out 