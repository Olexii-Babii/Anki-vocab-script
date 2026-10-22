import html
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import genanki

from .dedup import pair_key

# Generated once — do not change, otherwise Anki will treat it as a new deck/note type.
MODEL_ID = 1749764942
DECK_ID = 1638792007
REVERSE_MODEL_ID = 1771045556
REVERSE_DECK_ID = 1214390802

CSS = """
.card {
  font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  font-size: 24px;
  text-align: center;
  color: #222;
  background: #fafafa;
  padding: 20px 12px;
  line-height: 1.4;
}
.nightMode .card, .night_mode .card { color: #eee; background: #1e1e1e; }
.word { font-size: 30px; font-weight: 600; }
.example { margin-top: 14px; font-size: 18px; font-style: italic; color: #777; }
hr#answer { margin: 18px 0; border: 0; border-top: 1px solid #ccc; }
"""

EXAMPLE = "{{#Example}}<div class=example>{{Example}}</div>{{/Example}}"
FIELDS = [{"name": "Word"}, {"name": "Translation"}, {"name": "Example"}]

# EN → UK and UK → EN are separate note types so their cards can live in separate decks.
FORWARD_MODEL = genanki.Model(
    MODEL_ID, "English Vocabulary", fields=FIELDS, css=CSS,
    templates=[{
        "name": "EN → UK",
        "qfmt": "<div class=word>{{Word}}</div>" + EXAMPLE,
        "afmt": "{{FrontSide}}<hr id=answer><div class=word>{{Translation}}</div>",
    }],
)
REVERSE_MODEL = genanki.Model(
    REVERSE_MODEL_ID, "English Vocabulary (UK → EN)", fields=FIELDS, css=CSS,
    templates=[{
        "name": "UK → EN",
        "qfmt": "<div class=word>{{Translation}}</div>",
        "afmt": "{{FrontSide}}<hr id=answer><div class=word>{{Word}}</div>" + EXAMPLE,
    }],
)


@dataclass
class Card:
    word: str
    translation: str
    example: str = ""


def note_guid(word: str, translation: str, reverse: bool = False) -> str:
    key = pair_key(word, translation)
    return genanki.guid_for(*key, "reverse") if reverse else genanki.guid_for(*key)


def build_deck(cards: list[Card], deck_id: int, deck_name: str, reverse: bool = False) -> genanki.Deck:
    model = REVERSE_MODEL if reverse else FORWARD_MODEL
    deck = genanki.Deck(deck_id, deck_name)
    seen: set[str] = set()
    for c in cards:
        guid = note_guid(c.word, c.translation, reverse)
        if guid in seen:
            continue
        seen.add(guid)
        fields = [html.escape(c.word), html.escape(c.translation), html.escape(c.example)]
        deck.add_note(genanki.Note(model=model, fields=fields, guid=guid))
    return deck


def write_apkg(cards: list[Card], deck_name: str, reverse_deck_name: str | None, out_dir: str = ".") -> Path:
    """One file with the EN → UK deck and, if reverse_deck_name is set, the UK → EN deck."""
    decks = [build_deck(cards, DECK_ID, deck_name)]
    if reverse_deck_name:
        decks.append(build_deck(cards, REVERSE_DECK_ID, reverse_deck_name, reverse=True))
    path = Path(out_dir) / f"english-{date.today().isoformat()}.apkg"
    genanki.Package(decks).write_to_file(str(path))
    return path
