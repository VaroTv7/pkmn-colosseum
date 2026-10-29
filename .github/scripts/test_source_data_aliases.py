#!/usr/bin/env python3
"""Check complete-array alias views using only synthetic ELF data."""

import copy
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.source_data_aliases import create_views
from tools.source_object_metadata import Elf

GROUPS = [{"base": "flags", "size": 8, "aliases": [
    {"name": "status", "offset": 3, "size": 1},
    {"name": "mode", "offset": 5, "size": 1},
]}]


def fixture(source=True):
    names = ["", ".sdata", ".rela.sdata", ".symtab", ".strtab", ".shstrtab", ".comment"]
    # name, value, size, type/binding, visibility, section
    symbols = [("", 0, 0, 0, 0, 0), ("", 0, 0, 3, 0, 1)]
    if source:
        symbols += [("flags", 0, 8, 0x11, 0, 1)]
    else:
        symbols += [("flags", 0, 1, 0x11, 0, 1),
                    ("gap_07_80001001_sdata", 1, 2, 0x11, 2, 1),
                    ("status", 3, 1, 0x11, 0, 1),
                    ("gap_07_80001004_sdata", 4, 1, 0x11, 2, 1),
                    ("mode", 5, 1, 0x11, 0, 1),
                    ("gap_07_80001006_sdata", 6, 2, 0x11, 2, 1)]
    symbols += [("pointer", 8, 4, 0x11, 0, 1), ("external", 0, 0, 0x10, 0, 0)]
    strings = bytearray(b"\0")
    table = bytearray()
    comment = bytearray(44)
    comment[:11] = b"CodeWarrior"
    comment[11], comment[16], comment[17], comment[20] = 8, 1, 2, 44
    for name, value, size, info, visibility, section in symbols:
        offset = len(strings) if name else 0
        if name:
            strings.extend(name.encode() + b"\0")
        table.extend(struct.pack(">IIIBBH", offset, value, size, info, visibility, section))
        comment.extend(struct.pack(">IBBH", 8 if info == 3 else 1, 0, 8 if section else 0, 0))
    shstrings = b"\0".join(n.encode() for n in names) + b"\0"
    data = {".sdata": bytes([1, 0, 0, 2, 0, 3, 0, 0, 0, 0, 0, 0]),
            ".rela.sdata": struct.pack(">IIi", 8, (len(symbols) - 1) << 8 | 1, 12),
            ".symtab": table, ".strtab": strings,
            ".shstrtab": shstrings, ".comment": comment}
    blob, sections = bytearray(52), [(0,) * 10]
    for name in names[1:]:
        kind, flags, link, info, alignment, entry = 1, 0, 0, 0, 1, 0
        if name == ".sdata":
            flags, alignment = 3, 8
        elif name == ".rela.sdata":
            kind, link, info, alignment, entry = 4, 3, 1, 4, 12
        elif name == ".symtab":
            kind, link, info, alignment, entry = 2, 4, 2, 4, 16
        elif name in (".strtab", ".shstrtab"):
            kind = 3
        blob.extend(bytes(-len(blob) % alignment))
        payload = data[name]
        sections.append((shstrings.index(name.encode() + b"\0"), kind, flags, 0,
                         len(blob), len(payload), link, info, alignment, entry))
        blob.extend(payload)
    blob.extend(bytes(-len(blob) % 4))
    shoff = len(blob)
    blob.extend(b"".join(struct.pack(">10I", *s) for s in sections))
    struct.pack_into(">16sHHIIIIIHHHHHH", blob, 0,
                     b"\x7fELF\x01\x02\x01" + bytes(9), 1, 20, 1, 0, 0,
                     shoff, 0, 52, 0, 0, 40, len(sections), 5)
    return bytes(blob)


def symbol_patch(blob, name, field_offset, fmt, value):
    elf = Elf(blob)
    index, _ = elf.unique_symbol(name)
    output = bytearray(blob)
    struct.pack_into(fmt, output, elf.sections[elf.symtab][4] + index * 16 + field_offset, value)
    return bytes(output)


