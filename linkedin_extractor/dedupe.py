"""Deduplicate listings that surface from multiple sources.

The same opening often appears both as a formal job listing and as an HR
post about the same role. We keep one entry per `Listing.dedupe_key`,
preferring the job listing (richer, more structured data) over a post.
"""

from __future__ import annotations

from typing import Iterable

from .models import Listing, SourceType

_SOURCE_PRIORITY = {SourceType.JOB_LISTING: 0, SourceType.POST: 1}


def deduplicate(listings: Iterable[Listing]) -> list[Listing]:
    best: dict[str, Listing] = {}
    for listing in listings:
        key = listing.dedupe_key
        current = best.get(key)
        if current is None or _SOURCE_PRIORITY[listing.source_type] < _SOURCE_PRIORITY[current.source_type]:
            best[key] = listing
    return list(best.values())
