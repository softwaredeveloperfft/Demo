from datetime import date, timedelta

from linkedin_extractor.config import FilterConfig
from linkedin_extractor.filters import apply_filters, is_direct_employer, is_recent, is_within_experience
from linkedin_extractor.models import Listing, SourceType

TODAY = date(2026, 8, 19)


def make_listing(**overrides) -> Listing:
    defaults = dict(
        source_type=SourceType.JOB_LISTING,
        source_id="1",
        url="https://example.com/1",
        company="Acme",
        job_title="Engineer",
        posting_date=TODAY,
        experience_min_years=3,
        is_direct_employer=True,
    )
    defaults.update(overrides)
    return Listing(**defaults)


def test_is_recent_within_window():
    listing = make_listing(posting_date=TODAY - timedelta(days=5))
    assert is_recent(listing, max_age_days=5, today=TODAY) is True


def test_is_recent_outside_window():
    listing = make_listing(posting_date=TODAY - timedelta(days=6))
    assert is_recent(listing, max_age_days=5, today=TODAY) is False


def test_is_recent_no_date():
    listing = make_listing(posting_date=None)
    assert is_recent(listing, max_age_days=5, today=TODAY) is False


def test_is_within_experience_true():
    listing = make_listing(experience_min_years=8)
    assert is_within_experience(listing, max_years=8) is True


def test_is_within_experience_false():
    listing = make_listing(experience_min_years=9)
    assert is_within_experience(listing, max_years=8) is False


def test_is_within_experience_unspecified_kept():
    listing = make_listing(experience_min_years=None)
    assert is_within_experience(listing, max_years=8) is True


def test_is_direct_employer():
    assert is_direct_employer(make_listing(is_direct_employer=True)) is True
    assert is_direct_employer(make_listing(is_direct_employer=False)) is False
    assert is_direct_employer(make_listing(is_direct_employer=None)) is True


def test_apply_filters_combines_all():
    listings = [
        make_listing(source_id="a", posting_date=TODAY, experience_min_years=3, is_direct_employer=True),
        make_listing(source_id="b", posting_date=TODAY - timedelta(days=10), experience_min_years=3),
        make_listing(source_id="c", posting_date=TODAY, experience_min_years=10),
        make_listing(source_id="d", posting_date=TODAY, experience_min_years=3, is_direct_employer=False),
    ]
    config = FilterConfig(max_age_days=5, max_experience_years=8, direct_employer_only=True)
    result = list(apply_filters(listings, config, today=TODAY))
    assert [l.source_id for l in result] == ["a"]
