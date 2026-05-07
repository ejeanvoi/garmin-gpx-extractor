"""Summary reporter for GPX export operations."""

from typing import Dict, List, Optional
from datetime import datetime

from src.utils import extract_activity_type, extract_activity_date


class SummaryReporter:
    """Generates and displays export summary reports."""

    def __init__(self):
        """Initialize summary reporter."""
        self.total_exported = 0
        self.total_failed = 0
        self.type_counts: Dict[str, int] = {}
        self.date_range_start: Optional[str] = None
        self.date_range_end: Optional[str] = None
        self.output_dir: str = "output/"
        self.failed_activities: List[Dict] = []

    def generate_summary(
        self,
        activities: List[Dict],
        export_summary: Dict,
        output_dir: str = "output/"
    ) -> str:
        """Generate a formatted summary report.

        Args:
            activities: List of exported activities
            export_summary: Export summary from GpxExporter
            output_dir: Output directory path

        Returns:
            Formatted summary string
        """
        self.output_dir = output_dir
        self.total_exported = export_summary.get("exported", 0)
        self.total_failed = export_summary.get("failed", 0)
        self.total_skipped = export_summary.get("skipped", 0)
        self.failed_activities = export_summary.get("failed_activities", [])

        # Count by type
        self.type_counts = {}
        dates = []

        for activity in activities:
            activity_type = extract_activity_type(activity)
            self.type_counts[activity_type] = self.type_counts.get(activity_type, 0) + 1

            start_time = extract_activity_date(activity)
            if start_time:
                dates.append(start_time)

        # Calculate date range
        if dates:
            dates.sort()
            self.date_range_start = dates[0]
            self.date_range_end = dates[-1]

        return self._format_report()

    def _format_report(self) -> str:
        """Format the summary report."""
        lines = []
        lines.append("")
        lines.append("=" * 40)
        lines.append("=== GPX Export Summary ===")
        lines.append("=" * 40)
        lines.append(f"Total activities exported: {self.total_exported}")
        if self.total_skipped:
            lines.append(f"Already on disk (skipped): {self.total_skipped}")

        if self.type_counts:
            # Sort by count descending
            sorted_types = sorted(
                self.type_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            # Calculate max width for alignment
            max_type_len = max(len(t) for t, _ in sorted_types) if sorted_types else 0
            for activity_type, count in sorted_types:
                lines.append(f"  - {activity_type + ':':<{max_type_len + 2}} {count} activities")

        if self.date_range_start and self.date_range_end:
            lines.append(f"")
            lines.append(f"Date range: {self.date_range_start} to {self.date_range_end}")

        lines.append(f"")
        lines.append(f"Failed exports: {self.total_failed}")

        if self.total_failed > 0:
            lines.append(f"")
            lines.append(f"Failed activities:")
            for item in self._get_failed_activities():
                lines.append(f"  - {item['activity_id']}: {item['error']}")

        lines.append(f"")
        lines.append(f"GPX files saved to: {self.output_dir}")
        lines.append("=" * 40)
        lines.append("")

        return "\n".join(lines)


    def _get_failed_activities(self) -> List[Dict]:
        """Get list of failed activities with errors."""
        return [
            {
                "activity_id": item.get("activity", {}).get("activityId", "unknown"),
                "error": item.get("error", "Unknown error")
            }
            for item in self._get_failed_activities_raw()
        ]

    def _get_failed_activities_raw(self) -> List[Dict]:
        """Get raw failed activities data."""
        return self.failed_activities
