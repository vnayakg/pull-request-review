import re
import requests


class GitHubClient:
    PR_URL_REGEX = re.compile(
        r"https://github.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
    )

    def __init__(self, token, api_url="https://api.github.com"):
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})
        self.session.headers.update({"Accept": "application/vnd.github.v3+json"})

    @classmethod
    def parse_pr_url(cls, url):
        match = cls.PR_URL_REGEX.match(url)
        if not match:
            raise ValueError(f"Invalid PR URL: {url}")
        return match.group("owner"), match.group("repo"), int(match.group("number"))

    def get_pr_metadata(self, owner, repo, number):
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{number}"
        resp = self.session.get(url)
        self._handle_errors(resp)
        return resp.json()

    def get_pr_files(self, owner, repo, number):
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{number}/files"
        files = []
        page = 1
        while True:
            resp = self.session.get(url, params={"page": page, "per_page": 100})
            self._handle_errors(resp)
            data = resp.json()
            files.extend(data)
            if len(data) < 100:
                break
            page += 1
        return files

    def get_pr_diff(self, owner, repo, number):
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{number}"
        headers = self.session.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.diff"
        resp = self.session.get(url, headers=headers)
        self._handle_errors(resp)
        return resp.text

    def _handle_errors(self, resp):
        if resp.status_code == 401:
            raise Exception("Authentication failed: Invalid GitHub token.")
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise Exception("GitHub API rate limit exceeded.")
        if not resp.ok:
            raise Exception(f"GitHub API error: {resp.status_code} {resp.text}")
