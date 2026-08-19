"""End-to-end orchestration: search -> extract -> filter -> dedupe -> write."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from .client import LinkedInClient
from .config import FilterConfig, LinkedInConfig
from .dedupe import deduplicate
from .extract import listing_from_job, listing_from_post
from .filters import apply_filters
from .models import Listing
from . import writers


def run_pipeline(
    job_keywords: list[str],
    post_keywords: list[str],
    location: str | None = None,
    linkedin_config: LinkedInConfig | None = None,
    filter_config: FilterConfig | None = None,
    output_dir: str | Path = "output",
) -> list[Listing]:
    linkedin_config = linkedin_config or LinkedInConfig.from_env()
    filter_config = filter_config or FilterConfig.from_env()
    client = LinkedInClient(linkedin_config)

    listings: list[Listing] = []

    for kw in job_keywords:
        for raw in client.search_jobs(keywords=kw, location=location):
            listings.append(listing_from_job(raw))

    for kw in post_keywords:
        for raw in client.search_posts(keywords=kw):
            listings.append(listing_from_post(raw))

    filtered = list(apply_filters(listings, filter_config))
    deduped = deduplicate(filtered)
    deduped.sort(key=lambda l: l.posting_date or date.min, reverse=True)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    writers.write_markdown(deduped, out_dir / "listings.md")
    writers.write_csv(deduped, out_dir / "listings.csv")
    writers.write_json(deduped, out_dir / "listings.json")

    return deduped
