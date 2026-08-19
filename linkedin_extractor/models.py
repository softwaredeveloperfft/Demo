"""Data models for extracted LinkedIn listings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class SourceType(str, Enum):
    JOB_LISTING = "job_listing"
    POST = "post"


@dataclass
class Listing:
    """A single normalized job opportunity, extracted from either a job
    listing or a recruiter/HR post."""

    source_type: SourceType
    source_id: str
    url: str
    company: str
    job_title: str
    location: str = ""
    experience_min_years: float | None = None
    experience_max_years: float | None = None
    posting_date: date | None = None
    job_description: str = ""
    tech_stack: list[str] = field(default_factory=list)
    is_direct_employer: bool | None = None
    raw: dict = field(default_factory=dict)

    @property
    def dedupe_key(self) -> str:
        """Stable identity for a listing, independent of source_type.

        The same opening can appear as both a job listing and a recruiter
        post; company + normalized title + location catches that overlap,
        falling back to the URL when those fields are missing.
        """
        if self.company and self.job_title:
            return "|".join(
                part.strip().lower()
                for part in (self.company, self.job_title, self.location)
            )
        return self.url

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "url": self.url,
            "company": self.company,
            "job_title": self.job_title,
            "location": self.location,
            "experience_min_years": self.experience_min_years,
            "experience_max_years": self.experience_max_years,
            "posting_date": self.posting_date.isoformat() if self.posting_date else None,
            "job_description": self.job_description,
            "tech_stack": self.tech_stack,
            "is_direct_employer": self.is_direct_employer,
        }
