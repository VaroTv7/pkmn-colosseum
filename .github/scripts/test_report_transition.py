"""Prevent renames, missing identities and empty reports hiding regressions."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.audit_report_transition import compare_reports, index_report


def report(*functions):
    return {"units": [{"name": "main/test", "functions": [
        {"name": name, "size": size, "fuzzy_match_percent": score,
         "metadata": {"virtual_address": address}}
        for name, address, size, score in functions]}],
        "measures": {"total_functions": len(functions)}}


class ReportTransitionTests(unittest.TestCase):
    def test_renaming_cannot_hide_regression(self):
        result = compare_reports(report(("old", 100, 4, 100)), report(("new", 100, 4, 90)))
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["regressions"]), 1)

    def test_clean_rename_is_not_regression(self):
        result = compare_reports(report(("old", 100, 4, 100)), report(("new", 100, 4, 100)))
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["renamed_functions"]), 1)

    def test_missing_function_is_not_silently_ignored(self):
        result = compare_reports(report(("a", 100, 4, 100), ("b", 104, 4, 100)), report(("a", 100, 4, 100)))
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["missing_functions"]), 1)

    def test_exact_covering_interval_records_coalescence(self):
        result = compare_reports(report(("a", 100, 4, 90), ("b", 104, 4, 100)), report(("a", 100, 8, 100)))
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["coalesced_functions"]), 1)

    def test_nonexact_cover_does_not_excuse_removal(self):
        result = compare_reports(report(("a", 100, 4, 90), ("b", 104, 4, 100)), report(("a", 100, 8, 99)))
        self.assertFalse(result["passed"])

    def test_shrinking_function_requires_review(self):
        result = compare_reports(report(("a", 100, 8, 100)), report(("a", 100, 4, 100)))
        self.assertFalse(result["passed"])

    def test_duplicate_address_fails(self):
        with self.assertRaises(ValueError):
            index_report(report(("a", 100, 4, 100), ("b", 100, 4, 100)))

    def test_empty_report_fails(self):
        with self.assertRaises(ValueError):
            index_report(report())

    def test_report_total_must_agree(self):
        r = report(("a", 100, 4, 100))
        r["measures"]["total_functions"] = 2
        with self.assertRaises(ValueError):
            index_report(r)


if __name__ == "__main__":
    unittest.main()
