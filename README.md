# Garmin GPX Extractor

Extract all your GPX activities from Garmin Connect, organized by activity type.

## Features

- **Authentication**: Secure login with Garmin Connect credentials
- **Activity Filtering**: Filter by activity type (running, cycling, hiking, etc.) and date range
- **GPX Export**: Download all activities as GPX files
- **Progress Bars**: Real-time progress indicators during downloads, visible in TTY terminal sessions
- **Deduplication**: Skips activities already on disk (validates file completeness via XML parsing)
- **Organized Output**: Files organized by activity type (`output/running/`, `output/cycling/`, etc.)
- **Summary Report**: Detailed export summary with counts, statistics, and skipped activity counts
- **Environment Variables**: Support for secure credential management

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone or navigate to the project directory:

```bash
cd gpx-backup
```

2. Set up virtual environment (optional but recommended):

```bash
python -m venv v
source v/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure your credentials:

```bash
cp config/config.yaml.example config/config.yaml
```

Edit `config/config.yaml` and add your Garmin Connect credentials:

```yaml
garmin:
  email: "your_email@example.com"
  password: "your_password"
```

**Alternatively**, use environment variables (recommended for security):

```yaml
garmin:
  email: "${GARMIN_EMAIL}"
  password: "${GARMIN_PASSWORD}"
```

Then set the environment variables:

```bash
export GARMIN_EMAIL="your_email@example.com"
export GARMIN_PASSWORD="your_password"
```

## Usage

### Basic Usage

Export all activities:

```bash
python -m src.main --all
```

> **First Run**: You'll be prompted for an MFA code sent to your email. Subsequent runs use cached tokens (no MFA needed).

### Filter by Activity Type

Export only running activities:

```bash
python -m src.main --type running
```

Export multiple types:

```bash
python -m src.main --type running --type cycling
```

### Filter by Date Range

Export activities from a specific period:

```bash
python -m src.main --all --start 2024-01-01 --end 2024-12-31
```

### Combined Filters

Export running activities from a specific period:

```bash
python -m src.main --type running --start 2024-01-01 --end 2024-12-31
```

### Custom Output Directory

```bash
python -m src.main --all --output-dir /path/to/output
```

### Custom Config File

```bash
python -m src.main --all --config /path/to/config.yaml
```

### Clear Cached Tokens

To reset authentication (forces MFA on next run):

```bash
python -m src.main --all --clear-tokens
```

## CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--type` | `-t` | Activity type(s) to filter by (can be repeated) |
| `--all` | `-a` | Export all activity types |
| `--start` | `-s` | Start date filter (YYYY-MM-DD) |
| `--end` | `-e` | End date filter (YYYY-MM-DD) |
| `--config` | `-c` | Path to config file |
| `--output-dir` | `-o` | Output directory |
| `--clear-tokens` | | Clear cached authentication tokens (forces MFA on next run) |

## Supported Activity Types

The app automatically detects and organizes activities by type. Common types include:

- `running`
- `cycling`
- `trail_running`
- `mountain_biking`
- `hiking`
- `walking`
- `indoor_cycling`
- `indoor_rowing`
- `swimming`
- `strength_training`
- `breathwork`
- `cross_country_skiing_ws`
- `skate_skiing_ws`
- `snow_shoe_ws`
- `inline_skating`
- `kayaking_v2`
- `stand_up_paddleboarding_v2`
- `other` (for unrecognized types)

> **Note**: Activity types are extracted from Garmin's API and may include workout-specific suffixes (e.g., `_ws`). All variations are preserved as-is.

## Output Structure

GPX files are organized by activity type:

```
output/
├── running/
│   ├── 20240115_073000_morning_run.gpx
│   └── 20240120_064500_evening_jog.gpx
├── cycling/
│   └── 20240118_090000_weekend_ride.gpx
└── hiking/
    └── 20240201_080000_mountain_hike.gpx
```

> **Note**: Re-running the tool with the same filters will skip activities already saved to disk. Only new or corrupted activities are re-downloaded. The progress bar shows the total count, and the summary report indicates how many were skipped.

## Example Summary Output

```
=== GPX Export Summary ===
Total activities exported: 5
Already on disk (skipped): 37
  - running:    20 activities
  - cycling:    15 activities
  - hiking:      2 activities

Date range: 2023-01-15 to 2024-12-28
Failed exports: 0

GPX files saved to: output/
========================================
```

## Authentication & MFA

### First Run
1. The app will prompt you for an MFA code sent to your email
2. Enter the code when prompted
3. Tokens are cached locally (`.tokens/garmin_tokens.json`) for future use

### Subsequent Runs
- Cached tokens are used automatically (no MFA required)
- Tokens expire after some time - you'll need to re-authenticate when this happens

### Clearing Tokens
Use `--clear-tokens` to reset cached authentication:
```bash
python -m src.main --all --clear-tokens
```

## Security Notes

- **Never commit** your `config/config.yaml` file with real credentials
- The `.gitignore` file excludes `config/config.yaml` by default
- Use environment variables for credentials in production/shared environments
- Session tokens are cached locally (`.tokens/` directory) to avoid repeated logins

## Troubleshooting

### Authentication Failed

- Ensure your email and password are correct
- Check if you have 2FA enabled on your Garmin account
- Try logging in to Garmin Connect website directly

### No Activities Found

- Try removing filters to see all activities
- Check your date range format (YYYY-MM-DD)
- Verify you have activities in Garmin Connect

### Export Errors

- Check your network connection
- Garmin API may have rate limits - try again later
- Some activities may not have GPX data available

## Project Structure

```
gpx-backup/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── garmin_client.py     # Garmin Connect API client
│   ├── activity_filter.py   # Activity filtering logic
│   ├── gpx_exporter.py      # GPX file export logic
│   └── summary_reporter.py  # Summary report generator
├── config/
│   └── config.yaml.example  # Configuration template
├── requirements.txt
└── README.md
```

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE) - see the LICENSE file for details.

```
Garmin GPX Extractor - Extract GPX activities from Garmin Connect
Copyright (C) 2026 Emmanuel Jeanvoine

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
```
