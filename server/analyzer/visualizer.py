import os
import matplotlib

# Use 'Agg' background backend so matplotlib can save files without needing a GUI window
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class CodeGuardVisualizer:
    def __init__(self, output_base_dir: str = "server/static/reports"):
        """
        Initializes the visualizer with a base directory to save charts.
        """
        self.output_base_dir = output_base_dir

    def _prepare_commit_dir(self, commit_id: str) -> str:
        """
        Creates a specific directory for the current commit if it doesn't exist.
        """
        commit_dir = os.path.join(self.output_base_dir, commit_id)
        os.makedirs(commit_dir, exist_ok=True)
        return commit_dir

    def generate_charts(self, commit_id: str, report_data: dict):
        """
        Generates all visualization charts for a given commit report.
        """
        commit_dir = self._prepare_commit_dir(commit_id)

        # Extract metrics safely from the engine's report format
        metrics = report_data.get("metrics", {})
        file_lengths = metrics.get("file_lengths", {})

        # Accumulate alert categories across all files
        alert_categories = {"Too Long Function": 0, "Missing Docstring": 0, "Unused Variable": 0,
                            "Hebrew Characters": 0}

        for file_name, file_info in report_data.get("files", {}).items():
            for alert in file_info.get("alerts", []):
                if "too long" in alert.lower():
                    alert_categories["Too Long Function"] += 1
                elif "missing a docstring" in alert.lower():
                    alert_categories["Missing Docstring"] += 1
                elif "defined but never used" in alert.lower():
                    alert_categories["Unused Variable"] += 1
                elif "hebrew characters" in alert.lower():
                    alert_categories["Hebrew Characters"] += 1

        # 1. Create File Lengths Bar Chart
        if file_lengths:
            self._create_bar_chart(file_lengths, commit_dir)

        # 2. Create Alert Distribution Pie Chart
        total_alerts = sum(alert_categories.values())
        if total_alerts > 0:
            self._create_pie_chart(alert_categories, commit_dir)

    def _create_bar_chart(self, file_lengths: dict, commit_dir: str):
        plt.figure(figsize=(8, 4))
        files = list(file_lengths.keys())
        lengths = list(file_lengths.values())

        # Plot bars
        colors = ['#3498db' if l <= 200 else '#e74c3c' for l in lengths]
        plt.bar(files, lengths, color=colors, edgecolor='grey')

        # Threshold line at 200 lines limit
        plt.axhline(y=200, color='#e74c3c', linestyle='--', label='Max File Limit (200 lines)')

        plt.title("File Lengths Distribution", fontsize=14, fontweight='bold', pad=15)
        plt.xlabel("Files", fontsize=11)
        plt.ylabel("Line Count", fontsize=11)
        plt.xticks(rotation=15, ha='right')
        plt.tight_layout()

        # Save plot
        plt.savefig(os.path.join(commit_dir, "file_lengths.png"), dpi=100)
        plt.close()

    def _create_pie_chart(self, alert_categories: dict, commit_dir: str):
        plt.figure(figsize=(6, 6))

        # Filter out categories with 0 alerts to keep the pie clean
        filtered_cats = {k: v for k, v in alert_categories.items() if v > 0}
        labels = list(filtered_cats.keys())
        sizes = list(filtered_cats.values())

        colors = ['#e74c3c', '#f1c40f', '#34495e', '#9b59b6']

        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors,
                textprops={'fontsize': 10, 'weight': 'bold'})

        plt.title("Alert Breakdown by Category", fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()

        # Save plot
        plt.savefig(os.path.join(commit_dir, "alerts_pie.png"), dpi=100)
        plt.close()