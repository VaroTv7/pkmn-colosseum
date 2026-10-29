#!/usr/bin/env python3
"""Exercise metadata views with synthetic ELF objects, never retail inputs."""

import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import source_object_metadata as helper


def fixture(*, source=True, anonymous=False, text=False, section=".data",
            symbol_alignment=4, extra_symbol=False, relocation="external", pool=False,
            local_name="@11"):
    names = ["", section] + ([".text"] if text else [])
    names += [".rela" + section, ".comment", ".symtab", ".strtab", ".shstrtab"]
    index = {name: i for i, name in enumerate(names)}
    strings = bytearray(b"\0")
    # name, offset, size, type/binding, visibility, section, MWCC alignment
    symbols = [("", 0, 0, 0, 0, 0, 0), ("", 0, 0, 3, 0, 1, 8 if source else 4),
               (local_name if anonymous else "head", 0, 4, 1 if anonymous else 0x11, 0, 1, symbol_alignment),
               ("pointer", 4, 4, 0x11, 0, 1, 4),
               ("source_padding" if source else "gap_00_80000008_" + section[1:], 8, 4, 0x11, 0 if source else 2, 1, 1),
               ("external", 0, 0, 0x10, 0, 0, 0)]
    if pool:
        symbols.insert(2, ("..." + section[1:] + ".0", 0, 0, 0, 0, 1, 8))
    if extra_symbol:
        symbols.append(("unmapped", 0, 4, 0x11, 0, 1, 4))
    table = bytearray()
    comment = bytearray(44)
    comment[:11] = b"CodeWarrior"
    comment[11], comment[16], comment[17], comment[20] = 8, 1, 2, 44
    for name, offset, size, info, visibility, shndx, required in symbols:
        at = len(strings) if name else 0
        if name:
            strings.extend(name.encode("ascii") + b"\0")
        table.extend(struct.pack(">IIIBBH", at, offset, size, info, visibility, shndx))
        comment.extend(struct.pack(">IBB2x", required, 0, 8 if shndx else 0))
    symbol_index = next(i for i, sym in enumerate(symbols) if sym[0] == "external")
    if relocation != "external":
        symbol_index = 1 if source else next(i for i, sym in enumerate(symbols) if sym[0] == "head")
    addend = 0
    zero = section in {".bss", ".sbss", ".sbss2"}
    payloads = {section: struct.pack(">3I", 0x01020304, 0, 0),
                ".rela" + section: b"" if zero else struct.pack(">IIi", 4, symbol_index << 8 | 1, addend),
                ".comment": bytes(comment), ".symtab": bytes(table), ".strtab": bytes(strings)}
    if text:
        payloads[".text"] = b"\x01\x02\x03\x04"
    shstrings = b"\0".join(name.encode() for name in names) + b"\0"
    payloads[".shstrtab"] = shstrings
    blob = bytearray(52)
    headers = [(0,) * 10]
    for name in names[1:]:
        kind, flags, link, info, alignment, entry = 1, 0, 0, 0, 1, 0
        if name == section:
            kind = 8 if zero else 1
            flags, alignment = (2 if section == ".rodata" else 3), (8 if source else 4)
        elif name == ".text":
            flags, alignment = 6, 4
        elif name.startswith(".rela"):
            kind, link, info, alignment, entry = 4, index[".symtab"], 1, 4, 12
        elif name == ".symtab":
            kind, link, info, alignment, entry = 2, index[".strtab"], next(i for i, sym in enumerate(symbols) if sym[3] >> 4), 4, 16
        elif name in (".strtab", ".shstrtab"):
            kind = 3
        blob.extend(bytes(-len(blob) % alignment))
        data = payloads[name]
        headers.append((shstrings.index(name.encode() + b"\0"), kind, flags, 0,
                        len(blob), len(data), link, info, alignment, entry))
        if kind != 8:
            blob.extend(data)
    blob.extend(bytes(-len(blob) % 4))
    shoff = len(blob)
    blob.extend(b"".join(struct.pack(">10I", *header) for header in headers))
    struct.pack_into(">16sHHIIIIIHHHHHH", blob, 0,
                     b"\x7fELF\x01\x02\x01" + bytes(9), 1, 20, 1, 0, 0, shoff,
                     0, 52, 0, 0, 40, len(headers), index[".shstrtab"])
    return bytes(blob)


