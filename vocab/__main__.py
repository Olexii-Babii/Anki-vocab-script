import argparse
import logging
import sys
from datetime import date

from . import config, doc_source
from .config import ConfigError, require
from .dedup import new_pairs
from .parser import parse_text
from .telegram import TelegramError

log = logging.getLogger("vocab")


def cmd_import(args, cfg: config.Config) -> None:
    from . import sheets

    if args.file:
        text = doc_source.read_local(args.file)
    else:
        text = doc_source.read_google_doc(sheets.credentials(), require("GOOGLE_DOC_ID"))
    result = parse_text(text)

    sheet = None if args.dry_run else sheets.open_sheet(cfg.sheet_tab)
    existing = [(r.word, r.translation) for r in sheet.read_rows()] if sheet else []
    fresh, skipped = new_pairs(result.entries, existing)

    print(f"Parsed pairs: {len(result.entries)}")
    print(f"Empty lines: {result.empty_lines}")
    print(f"Already in sheet (skipped): {skipped}" if sheet else "Sheet comparison: skipped (--dry-run)")
    print(f"To add: {len(fresh)}")
    if result.unparsed:
        print(f"\nUnparsed ({len(result.unparsed)}):")
        for line_no, line in result.unparsed:
            print(f"  line {line_no}: {line}")

    if args.dry_run:
        print("\n--dry-run: nothing written to the sheet")
        return
    today = date.today().isoformat()
    exported = today if args.mark_exported else ""
    sheet.append_rows([[e.word, e.translation, "", today, exported, "doc-import"] for e in fresh])
    print(f"\nAdded to sheet: {len(fresh)}")

    if args.export_now:
        cmd_export(argparse.Namespace(force=True), cfg)


def cmd_export(args, cfg: config.Config) -> None:
    from . import sheets
    from .exporter import run_export

    run_export(sheets.open_sheet(cfg.sheet_tab), cfg, force=args.force)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="python -m vocab")
    sub = parser.add_subparsers(dest="command", required=True)

    imp = sub.add_parser("import-doc", help="one-time import of words from a Google Doc / file into the sheet")
    imp.add_argument("--file", help="local .docx or .txt instead of the Google Doc")
    imp.add_argument("--dry-run", action="store_true", help="only show the report")
    imp.add_argument("--mark-exported", action="store_true", help="mark imported words as already exported")
    imp.add_argument("--export-now", action="store_true", help="run export right after import")

    exp = sub.add_parser("export", help="build a deck from new words and send it to Telegram")
    exp.add_argument("--force", action="store_true", help="export even below the threshold")

    args = parser.parse_args(argv)
    try:
        cfg = config.load()
        {"import-doc": cmd_import, "export": cmd_export}[args.command](args, cfg)
    except ConfigError as e:
        log.error("%s", e)
        return 2
    except TelegramError as e:
        log.error("%s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
