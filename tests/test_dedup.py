from vocab.dedup import new_pairs, normalize
from vocab.parser import Entry


def e(w, t):
    return Entry(w, t, 0)


def test_normalize():
    assert normalize("  Whisk  ") == "whisk"
    assert normalize("To  Look,") == "to look"


def test_duplicates_in_doc_kept():
    fresh, skipped = new_pairs([e("run", "бігти"), e("run", "керувати"), e("run", "бігти")], [])
    assert len(fresh) == 3 and skipped == 0


def test_existing_rows_skipped_and_reimport_adds_nothing():
    doc = [e("Apple", "яблуко"), e("pear", "груша"), e("apple", "яблуко")]
    fresh, skipped = new_pairs(doc, [("apple", "Яблуко")])
    assert [(x.word, x.translation) for x in fresh] == [("pear", "груша"), ("apple", "яблуко")]
    assert skipped == 1
    existing = [("apple", "Яблуко")] + [(x.word, x.translation) for x in fresh]
    assert new_pairs(doc, existing) == ([], 3)
