import tempfile
import unittest
from pathlib import Path

from src.quality import inspect_csv


class QualityTests(unittest.TestCase):
    def inspect(self, content: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            path.write_text(content, encoding="utf-8")
            return inspect_csv(path, "synthetic test fixture")

    def test_valid_rows_and_date_gap(self):
        report = self.inspect("date,system,storage_pct\n2026-01-01,A,50\n2026-01-03,A,49.5\n")
        self.assertTrue(report.usable)
        self.assertEqual(report.date_gaps, {"A": 1})

    def test_duplicate_and_invalid_value_rejected(self):
        report = self.inspect("date,system,storage_pct\n2026-01-01,A,50\n2026-01-01,A,55\n2026-01-02,A,101\n")
        self.assertFalse(report.usable)
        self.assertEqual(report.duplicate_system_dates, 1)
        self.assertEqual(report.invalid_rows, 1)

    def test_missing_column_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing columns"):
            self.inspect("date,system\n2026-01-01,A\n")


if __name__ == "__main__":
    unittest.main()
