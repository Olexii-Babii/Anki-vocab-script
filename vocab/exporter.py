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


def run_export(sheet, cfg: Config, force: bool = False, tg=telegram) -> int:
    rows = sheet.read_rows()
    today = date.today().isoformat()

    missing_added = [r.row_no for r in rows if not r.added_at]
    if missing_added:
        sheet.set_column("added_at", missing_added, today)

    new = [r for r in rows if not r.exported_at and r.word and r.translation]
    cards_count = len({anki.note_guid(r.word, r.translation) for r in new})
    log.info("New words: %d (threshold %d)", cards_count, cfg.min_new_words)

    if cards_count == 0 or (cards_count < cfg.min_new_words and not force):
        if cfg.notify_when_not_enough:
            tg.send_message(f"New words: {cards_count}/{cfg.min_new_words}")
        return 0

    cards = [anki.Card(r.word, r.translation, r.example) for r in new]
    with tempfile.TemporaryDirectory() as tmp:
        path = anki.write_apkg(cards, cfg.deck_name, cfg.reverse_cards, tmp)
        tg.send_document(Path(path), caption(new))

    sheet.set_column("exported_at", [r.row_no for r in new], today)
    log.info("Exported %d words", cards_count)
    return cards_count
