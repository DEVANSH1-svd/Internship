import time
import requests
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime, timezone
from bs4 import BeautifulSoup

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/DEVANSH1-svd/Internship)"
TIMEOUT_SECONDS = 10
BASE_URL = "https://books.toscrape.com/catalogue/"
POLITENESS_DELAY = 0.5  # seconds, between real (non-cached) requests

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


def fetch_page(url: str, cache_filename: str) -> str:
    """Fetch a page politely, using a local cache to avoid repeated requests.
    Returns the page's HTML as a string."""
    cache_path = CACHE_DIR / cache_filename

    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    print(f"FETCH: {url}")
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SECONDS
    )

    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: status {response.status_code}")

    response.encoding = response.apparent_encoding
    html = response.text
    cache_path.write_text(html, encoding="utf-8")
    print(f"FETCH complete: {cache_filename} ({len(html)} bytes)")
    return html


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

        # Each book is inside <article class="product_pod"><h3><a href="...">
        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")
            if link and link.get("href"):
                absolute_url = urljoin(current_url, link["href"])
                all_book_urls.append(absolute_url)

        # Follow the site's own "next" link, don't hardcode page numbers
        next_link = soup.select_one("li.next a")
        if next_link and next_link.get("href"):
            current_url = urljoin(current_url, next_link["href"])
        else:
            current_url = None

    unique_urls = list(dict.fromkeys(all_book_urls))  # de-dupe, preserve order

    print(f"catalogue_pages={pages_visited} discovered={len(all_book_urls)} unique_urls={len(unique_urls)}")
    return unique_urls


def extract_book_record(detail_url: str, source_page: str) -> dict:
    """Fetch and parse a single book detail page into a raw record
    with all 8 required fields."""
    slug = detail_url.rstrip("/").split("/")[-2]
    html = fetch_page(detail_url, f"book-{slug}.html")

    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one(".product_main h1").get_text(strip=True)

    price_text = soup.select_one("p.price_color").get_text(strip=True)

    availability_text = soup.select_one("p.instock.availability").get_text(strip=True)

    rating_tag = soup.select_one("p.star-rating")
    # e.g. class="star-rating Three" -> the rating word is the second class
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


def extract_all_books(book_urls: list[str], source_page: str) -> list[dict]:
    """Extract raw records for every book URL, being polite between real fetches."""
    records = []
    for url in book_urls:
        cache_filename = f"book-{url.rstrip('/').split('/')[-2]}.html"
        was_cached = (CACHE_DIR / cache_filename).exists()

        record = extract_book_record(url, source_page)
        records.append(record)

        if not was_cached:
            time.sleep(POLITENESS_DELAY)

    print(f"detail_pages={len(records)}")
    return records


if __name__ == "__main__":
    book_urls = get_catalogue_pages()
    records = extract_all_books(book_urls, source_page=BASE_URL)
    print(records[0])