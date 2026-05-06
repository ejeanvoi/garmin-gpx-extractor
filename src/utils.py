"""Shared utility functions for Garmin GPX Extractor."""

from datetime import datetime
from typing import Dict, Optional


def extract_activity_type(activity: Dict) -> str:
    """Extract activity type from activity dictionary.

    The Garmin API returns activityType as a dict with 'typeKey' field
    (e.g., {'typeId': 1, 'typeKey': 'running', ...}).

    Args:
        activity: Activity dictionary from Garmin API

    Returns:
        Activity type string (lowercase)
    """
    for key in ["activityType", "typeDesc", "activity_type"]:
        if key in activity:
            type_value = activity[key]
            if isinstance(type_value, dict):
                # Try typeKey first (current API format), then 'type' as fallback
                return str(type_value.get("typeKey", type_value.get("type", "other"))).lower()
            return str(type_value).lower()
    return "other"


def extract_activity_start_time(activity: Dict) -> Optional[datetime]:
    """Extract start time from activity dictionary.

    Args:
        activity: Activity dictionary from Garmin API

    Returns:
        datetime object or None if not found
    """
    for key in ["startTimeLocal", "start_date", "start_time"]:
        if key in activity:
            time_str = str(activity[key])
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]:
                try:
                    return datetime.strptime(
                        time_str.split("+")[0].split("Z")[0],
                        fmt
                    )
                except ValueError:
                    continue
    return None


def extract_activity_date(activity: Dict) -> Optional[str]:
    """Extract date string (YYYY-MM-DD) from activity.

    Args:
        activity: Activity dictionary from Garmin API

    Returns:
        Date string or None if not found
    """
    dt = extract_activity_start_time(activity)
    if dt:
        return dt.strftime("%Y-%m-%d")
    return None


def extract_activity_id(activity: Dict) -> str:
    """Extract activity ID from activity dictionary.

    Args:
        activity: Activity dictionary from Garmin API

    Returns:
        Activity ID string
    """
    return str(activity.get("activityId", activity.get("id", "")))


def extract_activity_name(activity: Dict, default: str = "activity") -> str:
    """Extract activity name from activity dictionary.

    Args:
        activity: Activity dictionary from Garmin API
        default: Default name if not found

    Returns:
        Activity name string
    """
    return activity.get("activityName", activity.get("name", default))


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """Sanitize filename by removing invalid characters.

    Args:
        name: Filename string
        max_length: Maximum filename length

    Returns:
        Sanitized filename string
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    if len(name) > max_length:
        name = name[:max_length]
    return name.strip()


def format_timestamp(dt: Optional[datetime], default: str = None) -> str:
    """Format datetime as timestamp string for filenames.

    Args:
        dt: datetime object
        default: Default string if dt is None

    Returns:
        Timestamp string (YYYYMMDD_HHMMSS)
    """
    if dt:
        return dt.strftime("%Y%m%d_%H%M%S")
    return default or datetime.now().strftime("%Y%m%d_%H%M%S")
