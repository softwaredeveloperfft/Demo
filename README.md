# LinkedIn Job & Post Extraction Pipeline

Extracts job opportunities from LinkedIn's **official REST API** — both
formal job listings and HR/recruiter posts — normalizes them into a
common schema, filters by recency/experience/employer type, deduplicates
overlap between the two sources, and writes results to Markdown, CSV,
and JSON.

```
LinkedIn API
  ├── Jobs search  ─┐
  └── Posts search ─┴─► extract.py (normalize) ─► filters.py ─► dedupe.py ─► writers.py (md/csv/json)
```

## Why the official API, not scraping

LinkedIn's Terms of Service prohibit automated scraping of linkedin.com,
and this project intentionally does not do that — it only calls
LinkedIn's authenticated REST API using OAuth2 credentials from a
LinkedIn Developer Portal application.

That does mean real limits apply:

- **Job search** (`/simpleJobSearches` or equivalent) requires your app
  to have **Talent Solutions** partner access. It is not available to a
  default developer app.
- **Post/content search** requires **Marketing Developer Platform**
  access, and LinkedIn's content APIs are generally scoped to content
  *your own app/organization* has published rather than open full-text
  search of public posts — plan the `post_keywords` use case accordingly.
- Exact response field names differ by API version and partner tier.
  `extract.py` uses defensive, multi-key lookups; adjust the candidate
  keys in `_get(...)` calls to match the payload your access tier
  actually returns.

If you don't yet have partner access, request it via the LinkedIn
Developer Portal, or in the meantime feed this pipeline pre-fetched JSON
you're authorized to use (see `extract.listing_from_job` /
`listing_from_post`, which accept plain dicts).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in LINKEDIN_CLIENT_ID / SECRET / ACCESS_TOKEN
```

## Usage

```bash
python -m linkedin_extractor.cli \
  --job-keywords "backend engineer" "python developer" \
  --post-keywords "we are hiring" "#hiring" \
  --location "India" \
  --output-dir output
```

Writes `output/listings.md`, `output/listings.csv`, `output/listings.json`.

## Filters (defaults, overridable via env or CLI flags)

| Filter | Default | Env var |
|---|---|---|
| Max age | 5 days | `FILTER_MAX_AGE_DAYS` |
| Max experience required | 8 years | `FILTER_MAX_EXPERIENCE_YEARS` |
| Direct employer only | true | `FILTER_DIRECT_EMPLOYER_ONLY` |

"Direct employer" is a heuristic (`extract.guess_direct_employer`) based
on staffing/agency keywords in the company name and description — tune
`_AGENCY_KEYWORDS` in `linkedin_extractor/extract.py` for your use case.

## Extracted fields

Company, exact job title, location, experience required (min/max years),
posting date, job description, key tech stack (keyword-matched), direct
URL, source type (`job_listing` or `post`).

## Tests

```bash
pip install pytest
pytest
```

Tests cover extraction (experience/tech-stack parsing, employer
heuristic), filtering, deduplication, and output writers — all against
mock data, since there's no live API access in this environment.
