import re
import string
from collections import Counter

_EDGE_PUNCT = string.punctuation + "«»“”„…"


def normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text.strip(_EDGE_PUNCT + " ")


def pair_key(word: str, translation: str) -> tuple[str, str]:
    """Pair key: the same word with different translations gives different cards."""
    return normalize(word), normalize(translation)


def new_pairs(candidates: list, existing: list[tuple[str, str]]) -> tuple[list, int]:
    """Return candidates not yet in the sheet, plus the number skipped.

    Duplicates within the document are kept; occurrences are counted,
    so re-importing the same document adds nothing.
    """
    remaining = Counter(pair_key(w, t) for w, t in existing)
    fresh, skipped = [], 0
    for item in candidates:
        key = pair_key(item.word, item.translation)
        if remaining[key] > 0:
            remaining[key] -= 1
            skipped += 1
        else:
            fresh.append(item)
    return fresh, skipped
