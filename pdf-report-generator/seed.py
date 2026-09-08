import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "report.db"
BOOKS_JSON_PATH = Path(__file__).parent.parent / "scraper" / "output" / "books.json"

RATING_WORD_TO_NUMBER = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            rating INTEGER NOT NULL,
            url TEXT NOT NULL
        )
    """)

    # Delete all rows first, so running this script twice leaves exactly one clean copy
    cur.execute("DELETE FROM books")

    with open(BOOKS_JSON_PATH, encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        rating_number = RATING_WORD_TO_NUMBER.get(book["rating_text"], 0)
        cur.execute(
            "INSERT INTO books (title, price, rating, url) VALUES (?, ?, ?, ?)",
            (book["title"], book["price_gbp"], rating_number, book["product_url"])
        )

    conn.commit()

    count = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    print(f"Seeded {count} books into {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    seed()
