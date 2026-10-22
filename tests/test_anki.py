from vocab.anki import Card, build_deck, note_guid, write_apkg


def test_guid_stable_and_normalized():
    assert note_guid("Apple", "яблуко ") == note_guid("apple", "яблуко")
    assert note_guid("run", "бігти") != note_guid("run", "керувати")


def test_deck_fields_and_dedup():
    deck = build_deck([Card("apple", "яблуко"), Card("Apple", "яблуко"), Card("a<b", "x")], "D", False)
    assert [n.fields for n in deck.notes] == [["apple", "яблуко", ""], ["a&lt;b", "x", ""]]
    assert len(deck.notes[0].model.templates) == 1


def test_reverse_cards():
    deck = build_deck([Card("apple", "яблуко")], "D", True)
    assert len(deck.notes[0].model.templates) == 2


def test_write_apkg(tmp_path):
    path = write_apkg([Card("apple", "яблуко")], "English::Vocabulary", False, str(tmp_path))
    assert path.exists() and path.name.startswith("english-")
