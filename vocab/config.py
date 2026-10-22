import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigError(Exception):
    pass


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Environment variable {name} is not set (see .env.example)")
    return value


@dataclass
class Config:
    sheet_tab: str
    min_new_words: int
    deck_name: str
    reverse_cards: bool
    notify_when_not_enough: bool


def load() -> Config:
    load_dotenv()
    try:
        min_new = int(os.getenv("MIN_NEW_WORDS") or 10)
    except ValueError:
        raise ConfigError("MIN_NEW_WORDS must be an integer")
    return Config(
        sheet_tab=os.getenv("GOOGLE_SHEET_TAB") or "words",
        min_new_words=min_new,
        deck_name=os.getenv("ANKI_DECK_NAME") or "English::Vocabulary",
        reverse_cards=_bool("ANKI_REVERSE_CARDS", False),
        notify_when_not_enough=_bool("NOTIFY_WHEN_NOT_ENOUGH", False),
    )
