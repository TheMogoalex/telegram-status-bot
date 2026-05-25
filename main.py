from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.app import build_status_report, send_status_report
from src.config import ConfigError, load_config
from src.telegram_client import TelegramDeliveryError

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the status bot."""
    parser = argparse.ArgumentParser(description="Send a Linux status report to Telegram.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the report to stdout without sending anything to Telegram",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="optional path to an env file; defaults to .env when present",
    )
    return parser.parse_args()


def configure_logging() -> None:
    """Configure concise CLI logging."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> int:
    """Run the status bot CLI."""
    args = parse_args()
    configure_logging()

    try:
        config = load_config(require_telegram=not args.dry_run, env_file=args.env_file)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    try:
        if args.dry_run:
            print(build_status_report(config))
            return 0

        send_status_report(config)
    except TelegramDeliveryError as exc:
        print(f"Telegram delivery error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"System error: {exc}", file=sys.stderr)
        return 1

    LOGGER.info("Status report sent to Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
