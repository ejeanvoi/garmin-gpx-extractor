"""Activity filtering utilities."""

from typing import List, Optional
from datetime import datetime

from src.utils import extract_activity_type, extract_activity_start_time


class ActivityFilter:
    """Filters Garmin activities by type and date range."""

    # Common activity types (not exhaustive - API may return more)
    COMMON_ACTIVITY_TYPES = [
        "running",
        "cycling",
        "swimming",
        "hiking",
        "walking",
        "mountain_biking",
        "trail_running",
        "indoor_cycling",
        "indoor_rowing",
        "strength_training",
    ]

    @staticmethod
    def validate_activity_types(types: Optional[List[str]], valid_types: Optional[List[str]] = None) -> List[str]:
        """Validate and normalize activity types.

        Args:
            types: List of activity type strings
            valid_types: List of valid types (defaults to COMMON_ACTIVITY_TYPES)

        Returns:
            Normalized list of activity types (empty = all types)

        Raises:
            ValueError: If invalid activity type is provided
        """
        if not types:
            return []

        if valid_types is None:
            valid_types = ActivityFilter.COMMON_ACTIVITY_TYPES

        normalized = []
        for t in types:
            t_lower = t.lower().strip()
            # Handle comma-separated types
            for subtype in t_lower.split(","):
                subtype = subtype.strip()
                if subtype and subtype not in valid_types:
                    raise ValueError(
                        f"Invalid activity type: '{subtype}'. "
                        f"Common types: {', '.join(valid_types)}"
                    )
                if subtype:
                    normalized.append(subtype)

        return list(set(normalized))  # Remove duplicates

    @staticmethod
    def validate_date(date_str: Optional[str], field_name: str) -> Optional[str]:
        """Validate date format.

        Args:
            date_str: Date string in YYYY-MM-DD format
            field_name: Field name for error messages

        Returns:
            Validated date string

        Raises:
            ValueError: If date format is invalid
        """
        if not date_str:
            return None

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            raise ValueError(f"{field_name} must be in YYYY-MM-DD format: {date_str}")

    @staticmethod
    def filter_by_types(
        activities: List[dict],
        activity_types: List[str]
    ) -> List[dict]:
        """Filter activities by type.

        Args:
            activities: List of activity dictionaries
            activity_types: List of types to include (empty = all)

        Returns:
            Filtered activities
        """
        if not activity_types:
            return activities

        return [
            a for a in activities
            if extract_activity_type(a) in activity_types
        ]

    @staticmethod
    def filter_by_date_range(
        activities: List[dict],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> List[dict]:
        """Filter activities by date range.

        Args:
            activities: List of activity dictionaries
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Filtered activities
        """
        filtered = activities

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            filtered = [
                a for a in filtered
                if extract_activity_start_time(a) >= start_dt
            ]

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
            filtered = [
                a for a in filtered
                if extract_activity_start_time(a) <= end_dt
            ]

        return filtered
