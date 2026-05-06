"""Configuration loader for Garmin GPX Extractor."""

import os
import re
import yaml
from pathlib import Path


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class ConfigLoader:
    """Loads and validates application configuration."""

    DEFAULT_CONFIG = {
        "garmin": {
            "email": "",
            "password": ""
        },
        "output": {
            "directory": "output",
            "organize_by": ["type"]
        },
        "filters": {
            "default_types": [],
            "date_range": {
                "start": None,
                "end": None
            }
        }
    }

    def __init__(self, config_path: str = None):
        """Initialize config loader.

        Args:
            config_path: Path to config file. Defaults to config/config.yaml
        """
        if config_path is None:
            config_path = os.path.join("config", "config.yaml")
        self.config_path = Path(config_path)
        self.config = dict(self.DEFAULT_CONFIG)

    def load(self) -> dict:
        """Load configuration from file.

        Returns:
            dict: Merged configuration dictionary.

        Raises:
            ConfigError: If config file is invalid or missing required fields.
        """
        if not self.config_path.exists():
            raise ConfigError(
                f"Config file not found: {self.config_path}\n"
                f"Please copy config/config.yaml.example to config/config.yaml "
                f"and fill in your credentials."
            )

        try:
            with open(self.config_path, "r") as f:
                file_config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")

        # Merge with defaults
        self._deep_merge(self.config, file_config)

        # Substitute environment variables
        self._substitute_env_vars(self.config)

        # Validate
        self._validate()

        return self.config

    def _deep_merge(self, base: dict, override: dict):
        """Deep merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _substitute_env_vars(self, obj):
        """Recursively substitute ${VAR_NAME} with environment variable values."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._substitute_env_vars(value)
        elif isinstance(obj, list):
            obj = [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            env_pattern = r"\$\{(\w+)\}"
            def replacer(match):
                var_name = match.group(1)
                env_value = os.environ.get(var_name)
                if env_value is None:
                    return match.group(0)  # Keep original if not found
                return env_value
            return re.sub(env_pattern, replacer, obj)
        return obj

    def _validate(self):
        """Validate configuration.

        Raises:
            ConfigError: If required fields are missing.
        """
        if not self.config.get("garmin", {}).get("email"):
            raise ConfigError("Garmin email is required in config.")
        if not self.config.get("garmin", {}).get("password"):
            raise ConfigError("Garmin password is required in config.")
