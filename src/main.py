"""Garmin GPX Extractor - CLI Entry Point.

Extract GPX activities from your Garmin Connect account.

Usage:
    python -m src.main --type running --start 2024-01-01 --end 2024-12-31
    python -m src.main --type cycling
    python -m src.main --all --start 2023-01-01

Authentication:
    First run: You'll be prompted for MFA code from your email
    Subsequent runs: Uses cached tokens (no MFA needed until they expire)
"""

import os
import sys

import click

from src.activity_filter import ActivityFilter
from src.garmin_client import GarminClient, GarminClientError
from src.gpx_exporter import GpxExporter
from src.summary_reporter import SummaryReporter
from src.config_loader import ConfigLoader, ConfigError


def get_mfa_code_interactive():
    """Prompt user for MFA code interactively."""
    return click.prompt(
        "Enter MFA code (check your email)",
        type=str,
        show_default=False
    )


# Note: Activity types are not strictly validated since Garmin API returns
# many dynamic types (e.g., cross_country_skiing_ws, skate_skiing_ws, etc.)
@click.command()
@click.option(
    "--type",
    "-t",
    multiple=True,
    help="Activity type(s) to filter by. Can be specified multiple times."
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Export all activity types."
)
@click.option(
    "--start",
    "-s",
    type=str,
    default=None,
    help="Start date filter (YYYY-MM-DD format)."
)
@click.option(
    "--end",
    "-e",
    type=str,
    default=None,
    help="End date filter (YYYY-MM-DD format)."
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=False),
    default=None,
    help="Path to config file (default: config/config.yaml)."
)
@click.option(
    "--output-dir",
    "-o",
    type=str,
    default=None,
    help="Output directory (default: output)."
)
@click.option(
    "--clear-tokens",
    is_flag=True,
    help="Clear cached authentication tokens (forces MFA on next run)."
)
def main(type, all, start, end, config, output_dir, clear_tokens):
    """Garmin GPX Extractor - Export your Garmin activities as GPX files."""

    # Validate dates
    try:
        start = ActivityFilter.validate_date(start, "Start date")
    except ValueError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)

    try:
        end = ActivityFilter.validate_date(end, "End date")
    except ValueError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)

    # Load configuration
    try:
        loader = ConfigLoader(config)
        config = loader.load()
    except ConfigError as e:
        click.echo(f"Configuration Error: {e}")
        sys.exit(1)

    # Determine activity types
    activity_types = list(type) if type else []
    if all:
        activity_types = []  # Empty means all types

    # Override output dir if specified
    if output_dir:
        config["output"]["directory"] = output_dir

    # Set up token cache path
    token_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".tokens")
    os.makedirs(token_dir, exist_ok=True)
    tokenstore_path = os.path.join(token_dir, "garmin_tokens.json")

    # Clear tokens if requested
    if clear_tokens and os.path.exists(tokenstore_path):
        os.remove(tokenstore_path)
        click.echo("Cleared cached authentication tokens.")

    # Authenticate
    click.echo("Authenticating with Garmin Connect...")
    click.echo("(First run requires MFA code from email. Subsequent runs use cached tokens.)")

    try:
        client = GarminClient(
            config["garmin"]["email"],
            config["garmin"]["password"],
            mfa_prompt=get_mfa_code_interactive,
            tokenstore_path=tokenstore_path
        )
        client.authenticate()
        click.echo("Authentication successful!")
    except GarminClientError as e:
        click.echo(f"Authentication Error: {e}")
        click.echo("")
        click.echo("Troubleshooting:")
        click.echo("1. Check your email and password in config/config.yaml")
        click.echo("2. If you have 2FA/MFA enabled, check your email for the code")
        click.echo("   when prompted during authentication")
        click.echo("3. Wait a few minutes if you see rate limit errors (429)")
        click.echo("4. Use --clear-tokens to reset cached tokens if needed")
        sys.exit(1)

    # Fetch activities
    click.echo("Fetching activities from Garmin Connect...")
    try:
        activities = client.get_all_activities(
            activity_types=activity_types if activity_types else None,
            start_date=start,
            end_date=end
        )
    except GarminClientError as e:
        click.echo(f"Error fetching activities: {e}")
        sys.exit(1)

    if not activities:
        click.echo("No activities found matching your criteria.")
        click.echo("Tip: Try removing filters to see all activities.")
        sys.exit(0)

    click.echo(f"Found {len(activities)} activity(ies) matching your criteria.")

    # Export GPX files
    output_dir = config["output"]["directory"]
    click.echo(f"Exporting GPX files to {output_dir}/...")

    exporter = GpxExporter(output_dir)

    def download_gpx(activity_id):
        return client.download_gpx(activity_id)

    export_summary = exporter.export_activities(activities, download_gpx)

    # Generate and display summary
    reporter = SummaryReporter()
    summary_text = reporter.generate_summary(
        activities,
        export_summary,
        output_dir
    )
    click.echo(summary_text)


if __name__ == "__main__":
    main()
