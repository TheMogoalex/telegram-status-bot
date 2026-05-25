from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*args: object, **kwargs: object) -> bool:
        """Return False when python-dotenv is not installed."""
        return False


SUPPORTED_LANGUAGES = {"en", "es"}


class ConfigError(ValueError):
    """Raised when application configuration is missing or invalid."""


@dataclass(frozen=True)
class AppConfig:
    """Validated runtime configuration for the status bot."""

    telegram_bot_token: str
    telegram_chat_id: str
    server_name: str
    disk_partitions: tuple[str, ...]
    language: str
    disk_usage_alert_percent: float
    ram_usage_alert_percent: float
    cpu_temperature_alert_celsius: float
    min_uptime_alert_minutes: int
    host_root: Path
    host_proc: Path
    host_sys: Path
    cpu_temperature_path: Path | None
    request_timeout_seconds: float


class ConfigLoader:
    """Loads and validates environment-based application configuration."""

    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        """Create a loader using the provided environment mapping."""
        self._env = env if env is not None else os.environ

    def load(self, require_telegram: bool = True) -> AppConfig:
        """Return a validated AppConfig instance."""
        token = self._optional_text("TELEGRAM_BOT_TOKEN")
        chat_id = self._optional_text("TELEGRAM_CHAT_ID")

        if require_telegram:
            token = self._required_text("TELEGRAM_BOT_TOKEN")
            chat_id = self._required_text("TELEGRAM_CHAT_ID")

        return AppConfig(
            telegram_bot_token=token,
            telegram_chat_id=chat_id,
            server_name=self._required_text("SERVER_NAME"),
            disk_partitions=self._partitions("DISK_PARTITIONS", default="/"),
            language=self._language("REPORT_LANGUAGE", default="en"),
            disk_usage_alert_percent=self._float(
                "DISK_USAGE_ALERT_PERCENT",
                default=80.0,
                minimum=0.0,
                maximum=100.0,
            ),
            ram_usage_alert_percent=self._float(
                "RAM_USAGE_ALERT_PERCENT",
                default=85.0,
                minimum=0.0,
                maximum=100.0,
            ),
            cpu_temperature_alert_celsius=self._float(
                "CPU_TEMPERATURE_ALERT_CELSIUS",
                default=75.0,
                minimum=0.0,
            ),
            min_uptime_alert_minutes=self._int(
                "MIN_UPTIME_ALERT_MINUTES",
                default=10,
                minimum=0,
            ),
            host_root=self._path("HOST_ROOT", default="/"),
            host_proc=self._path("HOST_PROC", default="/proc"),
            host_sys=self._path("HOST_SYS", default="/sys"),
            cpu_temperature_path=self._optional_path("CPU_TEMPERATURE_PATH"),
            request_timeout_seconds=self._float(
                "TELEGRAM_REQUEST_TIMEOUT_SECONDS",
                default=10.0,
                minimum=1.0,
            ),
        )

    def _required_text(self, name: str) -> str:
        """Return a non-empty environment value or raise ConfigError."""
        value = self._optional_text(name)
        if not value:
            raise ConfigError(f"Missing required environment variable: {name}")
        return value

    def _optional_text(self, name: str) -> str:
        """Return a trimmed environment value or an empty string."""
        return str(self._env.get(name, "")).strip()

    def _float(
        self,
        name: str,
        default: float,
        minimum: float | None = None,
        maximum: float | None = None,
    ) -> float:
        """Return a validated floating-point environment value."""
        raw_value = self._env.get(name)
        if raw_value is None:
            return default

        raw_text = str(raw_value).strip()
        try:
            value = float(raw_text)
        except ValueError as exc:
            raise ConfigError(f"Invalid numeric value for {name}: {raw_text!r}") from exc

        if minimum is not None and value < minimum:
            raise ConfigError(f"{name} must be greater than or equal to {minimum}.")
        if maximum is not None and value > maximum:
            raise ConfigError(f"{name} must be less than or equal to {maximum}.")
        return value

    def _int(self, name: str, default: int, minimum: int | None = None) -> int:
        """Return a validated integer environment value."""
        raw_value = self._env.get(name)
        if raw_value is None:
            return default

        raw_text = str(raw_value).strip()
        try:
            value = int(raw_text)
        except ValueError as exc:
            raise ConfigError(f"Invalid integer value for {name}: {raw_text!r}") from exc

        if minimum is not None and value < minimum:
            raise ConfigError(f"{name} must be greater than or equal to {minimum}.")
        return value

    def _language(self, name: str, default: str) -> str:
        """Return a supported language code."""
        value = str(self._env.get(name, default)).strip().lower()
        if value not in SUPPORTED_LANGUAGES:
            supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
            raise ConfigError(
                f"Unsupported REPORT_LANGUAGE value: {value!r}. Supported values: {supported}."
            )
        return value

    def _partitions(self, name: str, default: str) -> tuple[str, ...]:
        """Return normalized absolute disk partitions."""
        raw_value = str(self._env.get(name, default)).strip()
        partitions = tuple(
            self._normalize_partition(part) for part in raw_value.split(",") if part.strip()
        )
        if not partitions:
            raise ConfigError(f"{name} must include at least one absolute path.")
        return partitions

    def _normalize_partition(self, value: str) -> str:
        """Return a normalized display path for a configured disk partition."""
        partition = value.strip()
        if not partition.startswith("/"):
            raise ConfigError(f"DISK_PARTITIONS entries must be absolute paths: {partition!r}")
        if partition == "/":
            return partition
        return partition.rstrip("/")

    def _path(self, name: str, default: str) -> Path:
        """Return an absolute filesystem path from the environment."""
        raw_value = str(self._env.get(name, default)).strip()
        if not raw_value:
            raise ConfigError(f"{name} must not be empty.")
        path = Path(raw_value)
        if not path.is_absolute():
            raise ConfigError(f"{name} must be an absolute path: {raw_value!r}")
        return path

    def _optional_path(self, name: str) -> Path | None:
        """Return an optional absolute filesystem path from the environment."""
        raw_value = str(self._env.get(name, "")).strip()
        if not raw_value:
            return None
        path = Path(raw_value)
        if not path.is_absolute():
            raise ConfigError(f"{name} must be an absolute path: {raw_value!r}")
        return path


def load_config(
    require_telegram: bool = True,
    env_file: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> AppConfig:
    """Load environment variables and return validated application configuration."""
    if env is None:
        load_dotenv(dotenv_path=env_file)
    return ConfigLoader(env).load(require_telegram=require_telegram)
