import unittest

from srsconv import (
    Card,
    FormatError,
    parse_anki_txt,
    parse_sm2json,
    write_anki_txt,
    write_sm2json,
)

ANKI_HEADER = "#separator:tab\n#html:true\n"

# Each case: (name, anki_txt_body, expected_cards)
ANKI_PARSE_CASES = [
    (
        "plain_two_column",
        "What is 2+2?\t4\n",
        [Card(front="What is 2+2?", back="4")],
    ),
    (
        "empty_tags_column",
        "Capital of France?\tParis\t\n",
        [Card(front="Capital of France?", back="Paris")],
    ),
    (
        "missing_tags_column",
        "Capital of France?\tParis\n",
        [Card(front="Capital of France?", back="Paris")],
    ),
    (
        "hierarchical_and_multiple_tags",
        "Term\tDefinition\tgeography::europe capitals\n",
        [Card(front="Term", back="Definition", tags=("geography::europe", "capitals"))],
    ),
    (
        "multiline_field_via_br",
        "Line one<br>Line two\tanswer\n",
        [Card(front="Line one\nLine two", back="answer")],
    ),
    (
        "html_entities_pass_through",
        "A &amp; B\tC &lt; D\n",
        [Card(front="A &amp; B", back="C &lt; D")],
    ),
    (
        "hash_in_field_after_data_started",
        "Plain card\tanswer\n#include <stdio.h>\tC standard I/O header\n",
        [
            Card(front="Plain card", back="answer"),
            Card(front="#include <stdio.h>", back="C standard I/O header"),
        ],
    ),
    (
        "whitespace_only_tags_column",
        "Capital of Spain?\tMadrid\t   \n",
        [Card(front="Capital of Spain?", back="Madrid")],
    ),
    (
        "extra_trailing_column_is_ignored",
        "Term\tDefinition\ttagone\tnote-guid-1234\n",
        [Card(front="Term", back="Definition", tags=("tagone",))],
    ),
    (
        "crlf_line_endings",
        "Q1\tA1\r\nQ2\tA2\r\n",
        [Card(front="Q1", back="A1"), Card(front="Q2", back="A2")],
    ),
]


class TestAnkiTxt(unittest.TestCase):
    def test_parse_cases(self):
        for name, body, expected in ANKI_PARSE_CASES:
            with self.subTest(name=name):
                self.assertEqual(parse_anki_txt(ANKI_HEADER + body), expected)

    def test_parse_ignores_blank_lines_and_header_only_file(self):
        self.assertEqual(parse_anki_txt(ANKI_HEADER + "\n\n"), [])

    def test_parse_rejects_missing_back_column(self):
        with self.assertRaises(FormatError):
            parse_anki_txt(ANKI_HEADER + "front only\n")

    def test_write_rejects_literal_tab_in_field(self):
        with self.assertRaises(FormatError):
            write_anki_txt([Card(front="a\tb", back="c")])

    def test_write_html_false_rejects_embedded_newline(self):
        with self.assertRaises(FormatError):
            write_anki_txt([Card(front="a\nb", back="c")], html_mode=False)

    def test_round_trip_preserves_front_back_tags(self):
        cards = [Card(front="Q1\nmore", back="A1", tags=("x", "y::z"))]
        self.assertEqual(parse_anki_txt(write_anki_txt(cards)), cards)

    def test_parse_rejects_unknown_separator(self):
        with self.assertRaises(FormatError):
            parse_anki_txt("#separator:tilde\n#html:true\nQ~A\n")

    def test_write_rejects_unknown_separator(self):
        with self.assertRaises(FormatError):
            write_anki_txt([Card(front="Q", back="A")], separator="tilde")


# Each case: (name, anki_txt_body, expected_cards)
ANKI_COMMA_PARSE_CASES = [
    (
        "plain_fields",
        "What is 2+2?,4\n",
        [Card(front="What is 2+2?", back="4")],
    ),
    (
        "quoted_field_containing_separator",
        '"Cost, in dollars?",5,money\n',
        [Card(front="Cost, in dollars?", back="5", tags=("money",))],
    ),
    (
        "doubled_quote_escapes_literal_quote",
        '"She said ""hi""",greeting\n',
        [Card(front='She said "hi"', back="greeting")],
    ),
]


class TestAnkiTxtCommaSeparator(unittest.TestCase):
    def test_parse_cases(self):
        header = "#separator:comma\n#html:true\n"
        for name, body, expected in ANKI_COMMA_PARSE_CASES:
            with self.subTest(name=name):
                self.assertEqual(parse_anki_txt(header + body), expected)

    def test_write_quotes_field_containing_separator(self):
        cards = [Card(front="Cost, in dollars?", back="5", tags=("money",))]
        text = write_anki_txt(cards, separator="comma")
        self.assertIn('#separator:comma', text.splitlines())
        self.assertIn('"Cost, in dollars?",5,money', text)

    def test_round_trip_through_comma_separator(self):
        cards = [
            Card(front="Q, with comma", back='A "quoted"', tags=("tag,one", "tag two")),
            Card(front="Plain", back="Simple"),
        ]
        self.assertEqual(
            parse_anki_txt(write_anki_txt(cards, separator="comma")), cards
        )


# Each case: (name, sm2json_line, expected_card)
SM2JSON_PARSE_CASES = [
    (
        "full_record",
        '{"front": "Q", "back": "A", "tags": ["x"], "interval": 6, '
        '"repetitions": 2, "efactor": 2.36, "due": "2026-09-01"}',
        Card(front="Q", back="A", tags=("x",), interval=6, repetitions=2,
             efactor=2.36, due="2026-09-01"),
    ),
    (
        "defaults_for_new_card",
        '{"front": "Q", "back": "A"}',
        Card(front="Q", back="A"),
    ),
    (
        "null_due_means_unscheduled",
        '{"front": "Q", "back": "A", "due": null}',
        Card(front="Q", back="A", due=None),
    ),
]


class TestSm2Json(unittest.TestCase):
    def test_parse_cases(self):
        for name, line, expected in SM2JSON_PARSE_CASES:
            with self.subTest(name=name):
                self.assertEqual(parse_sm2json(line), [expected])

    def test_parse_rejects_invalid_json(self):
        with self.assertRaises(FormatError):
            parse_sm2json("{not json}")

    def test_parse_rejects_missing_required_field(self):
        with self.assertRaises(FormatError):
            parse_sm2json('{"front": "Q"}')

    def test_write_then_parse_round_trip(self):
        cards = [
            Card(front="Q", back="A", tags=("a", "b"), interval=10,
                 repetitions=3, efactor=2.1, due="2026-10-01"),
            Card(front="No tags", back="here"),
        ]
        self.assertEqual(parse_sm2json(write_sm2json(cards)), cards)

    def test_write_empty_list_produces_empty_string(self):
        self.assertEqual(write_sm2json([]), "")


if __name__ == "__main__":
    unittest.main()
