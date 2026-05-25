from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class DiskUsage:
    """Disk usage details for one configured partition."""

    mount_path: str
    resolved_path: Path
    total_bytes: int | None = None
    used_bytes: int | None = None
    free_bytes: int | None = None
    used_percent: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class SystemMetrics:
    """Collected system metrics ready for formatting."""

    server_name: str
    collected_at: datetime
    uptime_seconds: float | None
    uptime_error: str | None
    cpu_temperature_celsius: float | None
    cpu_temperature_error: str | None
    ram_used_percent: float | None
    ram_error: str | None
    disks: tuple[DiskUsage, ...]


class SystemInfoCollector:
    """Collects Linux system metrics from configurable filesystem paths."""

    def __init__(
        self,
        partitions: Iterable[str],
        host_root: Path = Path("/"),
        host_proc: Path = Path("/proc"),
        host_sys: Path = Path("/sys"),
        cpu_temperature_path: Path | None = None,
    ) -> None:
        """Create a collector for local or Docker-mounted host paths."""
        self._partitions = tuple(partitions)
        self._host_root = host_root
        self._host_proc = host_proc
        self._host_sys = host_sys
        self._cpu_temperature_path = cpu_temperature_path

    def collect(self, server_name: str) -> SystemMetrics:
        """Collect all supported metrics without raising on partial failures."""
        uptime_seconds, uptime_error = self._read_uptime_seconds()
        cpu_temp, cpu_temp_error = self._read_cpu_temperature()
        ram_used, ram_error = self._read_ram_used_percent()
        disks = tuple(self._read_disk_usage(partition) for partition in self._partitions)

        return SystemMetrics(
            server_name=server_name,
            collected_at=datetime.now().astimezone(),
            uptime_seconds=uptime_seconds,
            uptime_error=uptime_error,
            cpu_temperature_celsius=cpu_temp,
            cpu_temperature_error=cpu_temp_error,
            ram_used_percent=ram_used,
            ram_error=ram_error,
            disks=disks,
        )

    def _read_uptime_seconds(self) -> tuple[float | None, str | None]:
        """Read uptime seconds from the configured proc filesystem."""
        uptime_path = self._host_proc / "uptime"
        try:
            raw_value = uptime_path.read_text(encoding="utf-8").split()[0]
            uptime_seconds = float(raw_value)
        except (OSError, IndexError, ValueError) as exc:
            return None, self._format_error(exc)
        return uptime_seconds, None

    def _read_cpu_temperature(self) -> tuple[float | None, str | None]:
        """Read CPU temperature from an explicit path or thermal zone files."""
        if self._cpu_temperature_path is not None:
            return self._read_temperature_file(self._cpu_temperature_path)

        candidates = tuple(self._temperature_candidates())
        if not candidates:
            return None, "no readable thermal sensor found"

        last_error = "no readable thermal sensor found"
        for path in candidates:
            temperature, error = self._read_temperature_file(path)
            if temperature is not None:
                return temperature, None
            if error:
                last_error = error
        return None, last_error

    def _temperature_candidates(self) -> Iterable[Path]:
        """Yield likely Linux thermal sensor files under the configured sys path."""
        thermal_root = self._host_sys / "class" / "thermal"
        try:
            zones = sorted(thermal_root.glob("thermal_zone*/temp"))
        except OSError:
            return ()
        return zones

    def _read_temperature_file(self, path: Path) -> tuple[float | None, str | None]:
        """Read one Linux temperature file and return Celsius."""
        try:
            raw_value = path.read_text(encoding="utf-8").strip()
            temperature = float(raw_value)
        except (OSError, ValueError) as exc:
            return None, self._format_error(exc)

        if abs(temperature) > 1000:
            temperature = temperature / 1000.0
        return temperature, None

    def _read_ram_used_percent(self) -> tuple[float | None, str | None]:
        """Read RAM usage percent from the configured proc filesystem."""
        meminfo_path = self._host_proc / "meminfo"
        try:
            meminfo = self._parse_meminfo(meminfo_path.read_text(encoding="utf-8"))
            total_kib = meminfo["MemTotal"]
            available_kib = meminfo.get("MemAvailable", meminfo.get("MemFree"))
            if available_kib is None:
                return None, "MemAvailable and MemFree are missing from meminfo"
            if total_kib <= 0:
                return None, "MemTotal must be greater than zero"
        except (KeyError, OSError, ValueError) as exc:
            return None, self._format_error(exc)

        used_kib = max(total_kib - available_kib, 0)
        return (used_kib / total_kib) * 100.0, None

    def _parse_meminfo(self, content: str) -> dict[str, int]:
        """Parse Linux meminfo content into KiB values."""
        values: dict[str, int] = {}
        for line in content.splitlines():
            if ":" not in line:
                continue
            key, raw_value = line.split(":", 1)
            parts = raw_value.strip().split()
            if not parts:
                continue
            values[key] = int(parts[0])
        return values

    def _read_disk_usage(self, partition: str) -> DiskUsage:
        """Read disk usage for one configured partition."""
        resolved_path = self._resolve_partition_path(partition)
        try:
            stats = os.statvfs(resolved_path)
            total_bytes = stats.f_frsize * stats.f_blocks
            free_bytes = stats.f_frsize * stats.f_bavail
            if total_bytes <= 0:
                return DiskUsage(
                    mount_path=partition,
                    resolved_path=resolved_path,
                    error="filesystem size is zero",
                )
            used_bytes = max(total_bytes - free_bytes, 0)
            used_percent = (used_bytes / total_bytes) * 100.0
        except OSError as exc:
            return DiskUsage(
                mount_path=partition,
                resolved_path=resolved_path,
                error=f"{self._format_error(exc)} at {resolved_path}",
            )

        return DiskUsage(
            mount_path=partition,
            resolved_path=resolved_path,
            total_bytes=total_bytes,
            used_bytes=used_bytes,
            free_bytes=free_bytes,
            used_percent=used_percent,
        )

    def _resolve_partition_path(self, partition: str) -> Path:
        """Resolve a displayed host partition to the readable runtime path."""
        if self._host_root == Path("/"):
            return Path(partition)
        if partition == "/":
            return self._host_root
        return self._host_root / partition.lstrip("/")

    def _format_error(self, exc: BaseException) -> str:
        """Return a compact human-readable error message."""
        return str(exc) or exc.__class__.__name__
