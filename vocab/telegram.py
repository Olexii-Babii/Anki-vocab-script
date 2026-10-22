import logging
from pathlib import Path

import requests

from .config import require

log = logging.getLogger(__name__)
API = "https://api.telegram.org/bot{token}/{method}"


class TelegramError(Exception):
    pass


def _call(method: str, data: dict, files: dict | None = None) -> None:
    url = API.format(token=require("TELEGRAM_BOT_TOKEN"), method=method)
    data = {"chat_id": require("TELEGRAM_CHAT_ID"), **data}
    try:
        resp = requests.post(url, data=data, files=files, timeout=60)
    except requests.RequestException as e:
        raise TelegramError(f"Telegram is unreachable: {e}") from e
    if resp.status_code != 200:
        log.error("Telegram %s → %s: %s", method, resp.status_code, resp.text)
        raise TelegramError(f"Telegram {method} returned {resp.status_code}")


def send_message(text: str) -> None:
    _call("sendMessage", {"text": text})


def send_document(path: Path, caption: str) -> None:
    with open(path, "rb") as f:
        _call("sendDocument", {"caption": caption[:1024]}, files={"document": (path.name, f, "application/apkg")})
