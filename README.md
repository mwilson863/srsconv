# srsconv

I keep most of my flashcards in Anki but prototype scheduling changes in a
much smaller personal tool that implements the SM-2 algorithm directly.
Moving cards between the two meant hand-editing files, so this converts
between:

- **Anki plain text export** — the file you get from
  `Notes > Export > Notes in Plain Text`: front, back, and an optional
  space-separated tags column, separated by whatever character you
  picked in the export dialog (tab, comma, semicolon, pipe, colon, or
  space).
- **sm2json** — this project's own format, one JSON object per line,
  that also carries SM-2 scheduling state: interval, repetitions,
  easiness factor, and due date.

Anki notes don't carry SM-2 state (a note can back several cards, each
scheduled independently), so the conversion is intentionally one-way on
scheduling: importing from Anki always produces fresh, unscheduled
cards; exporting to Anki always drops scheduling and writes plain
front/back/tags. Round-tripping a deck through Anki will not preserve
review history, by design.

## Usage

```console
$ cat cards.txt
#separator:tab
#html:true
What is the capital of France?	Paris	geography::europe
Define "isogram"	A word with no repeating letters	vocabulary

$ python -m srsconv.cli anki2json cards.txt
{"front": "What is the capital of France?", "back": "Paris", "tags": ["geography::europe"], "interval": 0, "repetitions": 0, "efactor": 2.5, "due": "2026-08-26"}
{"front": "Define \"isogram\"", "back": "A word with no repeating letters", "tags": ["vocabulary"], "interval": 0, "repetitions": 0, "efactor": 2.5, "due": "2026-08-26"}
```

Going the other way, scheduling fields in the input are simply dropped:

```console
$ python -m srsconv.cli json2anki cards.jsonl -o deck.txt
```

`anki2json` reads the separator from the input file's own `#separator:`
header line, so tab and comma exports both import without any extra
flags. `json2anki` writes tab-separated by default; pass `--separator`
(`comma`, `semicolon`, `pipe`, `colon`, or `space`) to write one of the
others instead:

```console
$ python -m srsconv.cli json2anki cards.jsonl --separator comma -o deck.csv
```

Both subcommands accept `-` for stdin/stdout, so they compose with a shell
pipeline as well as with files.

Pass `--dry-run` to either subcommand to validate the input without writing
anything; it reports the number of valid cards (or the same `FormatError`
you'd get otherwise) and exits accordingly, ignoring `-o`/`--outfile`:

```console
$ python -m srsconv.cli anki2json cards.txt --dry-run
srsconv: 2 card(s) valid, no errors
```

## SM-2 grading

The personal flashcard tool this converter feeds does its own scheduling
with `srsconv.grade_card`, a plain SM-2 implementation:

```python
from srsconv import grade_card

card = grade_card(card, quality=4)  # quality: 0 (blackout) to 5 (perfect)
```

It returns an updated copy of the card (interval, repetitions, easiness
factor, and due date all recomputed) rather than mutating the one passed
in. A quality below 3 is a lapse: repetitions resets to 0 and the card
comes back due tomorrow, no matter how long its interval had grown.
There's no CLI command for this yet - it's called directly from the
personal app's review loop, not part of the anki2json/json2anki pipeline.

## Format notes

- Fields in a tab-separated Anki file can't contain literal tab
  characters (that's the column separator); the converter raises
  `FormatError` rather than writing a file Anki won't read back
  correctly. Non-tab separators (comma, semicolon, pipe, colon, space)
  don't have this restriction: a field containing the separator, or a
  literal `"`, is quoted the way Anki itself quotes it (wrapped in `"`,
  with `"` doubled inside).
- With `#html:true` (Anki's default), a literal `<br>` in a field is
  read back as a newline, and newlines are written out the same way.
- `#` lines are only read as header directives before the first data
  row; a card whose front field happens to start with `#` (a code
  snippet, a hashtag) is parsed as a normal card, not swallowed.
- Checking "Include tags/deck/notetype/guid" in Anki's export dialog
  adds a `#<role> column:<n>` header line and its own column for each
  one, shifting every field after it over. The importer locates those
  columns by their headers rather than assuming front/back are always
  columns 1 and 2; guid, notetype, and deck values are read past and
  discarded, since this project's Card has no fields for them.
- `sm2json`'s `due` is `null` for a card that has never been scheduled.

## Development

No third-party dependencies — everything here is the Python standard
library. Tests are plain `unittest`:

```console
$ python -m unittest discover -s tests
```

## License

MIT, see `LICENSE`.
