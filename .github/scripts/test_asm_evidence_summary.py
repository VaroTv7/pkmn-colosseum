"""Assembly reporting must not turn aliases or inline entries into C progress."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import asm_evidence_summary as summary


def unit(module, path, name, address, size, *, matched=True, linked=True):
    return dict(name=f"{module}/{path}",
                metadata=dict(module_name=module, source_path=path, complete=linked),
                sections=[dict(name=".text", size=size,
                               metadata=dict(virtual_address=address))],
                functions=[dict(name=name, size=size,
                                fuzzy_match_percent=100 if matched else 90,
                                metadata=dict(virtual_address=address))])


class AssemblySummaryTests(unittest.TestCase):
    def test_resolves_names_by_source_module_and_explicit_address(self):
        report = dict(units=[unit("main", "src/a.c", "same", 0x100, 16),
                             unit("main", "src/b.c", "same", 0x200, 64,
                                  matched=False, linked=False),
                             unit("room", "src/rel/room/a.c", "same", 0x100, 32)])
        entries = [dict(path="src/a.c", function="same"),
                   dict(path="src/old-owner.c", function="renamed", address="fn_00000200"),
                   dict(path="src/rel/room/a.c", function="same"),
                   dict(path="src/missing.c", function="same"),
                   dict(path="src/a.c", function="inlineOnly")]
        result = summary.summarize(entries, report)
        self.assertEqual(result["combined"],
                         dict(functions=3, bytes=112, matched_bytes=48, linked_bytes=48))
        self.assertEqual([e["function"] for e in result["unresolved"]],
                         ["same", "inlineOnly"])

    def test_duplicate_entries_aliases_and_policy_overlap_count_once(self):
        owner = unit("main", "src/a.c", "whole", 0x100, 16)
        owner["functions"].append(dict(owner["functions"][0], name="alias"))
        entry = dict(path="src/a.c", function="whole")
        result = summary.summarize(
            [entry, entry, dict(path="src/a.c", function="alias"),
             dict(entry, tier="paired-single-allowlist")], dict(units=[owner]))
        self.assertEqual(result["combined"]["functions"], 1)
        self.assertEqual(result["combined"]["bytes"], 16)
        self.assertEqual(result["tiers"]["library"]["resolved_entries"], 3)

    def test_cli_includes_separate_allowlist_without_claiming_pure_c(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry.json"
            report = Path(temporary) / "report.json"
            registry.write_text(json.dumps(dict(entries=[])))
            report.write_text(json.dumps(dict(units=[unit("main", "src/paired.c", "paired", 256, 16)])))
            output = io.StringIO()
            with patch.object(summary, "REGISTRY", registry), \
                 patch.object(summary, "DOLPHIN_PAIRED_SINGLE_PATH", "src/paired.c"), \
                 patch.object(summary, "DOLPHIN_PAIRED_SINGLE_FUNCTIONS", {"paired"}), \
                 patch("sys.argv", ["asm_evidence_summary.py", str(report)]), \
                 contextlib.redirect_stdout(output):
                self.assertEqual(summary.main(), 0)
            text = output.getvalue()
            self.assertIn("paired-single-allowlist: 1/1 entries resolved", text)
            self.assertIn("not assembly instruction bytes", text)
            self.assertIn("Pure-C coverage is not derivable", text)
            self.assertNotIn("%", text)


if __name__ == "__main__":
    unittest.main()
