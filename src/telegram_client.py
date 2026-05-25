from __future__ import annotations

import json
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError


class TelegramDeliveryError(RuntimeError):
    """Raised when a Telegram message cannot be delivered."""


class TelegramClient:
    """Minimal Telegram Bot API client for sending plain-text messages."""

    def __init__(self, token: str, timeout_seconds: float = 10.0) -> None:
        """Create a Telegram client with a bot token and request timeout."""
        if not token.strip():
            raise ValueError("Telegram bot token must not be empty.")
        self._token = token.strip()
        self._timeout_seconds = timeout_seconds

    def send_message(self, chat_id: str, text: str) -> None:
        """Send a plain-text message to the configured Telegram chat."""
        if not chat_id.strip():
            raise TelegramDeliveryError("Telegram chat ID must not be empty.")
        if not text.strip():
            raise TelegramDeliveryError("Telegram message text must not be empty.")

        payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
        request = urllib.request.Request(
            url=f"https://api.telegram.org/bot{self._token}/sendMessage",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            raise TelegramDeliveryError(
                f"Telegram API returned HTTP {exc.code}: {self._compact_response(response_body)}"
            ) from exc
        except URLError as exc:
            raise TelegramDeliveryError(f"Could not reach Telegram API: {exc.reason}") from exc
        except TimeoutError as exc:
            raise TelegramDeliveryError("Telegram request timed out.") from exc

        self._validate_response(response_body)

    def _validate_response(self, response_body: str) -> None:
        """Validate the Telegram API JSON response."""
        try:
            payload = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise TelegramDeliveryError("Telegram API returned an invalid JSON response.") from exc

        if not payload.get("ok"):
            description = str(payload.get("description", "unknown Telegram API error"))
            raise TelegramDeliveryError(f"Telegram API rejected the message: {description}")

    def _compact_response(self, response_body: str) -> str:
        """Return a short response body for error messages."""
        compact = " ".join(response_body.split())
        return compact[:300] if compact else "empty response body"
