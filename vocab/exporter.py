import logging
import tempfile
from datetime import date
from pathlib import Path

from . import anki, telegram
from .config import Config
from .sheets import Row

log = logging.getLogger(__name__)
PREVIEW = 10


def caption(rows: list[Row]) -> str:
    lines = [f"New words: {len(rows)}", ""]
    lines += [f"• {r.word} — {r.translation}" for r in rows[:PREVIEW]]
    if len(rows) > PREVIEW:
        lines.append(f"… and {len(rows) - PREVIEW} more")
    return "\n".join(lines)


def run_export(sheet, cfg: Config, force: bool = False, all_words: bool = False, tg=telegram) -> int:
    """all_words: re-send every word (e.g. to add UK → EN cards for already exported ones)."""
    rows = sheet.read_rows()
    today = date.today().isoformat()

    missing_added = [r.row_no for r in rows if not r.added_at]
    if missing_added:
        sheet.set_column("added_at", missing_added, today)

    new = [r for r in rows if not r.exported_at and r.word and r.translation]
    selected = [r for r in rows if r.word and r.translation] if all_words else new
    cards_count = len({anki.note_guid(r.word, r.translation) for r in selected})
    log.info("New words: %d (threshold %d)", cards_count, cfg.min_new_words)

    if cards_count == 0 or (cards_count < cfg.min_new_words and not (force or all_words)):
        if cfg.notify_when_not_enough:
            tg.send_message(f"New words: {cards_count}/{cfg.min_new_words}")
        return 0

    cards = [anki.Card(r.word, r.translation, r.example) for r in selected]
    with tempfile.TemporaryDirectory() as tmp:
        path = anki.write_apkg(cards, cfg.deck_name, cfg.reverse_deck_name if cfg.reverse_cards else None, tmp)
        tg.send_document(Path(path), caption(selected))

    sheet.set_column("exported_at", [r.row_no for r in new], today)
    log.info("Exported %d words", cards_count)
    return cards_count
