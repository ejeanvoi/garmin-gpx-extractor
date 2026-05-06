"""GPX file exporter with activity type organization."""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from src.utils import (
    extract_activity_type,
    extract_activity_start_time,
    extract_activity_id,
    extract_activity_name,
    sanitize_filename,
    format_timestamp
)


class GpxExporterError(Exception):
    """Custom exception for GPX exporter errors."""
    pass


class GpxExporter:
    """Exports GPX files organized by activity type."""

    def __init__(self, output_dir: str = "output"):
        """Initialize GPX exporter.

        Args:
            output_dir: Base output directory
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.exported_count = 0
        self.failed_count = 0
        self.failed_activities: List[Dict] = []

    def export_activities(
        self,
        activities: List[Dict],
        download_func
    ) -> Dict:
        """Export multiple activities to GPX files.

        Args:
            activities: List of activity dictionaries
            download_func: Function that takes activity_id and returns GPX content

        Returns:
            Export summary dictionary
        """
        self.exported_count = 0
        self.failed_count = 0
        self.failed_activities = []

        for activity in activities:
            activity_id = extract_activity_id(activity)
            if not activity_id:
                self.failed_count += 1
                self.failed_activities.append({
                    "activity": activity,
                    "error": "No activity ID found"
                })
                continue

            try:
                gpx_content = download_func(activity_id)
                if gpx_content:
                    self._save_gpx(activity, gpx_content)
                    self.exported_count += 1
                else:
                    self.failed_count += 1
                    self.failed_activities.append({
                        "activity": activity,
                        "error": "Empty GPX content"
                    })
            except Exception as e:
                self.failed_count += 1
                self.failed_activities.append({
                    "activity": activity,
                    "error": str(e)
                })

        return self.get_summary()

    def _save_gpx(self, activity: Dict, gpx_content: str):
        """Save a single GPX file.

        Args:
            activity: Activity dictionary
            gpx_content: GPX file content as string
        """
        activity_type = extract_activity_type(activity)
        activity_id = extract_activity_id(activity)
        start_time = extract_activity_start_time(activity)

        # Create type directory
        type_dir = self.output_dir / activity_type
        type_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = format_timestamp(start_time)

        # Get activity name for filename, sanitized
        name = extract_activity_name(activity)
        name = sanitize_filename(name)

        filename = f"{timestamp}_{name}.gpx"

        # Handle filename conflicts
        filepath = type_dir / filename
        counter = 1
        while filepath.exists():
            filename = f"{timestamp}_{name}_{counter}.gpx"
            filepath = type_dir / filename
            counter += 1

        # Write GPX file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(gpx_content)


    def get_summary(self) -> Dict:
        """Get export summary.

        Returns:
            Summary dictionary with counts
        """
        return {
            "exported": self.exported_count,
            "failed": self.failed_count,
            "failed_activities": self.failed_activities
        }
