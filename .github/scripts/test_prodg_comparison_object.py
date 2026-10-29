#!/usr/bin/env python3
"""Synthetic compiler/DTK object tests, with no retail payloads."""

from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import prodg_comparison_object as helper


def fixture(source=True):
    names = ["", ".data", ".rodata", ".rela.data", ".symtab", ".strtab", ".shstrtab"]
    shstr = b"\0".join(x.encode() for x in names) + b"\0"
    strings = b"\0.LC0\0.LC1\0target_first\0target_second\0fixture_table\0"

    def symbol(name, value, size, info, section):
        return struct.pack(">IIIBBH", strings.index(name.encode() + b"\0") if name else 0,
                           value, size, info, 0, section)

    symbols = bytes(16)
    symbols += symbol("", 0, 0, 3, 1)
    symbols += symbol("", 0, 0, 3, 2)
    symbols += symbol(".LC0" if source else "target_first", 0, 0 if source else 4,
                      0 if source else 1, 2)
    symbols += symbol(".LC1" if source else "target_second", 4, 0 if source else 4,
                      0 if source else 1, 2)
    symbols += symbol("fixture_table", 0, 12, 0x11, 1)
    relas = [(4, 2, 0), (8, 2, 4)] if source else [(4, 3, 0), (8, 4, 0)]
    rela = b"".join(struct.pack(">IIi", offset, sym << 8 | 1, addend)
                    for offset, sym, addend in relas)
    data = struct.pack(">3I", 0x01020304, 0, 4 if source else 0)
    payloads = [b"", data, b"one\0two\0", rela, symbols, strings, shstr]
    kinds = [0, 1, 1, 4, 2, 3, 3]
    flags = [0, 3, 2, 0, 0, 0, 0]
    links = [0, 0, 0, 4, 5, 0, 0]
    infos = [0, 0, 0, 1, 5, 0, 0]
    entsizes = [0, 0, 0, 12, 16, 0, 0]
    blob, sections = bytearray(52), [(0,) * 10]
    for i, payload in enumerate(payloads[1:], 1):
        blob.extend(bytes(-len(blob) % 4))
        sections.append((shstr.index(names[i].encode() + b"\0"), kinds[i], flags[i],
                         0, len(blob), len(payload), links[i], infos[i], 4, entsizes[i]))
        blob.extend(payload)
    blob.extend(bytes(-len(blob) % 4))
    shoff = len(blob)
    blob.extend(b"".join(struct.pack(">10I", *s) for s in sections))
    struct.pack_into(">16sHHIIIIIHHHHHH", blob, 0,
                     b"\x7fELF\x01\x02\x01" + bytes(9), 1, 20, 1, 0, 0,
                     shoff, 0, 52, 0, 0, 40, len(sections), 6)
    return bytes(blob)


def patch(blob, offset, fmt, *values):
    data = bytearray(blob)
    struct.pack_into(fmt, data, offset, *values)
    return bytes(data)


def section_offset(blob, name):
    elf = helper.Elf(blob)
    return elf.sections[elf.names.index(name)][4]


def header_offset(blob, section, field):
    h = struct.unpack_from(">16sHHIIIIIHHHHHH", blob)
    elf = helper.Elf(blob)
    return h[6] + elf.names.index(section) * 40 + field * 4


