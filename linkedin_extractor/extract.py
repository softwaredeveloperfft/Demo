"""Extraction engine: raw LinkedIn API payloads -> normalized `Listing`s.

Field names in LinkedIn's job/post payloads vary by API version and
partner tier, so lookups here are defensive (multiple candidate keys,
graceful fallback to "") rather than assuming one fixed schema. Adjust
the candidate key lists to match the exact payload your app receives.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

from .models import Listing, SourceType

# Common tech-stack keywords to pull out of free-text job descriptions.
# Extend this list as needed for the roles you're targeting.
TECH_KEYWORDS = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Golang", "Rust",
    "C++", "C#", ".NET", "Ruby", "PHP", "Kotlin", "Swift", "Scala",
    "React", "Angular", "Vue", "Next.js", "Node.js", "Django", "Flask",
    "FastAPI", "Spring", "Spring Boot", "Express",
    "AWS", "Azure", "GCP", "Kubernetes", "Docker", "Terraform",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "Kafka", "RabbitMQ", "Spark", "Hadoop", "Airflow",
    "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy",
    "GraphQL", "REST", "gRPC", "Microservices", "CI/CD", "Jenkins",
    "Git", "Linux",
]

_TECH_PATTERN = re.compile(
    r"(?<![\w.+#])(" + "|".join(re.escape(k) for k in TECH_KEYWORDS) + r")(?![\w])",
    re.IGNORECASE,
)

_EXPERIENCE_RANGE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*\+?\s*years?", re.IGNORECASE
)
_EXPERIENCE_MIN_PLUS_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+\s*years?", re.IGNORECASE
)
_EXPERIENCE_SINGLE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*years?(?:\s+of)?\s+experience", re.IGNORECASE
)

_AGENCY_KEYWORDS = (
    "staffing", "recruiting agency", "recruitment agency", "talent solutions",
    "consultancy", "consulting firm", "hiring for our client",
    "on behalf of our client", "workforce solutions", "rpo",
)


def parse_experience(text: str) -> tuple[float | None, float | None]:
    """Extract (min_years, max_years) experience from free text."""
    if not text:
        return None, None
    m = _EXPERIENCE_RANGE_RE.search(text)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = _EXPERIENCE_MIN_PLUS_RE.search(text)
    if m:
        return float(m.group(1)), None
    m = _EXPERIENCE_SINGLE_RE.search(text)
    if m:
        val = float(m.group(1))
        return val, val
    return None, None


def extract_tech_stack(text: str) -> list[str]:
    if not text:
        return []
    found = {m.group(1) for m in _TECH_PATTERN.finditer(text)}
    # Normalize casing back to the canonical form in TECH_KEYWORDS.
    canonical = {k.lower(): k for k in TECH_KEYWORDS}
    return sorted({canonical[f.lower()] for f in found})


def guess_direct_employer(company: str, description: str) -> bool:
    haystack = f"{company}\n{description}".lower()
    return not any(kw in haystack for kw in _AGENCY_KEYWORDS)


def _parse_posting_date(raw: dict) -> date | None:
    for key in ("listedAt", "postedAt", "publishedAt", "createdAt"):
        val = raw.get(key)
        if val is None:
            continue
        try:
            # LinkedIn timestamps are typically epoch millis.
            if isinstance(val, (int, float)):
                return datetime.fromtimestamp(val / 1000, tz=timezone.utc).date()
            return datetime.fromisoformat(str(val)).date()
        except (ValueError, OSError, OverflowError):
            continue
    return None


def _get(raw: dict, *keys: str, default=""):
    for key in keys:
        val = raw.get(key)
        if val:
            return val
    return default


def listing_from_job(raw: dict) -> Listing:
    company = _get(raw, "companyName", "company")
    if isinstance(company, dict):
        company = company.get("name", "")
    description = _get(raw, "description", "jobDescription", "descriptionText")
    if isinstance(description, dict):
        description = description.get("text", "")
    exp_min, exp_max = parse_experience(description)
    job_id = str(_get(raw, "id", "jobId", "entityUrn", default=""))
    url = _get(raw, "url", "applyUrl", default=f"https://www.linkedin.com/jobs/view/{job_id}")

    return Listing(
        source_type=SourceType.JOB_LISTING,
        source_id=job_id,
        url=url,
        company=company or "",
        job_title=_get(raw, "title", "jobTitle"),
        location=_get(raw, "location", "formattedLocation"),
        experience_min_years=exp_min,
        experience_max_years=exp_max,
        posting_date=_parse_posting_date(raw),
        job_description=description or "",
        tech_stack=extract_tech_stack(description or ""),
        is_direct_employer=guess_direct_employer(company or "", description or ""),
        raw=raw,
    )


def listing_from_post(raw: dict) -> Listing:
    text = _get(raw, "commentary", "text", "content")
    if isinstance(text, dict):
        text = text.get("text", "")
    author = raw.get("author", {})
    company = ""
    if isinstance(author, dict):
        company = author.get("name", "") or author.get("organizationName", "")
    exp_min, exp_max = parse_experience(text or "")
    post_id = str(_get(raw, "id", "entityUrn", default=""))
    url = _get(raw, "url", default=f"https://www.linkedin.com/feed/update/{post_id}")

    title_match = re.search(
        r"(?:hiring|looking for)\s+(?:a|an)?\s*([A-Za-z0-9 /+#().-]{3,60})",
        text or "",
        re.IGNORECASE,
    )
    job_title = title_match.group(1).strip() if title_match else ""

    return Listing(
        source_type=SourceType.POST,
        source_id=post_id,
        url=url,
        company=company,
        job_title=job_title,
        location="",
        experience_min_years=exp_min,
        experience_max_years=exp_max,
        posting_date=_parse_posting_date(raw),
        job_description=text or "",
        tech_stack=extract_tech_stack(text or ""),
        is_direct_employer=guess_direct_employer(company, text or ""),
        raw=raw,
    )
