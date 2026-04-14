from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
import sqlite3
import os

app = FastAPI()

# Database configuration
DB_PATH = "security_center.db"
ALERT_THRESHOLD_GB = float(os.getenv("ALERT_THRESHOLD_GB", "0.01"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            alert_level TEXT NOT NULL
        )
    ''')
    # storage report items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            folder_path TEXT NOT NULL,
            size_gb REAL NOT NULL,
            FOREIGN KEY (report_id) REFERENCES reports (id)
        )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_timestamp ON reports(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_alert_level ON reports(alert_level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_report_id ON report_items(report_id)")
    conn.commit()
    conn.close()


init_db()


class DiskEntry(BaseModel):
    folder_path: str
    size_gb: float = Field(ge=0)


class DiskReport(BaseModel):
    hostname: str
    timestamp: datetime = Field(default_factory=datetime.now)
    items: List[DiskEntry] = Field(min_length=1)


@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Multi-Pod Security Command Center Backend",
        "version": "1.3.0",
        "storage": "SQLite",
        "alert_threshold_gb": ALERT_THRESHOLD_GB,
    }


@app.get("/health")
async def health():
    try:
        conn = get_conn()
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"health check failed: {e}")


@app.post("/report")
async def upload_report(report: DiskReport):
    is_critical = any(item.size_gb > ALERT_THRESHOLD_GB for item in report.items)
    alert_level = "CRITICAL" if is_critical else "NORMAL"

    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO reports (hostname, timestamp, alert_level) VALUES (?, ?, ?)",
            (report.hostname, report.timestamp.isoformat(), alert_level)
        )
        report_id = cursor.lastrowid

        cursor.executemany(
            "INSERT INTO report_items (report_id, folder_path, size_gb) VALUES (?, ?, ?)",
            [(report_id, item.folder_path, item.size_gb) for item in report.items],
        )

        conn.commit()
        conn.close()

        print(f"[*] [SECURITY EVENT] Node: {report.hostname} | Level: {alert_level} | Saved to DB")
        return {"status": "received", "alert_level": alert_level, "id": report_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_latest_reports")
async def get_latest_reports(limit: int = Query(default=10, ge=1, le=500)):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reports ORDER BY id DESC LIMIT ?", (limit,))
        reports = cursor.fetchall()

        result = []
        for r in reports:
            report_id = r['id']
            cursor.execute("SELECT folder_path, size_gb FROM report_items WHERE report_id = ?", (report_id,))
            items = cursor.fetchall()

            result.append({
                "hostname": r['hostname'],
                "timestamp": r['timestamp'],
                "alert_level": r['alert_level'],
                "items": [{"folder_path": i['folder_path'], "size_gb": i['size_gb']} for i in items]
            })

        conn.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS c FROM reports")
        total_reports = cursor.fetchone()["c"]
        cursor.execute("SELECT COUNT(*) AS c FROM reports WHERE alert_level = 'CRITICAL'")
        critical_reports = cursor.fetchone()["c"]
        cursor.execute("SELECT MAX(timestamp) AS t FROM reports")
        latest_timestamp = cursor.fetchone()["t"]
        conn.close()

        critical_rate = round((critical_reports / total_reports) * 100, 2) if total_reports else 0.0
        return {
            "total_reports": total_reports,
            "critical_reports": critical_reports,
            "critical_rate_percent": critical_rate,
            "latest_timestamp": latest_timestamp,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
