import csv
import json
from datetime import date

from linkedin_extractor.models import Listing, SourceType
from linkedin_extractor.writers import write_csv, write_json, write_markdown


def make_listing():
    return Listing(
        source_type=SourceType.JOB_LISTING,
        source_id="1",
        url="https://example.com/1",
        company="Acme",
        job_title="Backend Engineer",
        location="Remote",
        experience_min_years=3,
        experience_max_years=5,
        posting_date=date(2026, 8, 15),
        job_description="Build things.",
        tech_stack=["Python", "AWS"],
        is_direct_employer=True,
    )


def test_write_json(tmp_path):
    path = tmp_path / "out.json"
    write_json([make_listing()], path)
    data = json.loads(path.read_text())
    assert data[0]["company"] == "Acme"
    assert data[0]["tech_stack"] == ["Python", "AWS"]


def test_write_csv(tmp_path):
    path = tmp_path / "out.csv"
    write_csv([make_listing()], path)
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["company"] == "Acme"
    assert rows[0]["tech_stack"] == "Python, AWS"


def test_write_markdown(tmp_path):
    path = tmp_path / "out.md"
    write_markdown([make_listing()], path)
    content = path.read_text()
    assert "Backend Engineer" in content
    assert "Acme" in content
    assert "3-5 years" in content


def test_write_markdown_empty(tmp_path):
    path = tmp_path / "out.md"
    write_markdown([], path)
    assert "No listings matched" in path.read_text()
