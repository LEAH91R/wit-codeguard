import os
import sys
import requests

# Configuration for the local CodeGuard CI server
SERVER_URL = "http://127.0.0.1:8000/analyze"


def discover_python_files(target_dir: str = ".") -> list:
    """
    Scans the target directory recursively and returns a list of paths
    for all Python files, excluding virtual environments and hidden folders.
    """
    py_files = []
    ignored_dirs = {".venv", "venv", ".git", "__pycache__", "build", "dist"}

    for root, dirs, files in os.walk(target_dir):
        # Modifying dirs in-place to prevent os.walk from entering ignored directories
        dirs[:] = [d for d in dirs if d not in ignored_dirs]

        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    return py_files


def run_ci_analysis(commit_id: str):
    """
    Gathers all project Python files and transmits them to the FastAPI
    backend engine for static code verification and analytics generation.
    """
    print(f"[*] Initializing CodeGuard CI Analysis for Commit: {commit_id}")

    # Discover files
    file_paths = discover_python_files()
    if not file_paths:
        print("[!] No Python files found in the current project directory.")
        return

    print(f"[*] Found {len(file_paths)} Python files. Preparing package...")

    # Open files and prepare payload for multipart/form-data upload
    opened_files = []
    multipart_files = []

    try:
        for path in file_paths:
            # We open the file in binary mode to safely transmit it over HTTP
            f = open(path, "rb")
            opened_files.append(f)
            # Standard tuple format for FastAPI UploadFile: (form_field_name, (filename, file_object))
            multipart_files.append(("files", (os.path.basename(path), f)))

        # Form data payload containing the commit ID
        data_payload = {"commit_id": commit_id}

        print("[*] Sending data to CodeGuard analysis server...")
        response = requests.post(SERVER_URL, data=data_payload, files=multipart_files)

        if response.status_code == 200:
            result = response.json()
            print("\n" + "=" * 40)
            print("🚀 CODEGUARD ANALYSIS SUCCESSFUL")
            print("=" * 40)
            print(f"Commit Reference : {result['commit_id']}")
            print(f"Files Evaluated  : {result['summary']['total_files']}")
            print(f"Total Alerts     : {result['summary']['total_alerts']}")
            print("-" * 40)
            print("[*] Analytics charts generated and hosted successfully.")
            print("=" * 40 + "\n")
        else:
            print(f"\n[X] Server Error (Status {response.status_code}): {response.text}")

    except requests.exceptions.ConnectionError:
        print("\n[X] Connection Error: Could not connect to the CodeGuard server.")
        print("[*] Please ensure that your FastAPI server is running (uvicorn server.main:app).")
    finally:
        # Crucial step: ensure all physical file hooks are closed properly
        for f in opened_files:
            f.close()


if __name__ == "__main__":
    # Expecting commit_id as the first argument, default to 'manual_run' if missing
    args = sys.argv[1:]
    current_commit = args[0] if args else "manual_run"
    run_ci_analysis(current_commit)