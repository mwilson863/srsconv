import contextlib
import io
import os
import tempfile
import unittest

from srsconv.cli import main

ANKI_TXT = (
    "#separator:tab\n#html:true\n"
    "What is 2+2?\t4\tmath\n"
)

SM2JSON = '{"front": "Q", "back": "A", "tags": ["x"]}\n'


def _run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = main(argv)
    return status, out.getvalue(), err.getvalue()


class TestDryRun(unittest.TestCase):
    def test_anki2json_dry_run_reports_count_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            infile = os.path.join(tmp, "cards.txt")
            outfile = os.path.join(tmp, "out.jsonl")
            with open(infile, "w", encoding="utf-8") as f:
                f.write(ANKI_TXT)

            status, out, err = _run(["anki2json", infile, "-o", outfile, "--dry-run"])

            self.assertEqual(status, 0)
            self.assertEqual(out, "")
            self.assertIn("1 card(s) valid", err)
            self.assertFalse(os.path.exists(outfile))

    def test_json2anki_dry_run_reports_count_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            infile = os.path.join(tmp, "cards.jsonl")
            outfile = os.path.join(tmp, "out.txt")
            with open(infile, "w", encoding="utf-8") as f:
                f.write(SM2JSON)

            status, out, err = _run(["json2anki", infile, "-o", outfile, "--dry-run"])

            self.assertEqual(status, 0)
            self.assertEqual(out, "")
            self.assertIn("1 card(s) valid", err)
            self.assertFalse(os.path.exists(outfile))

    def test_dry_run_still_reports_format_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            infile = os.path.join(tmp, "cards.txt")
            with open(infile, "w", encoding="utf-8") as f:
                f.write("#separator:tab\n#html:true\nfront only\n")

            status, out, err = _run(["anki2json", infile, "--dry-run"])

            self.assertEqual(status, 1)
            self.assertIn("srsconv:", err)

    def test_anki2json_writes_output_when_not_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            infile = os.path.join(tmp, "cards.txt")
            outfile = os.path.join(tmp, "out.jsonl")
            with open(infile, "w", encoding="utf-8") as f:
                f.write(ANKI_TXT)

            status, out, err = _run(["anki2json", infile, "-o", outfile, "--today", "2026-01-01"])

            self.assertEqual(status, 0)
            with open(outfile, encoding="utf-8") as f:
                content = f.read()
            self.assertIn('"due": "2026-01-01"', content)


if __name__ == "__main__":
    unittest.main()
