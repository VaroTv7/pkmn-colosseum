#!/usr/bin/env python3
"""Synthetic checks for bounded link diagnostics; no original objects or payloads."""
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

script = Path(__file__).resolve().parents[2] / "tools" / "probe_source_data_link.py"
spec = importlib.util.spec_from_file_location("link_probe", script)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class LinkProbeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="colosseum-link-probe-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / "synthetic.elf"
        names = b"\0.data\0.shstrtab\0"
        header = struct.pack(">16sHHIIIIIHHHHHH", b"\x7fELF\x01\x02\x01" + bytes(9),
                             2, 20, 1, 0, 0, 52, 0, 52, 0, 0, 40, 3, 2)
        rows = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                (1, 1, 3, 0x80000000, 172, 4, 0, 0, 4, 0),
                (7, 3, 0, 0, 176, len(names), 0, 0, 1, 0)]
        self.blob = header + b"".join(struct.pack(">10I", *row) for row in rows) + bytes(4) + names
        self.path.write_bytes(self.blob)

    def test_valid_header_and_sections(self):
        result = probe.elf_headers(self.path)
        self.assertTrue(result["structurally_bounded"])
        self.assertEqual(result["sections"][1]["name"], ".data")
        self.assertFalse(result["payload_read"])

    def test_oversized_section_rejected(self):
        blob = bytearray(self.blob)
        struct.pack_into(">I", blob, 52 + 40 + 20, 0xffffffff)
        self.path.write_bytes(blob)
        result = probe.elf_headers(self.path)
        self.assertFalse(result["structurally_bounded"])
        self.assertTrue(result["issues"])

    def test_truncated_header_rejected(self):
        self.path.write_bytes(bytes(12))
        result = probe.elf_headers(self.path)
        self.assertEqual(result["error_reason"], "metadata_range_outside_file")

    def test_only_sanitized_section_names_retained(self):
        result = probe.bounded_command(
            [sys.executable, "-c", 'print("Processing data section .sdata"); print("arbitrary raw diagnostic")'],
            self.root, 2, conversion=True)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["processing_sections"], [{"kind": "data", "name": ".sdata"}])
        self.assertNotIn("arbitrary raw diagnostic", str(result))

    def test_timeout_terminates_process(self):
        result = probe.bounded_command(
            [sys.executable, "-c", "import time; time.sleep(5)"], self.root, 1)
        self.assertTrue(result["timed_out"])
        self.assertLess(result["exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
