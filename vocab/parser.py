import re
from dataclasses import dataclass, field


SEPARATOR = re.compile(r"\s+[-–—]\s*|\s*[-–—]\s+|\t|:")


@dataclass
class Entry:
    word: str
    translation: str
    line_no: int


@dataclass
class ParseResult:
    entries: list[Entry] = field(default_factory=list)
    unparsed: list[tuple[int, str]] = field(default_factory=list)  # (line number, text)
    empty_lines: int = 0


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_line(line: str) -> tuple[str, str] | None:
    match = SEPARATOR.search(line)
    if not match:
        return None
    word = _clean(line[: match.start()])
    translation = _clean(line[match.end():])
    if not word or not translation:
        return None
    return word, translation


def parse_text(text: str) -> ParseResult:
    result = ParseResult()
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip().lstrip("﻿")
        if not line:
            result.empty_lines += 1
            continue
        parsed = parse_line(line)
        if parsed is None:
            result.unparsed.append((line_no, line))
        else:
            result.entries.append(Entry(parsed[0], parsed[1], line_no))
    return result
