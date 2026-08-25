from __future__ import annotations

import argparse
import datetime
import sys

from srsconv import FormatError, anki_to_sm2json, sm2json_to_anki


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

    json2anki = sub.add_parser("json2anki", help="sm2json -> Anki notes export")
    json2anki.add_argument("infile", help="sm2json file, or '-' for stdin")
    json2anki.add_argument("-o", "--outfile", default="-", help="output path, or '-' for stdout")

    args = parser.parse_args(argv)

    try:
        if args.command == "anki2json":
            today = args.today or datetime.date.today().isoformat()
            _write(args.outfile, anki_to_sm2json(_read(args.infile), today))
        elif args.command == "json2anki":
            _write(args.outfile, sm2json_to_anki(_read(args.infile)))
    except FormatError as exc:
        print(f"srsconv: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