def patch(blob, offset, fmt, value):
    output = bytearray(blob)
    struct.pack_into(fmt, output, offset, value)
    return bytes(output)


def section_offset(blob, name):
    elf = helper.Elf(blob)
    return elf.sections[elf.names.index(name)][4]


def section_field(blob, name, field):
    elf = helper.Elf(blob)
    return elf.header[6] + elf.names.index(name) * 40 + field * 4


def symbol_field(blob, index, field_offset):
    return section_offset(blob, ".symtab") + index * 16 + field_offset


class DataAlignmentViewTests(unittest.TestCase):
    def setUp(self):
        self.source, self.target = fixture(), fixture(source=False)

    def test_only_two_alignment_records_change(self):
        before_source, before_target = bytes(self.source), bytes(self.target)
        output, summary = helper.data_alignment(self.source, self.target, 4)
        expected = bytearray(self.source)
        struct.pack_into(">I", expected, section_field(self.source, ".data", 8), 4)
        struct.pack_into(">I", expected, section_offset(self.source, ".comment") + 44 + 8, 4)
        self.assertEqual(output, bytes(expected))
        self.assertEqual(self.source, before_source)
        self.assertEqual(self.target, before_target)
        self.assertEqual(summary["allocated_bytes_changed"], 0)
        self.assertEqual(summary["relocations_verified"], 1)
        self.assertEqual(summary["symbol_extents_verified"], 2)

    def test_equivalent_named_and_section_relative_relocations_pass(self):
        source, target = fixture(relocation="internal"), fixture(source=False, relocation="internal")
        output, _ = helper.data_alignment(source, target, 4)
        self.assertEqual(helper.Elf(output).data_relocations(), helper.Elf(source).data_relocations())
        self.assertEqual(helper.Elf(output).payload(2), helper.Elf(source).payload(2))

    def test_exact_compiler_pool_marker_adjusts_only_its_alignment(self):
        source = fixture(pool=True)
        output, summary = helper.data_alignment(source, self.target, 4)
        elf = helper.Elf(source)
        pool_index, _ = elf.unique_symbol("...data.0")
        expected = bytearray(source)
        struct.pack_into(">I", expected, section_field(source, ".data", 8), 4)
        for index in (1, pool_index):
            struct.pack_into(">I", expected, section_offset(source, ".comment") + 44 + index * 8, 4)
        self.assertEqual(output, bytes(expected))
        self.assertEqual(summary["section_pool_alignments_adjusted"], 1)
        self.assertEqual(elf.symbols, helper.Elf(output).symbols)
        with self.assertRaisesRegex(ValueError, "unsupported alignment"):
            helper.data_alignment(fixture(pool=True, symbol_alignment=8), self.target, 4)

    def test_untyped_marker_cannot_disguise_non_base_storage(self):
        source = fixture(pool=True)
        index, _ = helper.Elf(source).unique_symbol("...data.0")
        changed = patch(source, symbol_field(source, index, 4), ">I", 4)
        with self.assertRaises(ValueError):
            helper.data_alignment(changed, self.target, 4)

    def test_uncovered_zero_bytes_are_not_layout_evidence(self):
        source = patch(self.source, symbol_field(self.source, 2, 8), ">I", 3)
        target = patch(self.target, symbol_field(self.target, 2, 8), ">I", 3)
        source = patch(source, section_offset(source, ".data") + 3, ">B", 0)
        target = patch(target, section_offset(target, ".data") + 3, ">B", 0)
        with self.assertRaises(ValueError):
            helper.data_alignment(source, target, 4)

    def test_actual_required_eight_byte_alignment_rejects(self):
        with self.assertRaisesRegex(ValueError, "unsupported alignment"):
            helper.data_alignment(fixture(symbol_alignment=8), self.target, 4)

    def test_data_byte_and_relocation_differences_reject(self):
        mutations = [patch(self.source, section_offset(self.source, ".data"), ">B", 9),
                     patch(self.source, section_offset(self.source, ".rela.data") + 8, ">i", 1),
                     patch(self.source, section_offset(self.source, ".rela.data") + 4, ">I", 2 << 8 | 1)]
        for source in mutations:
            with self.subTest(source_sha256=hashlib.sha256(source).hexdigest()):
                with self.assertRaises(ValueError):
                    helper.data_alignment(source, self.target, 4)

    def test_wrong_symbol_offset_size_or_extra_storage_rejects(self):
        mutations = [patch(self.source, symbol_field(self.source, 2, 4), ">I", 1),
                     patch(self.source, symbol_field(self.source, 2, 8), ">I", 3),
                     fixture(extra_symbol=True)]
        for source in mutations:
            with self.assertRaises(ValueError):
                helper.data_alignment(source, self.target, 4)

    def test_extra_named_zero_storage_only_fits_independent_target_gap(self):
        helper.data_alignment(self.source, self.target, 4)
        outside = patch(self.source, symbol_field(self.source, 4, 4), ">I", 7)
        with self.assertRaisesRegex(ValueError, "Unexpected source storage"):
            helper.data_alignment(outside, self.target, 4)
        source = patch(self.source, section_offset(self.source, ".data") + 8, ">I", 1)
        target = patch(self.target, section_offset(self.target, ".data") + 8, ">I", 1)
        with self.assertRaisesRegex(ValueError, "zero-padding gap|Unexpected source storage"):
            helper.data_alignment(source, target, 4)

    def test_code_and_unsupported_section_or_requested_alignment_reject(self):
        for source, target, alignment in [
                (fixture(text=True), fixture(source=False, text=True), 4),
                (fixture(section=".sdata"), fixture(source=False, section=".sdata"), 4),
                (self.source, self.target, 1), (self.source, self.target, 8)]:
            with self.assertRaises(ValueError):
                helper.data_alignment(source, target, alignment)

    def test_wrong_section_flags_extents_and_native_alignment_reject(self):
        for field, value in [(2, 7), (5, 11), (8, 4)]:
            source = patch(self.source, section_field(self.source, ".data", field), ">I", value)
            with self.assertRaises(ValueError):
                helper.data_alignment(source, self.target, 4)
        target = patch(self.target, section_field(self.target, ".data", 8), ">I", 8)
        with self.assertRaises(ValueError):
            helper.data_alignment(self.source, target, 4)

    def test_unknown_compiler_metadata_rejects(self):
        comment = section_offset(self.source, ".comment")
        for offset, fmt, value in [(11, ">B", 1), (20, ">B", 0), (22, ">B", 1),
                                   (44 + 2 * 8 + 5, ">B", 7),
                                   (44 + 2 * 8 + 6, ">H", 1),
                                   (44 + 8, ">I", 4)]:
            source = patch(self.source, comment + offset, fmt, value)
            with self.assertRaises(ValueError):
                helper.data_alignment(source, self.target, 4)

    def test_malformed_relocations_reject(self):
        rela = section_offset(self.source, ".rela.data")
        mutations = [patch(self.source, rela, ">I", 3),
                     patch(self.source, rela + 4, ">I", 5 << 8 | 4),
                     patch(self.source, rela + 4, ">I", 255 << 8 | 1),
                     patch(self.source, section_field(self.source, ".rela.data", 1), ">I", 9)]
        for source in mutations:
            with self.assertRaises(ValueError):
                helper.data_alignment(source, self.target, 4)


