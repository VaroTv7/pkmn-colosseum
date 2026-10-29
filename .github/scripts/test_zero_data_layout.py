#!/usr/bin/env python3
"""Reject equal-zero objects whose symbols would occupy wrong addresses."""

import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.verify_zero_data_layout import check_object, expectations


def object_blob(symbols=None, size=8, kind=8, alignment=4, extra_data=False):
    symbols = symbols or [("first", 0, 4), ("second", 4, 4)]
    strings = bytearray(b"\0")
    table = bytearray(16)
    for name, offset, symbol_size in symbols:
        at = len(strings)
        strings.extend(name.encode() + b"\0")
        table.extend(struct.pack(">IIIBBH", at, offset, symbol_size, 0x11, 0, 1))
    # name, type, flags, payload, section size, link, info, alignment, entry size
    sections = [("", 0, 0, b"", 0, 0, 0, 1, 0),
                (".sbss", kind, 3, b"" if kind == 8 else bytes(size), size, 0, 0, alignment, 0),
                (".strtab", 3, 0, bytes(strings), len(strings), 0, 0, 1, 0),
                (".symtab", 2, 0, bytes(table), len(table), 2, 1, 4, 16)]
    if extra_data:
        sections.append((".data", 1, 3, bytes(4), 4, 0, 0, 4, 0))
    names = bytearray(b"\0")
    offsets = []
    for name in [row[0] for row in sections] + [".shstrtab"]:
        offsets.append(len(names))
        names.extend(name.encode() + b"\0")
    sections.append((".shstrtab", 3, 0, bytes(names), len(names), 0, 0, 1, 0))
    blob = bytearray(52)
    headers = []
    for index, row in enumerate(sections):
        name, kind, flags, data, size, link, info, align, entsize = row
        blob.extend(bytes(-len(blob) % align))
        at = len(blob)
        blob.extend(data)
        headers.append((offsets[index], kind, flags, 0, at, size, link, info, align, entsize))
    blob.extend(bytes(-len(blob) % 4))
    shoff = len(blob)
    for header in headers:
        blob.extend(struct.pack(">10I", *header))
    ident = b"\x7fELF\x01\x02\x01" + bytes(9)
    blob[:52] = struct.pack(">16sHHIIIIIHHHHHH", ident, 1, 20, 1, 0, 0,
                            shoff, 0, 52, 0, 0, 40, len(sections), len(sections) - 1)
    return bytes(blob)


class ZeroDataLayoutTests(unittest.TestCase):
    def expected(self):
        return {"section": ".sbss", "start": 0x80470000, "size": 8,
                "symbols": [{"name": "first", "offset": 0, "size": 4},
                            {"name": "second", "offset": 4, "size": 4}]}

    def test_correct_symbol_layout_passes(self):
        self.assertEqual(check_object(object_blob(), self.expected()), [])

    def test_swapped_offsets_fail_despite_identical_zero_section(self):
        errors = check_object(object_blob([("first", 4, 4), ("second", 0, 4)]), self.expected())
        self.assertEqual(len(errors), 2)

    def test_wrong_symbol_extent_fails_despite_identical_zero_section(self):
        self.assertTrue(check_object(object_blob([("first", 0, 8), ("second", 4, 4)]), self.expected()))

    def test_missing_and_duplicate_definitions_fail(self):
        self.assertTrue(check_object(object_blob([("first", 0, 4)]), self.expected()))
        self.assertTrue(check_object(object_blob([("first", 0, 4), ("first", 0, 4),
                                                  ("second", 4, 4)]), self.expected()))

    def test_extra_storage_and_initialized_zero_storage_fail(self):
        self.assertTrue(check_object(object_blob(extra_data=True), self.expected()))
        self.assertTrue(check_object(object_blob(size=12), self.expected()))
        self.assertTrue(check_object(object_blob(kind=1), self.expected()))

    def test_incompatible_link_alignment_fails(self):
        expected = self.expected()
        expected["start"] += 4
        self.assertTrue(check_object(object_blob(alignment=8), expected))

    def test_metadata_derives_local_alias_and_gap_without_source_declarations(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "units.json").write_text(json.dumps({"version": 1, "units": ["game/data/test.c"]}))
            (base / "splits.txt").write_text("game/data/test.c:\n\t.sbss start:0x80470000 end:0x80470008\n")
            (base / "symbols.txt").write_text(
                "first = .sbss:0x80470000; // type:object size:0x1 scope:local\n"
                "second = .sbss:0x80470004; // type:object size:0x4\n")
            result = expectations(base / "units.json", base / "symbols.txt", base / "splits.txt")
            self.assertEqual(result[0]["symbols"], [
                {"name": "first_80470000", "offset": 0, "size": 1},
                {"name": "padding_80470001", "offset": 1, "size": 3},
                {"name": "second", "offset": 4, "size": 4}])
            (base / "splits.txt").write_text("game/data/test.c:\n\t.sbss start:0x80470000 end:0x80470006\n")
            with self.assertRaises(ValueError):
                expectations(base / "units.json", base / "symbols.txt", base / "splits.txt")


if __name__ == "__main__":
    unittest.main()
