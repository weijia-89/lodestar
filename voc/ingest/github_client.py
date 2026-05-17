"""Thin GitHub Issues client. Pagination + 429/5xx retry. Pull-requests filtered out."""
from datetime import datetime
from typing import Iterator, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

API = "https://api.github.com/repos/{repo}/issues"


class GitHubIssuesClient:
    """Iterate GitHub issues since a given datetime.

    Authenticated (5000 req/hr) if GITHUB_TOKEN passed; unauthenticated (60 req/hr) otherwise.
    Pull requests are excluded (GitHub conflates them with issues at the API level).
    """

    def __init__(self, token: Optional[str] = None, timeout: float = 15.0):
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "lodestar/0.1"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(headers=headers, timeout=timeout)

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        reraise=True,
    )
    def _get(self, url: str, params: dict) -> httpx.Response:
        r = self._client.get(url, params=params)
        # Retry on 429 (rate limit) and 5xx (server error). 4xx other-than-429 fails immediately.
        if r.status_code == 429 or r.status_code >= 500:
            r.raise_for_status()
        return r

    def fetch_issues_since(self, repo: str, since: datetime) -> Iterator[dict]:
        page = 1
        url = API.format(repo=repo)
        while True:
            params = {
                "page": str(page),
                "per_page": "100",
                "state": "all",
                "since": since.isoformat(),
            }
            r = self._get(url, params)
            r.raise_for_status()
            batch = r.json()
            if not batch:
                return
            for item in batch:
                if "pull_request" in item:  # GitHub conflates PRs and issues
                    continue
                yield item
            page += 1
