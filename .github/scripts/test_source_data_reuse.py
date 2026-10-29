#!/usr/bin/env python3
"""Test compiled-source reuse boundaries, relocation safety and native routing."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.source_data_reuse import find_source_reuse, matching_intervals


def section(data, symbols, relocations=()):
    return {"size": len(data), "nobits": False,
            "symbols": [{"name": name, "offset": start, "size": size, "type": 1}
                        for name, start, size in symbols], "relocations": list(relocations)}


class SourceDataReuseTests(unittest.TestCase):
    def test_matches_inside_defined_symbols_but_not_padding_or_relocations(self):
        data = b"padNAME\0padNAME\0"
        meta = section(data, [("literal", 3, 5)])
        self.assertEqual(list(matching_intervals(meta, data, b"NAME\0")),
                         [{"source_symbol": "literal", "offset": 3, "symbol_offset": 0}])
        meta["relocations"] = [{"offset": 4, "type": 1}]
        self.assertEqual(list(matching_intervals(meta, data, b"NAME\0")), [])
        self.assertEqual(list(matching_intervals(section(data, []), data, data)),
                         [{"source_symbol": None, "offset": 0, "symbol_offset": None}])

    def test_scans_native_code_owner_even_when_report_has_no_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / "build/GC6E01/obj/missing.o", root / "build/GC6E01/src/code.o"]
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic ELF placeholder")
            config = {"units": [
                {"name": "main/missing", "target_path": "build/GC6E01/obj/missing.o"},
                {"name": "main/code", "base_path": "build/GC6E01/compare/code.o",
                 "metadata": {"source_path": "src/code.c"}},
                {"name": "main/untracked", "base_path": "build/GC6E01/src/untracked.o",
                 "metadata": {"source_path": "src/untracked.c"}}]}
            report = {"units": [
                {"name": "main/missing", "sections": [{"name": ".data"}]},
                {"name": "main/code", "measures": {"total_data": 0},
                 "metadata": {"source_path": "src/code.c"}, "sections": []}]}
            calls = []
            def reader(path):
                calls.append(path)
                data = b"REUSED_NAME\0"
                prefix = b"" if path == paths[0] else b"PREFIX"
                meta = section(prefix + data, [("target" if not prefix else "literal_pool", 0,
                                               len(prefix + data))])
                return {".data": meta}, {".data": prefix + data}
            result = find_source_reuse(config, report, root, root / "build/GC6E01", reader,
                                       tracked_paths={"src/code.c"})
            self.assertEqual(calls, paths)
            self.assertEqual(result["summary"]["target_symbols_with_matches"], 1)
            match = result["targets"][0]["matches"][0]
            self.assertEqual(match["object"], "build/GC6E01/src/code.o")
            self.assertEqual(match["offset"], 6)
            self.assertNotIn("REUSED_NAME", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
