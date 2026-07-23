import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg.connect(DATABASE_URL)


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)

            cur.execute("SELECT COUNT(*) FROM tasks")
            row_count = cur.fetchone()[0]

            if row_count == 0:
                cur.execute("""
                    INSERT INTO tasks (title, done) VALUES
                        ('Learn FastAPI', FALSE),
                        ('Build a CRUD API', FALSE),
                        ('Buy milk', TRUE)
                """)

        conn.commit()