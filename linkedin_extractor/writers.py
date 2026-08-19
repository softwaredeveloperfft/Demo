"""Output writers: Markdown, CSV, JSON."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Sequence

from .models import Listing


def write_json(listings: Sequence[Listing], path: str | Path) -> None:
    data = [listing.to_dict() for listing in listings]
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_csv(listings: Sequence[Listing], path: str | Path) -> None:
    fieldnames = [
        "company", "job_title", "location", "experience_min_years",
        "experience_max_years", "posting_date", "tech_stack",
        "is_direct_employer", "source_type", "url", "job_description",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for listing in listings:
            row = listing.to_dict()
            row["tech_stack"] = ", ".join(row["tech_stack"])
            writer.writerow(row)


def write_markdown(listings: Sequence[Listing], path: str | Path) -> None:
    lines = ["# LinkedIn Job Extraction Results", ""]
    if not listings:
        lines.append("_No listings matched the current filters._")
    for listing in listings:
        lines.append(f"## {listing.job_title or '(untitled)'} — {listing.company or 'Unknown company'}")
        lines.append("")
        lines.append(f"- **Location:** {listing.location or 'N/A'}")
        exp = _format_experience(listing)
        lines.append(f"- **Experience:** {exp}")
        lines.append(
            f"- **Posted:** {listing.posting_date.isoformat() if listing.posting_date else 'N/A'}"
        )
        lines.append(f"- **Source:** {listing.source_type.value}")
        lines.append(f"- **Direct employer:** {listing.is_direct_employer}")
        if listing.tech_stack:
            lines.append(f"- **Tech stack:** {', '.join(listing.tech_stack)}")
        lines.append(f"- **URL:** {listing.url}")
        lines.append("")
        if listing.job_description:
            snippet = listing.job_description.strip().replace("\n", " ")
            if len(snippet) > 400:
                snippet = snippet[:400].rstrip() + "…"
            lines.append(f"> {snippet}")
            lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _format_experience(listing: Listing) -> str:
    lo, hi = listing.experience_min_years, listing.experience_max_years
    if lo is None and hi is None:
        return "Not specified"
    if lo is not None and hi is not None and lo != hi:
        return f"{lo:g}-{hi:g} years"
    if lo is not None:
        return f"{lo:g}+ years"
    return f"Up to {hi:g} years"
