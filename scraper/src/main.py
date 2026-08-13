import requests
from pathlib import Path

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/DEVANSH1-svd/Internship)"
TIMEOUT_SECONDS = 10

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

    html = response.text
    cache_path.write_text(html, encoding="utf-8")
    print(f"FETCH complete: {cache_filename} ({len(html)} bytes)")
    return html


if __name__ == "__main__":
    fetch_page(
        "https://books.toscrape.com/catalogue/page-1.html",
        "catalogue-page-1.html"
    )