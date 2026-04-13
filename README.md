# Multi-Pod Security Command Center

`Multi_pod` is the server-side monitoring center (Project A).  
This repository only contains the command center components and excludes the Disk Analyzer client.

The system provides three core capabilities:
- Receive disk-monitoring reports from external nodes via `POST /report`.
- Classify events as `NORMAL` or `CRITICAL` based on a configurable threshold.
- Visualize live and historical events in a Streamlit dashboard.

---

## 1. Project Structure

```text
Multi_pod/
├── backEnd/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontEnd/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── k8s-deployment.yaml
```

Key files:
- `backEnd/main.py`: FastAPI backend, detection logic, SQLite persistence.
- `frontEnd/app.py`: Streamlit dashboard for event visualization and filtering.
- `security_center.db`: SQLite database file generated at runtime.

---

## 2. Architecture and Data Flow

End-to-end flow:
1. External nodes (your separate Disk Analyzer project) send JSON payloads to `POST /report`.
2. Backend applies threshold-based detection using `ALERT_THRESHOLD_GB`.
3. Backend stores data in SQLite tables (`reports` and `report_items`).
4. Frontend calls `GET /get_latest_reports` and `GET /stats` to render metrics and charts.

---

## 3. Prerequisites

- Python 3.10+ (3.12 is supported)
- `pip`
- Optional: Docker Desktop for containerized deployment

Install dependencies:

```bash
# Terminal 1: backend dependencies
cd backEnd
pip install -r requirements.txt

# Terminal 2: frontend dependencies
cd ../frontEnd
pip install -r requirements.txt
```

---

## 4. Local Run (Recommended)

### Step A: Start Backend

```bash
cd backEnd
python -m uvicorn main:app --reload --port 8000
```

Expected startup output:
- `Uvicorn running on http://127.0.0.1:8000`

### Step B: Start Frontend

```bash
cd frontEnd
python -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
```

Expected startup output:
- `Local URL: http://localhost:8501`

Open the dashboard:
- `http://localhost:8501`

---

## 5. API Reference

Swagger UI:
- `http://localhost:8000/docs`

### `GET /`
Purpose: Basic service metadata and runtime config.

Example:

```json
{
  "status": "online",
  "message": "Multi-Pod Security Command Center Backend",
  "version": "1.3.0",
  "alert_threshold_gb": 0.01
}
```

### `GET /health`
Purpose: Service and database connectivity check.

Example:

```json
{"status":"ok","db":"ok"}
```

### `POST /report`
Purpose: Ingest node security report.

Request example:

```json
{
  "hostname": "node-a",
  "timestamp": "2026-04-13T15:30:00",
  "items": [
    {"folder_path": "/var/log", "size_gb": 0.02},
    {"folder_path": "/etc", "size_gb": 0.001}
  ]
}
```

### `GET /get_latest_reports?limit=10`
Purpose: Fetch latest reports (default `10`, allowed range `1-500`).

### `GET /stats`
Purpose: Fetch global statistics.

Example:

```json
{
  "total_reports": 120,
  "critical_reports": 32,
  "critical_rate_percent": 26.67,
  "latest_timestamp": "2026-04-13T15:35:01"
}
```

---

## 6. Threshold Configuration

Detection threshold is controlled by environment variable:
- `ALERT_THRESHOLD_GB` (default `0.01`)

Example:

```bash
export ALERT_THRESHOLD_GB=0.05
python -m uvicorn main:app --reload --port 8000
```

---

## 7. Docker Deployment

From project root:

```bash
docker-compose up --build
```

Endpoints:
- Frontend: `http://localhost:8501`
- Backend docs: `http://localhost:8000/docs`

---

## 8. Kubernetes Deployment (Optional)

```bash
kubectl apply -f k8s-deployment.yaml
```

Note:
- The current manifest is course/demo oriented.
- For production, add:
  - `Secret` for credentials/keys
  - `PVC` for persistent database storage
  - `NetworkPolicy` for least-privilege network access

---

## 9. Troubleshooting

### Frontend not reachable on `localhost:8501`
- Confirm Streamlit process is still running.
- If terminal prompts `Email:`, press Enter to continue.
- Use `frontEnd/app.py` path (not `frontEnd.app`).

### Pandas Styler rendering error
- Current code uses `Styler.map` for newer pandas versions.
- If needed, update packages:
  - `pip install -U pandas streamlit`

### No data shown
- Check backend health: `http://localhost:8000/health`
- Verify external node is posting valid payloads to `/report`

---

## 10. Suggested Next Upgrades

Recommended order:
1. Build Disk Analyzer in a separate repository and integrate with `/report`.
2. Add authentication (API key or JWT) to prevent forged reports.
3. Upgrade storage from SQLite to PostgreSQL.
4. Add outbound alert channels (email, Slack, webhook).
