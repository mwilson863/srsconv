"""Convert flashcards between Anki's plain text export and sm2json.

sm2json is this project's own format for a personal SM-2 flashcard tool:
one JSON object per line, carrying the scheduling state (interval,
repetitions, easiness factor, due date) that Anki's plain text export
doesn't have room for, since a single Anki note can back several cards
each with their own schedule.

Importing from Anki always produces fresh, unscheduled cards. Exporting
to Anki always drops scheduling state. That's by design, not a bug: the
two formats don't agree on what a "card" is, so round-tripping through
Anki loses schedule data the same way round-tripping through a CSV of
just front/back would.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

DEFAULT_EFACTOR = 2.5


class FormatError(ValueError):
    """Input doesn't match the expected format."""


@dataclass
class Card:
    front: str
    back: str
    tags: tuple = ()
    interval: int = 0
    repetitions: int = 0
    efactor: float = DEFAULT_EFACTOR
    due: "str | None" = None  # ISO 8601 date, None if never scheduled


# ---------------------------------------------------------------------------
# Anki plain text export (Notes menu > Export > Notes in Plain Text)
# ---------------------------------------------------------------------------

def parse_anki_txt(text: str) -> list:
    """Parse Anki's tab-separated notes export into Cards.

    Header lines (starting with '#') are read for '#html:' to decide
    whether '<br>' in a field means a line break. Columns are
    front, back, and an optional space-separated tags column; an empty
    or missing tags column means no tags.
    """
    html_mode = True
    rows = []
    in_header = True
    for line in text.splitlines():
        if in_header and line.startswith("#"):
            if line.startswith("#html:"):
                html_mode = line.split(":", 1)[1].strip().lower() == "true"
            continue
        # Header directives only appear before the first data row, so a
        # card whose front field happens to start with '#' (e.g. a C
        # #include snippet) isn't mistaken for one and dropped.
        in_header = False
        if not line:
            continue
        rows.append(line)

    cards = []
    for line in rows:
        parts = line.split("\t")
        if len(parts) < 2:
            raise FormatError(f"expected front and back columns, got: {line!r}")
        front, back = parts[0], parts[1]
        tags_field = parts[2] if len(parts) > 2 else ""
        if html_mode:
            front = front.replace("<br>", "\n")
            back = back.replace("<br>", "\n")
        tags = tuple(tags_field.split()) if tags_field.strip() else ()
        cards.append(Card(front=front, back=back, tags=tags))
    return cards


def write_anki_txt(cards, html_mode: bool = True) -> str:
    """Render Cards as an Anki plain text notes export, dropping schedule state."""
    lines = ["#separator:tab", f"#html:{'true' if html_mode else 'false'}"]
    for card in cards:
        front, back = card.front, card.back
        if "\t" in front or "\t" in back:
            raise FormatError("Anki plain text export cannot contain literal tabs in a field")
        if html_mode:
            front = front.replace("\n", "<br>")
            back = back.replace("\n", "<br>")
        elif "\n" in front or "\n" in back:
            raise FormatError("multi-line field requires html_mode=True to encode as <br>")
        lines.append("\t".join([front, back, " ".join(card.tags)]))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# sm2json
# ---------------------------------------------------------------------------

def parse_sm2json(text: str) -> list:
    cards = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FormatError(f"line {lineno}: invalid JSON ({exc})") from exc
        try:
            cards.append(Card(
                front=obj["front"],
                back=obj["back"],
                tags=tuple(obj.get("tags", ())),
                interval=obj.get("interval", 0),
                repetitions=obj.get("repetitions", 0),
                efactor=obj.get("efactor", DEFAULT_EFACTOR),
                due=obj.get("due"),
            ))
        except KeyError as exc:
            raise FormatError(f"line {lineno}: missing required field {exc}") from exc
    return cards


def write_sm2json(cards) -> str:
    lines = []
    for card in cards:
        obj = {
            "front": card.front,
            "back": card.back,
            "tags": list(card.tags),
            "interval": card.interval,
            "repetitions": card.repetitions,
            "efactor": card.efactor,
            "due": card.due,
        }
        lines.append(json.dumps(obj, ensure_ascii=False))
    return "\n".join(lines) + ("\n" if lines else "")


# ---------------------------------------------------------------------------
# Cross-format conversion
# ---------------------------------------------------------------------------

def anki_to_sm2json(text: str, today: str) -> str:
    """Import Anki notes as new, unscheduled sm2json cards due today."""
    cards = parse_anki_txt(text)
    for card in cards:
        card.due = today
    return write_sm2json(cards)


def sm2json_to_anki(text: str) -> str:
    """Export sm2json cards as Anki notes, dropping scheduling state."""
    return write_anki_txt(parse_sm2json(text))
