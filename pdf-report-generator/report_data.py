import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "report.db"


def get_report_data() -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    total_books = cur.execute("SELECT COUNT(*) AS count FROM books").fetchone()["count"]

    average_price = cur.execute("SELECT AVG(price) AS avg_price FROM books").fetchone()["avg_price"]

    top_5_expensive = cur.execute("""
        SELECT title, price
        FROM books
        ORDER BY price DESC
        LIMIT 5
    """).fetchall()

    books_per_rating = cur.execute("""
        SELECT rating, COUNT(*) AS count
        FROM books
        GROUP BY rating
        ORDER BY rating
    """).fetchall()

    conn.close()

    return {
        "total_books": total_books,
        "average_price": round(average_price, 2),
        "top_5_expensive": [dict(row) for row in top_5_expensive],
        "books_per_rating": [dict(row) for row in books_per_rating],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_report_data(), indent=2))