class SourceArrayAliasTests(unittest.TestCase):
    def setUp(self):
        self.source, self.target = fixture(), fixture(False)

    def test_link_aliases_keep_full_native_array_and_exact_bytes(self):
        before_source, before_target = self.source, self.target
        link, comparison, summary = create_views(self.source, self.target, GROUPS)
        native, linked, compared = Elf(self.source), Elf(link), Elf(comparison)
        self.assertEqual(native.unique_symbol("flags")[1][2], 8)
        self.assertEqual(linked.unique_symbol("flags")[1][2], 8)
        self.assertEqual(compared.unique_symbol("flags")[1][2], 1)
        self.assertEqual(linked.unique_symbol("status")[1][1:6], (3, 0, 0x10, 0, 1))
        self.assertEqual(linked.unique_symbol("mode")[1][1:6], (5, 0, 0x10, 0, 1))
        self.assertEqual(compared.unique_symbol("status")[1][1:6], (3, 1, 0x11, 0, 1))
        for view in (linked, compared):
            self.assertEqual(view.payload(1), native.payload(1))
            self.assertEqual(view.payload(2), native.payload(2))
            self.assertEqual(view.data_relocations(), native.data_relocations())
        self.assertEqual((self.source, self.target), (before_source, before_target))
        self.assertEqual(summary["link_labels_added"], 2)
        self.assertEqual(summary["comparison_fragment_symbols_added"], 5)
        self.assertEqual(summary["allocated_bytes_changed"], 0)

    def test_comparison_fragments_partition_exact_native_extent(self):
        _, comparison, _ = create_views(self.source, self.target, GROUPS)
        expected = sorted((n, s[1:5]) for n, s in Elf(self.target).symbols if s[5] == 1 and s[2])
        actual = sorted((n, s[1:5]) for n, s in Elf(comparison).symbols if s[5] == 1 and s[2])
        self.assertEqual(actual, expected)
        self.assertEqual(sum(s[2] for _, s in Elf(comparison).symbols if s[5] == 1), 12)

    def test_source_byte_mismatch_rejected(self):
        source = bytearray(self.source)
        source[Elf(self.source).sections[1][4]] ^= 1
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            create_views(bytes(source), self.target, GROUPS)

    def test_relocation_mismatch_rejected(self):
        source = bytearray(self.source)
        struct.pack_into(">i", source, Elf(self.source).sections[2][4] + 8, 13)
        with self.assertRaisesRegex(ValueError, "relocation semantics"):
            create_views(bytes(source), self.target, GROUPS)

    def test_incorrect_native_array_bound_rejected(self):
        source = symbol_patch(self.source, "flags", 8, ">I", 7)
        with self.assertRaisesRegex(ValueError, "complete registered C array"):
            create_views(source, self.target, GROUPS)

    def test_unrelated_source_extent_mismatch_rejected(self):
        source = symbol_patch(self.source, "pointer", 8, ">I", 3)
        with self.assertRaisesRegex(ValueError, "Unrelated source object"):
            create_views(source, self.target, GROUPS)

    def test_alias_offset_extent_and_duplicate_registration_rejected(self):
        for key, value in (("offset", 8), ("offset", -1), ("offset", True),
                           ("offset", 2), ("size", 2), ("size", 0), ("name", "flags")):
            groups = copy.deepcopy(GROUPS)
            groups[0]["aliases"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                create_views(self.source, self.target, groups)
        with self.assertRaisesRegex(ValueError, "overlap"):
            create_views(self.source, self.target, GROUPS + GROUPS)

    def test_unregistered_interior_object_rejected(self):
        groups = copy.deepcopy(GROUPS)
        groups[0]["aliases"].pop()
        with self.assertRaisesRegex(ValueError, "Unregistered target storage"):
            create_views(self.source, self.target, groups)

    def test_unknown_registration_keys_rejected(self):
        groups = copy.deepcopy(GROUPS)
        groups[0]["copy_target_bytes"] = True
        with self.assertRaisesRegex(ValueError, "registration fields"):
            create_views(self.source, self.target, groups)

    def test_target_partition_overlap_and_uncovered_gap_rejected(self):
        for size in (1, 3):
            target = symbol_patch(self.target, "gap_07_80001001_sdata", 8, ">I", size)
            source = self.source
            if size == 3:
                # Keep the overlapping span zero, so this exercises extent
                # validation rather than the independent zero-gap check.
                source, target = bytearray(source), bytearray(target)
                for blob in (source, target):
                    blob[Elf(blob).sections[1][4] + 3] = 0
                source, target = bytes(source), bytes(target)
            with self.subTest(size=size), self.assertRaisesRegex(ValueError, "partition"):
                create_views(source, target, GROUPS)

    def test_nonzero_hidden_gap_rejected_even_if_bytes_equal(self):
        source, target = bytearray(self.source), bytearray(self.target)
        for blob in (source, target):
            blob[Elf(blob).sections[1][4] + 1] = 4
        with self.assertRaisesRegex(ValueError, "zero gap"):
            create_views(bytes(source), bytes(target), GROUPS)

    def test_alias_name_already_present_in_native_rejected(self):
        source = bytearray(self.source)
        elf = Elf(source)
        strings = elf.sections[elf.sections[elf.symtab][6]]
        start = strings[4] + elf.unique_symbol("pointer")[1][0]
        source[start:start + 8] = b"status\0\0"
        with self.assertRaisesRegex(ValueError, "already exists"):
            create_views(bytes(source), self.target, GROUPS)

    def test_missing_compiler_metadata_rejected(self):
        source = bytearray(self.source)
        source[Elf(self.source).sections[6][4]] ^= 1
        with self.assertRaisesRegex(ValueError, "compiler metadata"):
            create_views(bytes(source), self.target, GROUPS)

    def test_cli_refuses_overwriting_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.o"
            source.write_bytes(self.source)
            command = [sys.executable, str(ROOT / "tools/source_data_aliases.py"),
                       "--source", str(source), "--target", str(root / "target.o"),
                       "--groups", str(root / "groups.json"), "--link-output", str(source),
                       "--comparison-output", str(root / "comparison.o")]
            process = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("distinct paths", process.stderr)
            self.assertEqual(source.read_bytes(), self.source)


if __name__ == "__main__":
    unittest.main()
