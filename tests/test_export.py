from unittest.mock import MagicMock

import pytest

from vocab.config import Config
from vocab.exporter import run_export
from vocab.sheets import Row
from vocab.telegram import TelegramError


def cfg(min_new=3, notify=False):
    return Config("words", min_new, "English::Vocabulary", True, "English::Vocabulary (UK → EN)", notify)


def make_sheet(n, exported_first=0):
    sheet = MagicMock()
    sheet.read_rows.return_value = [
        Row(i + 2, f"w{i}", f"п{i}", "", "2026-01-01", "2026-01-01" if i < exported_first else "", "manual")
        for i in range(n)
    ]
    return sheet


def exported_calls(sheet):
    return [c.args for c in sheet.set_column.call_args_list if c.args[0] == "exported_at"]


def test_below_threshold_does_nothing():
    sheet, tg = make_sheet(2), MagicMock()
    assert run_export(sheet, cfg(), tg=tg) == 0
    tg.send_document.assert_not_called()
    tg.send_message.assert_not_called()
    assert exported_calls(sheet) == []


def test_below_threshold_notify():
    tg = MagicMock()
    run_export(make_sheet(2), cfg(notify=True), tg=tg)
    tg.send_message.assert_called_once_with("New words: 2/3")


def test_at_threshold_sends_and_marks():
    sheet, tg = make_sheet(4, exported_first=1), MagicMock()
    assert run_export(sheet, cfg(), tg=tg) == 3
    tg.send_document.assert_called_once()
    assert exported_calls(sheet)[0][1] == [3, 4, 5]


def test_force():
    sheet, tg = make_sheet(1), MagicMock()
    assert run_export(sheet, cfg(), force=True, tg=tg) == 1


def test_telegram_failure_keeps_sheet():
    sheet, tg = make_sheet(5), MagicMock()
    tg.send_document.side_effect = TelegramError("boom")
    with pytest.raises(TelegramError):
        run_export(sheet, cfg(), tg=tg)
    assert exported_calls(sheet) == []


def test_fills_missing_added_at():
    sheet = make_sheet(1)
    sheet.read_rows.return_value[0].added_at = ""
    run_export(sheet, cfg(), tg=MagicMock())
    assert sheet.set_column.call_args_list[0].args[:2] == ("added_at", [2])


def test_all_resends_exported_words():
    sheet, tg = make_sheet(3, exported_first=2), MagicMock()
    assert run_export(sheet, cfg(min_new=10), all_words=True, tg=tg) == 3
    tg.send_document.assert_called_once()
    assert exported_calls(sheet)[0][1] == [4]
