from __future__ import annotations

from datetime import datetime

from .config import AppConfig
from .system_info import DiskUsage, SystemMetrics


class MessageFormatter:
    """Formats system metrics into a plain-text Telegram report."""

    def __init__(self, config: AppConfig) -> None:
        """Create a formatter using validated runtime configuration."""
        self._config = config
        self._language = config.language

    def format(self, metrics: SystemMetrics) -> str:
        """Return a localized plain-text report for Telegram or console output."""
        lines = [
            f"{self._label('server')}: {metrics.server_name}",
            f"{self._label('time')}: {self._format_datetime(metrics.collected_at)}",
            f"{self._label('uptime')}: {self._format_uptime(metrics)}",
            f"{self._label('cpu_temperature')}: {self._format_temperature(metrics)}",
            f"{self._label('ram_usage')}: {self._format_ram(metrics)}",
            "",
            f"{self._label('disks')}:",
        ]

        lines.extend(self._format_disk(disk) for disk in metrics.disks)
        lines.extend(["", f"{self._label('alerts')}:"],)

        alerts = self._build_alerts(metrics)
        if alerts:
            lines.extend(f"- {alert}" for alert in alerts)
        else:
            lines.append(self._label("no_alerts"))

        return "\n".join(lines)

    def _format_datetime(self, value: datetime) -> str:
        """Return a compact local date and time string."""
        return value.strftime("%Y-%m-%d %H:%M")

    def _format_uptime(self, metrics: SystemMetrics) -> str:
        """Return localized uptime text or an unavailable marker."""
        if metrics.uptime_seconds is None:
            return self._unavailable(metrics.uptime_error)
        return self._format_duration(metrics.uptime_seconds)

    def _format_temperature(self, metrics: SystemMetrics) -> str:
        """Return localized CPU temperature text or an unavailable marker."""
        if metrics.cpu_temperature_celsius is None:
            return self._unavailable(metrics.cpu_temperature_error)
        return f"{metrics.cpu_temperature_celsius:.1f}°C"

    def _format_ram(self, metrics: SystemMetrics) -> str:
        """Return localized RAM usage text or an unavailable marker."""
        if metrics.ram_used_percent is None:
            return self._unavailable(metrics.ram_error)
        return f"{metrics.ram_used_percent:.1f}%"

    def _format_disk(self, disk: DiskUsage) -> str:
        """Return one localized disk usage line."""
        if disk.error is not None:
            return f"- {disk.mount_path}: {self._unavailable(disk.error)}"

        if disk.used_percent is None or disk.used_bytes is None or disk.total_bytes is None:
            return f"- {disk.mount_path}: {self._unavailable('missing disk values')}"

        return (
            f"- {disk.mount_path}: {disk.used_percent:.1f}% "
            f"{self._label('used')} "
            f"({self._format_gib(disk.used_bytes)} / {self._format_gib(disk.total_bytes)})"
        )

    def _format_gib(self, value: int) -> str:
        """Return a byte value formatted as GiB with a familiar GB suffix."""
        return f"{value / (1024 ** 3):.1f} GB"

    def _build_alerts(self, metrics: SystemMetrics) -> list[str]:
        """Return localized alert messages based on configured thresholds."""
        alerts: list[str] = []

        if self._config.disk_usage_alert_percent > 0:
            for disk in metrics.disks:
                if (
                    disk.used_percent is not None
                    and disk.used_percent > self._config.disk_usage_alert_percent
                ):
                    alerts.append(
                        self._alert(
                            "disk_alert",
                            path=disk.mount_path,
                            threshold=self._config.disk_usage_alert_percent,
                            value=disk.used_percent,
                        )
                    )

        if (
            self._config.ram_usage_alert_percent > 0
            and metrics.ram_used_percent is not None
            and metrics.ram_used_percent > self._config.ram_usage_alert_percent
        ):
            alerts.append(
                self._alert(
                    "ram_alert",
                    threshold=self._config.ram_usage_alert_percent,
                    value=metrics.ram_used_percent,
                )
            )

        if (
            self._config.cpu_temperature_alert_celsius > 0
            and metrics.cpu_temperature_celsius is not None
            and metrics.cpu_temperature_celsius > self._config.cpu_temperature_alert_celsius
        ):
            alerts.append(
                self._alert(
                    "temperature_alert",
                    threshold=self._config.cpu_temperature_alert_celsius,
                    value=metrics.cpu_temperature_celsius,
                )
            )

        if (
            self._config.min_uptime_alert_minutes > 0
            and metrics.uptime_seconds is not None
            and metrics.uptime_seconds < self._config.min_uptime_alert_minutes * 60
        ):
            alerts.append(
                self._alert(
                    "uptime_alert",
                    threshold=float(self._config.min_uptime_alert_minutes),
                    value=metrics.uptime_seconds / 60.0,
                )
            )

        return alerts

    def _format_duration(self, seconds: float) -> str:
        """Return a localized duration using up to two major units."""
        total_minutes = max(int(seconds // 60), 0)
        if total_minutes < 1:
            return self._label("less_than_minute")

        days, remainder = divmod(total_minutes, 24 * 60)
        hours, minutes = divmod(remainder, 60)
        units = (
            (days, "day", "days"),
            (hours, "hour", "hours"),
            (minutes, "minute", "minutes"),
        )
        parts = [
            self._plural(value, singular, plural)
            for value, singular, plural in units
            if value
        ]
        return ", ".join(parts[:2])

    def _plural(self, value: int, singular_key: str, plural_key: str) -> str:
        """Return a localized pluralized unit."""
        key = singular_key if value == 1 else plural_key
        return f"{value} {self._label(key)}"

    def _unavailable(self, reason: str | None) -> str:
        """Return localized unavailable text with an optional reason."""
        if reason:
            return f"{self._label('unavailable')} ({reason})"
        return self._label("unavailable")

    def _label(self, key: str) -> str:
        """Return a localized label for the active language."""
        return LABELS[self._language][key]

    def _alert(self, key: str, **values: float | str) -> str:
        """Return a localized alert rendered with numeric values."""
        return ALERTS[self._language][key].format(**values)


LABELS = {
    "en": {
        "server": "Server",
        "time": "Time",
        "uptime": "Uptime",
        "cpu_temperature": "CPU temperature",
        "ram_usage": "RAM usage",
        "disks": "Disks",
        "alerts": "Alerts",
        "no_alerts": "No active alerts.",
        "unavailable": "unavailable",
        "used": "used",
        "less_than_minute": "less than 1 minute",
        "day": "day",
        "days": "days",
        "hour": "hour",
        "hours": "hours",
        "minute": "minute",
        "minutes": "minutes",
    },
    "es": {
        "server": "Servidor",
        "time": "Hora",
        "uptime": "Tiempo activo",
        "cpu_temperature": "Temperatura CPU",
        "ram_usage": "Uso de RAM",
        "disks": "Discos",
        "alerts": "Alertas",
        "no_alerts": "No hay alertas activas.",
        "unavailable": "no disponible",
        "used": "usado",
        "less_than_minute": "menos de 1 minuto",
        "day": "día",
        "days": "días",
        "hour": "hora",
        "hours": "horas",
        "minute": "minuto",
        "minutes": "minutos",
    },
}

ALERTS = {
    "en": {
        "disk_alert": "Disk usage for {path} is above {threshold:.1f}% ({value:.1f}%).",
        "ram_alert": "RAM usage is above {threshold:.1f}% ({value:.1f}%).",
        "temperature_alert": "CPU temperature is above {threshold:.1f}°C ({value:.1f}°C).",
        "uptime_alert": (
            "Uptime is below {threshold:.0f} minutes. "
            "The server may have restarted recently."
        ),
    },
    "es": {
        "disk_alert": "El uso de disco en {path} supera el {threshold:.1f}% ({value:.1f}%).",
        "ram_alert": "El uso de RAM supera el {threshold:.1f}% ({value:.1f}%).",
        "temperature_alert": "La temperatura CPU supera {threshold:.1f}°C ({value:.1f}°C).",
        "uptime_alert": (
            "El uptime es inferior a {threshold:.0f} minutos. "
            "El servidor puede haberse reiniciado recientemente."
        ),
    },
}
