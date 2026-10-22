import pytest

from vocab.parser import parse_line, parse_text


@pytest.mark.parametrize("line", [
    "apple - яблуко", "apple — яблуко", "apple – яблуко", "apple: яблуко",
    "apple\tяблуко", "apple -яблуко", "apple-  яблуко", "apple -  яблуко ",
])
def test_separators(line):
    assert parse_line(line) == ("apple", "яблуко")


def test_first_separator_wins_and_hyphenated_words():
    assert parse_line("well-known - добре відомий - факт") == ("well-known", "добре відомий - факт")


def test_parentheses_stay_in_translation():
    assert parse_line("cuisine - кухня(набір страв)") == ("cuisine", "кухня(набір страв)")


def test_phrase_keeps_to():
    assert parse_line("to look forward to - чекати") == ("to look forward to", "чекати")


def test_unparsed_and_empty_reported():
    r = parse_text("apple - яблуко\n\nspare time вільний час\nword -\n")
    assert [(e.word, e.line_no) for e in r.entries] == [("apple", 1)]
    assert r.unparsed == [(3, "spare time вільний час"), (4, "word -")]
    assert r.empty_lines == 1