class ComparisonNamesTests(unittest.TestCase):
    def setUp(self):
        self.source, self.target = fixture(anonymous=True, text=True), fixture(source=False, text=True)

    def test_function_local_compiler_name_preserves_native_identity(self):
        source = fixture(anonymous=True, local_name="zero$288", text=True)
        output, _ = helper.comparison_names(source, self.target, {"head": "zero$288"})
        before, after = helper.Elf(source), helper.Elf(output)
        self.assertEqual(before.unique_symbol("zero$288")[1][1:], after.unique_symbol("head")[1][1:])
        self.assertEqual(before.payload(1), after.payload(1))
        self.assertEqual(before.payload(2), after.payload(2))

    def test_names_view_preserves_every_non_name_record_and_source_payload(self):
        target = patch(self.target, section_offset(self.target, ".data"), ">I", 0x55667788)
        output, summary = helper.comparison_names(self.source, target, {"head": "@11"})
        before, after = helper.Elf(self.source), helper.Elf(output)
        self.assertEqual(after.symbols[2][0], "head")
        self.assertEqual(before.symbols[2][1][1:], after.symbols[2][1][1:])
        for name in (".data", ".text", ".rela.data", ".comment"):
            self.assertEqual(before.payload(before.names.index(name)), after.payload(after.names.index(name)))
        self.assertNotEqual(after.payload(1), helper.Elf(target).payload(1))
        self.assertEqual(summary["symbols_named"], 1)
        self.assertEqual(summary["allocated_bytes_changed"], 0)
        self.assertEqual(self.source, fixture(anonymous=True, text=True))

    def test_nobits_anonymous_names_preserve_zero_storage_metadata(self):
        for section in (".bss", ".sbss", ".sbss2"):
            source = fixture(anonymous=True, section=section)
            target = fixture(source=False, section=section)
            output, _ = helper.comparison_names(source, target, {"head": "@11"})
            before, after = helper.Elf(source), helper.Elf(output)
            self.assertEqual(after.symbols[2][0], "head")
            self.assertEqual(before.sections[1], after.sections[1])
            self.assertEqual(after.sections[1][1], 8)
            self.assertEqual(after.sections[1][5], 12)
            for (_, a), (_, b) in zip(before.symbols, after.symbols):
                self.assertEqual(a[1:], b[1:])

    def test_named_and_duplicate_or_missing_mappings_reject(self):
        for mappings in [{}, {"head": "pointer"}, {"head": "@99"},
                         {"head": "@11", "pointer": "@11"}, {"missing": "@11"},
                         {"pointer": "@11"}]:
            with self.assertRaises(ValueError):
                helper.comparison_names(self.source, self.target, mappings)

    def test_wrong_size_binding_type_or_section_rejects(self):
        mutations = [patch(self.source, symbol_field(self.source, 2, 8), ">I", 3),
                     patch(self.source, symbol_field(self.source, 2, 12), ">B", 2),
                     patch(self.source, symbol_field(self.source, 2, 14), ">H", 2)]
        for source in mutations:
            with self.assertRaises(ValueError):
                helper.comparison_names(source, self.target, {"head": "@11"})
        with self.assertRaises(ValueError):
            helper.comparison_names(fixture(anonymous=True, section=".sdata2"),
                                    fixture(source=False), {"head": "@11"})


class CommandLinePreservationTests(unittest.TestCase):
    def test_native_source_target_and_failed_output_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, target, output = [base / name for name in ("source.o", "target.o", "link.o")]
            source.write_bytes(fixture()); target.write_bytes(fixture(source=False))
            command = [sys.executable, str(ROOT / "tools/source_object_metadata.py"), "align",
                       "--source", str(source), "--target", str(target), "--alignment", "4", "--output"]
            result = subprocess.run(command + [str(output)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertEqual(source.read_bytes(), fixture())
            self.assertEqual(target.read_bytes(), fixture(source=False))
            for destination in (source, target):
                result = subprocess.run(command + [str(destination)], capture_output=True)
                self.assertNotEqual(result.returncode, 0)
            output.write_bytes(b"keep existing output")
            target.write_bytes(patch(fixture(source=False), section_offset(fixture(source=False), ".data"), ">B", 9))
            result = subprocess.run(command + [str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), b"keep existing output")
            self.assertEqual(source.read_bytes(), fixture())


if __name__ == "__main__":
    unittest.main()
