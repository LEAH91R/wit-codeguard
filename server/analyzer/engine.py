import ast
from typing import List, Dict, Any
from server.analyzer.visitors import CodeGuardVisitor


class AnalysisEngine:
    def __init__(self, max_file_lines: int = 200):
        """
        Initializes the engine with threshold configuration.
        """
        self.max_file_lines = max_file_lines

    def analyze_single_file(self, file_name: str, file_content: str) -> Dict[str, Any]:
        """
        Analyzes a single file's content using the AST Visitor and file-level checks.
        """
        file_alerts = []

        # 1. Check total file length (Max 200 lines)
        lines = file_content.splitlines()
        total_lines = len(lines)
        if total_lines > self.max_file_lines:
            file_alerts.append(f"File '{file_name}' too long ({total_lines} lines)")

        # 2. Run AST Analysis if the file is not empty and valid
        try:
            tree = ast.parse(file_content)
            visitor = CodeGuardVisitor(file_content)

            # Walk the tree
            visitor.visit(tree)

            # Run post-walk validation (Unused variables check)
            visitor.check_unused_variables()

            # Collect alerts from the visitor
            file_alerts.extend(visitor.alerts)

        except SyntaxError as e:
            # If the file has a syntax error, we report it immediately
            file_alerts.append(f"Syntax error in '{file_name}' at line {e.lineno}: {e.msg}")

        # Return structured results for this specific file
        return {
            "total_lines": total_lines,
            "alerts": file_alerts,
            "alert_count": len(file_alerts)
        }

    def analyze_project(self, files_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyzes multiple files and aggregates metrics for the dashboard.
        """
        project_report = {
            "summary": {"total_files": len(files_data), "total_alerts": 0},
            "files": {},
            "metrics": {
                "file_lengths": {},
                "alert_summary": {}
            }
        }

        total_alerts_accumulator = 0

        for file_name, file_content in files_data.items():
            # Run analysis for each file
            file_result = self.analyze_single_file(file_name, file_content)

            # Store per-file details
            project_report["files"][file_name] = file_result
            project_report["metrics"]["file_lengths"][file_name] = file_result["total_lines"]

            # Accumulate overall alert count
            total_alerts_accumulator += file_result["alert_count"]

        project_report["summary"]["total_alerts"] = total_alerts_accumulator
        return project_report