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
