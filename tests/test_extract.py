from datetime import date, datetime, timezone

from linkedin_extractor.extract import (
    extract_tech_stack,
    guess_direct_employer,
    listing_from_job,
    listing_from_post,
    parse_experience,
)
from linkedin_extractor.models import SourceType


def test_parse_experience_range():
    assert parse_experience("3-5 years of experience") == (3.0, 5.0)


def test_parse_experience_plus():
    assert parse_experience("5+ years experience required") == (5.0, None)


def test_parse_experience_single():
    assert parse_experience("2 years of experience needed") == (2.0, 2.0)


def test_parse_experience_none():
    assert parse_experience("Great opportunity for engineers") == (None, None)


def test_extract_tech_stack():
    text = "We use Python, React and Kubernetes on AWS. Also some Golang."
    assert extract_tech_stack(text) == ["AWS", "Golang", "Kubernetes", "Python", "React"]


def test_guess_direct_employer_true():
    assert guess_direct_employer("Acme Corp", "Join our backend team") is True


def test_guess_direct_employer_false():
    assert guess_direct_employer(
        "Bright Staffing Solutions", "Hiring for our client, a Fortune 500 company"
    ) is False


def test_listing_from_job_basic():
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    raw = {
        "id": "12345",
        "companyName": "Acme Corp",
        "title": "Backend Engineer",
        "location": "Bengaluru, India",
        "description": "3-5 years of experience with Python and AWS.",
        "listedAt": now_ms,
        "url": "https://www.linkedin.com/jobs/view/12345",
    }
    listing = listing_from_job(raw)
    assert listing.source_type == SourceType.JOB_LISTING
    assert listing.company == "Acme Corp"
    assert listing.job_title == "Backend Engineer"
    assert listing.experience_min_years == 3.0
    assert listing.experience_max_years == 5.0
    assert "Python" in listing.tech_stack
    assert listing.is_direct_employer is True
    assert listing.posting_date == date.today()


def test_listing_from_post_extracts_title():
    raw = {
        "id": "post1",
        "author": {"name": "Jane Recruiter"},
        "commentary": "We are hiring a Senior Data Engineer with 4+ years experience in Spark.",
        "url": "https://www.linkedin.com/feed/update/post1",
    }
    listing = listing_from_post(raw)
    assert listing.source_type == SourceType.POST
    assert "Senior Data Engineer" in listing.job_title
    assert listing.experience_min_years == 4.0
    assert "Spark" in listing.tech_stack
