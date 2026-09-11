import unittest

from srsconv import (
    Card,
    FormatError,
    grade_card,
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

    def test_notetype_and_deck_columns_dont_get_mistaken_for_fields(self):
        text = (
            ANKI_HEADER
            + "#notetype column:1\n#deck column:2\n"
            + "Basic\tDefault\tWhat is 2+2?\t4\n"
        )
        self.assertEqual(
            parse_anki_txt(text), [Card(front="What is 2+2?", back="4")]
        )

    def test_explicit_tags_column_used_over_positional_fallback(self):
        text = (
            ANKI_HEADER
            + "#notetype column:1\n#tags column:2\n"
            + "Basic\tgeography::europe\tCapital of France?\tParis\n"
        )
        self.assertEqual(
            parse_anki_txt(text),
            [Card(front="Capital of France?", back="Paris", tags=("geography::europe",))],
        )

    def test_guid_column_is_skipped(self):
        text = ANKI_HEADER + "#guid column:1\n" + "abc123\tTerm\tDefinition\n"
        self.assertEqual(parse_anki_txt(text), [Card(front="Term", back="Definition")])

    def test_parse_rejects_non_numeric_column_header(self):
        with self.assertRaises(FormatError):
            parse_anki_txt(ANKI_HEADER + "#deck column:one\nQ\tA\n")


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


class TestGradeCard(unittest.TestCase):
    def test_first_correct_review_sets_interval_one(self):
        card = Card(front="Q", back="A")
        graded = grade_card(card, 4, today="2026-09-01")
        self.assertEqual(graded.interval, 1)
        self.assertEqual(graded.repetitions, 1)
        self.assertEqual(graded.due, "2026-09-02")

    def test_second_correct_review_sets_interval_six(self):
        card = Card(front="Q", back="A", interval=1, repetitions=1)
        graded = grade_card(card, 4, today="2026-09-01")
        self.assertEqual(graded.interval, 6)
        self.assertEqual(graded.repetitions, 2)
        self.assertEqual(graded.due, "2026-09-07")

    def test_third_correct_review_multiplies_by_efactor(self):
        card = Card(front="Q", back="A", interval=6, repetitions=2, efactor=2.5)
        graded = grade_card(card, 4, today="2026-09-01")
        self.assertEqual(graded.interval, 15)
        self.assertEqual(graded.repetitions, 3)

    def test_lapse_resets_repetitions_and_interval(self):
        card = Card(front="Q", back="A", interval=15, repetitions=3, efactor=2.5)
        graded = grade_card(card, 2, today="2026-09-01")
        self.assertEqual(graded.interval, 1)
        self.assertEqual(graded.repetitions, 0)
        self.assertEqual(graded.due, "2026-09-02")

    def test_efactor_never_drops_below_1_3(self):
        card = Card(front="Q", back="A", efactor=1.3)
        graded = grade_card(card, 0, today="2026-09-01")
        self.assertEqual(graded.efactor, 1.3)

    def test_perfect_recall_raises_efactor(self):
        card = Card(front="Q", back="A", efactor=2.5)
        graded = grade_card(card, 5, today="2026-09-01")
        self.assertGreater(graded.efactor, 2.5)

    def test_original_card_is_not_mutated(self):
        card = Card(front="Q", back="A")
        grade_card(card, 5, today="2026-09-01")
        self.assertEqual(card.interval, 0)
        self.assertEqual(card.repetitions, 0)
        self.assertIsNone(card.due)

    def test_rejects_quality_out_of_range(self):
        with self.assertRaises(ValueError):
            grade_card(Card(front="Q", back="A"), 6)

    def test_rejects_non_integer_quality(self):
        with self.assertRaises(ValueError):
            grade_card(Card(front="Q", back="A"), 4.5)

    def test_today_defaults_to_real_current_date(self):
        graded = grade_card(Card(front="Q", back="A"), 4)
        self.assertIsNotNone(graded.due)


if __name__ == "__main__":
    unittest.main()
