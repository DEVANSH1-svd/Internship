# Books to Scrape — Polite Scraper

A small, polite scraping pipeline that collects book data from a public practice sandbox, cleans it, validates it against a schema, and produces checked JSON output.

## Target classification

- **Site:** `books.toscrape.com`
- **Why this site is appropriate:** the parent site, `toscrape.com`, states directly: "A fictional bookstore that desperately wants to be scraped. It's a safe place for beginners learning web scraping and for developers validating their scraping technologies as well." This is an explicit, stated invitation from the site owner — not an assumption on my part.
- **Scope:** the first 3 catalogue pages only (60 books total), not the full 1000-item catalogue.
- **Data collected:** for each book — title, product URL, price, availability, star rating, description, and provenance (source page + fetch timestamp).
- **robots.txt result:** `https://books.toscrape.com/robots.txt` returns `404 Not Found` — no robots file exists. This is not the same as permission; it simply means no crawling rules are published. Permission for this project comes from the site's own stated purpose (above), not from the absence of a robots file.

I will not reuse this code on another site without checking its rules and terms first.