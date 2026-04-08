from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI()

class DiskEntry (BaseModel):
    folder_path: str
    size_gb: float

class DiskReport(BaseModel):
    hostname: str
    timestamp: datetime = datetime.now()
    items: List[DiskEntry]

# In-memory "database" to store reports for the frontend
reports_db = []

@app.get("/")
async def root():
    return {"status": "online", "message": "Security Command Center Backend"}

@app.post("/report")
async def upload_report(report: DiskReport):
    """
    Endpoint for Project B (Disk Analyzer) to send data.
    In a real scenario, this is where anomaly detection would happen.
    """
    # 简单的异常检测逻辑模拟
    is_critical = any(item.size_gb > 10.0 for item in report.items) # 示例：单目录超过10GB视为警告
    
    report_data = report.dict()
    report_data["alert_level"] = "CRITICAL" if is_critical else "NORMAL"
    
    reports_db.append(report_data)
    
    print(f"[*] Received report from {report.hostname} - Status: {report_data['alert_level']}")
    return {"status": "received", "alert_level": report_data["alert_level"]}

@app.get("/get_latest_reports")
async def get_latest_reports():
    """
    Endpoint for Project A (Frontend) to fetch the latest data.
    """
    return reports_db[-10:] # 返回最近10条记录
:
    