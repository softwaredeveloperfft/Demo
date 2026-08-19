"""Filter listings per the pipeline's inclusion criteria."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Iterator

from .config import FilterConfig
from .models import Listing


def is_recent(listing: Listing, max_age_days: int, today: date | None = None) -> bool:
    if listing.posting_date is None:
        return False
    today = today or date.today()
    return today - listing.posting_date <= timedelta(days=max_age_days)


def is_within_experience(listing: Listing, max_years: float) -> bool:
    """Keep listings with no stated experience requirement (can't rule
    them out) or whose minimum requirement is within the cap."""
    if listing.experience_min_years is None:
        return True
    return listing.experience_min_years <= max_years


def is_direct_employer(listing: Listing) -> bool:
    return listing.is_direct_employer is not False


def apply_filters(
    listings: Iterable[Listing], config: FilterConfig, today: date | None = None
) -> Iterator[Listing]:
    for listing in listings:
        if not is_recent(listing, config.max_age_days, today):
            continue
        if not is_within_experience(listing, config.max_experience_years):
            continue
        if config.direct_employer_only and not is_direct_employer(listing):
            continue
        yield listing