class ComparisonCopyTests(unittest.TestCase):
    def setUp(self):
        self.source, self.target = fixture(True), fixture(False)

    def test_exact_bytes_and_semantics_with_distinct_symbol_names(self):
        output, summary = helper.comparison_copy(self.source, self.target)
        elf = helper.Elf(output)
        self.assertEqual(elf.payload(1), struct.pack(">3I", 0x01020304, 0, 0))
        self.assertEqual(elf.payload(2), b"one\0two\0")
        self.assertEqual(elf.symbols[3][0], ".LC0")
        self.assertEqual(elf.symbols[4][0], ".LC1")
        self.assertEqual(elf.symbols[3][1][1:4], (0, 4, 1))
        self.assertEqual(elf.symbols[4][1][1:4], (4, 4, 1))
        self.assertEqual(elf.relocations(), helper.Elf(self.source).relocations())
        self.assertEqual(summary["data_bytes_verified"], 20)
        self.assertEqual(summary["relocations_verified"], 2)
        self.assertEqual(summary["duplicate_addend_words_normalized"], 1)
        self.assertEqual(summary["literal_labels_sized"], 2)
        self.assertNotEqual(output, self.target)
        self.assertEqual(self.source, fixture(True))
        self.assertEqual(self.target, fixture(False))

    def test_zero_in_place_addend_is_already_normalized(self):
        source = patch(self.source, section_offset(self.source, ".data") + 8, ">I", 0)
        _, summary = helper.comparison_copy(source, self.target)
        self.assertEqual(summary["duplicate_addend_words_normalized"], 0)

    def test_named_source_strings_need_no_literal_metadata_changes(self):
        source = bytearray(self.source)
        elf = helper.Elf(self.source)
        strings = elf.payload(elf.sections[elf.table_index][6])
        table = section_offset(self.source, ".symtab")
        for index, name in ((3, b'target_first\0'), (4, b'target_second\0')):
            struct.pack_into('>I', source, table + index * 16, strings.index(name))
            struct.pack_into('>I', source, table + index * 16 + 8, 4)
            source[table + index * 16 + 12] = 1
        output, summary = helper.comparison_copy(bytes(source), self.target)
        self.assertEqual(summary['literal_labels_sized'], 0)
        self.assertEqual(summary['named_literal_objects_verified'], 2)
        self.assertEqual(helper.Elf(output).payload(elf.table_index), bytes(source)[table:table + 96])
        bad = patch(bytes(source), table + 3 * 16 + 8, '>I', 3)
        with self.assertRaisesRegex(ValueError, 'terminated source string'):
            helper.comparison_copy(bad, self.target)

    def test_different_data_value_is_not_hidden(self):
        source = patch(self.source, section_offset(self.source, ".data"), ">I", 0x01020305)
        with self.assertRaisesRegex(ValueError, "Non-relocation bytes differ"):
            helper.comparison_copy(source, self.target)

    def test_different_literal_byte_is_not_hidden(self):
        source = patch(self.source, section_offset(self.source, ".rodata"), ">B", ord("O"))
        with self.assertRaisesRegex(ValueError, "Non-relocation bytes differ"):
            helper.comparison_copy(source, self.target)

    def test_wrong_addend_is_not_hidden(self):
        source = patch(self.source, section_offset(self.source, ".rela.data") + 20, ">i", 5)
        with self.assertRaisesRegex(ValueError, "relocation semantics differ"):
            helper.comparison_copy(source, self.target)

    def test_wrong_symbol_target_is_not_hidden(self):
        source = patch(self.source, section_offset(self.source, ".rela.data") + 16, ">I", 1 << 8 | 1)
        with self.assertRaisesRegex(ValueError, "relocation semantics differ"):
            helper.comparison_copy(source, self.target)

    def test_nonduplicate_relocated_word_rejected(self):
        source = patch(self.source, section_offset(self.source, ".data") + 8, ">I", 7)
        with self.assertRaisesRegex(ValueError, "not its explicit addend"):
            helper.comparison_copy(source, self.target)

    def test_target_must_have_zero_relocation_words(self):
        target = patch(self.target, section_offset(self.target, ".data") + 8, ">I", 4)
        with self.assertRaisesRegex(ValueError, "Target relocation word is not normalized"):
            helper.comparison_copy(self.source, target)

    def test_duplicate_relocation_site_rejected(self):
        source = patch(self.source, section_offset(self.source, ".rela.data") + 12, ">I", 4)
        with self.assertRaisesRegex(ValueError, "Duplicate relocation site"):
            helper.comparison_copy(source, self.target)

    def test_non_addr32_relocations_rejected(self):
        source = patch(self.source, section_offset(self.source, ".rela.data") + 4, ">I", 2 << 8 | 4)
        with self.assertRaisesRegex(ValueError, "R_PPC_ADDR32"):
            helper.comparison_copy(source, self.target)

    def test_implicit_relocations_rejected(self):
        source = patch(self.source, header_offset(self.source, ".rela.data", 1), ">I", 9)
        with self.assertRaisesRegex(ValueError, "Implicit REL"):
            helper.comparison_copy(source, self.target)

    def test_section_layout_change_rejected(self):
        source = patch(self.source, header_offset(self.source, ".rodata", 2), ">I", 3)
        with self.assertRaisesRegex(ValueError, "Allocated section layout differs"):
            helper.comparison_copy(source, self.target)

    def test_code_in_source_rejected(self):
        source = patch(self.source, header_offset(self.source, ".rodata", 2), ">I", 6)
        with self.assertRaisesRegex(ValueError, "only nonempty .data and .rodata"):
            helper.comparison_copy(source, self.target)

    def test_source_literal_metadata_must_be_compiler_local(self):
        source = patch(self.source, section_offset(self.source, ".symtab") + 3 * 16 + 8, ">I", 4)
        with self.assertRaisesRegex(ValueError, "Unexpected compiler-local literal metadata"):
            helper.comparison_copy(source, self.target)

    def test_pool_must_begin_with_a_literal_label(self):
        source = patch(self.source, section_offset(self.source, ".symtab") + 3 * 16 + 4, ">I", 1)
        with self.assertRaisesRegex(ValueError, "starting at zero"):
            helper.comparison_copy(source, self.target)

    def test_symbol_size_outside_section_rejected(self):
        source = patch(self.source, section_offset(self.source, ".symtab") + 5 * 16 + 8, ">I", 13)
        with self.assertRaisesRegex(ValueError, "Symbol extends beyond"):
            helper.comparison_copy(source, self.target)

    def test_bad_symbol_table_boundary_rejected(self):
        source = patch(self.source, header_offset(self.source, ".symtab", 7), ">I", 4)
        with self.assertRaisesRegex(ValueError, "sh_info"):
            helper.comparison_copy(source, self.target)

    def test_truncated_and_overlapping_objects_rejected(self):
        with self.assertRaisesRegex(ValueError, "beyond the file"):
            helper.comparison_copy(self.source[:-1], self.target)
        source = patch(self.source, header_offset(self.source, ".rodata", 4), ">I", 52)
        with self.assertRaisesRegex(ValueError, "Overlapping ELF"):
            helper.comparison_copy(source, self.target)

    def test_cli_keeps_inputs_and_refuses_in_place_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target, output = [Path(directory) / name for name in ("source.o", "target.o", "view.o")]
            source.write_bytes(self.source)
            target.write_bytes(self.target)
            command = [sys.executable, str(ROOT / "tools/prodg_comparison_object.py"),
                       "--source", str(source), "--target", str(target)]
            result = subprocess.run(command + ["--output", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), helper.comparison_copy(self.source, self.target)[0])
            self.assertEqual(source.read_bytes(), self.source)
            self.assertEqual(target.read_bytes(), self.target)
            for existing in (source, target):
                result = subprocess.run(command + ["--output", str(existing)], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("must not replace", result.stderr)


if __name__ == "__main__":
    unittest.main()
