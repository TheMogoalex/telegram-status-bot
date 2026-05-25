from __future__ import annotations

from typing import Protocol

from .config import AppConfig
from .message_formatter import MessageFormatter
from .system_info import SystemInfoCollector, SystemMetrics
from .telegram_client import TelegramClient


class MetricsCollector(Protocol):
    """Protocol for objects that collect system metrics."""

    def collect(self, server_name: str) -> SystemMetrics:
        """Collect metrics for the provided server name."""
        ...


class MessageClient(Protocol):
    """Protocol for objects that send status messages."""

    def send_message(self, chat_id: str, text: str) -> None:
        """Send text to the provided chat ID."""
        ...


def build_status_report(config: AppConfig, collector: MetricsCollector | None = None) -> str:
    """Collect metrics and return a formatted plain-text status report."""
    metrics_collector = collector or SystemInfoCollector(
        partitions=config.disk_partitions,
        host_root=config.host_root,
        host_proc=config.host_proc,
        host_sys=config.host_sys,
        cpu_temperature_path=config.cpu_temperature_path,
    )
    metrics = metrics_collector.collect(config.server_name)
    return MessageFormatter(config).format(metrics)


def send_status_report(
    config: AppConfig,
    client: MessageClient | None = None,
    collector: MetricsCollector | None = None,
) -> str:
    """Build and send a status report, returning the sent text."""
    report = build_status_report(config=config, collector=collector)
    message_client = client or TelegramClient(
        token=config.telegram_bot_token,
        timeout_seconds=config.request_timeout_seconds,
    )
    message_client.send_message(config.telegram_chat_id, report)
    return report
