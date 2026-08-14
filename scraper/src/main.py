import time
import json
import re
import requests
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime, timezone
from typing import Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl, ValidationError

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/DEVANSH1-svd/Internship)"
TIMEOUT_SECONDS = 10
BASE_URL = "https://books.toscrape.com/catalogue/"
POLITENESS_DELAY = 0.5  # seconds, between real (non-cached) requests

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


class FetchError(Exception):
    """Raised when a page cannot be fetched, after retries where appropriate."""
    def __init__(self, url, reason):
        self.url = url
        self.reason = reason
        super().__init__(f"{url}: {reason}")


def fetch_page(url: str, cache_filename: str, retry: bool = True) -> str:
    """Fetch a page politely, using a local cache to avoid repeated requests.
    Retries once on timeout or 5xx (transient failures).
    Never retries on 404 or 403 (permanent failures).
    Raises FetchError if the page cannot be obtained."""
    cache_path = CACHE_DIR / cache_filename

    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    attempts = 2 if retry else 1
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            print(f"FETCH: {url} (attempt {attempt})")
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT_SECONDS
            )
        except requests.exceptions.Timeout:
            last_error = "timeout"
            if attempt < attempts:
                time.sleep(1)
                continue
            raise FetchError(url, "timeout after retry")

        if response.status_code == 200:
            response.encoding = response.apparent_encoding
            html = response.text
            cache_path.write_text(html, encoding="utf-8")
            print(f"FETCH complete: {cache_filename} ({len(html)} bytes)")
            return html

        if response.status_code == 404:
            raise FetchError(url, "404 not found")
        if response.status_code == 403:
            raise FetchError(url, "403 forbidden")

        if response.status_code >= 500:
            last_error = f"server error {response.status_code}"
            if attempt < attempts:
                time.sleep(1)
                continue
            raise FetchError(url, f"{last_error} after retry")

        raise FetchError(url, f"unexpected status {response.status_code}")

    raise FetchError(url, last_error or "unknown failure")


def get_catalogue_pages(max_pages: int = 3) -> list[str]:
    """Follow the catalogue's own 'next' links to discover book URLs
    across the first `max_pages` pages. Returns a list of unique,
    absolute book detail URLs."""
    all_book_urls = []
    current_url = urljoin(BASE_URL, "page-1.html")
    pages_visited = 0

    while current_url and pages_visited < max_pages:
        cache_filename = f"catalogue-page-{pages_visited + 1}.html"
        was_cached = (CACHE_DIR / cache_filename).exists()

        html = fetch_page(current_url, cache_filename)
        pages_visited += 1

        if not was_cached:
            time.sleep(POLITENESS_DELAY)

        soup = BeautifulSoup(html, "html.parser")

        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")
            if link and link.get("href"):
                absolute_url = urljoin(current_url, link["href"])
                all_book_urls.append(absolute_url)

        next_link = soup.select_one("li.next a")
        if next_link and next_link.get("href"):
            current_url = urljoin(current_url, next_link["href"])
        else:
            current_url = None

    unique_urls = list(dict.fromkeys(all_book_urls))

    print(f"catalogue_pages={pages_visited} discovered={len(all_book_urls)} unique_urls={len(unique_urls)}")
    return unique_urls


def extract_book_record(detail_url: str, source_page: str) -> dict:
    """Fetch and parse a single book detail page into a raw record
    with all 8 required fields. Raises FetchError if the page can't be fetched."""
    slug = detail_url.rstrip("/").split("/")[-2]
    html = fetch_page(detail_url, f"book-{slug}.html")

    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one(".product_main h1").get_text(strip=True)
    price_text = soup.select_one("p.price_color").get_text(strip=True)
    availability_text = soup.select_one("p.instock.availability").get_text(strip=True)

    rating_tag = soup.select_one("p.star-rating")
    rating_text = rating_tag["class"][1] if rating_tag else None

    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.get_text(strip=True) if description_tag else None

    return {
        "title": title,
        "product_url": detail_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


def extract_all_books(book_urls: list[str], source_page: str) -> tuple[list[dict], list[dict]]:
    """Extract raw records for every book URL, being polite between real fetches.
    One bad page is logged and skipped, not fatal to the run.
    Returns (records, failed_pages)."""
    records = []
    failed_pages = []

    for url in book_urls:
        cache_filename = f"book-{url.rstrip('/').split('/')[-2]}.html"
        was_cached = (CACHE_DIR / cache_filename).exists()

        try:
            record = extract_book_record(url, source_page)
            records.append(record)
        except FetchError as e:
            print(f"FAILED: {e.url} ({e.reason})")
            failed_pages.append({"url": e.url, "reason": e.reason})
        except Exception as e:
            print(f"FAILED: {url} (unexpected error: {e})")
            failed_pages.append({"url": url, "reason": str(e)})

        if not was_cached:
            time.sleep(POLITENESS_DELAY)

    print(f"detail_pages={len(records)} failed_pages={len(failed_pages)}")
    return records, failed_pages


class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: Optional[str] = None
    description: Optional[str] = None
    source_page: str
    fetched_at: str


def parse_price(price_text: str) -> float:
    """Turn '£51.77' into 51.77. Strips any non-digit, non-dot characters."""
    cleaned = re.sub(r"[^\d.]", "", price_text)
    return float(cleaned)


def normalize_and_validate(raw_records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Normalize raw records and validate each against BookRecord.
    Returns (valid_records, error_records)."""
    seen_urls = set()
    valid_records = []
    error_records = []

    for raw in raw_records:
        try:
            product_url = raw["product_url"]
            if product_url in seen_urls:
                continue
            seen_urls.add(product_url)

            enriched = {
                **raw,
                "price_gbp": parse_price(raw["price_text"])
            }

            record = BookRecord(**enriched)
            valid_records.append(json.loads(record.model_dump_json()))

        except (ValidationError, ValueError, KeyError) as e:
            error_records.append({
                "record": raw,
                "reason": str(e)
            })

    return valid_records, error_records


def save_output(valid_records: list[dict], error_records: list[dict]):
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    (output_dir / "books.json").write_text(
        json.dumps(valid_records, indent=2), encoding="utf-8"
    )
    (output_dir / "errors.json").write_text(
        json.dumps(error_records, indent=2), encoding="utf-8"
    )

    print(f"valid_records={len(valid_records)} error_records={len(error_records)}")


def save_run_report(start_time, catalogue_pages, cache_hits_estimate, valid_records,
                     error_records, failed_pages):
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    end_time = datetime.now(timezone.utc)
    duration_seconds = (end_time - start_time).total_seconds()

    report = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": round(duration_seconds, 2),
        "catalogue_pages_fetched": catalogue_pages,
        "valid_records": len(valid_records),
        "invalid_records": len(error_records),
        "failed_pages": len(failed_pages),
        "failed_page_details": failed_pages
    }

    (output_dir / "run-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(f"run-report.json written: duration={report['duration_seconds']}s "
          f"failed_pages={report['failed_pages']}")


if __name__ == "__main__":
    start_time = datetime.now(timezone.utc)

    book_urls = get_catalogue_pages()

    # book_urls.append("https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html")

    raw_records, failed_pages = extract_all_books(book_urls, source_page=BASE_URL)
    valid_records, error_records = normalize_and_validate(raw_records)
    save_output(valid_records, error_records)
    save_run_report(start_time, catalogue_pages=3, cache_hits_estimate=None,
                     valid_records=valid_records, error_records=error_records,
                     failed_pages=failed_pages)