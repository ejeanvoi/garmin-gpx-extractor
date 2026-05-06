"""Garmin Connect API client for GPX extraction."""

import os
import time
from garminconnect import Garmin, GarminConnectAuthenticationError
from garminconnect import GarminConnectTooManyRequestsError
from garminconnect import GarminConnectConnectionError
from typing import List, Dict, Optional, Callable
from datetime import datetime

from src.utils import extract_activity_type, extract_activity_start_time


class GarminClientError(Exception):
    """Custom exception for Garmin client errors."""
    pass


class GarminClient:
    """Client for interacting with Garmin Connect API."""

    def __init__(
        self,
        email: str,
        password: str,
        mfa_prompt: Optional[Callable[[], str]] = None,
        tokenstore_path: Optional[str] = None
    ):
        """Initialize Garmin client.

        Args:
            email: Garmin Connect email
            password: Garmin Connect password
            mfa_prompt: Optional function to prompt for MFA code
            tokenstore_path: Path to cache authentication tokens
        """
        self.email = email
        self.password = password
        self.mfa_prompt = mfa_prompt
        self.tokenstore_path = tokenstore_path
        self.api = None

    def authenticate(self):
        """Authenticate with Garmin Connect.

        Uses token caching to avoid repeated MFA prompts.
        First login with MFA will cache tokens for future use.

        Raises:
            GarminClientError: If authentication fails.
        """
        # First, try to login with stored tokens
        if self.tokenstore_path and os.path.exists(self.tokenstore_path):
            try:
                self.api = Garmin()
                self.api.login(self.tokenstore_path)
                return  # Successfully logged in with cached tokens
            except (GarminConnectAuthenticationError, FileNotFoundError):
                # Tokens expired or invalid, proceed with fresh login
                pass

        # Fresh login with credentials
        try:
            self.api = Garmin(
                self.email,
                self.password,
                is_cn=False,
                return_on_mfa=True
            )
            result1, result2 = self.api.login()

            if result1 == "needs_mfa":
                # MFA required
                if self.mfa_prompt:
                    mfa_code = self.mfa_prompt()
                else:
                    raise GarminClientError(
                        "MFA required but no prompt_mfa mechanism supplied."
                    )

                # Resume login with MFA code
                self.api.resume_login(result2, mfa_code)

            # Save tokens for future use
            if self.tokenstore_path:
                self.api.client.dump(self.tokenstore_path)

        except GarminConnectAuthenticationError as e:
            raise GarminClientError(f"Authentication failed: {e}")
        except Exception as e:
            raise GarminClientError(f"Authentication error: {e}")

    def get_activities(
        self,
        start: int = 0,
        limit: int = 20
    ) -> List[Dict]:
        """Get activities from Garmin Connect.

        Args:
            start: Starting index for pagination
            limit: Number of activities to fetch per request

        Returns:
            List of activity dictionaries

        Raises:
            GarminClientError: If API request fails.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.api.get_activities(start, limit)
                if isinstance(result, dict):
                    return result.get("activityList", [])
                return result if result else []
            except GarminConnectTooManyRequestsError:
                wait_time = 10 * (attempt + 1)
                print(f"Rate limit hit. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            except GarminConnectConnectionError:
                wait_time = 5 * (attempt + 1)
                print(f"Connection error. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
        raise GarminClientError(
            "Failed to fetch activities after retries"
        )

    def get_all_activities(
        self,
        activity_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Get all activities with optional filtering.

        Args:
            activity_types: List of activity types to filter by (None = all)
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)

        Returns:
            List of filtered activity dictionaries

        Raises:
            GarminClientError: If API request fails.
        """
        all_activities = []
        start_index = 0
        limit = 200  # Fetch in larger batches

        while True:
            activities = self.get_activities(start_index, limit)
            if not activities:
                break

            all_activities.extend(activities)
            start_index += limit

            # Stop if we got fewer activities than limit
            if len(activities) < limit:
                break

            # Small delay to avoid rate limiting
            time.sleep(1.0)

        # Apply filters
        filtered = self._filter_activities(
            all_activities,
            activity_types,
            start_date,
            end_date
        )

        return filtered

    def _filter_activities(
        self,
        activities: List[Dict],
        activity_types: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> List[Dict]:
        """Filter activities by type and date range.

        Args:
            activities: List of activity dictionaries
            activity_types: List of activity types to filter by
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Filtered list of activities
        """
        filtered = activities

        # Filter by activity type
        if activity_types:
            filtered = [
                a for a in filtered
                if extract_activity_type(a) in activity_types
            ]

        # Filter by date range
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            filtered = [
                a for a in filtered
                if extract_activity_start_time(a) >= start_dt
            ]

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            # Include the entire end date
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            filtered = [
                a for a in filtered
                if extract_activity_start_time(a) <= end_dt
            ]

        return filtered

    def download_gpx(self, activity_id) -> Optional[str]:
        """Download GPX file for an activity.

        Args:
            activity_id: Garmin activity ID (can be int or str)

        Returns:
            GPX content as string, or None if download fails
        """
        # Convert activity_id to string if needed
        activity_id_str = str(activity_id)
        
        max_retries = 3
        last_error = None
        for attempt in range(max_retries):
            try:
                gpx_data = self.api.download_activity(
                    activity_id,
                    dl_fmt=Garmin.ActivityDownloadFormat.GPX
                )
                if gpx_data:
                    if isinstance(gpx_data, bytes):
                        return gpx_data.decode("utf-8")
                    return str(gpx_data)
                return None
            except GarminConnectTooManyRequestsError as e:
                last_error = e
                wait_time = 10 * (attempt + 1)
                print(f"Rate limit hit during download. "
                      f"Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            except Exception as e:
                last_error = e
                # Don't retry on non-429 errors, but still return the error
                break
                
        if last_error:
            print(f"Error downloading activity {activity_id_str}: {last_error}")
        return None
