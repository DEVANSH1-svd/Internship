# The Polite Scraper

A small, polite scraping pipeline that collects book data from a public practice sandbox, cleans it, validates it against a schema, and produces checked JSON — without ever hammering the server.

## Target classification

- **Site:** `books.toscrape.com`
- **Why this site is appropriate:** the parent site, `toscrape.com`, states directly: "A fictional bookstore that desperately wants to be scraped. It's a safe place for beginners learning web scraping and for developers validating their scraping technologies as well." This is an explicit, stated invitation from the site owner — not an assumption on my part.
- **Scope:** the first 3 catalogue pages only (60 books total), not the full 1000-item catalogue.
- **Data collected:** for each book — title, product URL, price, availability, star rating, description, and provenance (source page + fetch timestamp).
- **robots.txt result:** `https://books.toscrape.com/robots.txt` returns `404 Not Found` — no robots file exists. This is not the same as permission; it simply means no crawling rules are published. Permission for this project comes from the site's own stated purpose (above), not from the absence of a robots file.

I will not reuse this code on another site without checking its rules and terms first.

## Run it

**Requirements:** Python 3.10+

```bash
cd scraper
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python src/main.py
```

Output lands in `output/books.json`, `output/errors.json`, and `output/run-report.json`. Cached HTML lives in `cache/` (gitignored — not committed, since it's throwaway local state, not project evidence).

## Record schema

Each validated record in `books.json`:

| Field | Type | Notes |
|---|---|---|
| `title` | string | |
| `product_url` | string (URL) | canonical identity — used to de-duplicate |
| `price_text` | string | original text as scraped, e.g. `"£51.77"` |
| `price_gbp` | number | normalized from `price_text` |
| `availability_text` | string | |
| `rating_text` | string or `null` | e.g. `"Three"` |
| `description` | string or `null` | `null` when the book genuinely has no description — never invented |
| `source_page` | string | provenance: which catalogue page this was discovered from |
| `fetched_at` | string (ISO 8601 UTC) | provenance: when this record was fetched |

Records that fail validation are written to `errors.json` with a reason, and never reach `books.json`.

## Politeness rules

- **User-agent:** every request identifies itself as `FlyRankInternshipA9/1.0 (+https://github.com/DEVANSH1-svd/Internship)`, so a site owner reviewing logs can see who made the request and why.
- **Timeout:** every request gives up after 10 seconds rather than hanging indefinitely.
- **Delay:** at least 500ms between real (non-cached) requests to the live site.
- **Cache:** every fetched page is saved locally on first fetch; all subsequent runs during development read from the cache instead of re-hitting the site.
- **Retry discipline:** timeouts and 5xx server errors get one retry after a short pause (transient failures worth retrying). 404 and 403 are never retried — the page either doesn't exist or the server explicitly said no, and retrying either would be pointless or rude.

## Sample run report

A real run against the live site (`output/run-report.json`):

```json
{
  "start_time": "2026-08-14T06:21:34.215029+00:00",
  "end_time": "2026-08-14T06:21:35.585455+00:00",
  "duration_seconds": 1.37,
  "catalogue_pages_fetched": 3,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failed_page_details": []
}
```

(This particular run read entirely from cache, hence the short duration — a fully live run without any caching takes roughly 30-40 seconds, dominated by the 500ms politeness delay across ~60 requests.)

## Why this needed no browser

The book data (title, price, availability, rating, description) is present directly in the HTML the server sends on first response — confirmed by `toscrape.com` itself, which states "Requires JavaScript: ✘" for the Books catalogue. A headless browser like Playwright would only add startup cost and memory overhead here, with no benefit: there's nothing rendered client-side that a plain HTTP request doesn't already receive.

## Ethics note

- Use an official API when one exists, rather than scraping — scraping is a fallback, not a first choice.
- Never bypass logins, paywalls, or explicit blocks (a 403 or a robots.txt disallow is a "no," not a puzzle to solve).
- Collect only the data actually needed for the task — this project intentionally scoped itself to 3 catalogue pages (60 books) out of the site's full 1000-item catalogue, rather than scraping everything just because it was possible.
- Identify the scraper honestly (see politeness rules above) so a site owner can always tell who is making requests and why.

## One honest limitation

This scraper does not currently handle pagination edge cases beyond the standard "next" link pattern (e.g. a category page with no results, or a site that paginates via JavaScript-driven infinite scroll). It's built and tested specifically against `books.toscrape.com`'s catalogue structure — reusing it against a different site would require re-verifying the CSS selectors and pagination logic first, not just swapping the base URL.