import logging
import sqlite3
from datetime import datetime, date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from render_pdf import render_report_pdf

app = FastAPI()

DB_PATH = Path(__file__).parent / "report.db"
OUTPUT_DIR = Path(__file__).parent / "reports_output"
OUTPUT_DIR.mkdir(exist_ok=True)


class CreateReportRequest(BaseModel):
    force: bool = False


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


def report_to_dict(row) -> dict:
    """Public shape of a report. Gives a link, never the server's disk path."""
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "report_date": row["report_date"],
        "status": row["status"],
        "file": f"/reports/{row['id']}/file",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/reports", status_code=201)
def create_report(response: Response, body: CreateReportRequest | None = None):
    force = body.force if body else False
    conn = get_db()
    today = date.today().isoformat()

    # Idempotency check: reuse today's report (finished or still rendering)
    # unless the caller asked for a fresh one with force.
    if not force:
        existing = conn.execute(
            "SELECT * FROM reports "
            "WHERE report_date = ? AND status IN ('pending', 'complete') "
            "ORDER BY id DESC LIMIT 1",
            (today,),
        ).fetchone()

        if existing is not None:
            conn.close()
            response.status_code = 200
            return report_to_dict(existing)

    now = datetime.now().isoformat()

    # Insert a placeholder row first, so we get an id to name the file after
    # and so a second request can see that work is already in progress.
    cur = conn.execute(
        "INSERT INTO reports (created_at, report_date, file_path, status) VALUES (?, ?, ?, ?)",
        (now, today, "", "pending"),
    )
    report_id = cur.lastrowid
    conn.commit()

    file_path = OUTPUT_DIR / f"report_{report_id}.pdf"
    try:
        render_report_pdf(output_path=str(file_path))
    except Exception:
        logging.exception("Report %s failed to render", report_id)
        conn.execute("UPDATE reports SET status = 'failed' WHERE id = ?", (report_id,))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=500, detail="Report generation failed")

    conn.execute(
        "UPDATE reports SET file_path = ?, status = ? WHERE id = ?",
        (str(file_path), "complete", report_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()

    return report_to_dict(row)


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No report with id {report_id}")

    return report_to_dict(row)


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No report with id {report_id}")

    if row["status"] != "complete":
        raise HTTPException(
            status_code=409,
            detail=f"Report is not available (status: {row['status']})",
        )

    return FileResponse(
        path=row["file_path"],
        media_type="application/pdf",
        filename=f"report_{report_id}.pdf",
    )