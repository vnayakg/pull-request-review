import pytest
from pr_review_agent.github_client import GitHubClient

def test_parse_pr_url_valid():
    url = 'https://github.com/owner/repo/pull/123'
    owner, repo, number = GitHubClient.parse_pr_url(url)
    assert owner == 'owner'
    assert repo == 'repo'
    assert number == 123

def test_parse_pr_url_invalid():
    url = 'https://github.com/owner/repo/issues/123'
    with pytest.raises(ValueError):
        GitHubClient.parse_pr_url(url) 