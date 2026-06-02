import os
from typing import List
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from server.analyzer.engine import AnalysisEngine
from server.analyzer.visualizer import CodeGuardVisualizer

app = FastAPI(title="CodeGuard CI Engine")
engine = AnalysisEngine()
visualizer = CodeGuardVisualizer()

# --- Static Files Configuration ---
# Define the static directory path
STATIC_DIR = "server/static"
# Create the directory automatically if it doesn't exist
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount the physical directory to the /static URL route
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ----------------------------------

@app.post("/alerts")
async def get_alerts(files: List[UploadFile] = File(...)):
    """
    Accepts a list of python files and returns a quick JSON response
    containing only the validation alerts without generating charts.
    """
    files_data = {}
    for uploaded_file in files:
        content_bytes = await uploaded_file.read()
        files_data[uploaded_file.filename] = content_bytes.decode("utf-8")

    report = engine.analyze_project(files_data)

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
    Accepts a commit ID and files, processes them, and automatically
    generates visual breakdown charts saved under the commit directory.
    """
    files_data = {}
    for uploaded_file in files:
        content_bytes = await uploaded_file.read()
        files_data[uploaded_file.filename] = content_bytes.decode("utf-8")

    # 1. Run analysis
    report = engine.analyze_project(files_data)

    # 2. Generate and save visualization charts
    visualizer.generate_charts(commit_id, report)

    return {
        "status": "success",
        "commit_id": commit_id,
        "summary": report["summary"],
        "metrics": report["metrics"],
        "charts_generated": True
    }