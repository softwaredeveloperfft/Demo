"""CLI entry point.

Example:
    python -m linkedin_extractor.cli \
        --job-keywords "backend engineer" "python developer" \
        --post-keywords "we are hiring" "#hiring" \
        --location "India"
"""

from __future__ import annotations

import argparse
import sys

from .config import ConfigError, FilterConfig, LinkedInConfig
from .pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LinkedIn job & post extraction pipeline")
    parser.add_argument("--job-keywords", nargs="*", default=["software engineer"])
    parser.add_argument("--post-keywords", nargs="*", default=["#hiring"])
    parser.add_argument("--location", default=None)
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--max-age-days", type=int, default=None)
    parser.add_argument("--max-experience-years", type=float, default=None)
    args = parser.parse_args(argv)

    try:
        linkedin_config = LinkedInConfig.from_env()
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    filter_config = FilterConfig.from_env()
    if args.max_age_days is not None:
        filter_config = FilterConfig(
            max_age_days=args.max_age_days,
            max_experience_years=filter_config.max_experience_years,
            direct_employer_only=filter_config.direct_employer_only,
        )
    if args.max_experience_years is not None:
        filter_config = FilterConfig(
            max_age_days=filter_config.max_age_days,
            max_experience_years=args.max_experience_years,
            direct_employer_only=filter_config.direct_employer_only,
        )

    results = run_pipeline(
        job_keywords=args.job_keywords,
        post_keywords=args.post_keywords,
        location=args.location,
        linkedin_config=linkedin_config,
        filter_config=filter_config,
        output_dir=args.output_dir,
    )
    print(f"Wrote {len(results)} listings to {args.output_dir}/ (md, csv, json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
