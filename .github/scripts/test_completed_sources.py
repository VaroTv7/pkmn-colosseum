"""Completed objects must not silently become original-object fallback."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools import project


class CompletedSourceTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.config = project.ProjectConfig()
        self.config.version = "TEST"
        self.config.build_dir = self.root / "build"
        self.config.src_dir = self.root / "src"
        self.config.src_dir.mkdir()
        self.config.check_sha_path = self.root / "build.sha1"
        self.config.config_path = self.root / "config.yml"
        self.config.linker_version = "test"
        self.config.ldflags = []
        for name in ("load_build_config", "generate_build_ninja",
                     "generate_objdiff_config", "generate_compile_commands"):
            mock = patch.object(project, name)
            setattr(self, name, mock.start())
            self.addCleanup(mock.stop)

    def object(self, completed, **options):
        self.config.libs = [{"lib": "test", "objects": [
            project.Object(completed, "object.c", **options)]}]

    def assert_no_build_output(self):
        self.load_build_config.assert_not_called()
        self.generate_build_ninja.assert_not_called()
        self.generate_objdiff_config.assert_not_called()
        self.generate_compile_commands.assert_not_called()

    def test_missing_completed_source_fails_before_build_generation(self):
        self.object(True)
        with self.assertRaisesRegex(SystemExit, "Completed object object.c has no source file"):
            project.generate_build(self.config)
        self.assert_no_build_output()

    def test_missing_incomplete_source_keeps_original_fallback(self):
        self.object(False)
        project.generate_build(self.config)
        self.generate_build_ninja.assert_called_once()
        obj = self.generate_build_ninja.call_args.args[1]["object.c"]
        self.assertFalse(obj.completed)
        self.assertFalse(obj.src_path.exists())

    def test_existing_completed_source_uses_resolved_source_path(self):
        self.object(True, source="actual.cpp")
        source = self.config.src_dir / "actual.cpp"
        source.write_text("int value;\n")
        project.generate_build(self.config)
        self.generate_build_ninja.assert_called_once()
        obj = self.generate_build_ninja.call_args.args[1]["object.c"]
        self.assertTrue(obj.completed)
        self.assertEqual(obj.src_path, source)

    def test_directory_is_not_completed_source(self):
        self.object(True)
        (self.config.src_dir / "object.c").mkdir()
        with self.assertRaisesRegex(SystemExit, "has no source file"):
            project.generate_build(self.config)
        self.assert_no_build_output()


if __name__ == "__main__":
    unittest.main()
