import zipfile

from vocab.anki import (DECK_ID, FORWARD_MODEL, REVERSE_DECK_ID, REVERSE_MODEL, Card,
                        build_deck, note_guid, write_apkg)


def test_guid_stable_and_normalized():
    assert note_guid("Apple", "яблуко ") == note_guid("apple", "яблуко")
    assert note_guid("run", "бігти") != note_guid("run", "керувати")
    assert note_guid("apple", "яблуко") != note_guid("apple", "яблуко", reverse=True)


def test_deck_fields_and_dedup():
    deck = build_deck([Card("apple", "яблуко"), Card("Apple", "яблуко"), Card("a<b", "x")], DECK_ID, "D")
    assert [n.fields for n in deck.notes] == [["apple", "яблуко", ""], ["a&lt;b", "x", ""]]
    assert all(n.model is FORWARD_MODEL for n in deck.notes)


def test_reverse_deck_is_separate():
    deck = build_deck([Card("apple", "яблуко")], REVERSE_DECK_ID, "R", reverse=True)
    assert deck.deck_id != DECK_ID
    assert deck.notes[0].model is REVERSE_MODEL
    assert len(FORWARD_MODEL.templates) == len(REVERSE_MODEL.templates) == 1


def test_write_apkg(tmp_path):
    for reverse_name in (None, "English::Vocabulary (UK → EN)"):
        path = write_apkg([Card("apple", "яблуко")], "English::Vocabulary", reverse_name, str(tmp_path))
        assert path.name.startswith("english-") and zipfile.is_zipfile(path)
