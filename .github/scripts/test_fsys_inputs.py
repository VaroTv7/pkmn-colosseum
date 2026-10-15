"""Original-input planning accepts loose RELs without weakening validation."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.fsys_inputs import extraction_steps


class FsysInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.files = self.root / "GC6E01" / "files"
        self.files.mkdir(parents=True)
        self.archives = {"common.fsys": ["common_rel", "mail"]}

    def plan(self):
        return extraction_steps("GC6E01", self.archives, self.root)

    def test_missing_inputs_are_not_silently_dropped(self):
        steps = self.plan()
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["inputs"], str(self.files / "common.fsys"))
        self.assertEqual(len(steps[0]["outputs"]), 2)

    def test_complete_loose_modules_do_not_need_archive(self):
        for name in ("common_rel", "mail"):
            (self.files / f"{name}.rel").write_bytes(b"synthetic-test-fixture")
        self.assertEqual(self.plan(), [])

    def test_incomplete_loose_set_still_requires_archive(self):
        (self.files / "common_rel.rel").touch()
        self.assertEqual(len(self.plan()), 1)

    def test_archive_is_authoritative_when_present(self):
        (self.files / "common.fsys").touch()
        for name in ("common_rel", "mail"):
            (self.files / f"{name}.rel").touch()
        self.assertEqual(len(self.plan()), 1)

    def test_directory_does_not_count_as_loose_module(self):
        (self.files / "common_rel.rel").mkdir()
        (self.files / "mail.rel").touch()
        self.assertEqual(len(self.plan()), 1)

    def test_empty_archive_manifest_is_rejected(self):
        with self.assertRaises(ValueError):
            extraction_steps("GC6E01", {"empty.fsys": []}, self.root)


if __name__ == "__main__":
    unittest.main()
