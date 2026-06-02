import os
from typing import List
from fastapi import FastAPI, UploadFile, File, Form
from server.analyzer.engine import AnalysisEngine

app = FastAPI(title="CodeGuard CI Engine")
engine = AnalysisEngine()


@app.post("/alerts")
async def get_alerts(files: List[UploadFile] = File(...)):
    """
    Accepts a list of python files and returns a quick JSON response
    containing only the validation alerts without generating charts.
    """
    # 1. Convert uploaded files into the dictionary format the engine expects
    files_data = {}
    for uploaded_file in files:
        content_bytes = await uploaded_file.read()
        # Decode bytes to string text
        files_data[uploaded_file.filename] = content_bytes.decode("utf-8")

    # 2. Run the analysis engine
    report = engine.analyze_project(files_data)

    # 3. Return only the raw alerts and summary
    return {
        "total_alerts": report["summary"]["total_alerts"],
        "files_checked": report["summary"]["total_files"],
        "detailed_alerts": {
            name: data["alerts"] for name, data in report["files"].items() if data["alert_count"] > 0
        }
    }


@app.post("/analyze")
async def analyze_code(commit_id: str = Form(...), files: List[UploadFile] = File(...)):
    """
    Accepts a commit ID and files, processes them, and will later
    trigger full visualization reports based on the commit sequence.
    """
    files_data = {}
    for uploaded_file in files:
        content_bytes = await uploaded_file.read()
        files_data[uploaded_file.filename] = content_bytes.decode("utf-8")

    report = engine.analyze_project(files_data)

    # We embed the commit context for tracking over time
    return {
        "status": "success",
        "commit_id": commit_id,
        "summary": report["summary"],
        "metrics": report["metrics"]
    }