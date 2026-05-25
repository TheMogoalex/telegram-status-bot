from __future__ import annotations

import pytest

from src.config import ConfigError, load_config

BASE_ENV = {
    "SERVER_NAME": "test-server",
    "TELEGRAM_BOT_TOKEN": "fake-token",
    "TELEGRAM_CHAT_ID": "123456",
}


def test_missing_required_variable_fails_clearly() -> None:
    """Configuration loading must fail clearly when a required value is missing."""
    env = dict(BASE_ENV)
    del env["SERVER_NAME"]

    with pytest.raises(ConfigError, match="SERVER_NAME"):
        load_config(env=env)


def test_invalid_numeric_value_fails_clearly() -> None:
    """Configuration loading must reject invalid numeric thresholds."""
    env = {**BASE_ENV, "RAM_USAGE_ALERT_PERCENT": "not-a-number"}

    with pytest.raises(ConfigError, match="RAM_USAGE_ALERT_PERCENT"):
        load_config(env=env)


def test_dry_run_config_does_not_require_telegram_credentials() -> None:
    """Dry-run configuration must work without real Telegram credentials."""
    config = load_config(require_telegram=False, env={"SERVER_NAME": "test-server"})

    assert config.telegram_bot_token == ""
    assert config.telegram_chat_id == ""
    assert config.disk_partitions == ("/",)
