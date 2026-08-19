from linkedin_extractor.dedupe import deduplicate
from linkedin_extractor.models import Listing, SourceType


def test_deduplicate_prefers_job_listing_over_post():
    job = Listing(
        source_type=SourceType.JOB_LISTING,
        source_id="job1",
        url="https://example.com/job1",
        company="Acme",
        job_title="Backend Engineer",
        location="Remote",
    )
    post = Listing(
        source_type=SourceType.POST,
        source_id="post1",
        url="https://example.com/post1",
        company="Acme",
        job_title="Backend Engineer",
        location="Remote",
    )
    result = deduplicate([post, job])
    assert len(result) == 1
    assert result[0].source_type == SourceType.JOB_LISTING


def test_deduplicate_keeps_distinct_listings():
    a = Listing(
        source_type=SourceType.JOB_LISTING, source_id="1", url="u1",
        company="Acme", job_title="Backend Engineer", location="Remote",
    )
    b = Listing(
        source_type=SourceType.JOB_LISTING, source_id="2", url="u2",
        company="Beta", job_title="Frontend Engineer", location="Remote",
    )
    result = deduplicate([a, b])
    assert len(result) == 2


def test_deduplicate_falls_back_to_url_when_fields_missing():
    a = Listing(
        source_type=SourceType.POST, source_id="1", url="https://example.com/1",
        company="", job_title="",
    )
    b = Listing(
        source_type=SourceType.POST, source_id="2", url="https://example.com/2",
        company="", job_title="",
    )
    result = deduplicate([a, b])
    assert len(result) == 2
