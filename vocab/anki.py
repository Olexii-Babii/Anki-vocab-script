import html
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import genanki

from .dedup import pair_key

# Generated once — do not change, otherwise Anki will treat it as a new deck/note type.
MODEL_ID = 1749764942
DECK_ID = 1638792007

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


def build_model(reverse: bool) -> genanki.Model:
    templates = [{
        "name": "EN → UK",
        "qfmt": "<div class=word>{{Word}}</div>" + EXAMPLE,
        "afmt": "{{FrontSide}}<hr id=answer><div class=word>{{Translation}}</div>",
    }]
    if reverse:
        templates.append({
            "name": "UK → EN",
            "qfmt": "<div class=word>{{Translation}}</div>",
            "afmt": "{{FrontSide}}<hr id=answer><div class=word>{{Word}}</div>" + EXAMPLE,
        })
    return genanki.Model(
        MODEL_ID, "English Vocabulary",
        fields=[{"name": "Word"}, {"name": "Translation"}, {"name": "Example"}],
        templates=templates, css=CSS,
    )


@dataclass
class Card:
    word: str
    translation: str
    example: str = ""


def note_guid(word: str, translation: str) -> str:
    return genanki.guid_for(*pair_key(word, translation))


def build_deck(cards: list[Card], deck_name: str, reverse: bool) -> genanki.Deck:
    model = build_model(reverse)
    deck = genanki.Deck(DECK_ID, deck_name)
    seen: set[str] = set()
    for c in cards:
        guid = note_guid(c.word, c.translation)
        if guid in seen:
            continue
        seen.add(guid)
        fields = [html.escape(c.word), html.escape(c.translation), html.escape(c.example)]
        deck.add_note(genanki.Note(model=model, fields=fields, guid=guid))
    return deck


def write_apkg(cards: list[Card], deck_name: str, reverse: bool, out_dir: str = ".") -> Path:
    path = Path(out_dir) / f"english-{date.today().isoformat()}.apkg"
    genanki.Package(build_deck(cards, deck_name, reverse)).write_to_file(str(path))
    return path
