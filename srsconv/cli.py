from __future__ import annotations

import argparse
import datetime
import sys

from srsconv import (
    SEPARATORS,
    FormatError,
    parse_anki_txt,
    parse_sm2json,
    write_anki_txt,
    write_sm2json,
)


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write(path: str, text: str) -> None:
    if path == "-":
        sys.stdout.write(text)
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="srsconv",
        description="Convert flashcards between Anki plain text export and sm2json.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    anki2json = sub.add_parser("anki2json", help="Anki notes export -> sm2json")
    anki2json.add_argument("infile", help="Anki plain text export, or '-' for stdin")
    anki2json.add_argument("-o", "--outfile", default="-", help="output path, or '-' for stdout")
    anki2json.add_argument(
        "--today",
        default=None,
        help="due date (YYYY-MM-DD) to stamp on imported cards; defaults to today",
    )
    anki2json.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the input and report errors without writing output",
    )

    json2anki = sub.add_parser("json2anki", help="sm2json -> Anki notes export")
    json2anki.add_argument("infile", help="sm2json file, or '-' for stdin")
    json2anki.add_argument("-o", "--outfile", default="-", help="output path, or '-' for stdout")
    json2anki.add_argument(
        "--separator",
        default="tab",
        choices=sorted(SEPARATORS),
        help="column separator for the Anki export (default: tab)",
    )
    json2anki.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the input and report errors without writing output",
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "anki2json":
            cards = parse_anki_txt(_read(args.infile))
            if args.dry_run:
                print(f"srsconv: {len(cards)} card(s) valid, no errors", file=sys.stderr)
            else:
                today = args.today or datetime.date.today().isoformat()
                for card in cards:
                    card.due = today
                _write(args.outfile, write_sm2json(cards))
        elif args.command == "json2anki":
            cards = parse_sm2json(_read(args.infile))
            if args.dry_run:
                print(f"srsconv: {len(cards)} card(s) valid, no errors", file=sys.stderr)
            else:
                _write(args.outfile, write_anki_txt(cards, separator=args.separator))
    except FormatError as exc:
        print(f"srsconv: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
