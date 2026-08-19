"""Thin client over LinkedIn's official REST API.

Only wraps authenticated, ToS-compliant calls: OAuth2 bearer auth against
endpoints your app has been granted access to (Talent Solutions for jobs,
Marketing Developer Platform for posts). It does not scrape linkedin.com
or emulate a browser session.

Response shapes vary by product/version, so this client returns raw JSON
and leaves normalization to `extract.py`.
"""

from __future__ import annotations

from typing import Any, Iterator

import requests

from .config import LinkedInConfig


class LinkedInAPIError(RuntimeError):
    def __init__(self, status_code: int, message: str):
        super().__init__(f"LinkedIn API error {status_code}: {message}")
        self.status_code = status_code


class LinkedInClient:
    def __init__(self, config: LinkedInConfig, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "LinkedIn-Version": self.config.linkedin_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Accept": "application/json",
        }

    def _get(self, path: str, params: dict) -> dict:
        url = f"{self.config.api_base_url}{path}"
        resp = self.session.get(
            url,
            headers=self._headers(),
            params=params,
            timeout=self.config.request_timeout_seconds,
        )
        if not resp.ok:
            raise LinkedInAPIError(resp.status_code, resp.text[:500])
        return resp.json()

    def search_jobs(
        self,
        keywords: str,
        location: str | None = None,
        page_size: int = 25,
        max_pages: int = 10,
    ) -> Iterator[dict]:
        """Yield raw job-listing elements from LinkedIn's job search API."""
        start = 0
        for _ in range(max_pages):
            params = {"keywords": keywords, "start": start, "count": page_size}
            if location:
                params["location"] = location
            payload = self._get(self.config.jobs_search_path, params)
            elements = payload.get("elements", [])
            if not elements:
                return
            yield from elements
            if len(elements) < page_size:
                return
            start += page_size

    def get_job_detail(self, job_id: str) -> dict:
        return self._get(f"{self.config.jobs_search_path}/{job_id}", {})

    def search_posts(
        self,
        keywords: str,
        page_size: int = 25,
        max_pages: int = 10,
    ) -> Iterator[dict]:
        """Yield raw post elements (HR/recruiter posts, hiring keywords,
        hashtags) from LinkedIn's content search API."""
        start = 0
        for _ in range(max_pages):
            params = {"q": "keywords", "keywords": keywords, "start": start, "count": page_size}
            payload = self._get(self.config.posts_search_path, params)
            elements = payload.get("elements", [])
            if not elements:
                return
            yield from elements
            if len(elements) < page_size:
                return
            start += page_size
