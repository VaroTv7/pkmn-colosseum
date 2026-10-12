"""Private input installation and canonical output gates use synthetic fixtures."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.ci_retail import compare_outputs, prepare_inputs, read_manifest


class RetailInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.orig = self.root / "orig/GC6E01"
        self.orig.joinpath("sys").mkdir(parents=True)
        self.dol, self.rel = b"synthetic-dol", b"synthetic-rel"
        self.orig.joinpath("sys/main.dol").write_bytes(self.dol)
        self.manifest = self.root / "build.sha1"
        self.manifest.write_text(
            hashlib.sha1(self.dol).hexdigest() + "  build/GC6E01/main.dol\n" +
            hashlib.sha1(self.rel).hexdigest() + "  build/GC6E01/module/module.rel\n")
        self.archive = self.root / "inputs.zip"

    def zip(self, data=None, extra=None):
        with zipfile.ZipFile(self.archive, "w") as bundle:
            bundle.writestr("orig/GC6E01/files/module.rel", self.rel if data is None else data)
            if extra:
                bundle.writestr(*extra)

    def test_install_and_direct_output_comparison(self):
        self.zip(extra=("verification.json", "{}"))
        entries = prepare_inputs(self.manifest, self.orig, self.archive)
        for relative, output, _ in entries:
            path = self.root / output
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((self.orig / relative).read_bytes())
        compare_outputs(entries, self.orig, self.root)

    def test_complete_loose_inputs_need_no_zip(self):
        self.zip()
        prepare_inputs(self.manifest, self.orig, self.archive)
        prepare_inputs(self.manifest, self.orig, self.root / "absent.zip")

    def test_missing_inputs_fail(self):
        with self.assertRaisesRegex(ValueError, "Missing original"):
            prepare_inputs(self.manifest, self.orig)

    def test_corrupt_archive_cannot_install(self):
        self.zip(b"incorrect")
        with self.assertRaisesRegex(ValueError, "ZIP hash mismatch"):
            prepare_inputs(self.manifest, self.orig, self.archive)
        self.assertFalse((self.orig / "files/module.rel").exists())

    def test_existing_wrong_original_not_overwritten(self):
        self.zip()
        self.orig.joinpath("files").mkdir()
        existing = self.orig / "files/module.rel"
        existing.write_bytes(b"preserve me")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            prepare_inputs(self.manifest, self.orig, self.archive)
        self.assertEqual(existing.read_bytes(), b"preserve me")

    def test_missing_dol_prevents_partial_install(self):
        self.zip()
        self.orig.joinpath("sys/main.dol").unlink()
        with self.assertRaises(ValueError):
            prepare_inputs(self.manifest, self.orig, self.archive)
        self.assertFalse(self.orig.joinpath("files/module.rel").exists())

    def test_zip_traversal_is_rejected(self):
        self.zip(extra=("../escape", "bad"))
        with self.assertRaisesRegex(ValueError, "Unsafe ZIP"):
            prepare_inputs(self.manifest, self.orig, self.archive)

    def test_unconfigured_input_is_rejected(self):
        self.zip(extra=("orig/GC6E01/files/unexpected.rel", "bad"))
        with self.assertRaisesRegex(ValueError, "Unconfigured original"):
            prepare_inputs(self.manifest, self.orig, self.archive)

    def test_duplicate_zip_member_is_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self.zip(extra=("orig/GC6E01/files/module.rel", self.rel))
        with self.assertRaisesRegex(ValueError, "Duplicate ZIP"):
            prepare_inputs(self.manifest, self.orig, self.archive)

    def test_manifest_duplicate_is_rejected(self):
        self.manifest.write_text(self.manifest.read_text() * 2)
        with self.assertRaisesRegex(ValueError, "Duplicate input"):
            read_manifest(self.manifest)

    def test_manifest_without_dol_is_rejected(self):
        self.manifest.write_text("")
        with self.assertRaises(ValueError):
            read_manifest(self.manifest)

    def test_manifest_traversal_is_rejected(self):
        self.manifest.write_text("0" * 40 + "  build/GC6E01/../main.dol\n")
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            read_manifest(self.manifest)

    def test_bad_output_is_rejected(self):
        self.zip()
        entries = prepare_inputs(self.manifest, self.orig, self.archive)
        path = self.root / "build/GC6E01/main.dol"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"wrong")
        with self.assertRaisesRegex(ValueError, "Rebuilt hash mismatch"):
            compare_outputs(entries, self.orig, self.root)

    def test_symlink_destination_is_rejected(self):
        self.zip()
        destination = self.root / "elsewhere"
        destination.mkdir()
        self.orig.joinpath("files").symlink_to(destination, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            prepare_inputs(self.manifest, self.orig, self.archive)


if __name__ == "__main__":
    unittest.main()
