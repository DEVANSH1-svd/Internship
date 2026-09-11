import sqlite3
from datetime import datetime, date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from render_pdf import render_report_pdf

app = FastAPI()

DB_PATH = Path(__file__).parent / "report.db"
OUTPUT_DIR = Path(__file__).parent / "reports_output"
OUTPUT_DIR.mkdir(exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_reports_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            report_date TEXT NOT NULL,
            file_path TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_reports_table()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/reports")
def create_report():
    conn = get_db()

    now = datetime.now().isoformat()
    today = date.today().isoformat()

    # Insert a placeholder row first, so we get an id to name the file after.
    cur = conn.execute(
        "INSERT INTO reports (created_at, report_date, file_path, status) VALUES (?, ?, ?, ?)",
        (now, today, "", "pending"),
    )
    report_id = cur.lastrowid
    conn.commit()

    file_path = OUTPUT_DIR / f"report_{report_id}.pdf"
    render_report_pdf(output_path=str(file_path))

    conn.execute(
        "UPDATE reports SET file_path = ?, status = ? WHERE id = ?",
        (str(file_path), "complete", report_id),
    )
    conn.commit()
    conn.close()

    return {
        "id": report_id,
        "created_at": now,
        "report_date": today,
        "status": "complete",
    }


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No report with id {report_id}")

    return dict(row)


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No report with id {report_id}")

    if row["status"] != "complete":
        raise HTTPException(status_code=409, detail="Report is not ready yet")

    return FileResponse(
        path=row["file_path"],
        media_type="application/pdf",
        filename=f"report_{report_id}.pdf",
    )