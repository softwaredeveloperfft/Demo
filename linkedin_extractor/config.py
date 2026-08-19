"""Runtime configuration, loaded from environment variables.

LinkedIn does not expose a general-purpose "search all public jobs/posts"
endpoint to ordinary developer apps. Job search access requires a Talent
Solutions partnership; content (post) search requires Marketing Developer
Platform access. Both grant an OAuth2 access token plus partner-specific
base URLs — set them here once your LinkedIn Developer Portal application
has been approved for the relevant product.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class LinkedInConfig:
    client_id: str
    client_secret: str
    access_token: str
    api_base_url: str = "https://api.linkedin.com/rest"
    jobs_search_path: str = "/simpleJobSearches"
    posts_search_path: str = "/posts"
    request_timeout_seconds: float = 15.0
    linkedin_version: str = "202405"

    @classmethod
    def from_env(cls) -> "LinkedInConfig":
        client_id = os.environ.get("LINKEDIN_CLIENT_ID", "")
        client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
        access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
        missing = [
            name
            for name, val in (
                ("LINKEDIN_CLIENT_ID", client_id),
                ("LINKEDIN_CLIENT_SECRET", client_secret),
                ("LINKEDIN_ACCESS_TOKEN", access_token),
            )
            if not val
        ]
        if missing:
            raise ConfigError(
                "Missing required LinkedIn API credentials in environment: "
                + ", ".join(missing)
                + ". See .env.example."
            )
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            api_base_url=os.environ.get(
                "LINKEDIN_API_BASE_URL", "https://api.linkedin.com/rest"
            ),
            jobs_search_path=os.environ.get(
                "LINKEDIN_JOBS_SEARCH_PATH", "/simpleJobSearches"
            ),
            posts_search_path=os.environ.get("LINKEDIN_POSTS_SEARCH_PATH", "/posts"),
        )


@dataclass(frozen=True)
class FilterConfig:
    max_age_days: int = 5
    max_experience_years: float = 8
    direct_employer_only: bool = True

    @classmethod
    def from_env(cls) -> "FilterConfig":
        return cls(
            max_age_days=int(os.environ.get("FILTER_MAX_AGE_DAYS", 5)),
            max_experience_years=float(
                os.environ.get("FILTER_MAX_EXPERIENCE_YEARS", 8)
            ),
            direct_employer_only=os.environ.get(
                "FILTER_DIRECT_EMPLOYER_ONLY", "true"
            ).lower()
            in ("1", "true", "yes"),
        )
