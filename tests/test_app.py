from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from src.app import build_status_report, send_status_report
from src.config import AppConfig
from src.system_info import DiskUsage, SystemMetrics

GIB = 1024**3


class FakeCollector:
    """Test collector that returns deterministic metrics."""

    def collect(self, server_name: str) -> SystemMetrics:
        """Return stable metrics without touching the host system."""
        return SystemMetrics(
            server_name=server_name,
            collected_at=datetime(2026, 5, 25, 10, 30, tzinfo=timezone.utc),
            uptime_seconds=4 * 24 * 60 * 60 + 2 * 60 * 60,
            uptime_error=None,
            cpu_temperature_celsius=48.2,
            cpu_temperature_error=None,
            ram_used_percent=62.4,
            ram_error=None,
            disks=(
                DiskUsage(
                    mount_path="/",
                    resolved_path=Path("/"),
                    total_bytes=100 * GIB,
                    used_bytes=40 * GIB,
                    free_bytes=60 * GIB,
                    used_percent=40.0,
                ),
                DiskUsage(
                    mount_path="/missing",
                    resolved_path=Path("/host/missing"),
                    error="not found",
                ),
            ),
        )


def make_config(
    language: str = "en",
    telegram_bot_token: str = "fake-token",
    telegram_chat_id: str = "123456",
) -> AppConfig:
    """Build a valid test configuration."""
    return AppConfig(
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        server_name="test-server",
        disk_partitions=("/", "/missing"),
        language=language,
        disk_usage_alert_percent=80.0,
        ram_usage_alert_percent=85.0,
        cpu_temperature_alert_celsius=75.0,
        min_uptime_alert_minutes=10,
        host_root=Path("/"),
        host_proc=Path("/proc"),
        host_sys=Path("/sys"),
        cpu_temperature_path=None,
        request_timeout_seconds=10.0,
    )


def test_dry_run_report_builds_without_telegram() -> None:
    """Dry-run report generation must not require Telegram delivery."""
    config = make_config(telegram_bot_token="", telegram_chat_id="")
    report = build_status_report(config=config, collector=FakeCollector())

    assert "Server: test-server" in report
    assert "CPU temperature: 48.2°C" in report
    assert "RAM usage: 62.4%" in report
    assert "- /: 40.0% used (40.0 GB / 100.0 GB)" in report
    assert "- /missing: unavailable (not found)" in report
    assert "No active alerts." in report


def test_send_status_report_uses_telegram_client_mock() -> None:
    """Telegram delivery must call the client with chat ID and report text."""
    config = make_config()
    client = Mock()

    report = send_status_report(config=config, client=client, collector=FakeCollector())

    client.send_message.assert_called_once_with("123456", report)
    assert "Server: test-server" in report
