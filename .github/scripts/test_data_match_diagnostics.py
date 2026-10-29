#!/usr/bin/env python3
"""Ensure publicly uploadable data diagnostics omit private object payloads."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.data_match_diagnostics import (
    comparisons, elf_metadata, resource_reuse_checks, sanitized_diff,
    selected_units, source_alignment_at_original_address,
)


def synthetic_elf(data=b"PRIVATE_OBJECT_CONTENT", *, nobits=False,
                  symbol_size=None, relocation_offset=None):
    """A small PowerPC fixture containing no retail bytes."""
    section_name = ".bss" if nobits else ".data"
    names = ["", ".shstrtab", ".strtab", ".symtab", section_name, ".rela" + section_name]
    strings = b""
    name_offsets = []
    for name in names:
        name_offsets.append(len(strings))
        strings += name.encode() + b"\0"
    symbols = b"\0" * 16 + struct.pack(
        ">IIIBBH", 1, 0, len(data) if symbol_size is None else symbol_size, 0x11, 0, 4)
    relocations = (b"" if relocation_offset is None else
                   struct.pack(">IIi", relocation_offset, 1 << 8 | 1, 0))
    values = [b"", strings, b"\0value\0", symbols, b"" if nobits else data, relocations]
    blob = bytearray(52)
    records = [(0,) * 10]
    for index in range(1, len(names)):
        blob += b"\0" * (-len(blob) % 4)
        offset = len(blob)
        blob += values[index]
        section_type = {1: 3, 2: 3, 3: 2, 4: 8 if nobits else 1, 5: 4}[index]
        size = len(data) if index == 4 else len(values[index])
        link = 2 if index == 3 else 3 if index == 5 else 0
        info = 1 if index == 3 else 4 if index == 5 else 0
        entry_size = 16 if index == 3 else 12 if index == 5 else 0
        records.append((name_offsets[index], section_type, 3 if index == 4 else 0,
                        0, offset, size, link, info, 4, entry_size))
    blob += b"\0" * (-len(blob) % 4)
    section_offset = len(blob)
    for record in records:
        blob += struct.pack(">10I", *record)
    identity = b"\x7fELF\x01\x02\x01" + b"\0" * 9
    struct.pack_into(">16sHHIIIIIHHHHHH", blob, 0, identity, 1, 20, 1, 0,
                     0, section_offset, 0, 52, 0, 0, 40, len(records), 1)
    return blob


class DataMatchDiagnosticTests(unittest.TestCase):
    def test_exact_unlinked_and_explicit_promoted_units_are_included(self):
        def unit(name, *, linked, code=0, source=True, matched=True):
            return {"name": name, "measures": {
                "total_data": "8", "matched_data": "8" if matched else "0",
                "complete_data": "8" if linked else "0", "total_code": str(code),
            }, "metadata": {"source_path": "src/example.c"} if source else {},
                "sections": [{"name": ".bss", "size": "8"}]}
        report = {"units": [unit("main/unlinked", linked=False),
                            unit("main/promoted", linked=True),
                            unit("main/mixed", linked=True, code=4),
                            unit("main/original", linked=False, source=False, matched=False)]}
        names = lambda values: [value["name"] for value in values]
        self.assertEqual(names(selected_units(report)), ["main/unlinked"])
        self.assertEqual(names(selected_units(report, include_data_only=True)),
                         ["main/unlinked", "main/promoted"])
        self.assertEqual(names(selected_units(report, ["main/mixed", "main/mixed"])),
                         ["main/unlinked", "main/mixed"])
        self.assertEqual(names(selected_units(report, ["main/original"])),
                         ["main/unlinked", "main/original"])

    def test_unknown_or_dataless_explicit_units_fail(self):
        report = {"units": [{"name": "main/code", "measures": {"total_code": "4"}}]}
        for name in ("main/missing", "main/code"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                list(selected_units(report, [name]))

    def test_elf_payload_is_private_while_symbol_metadata_and_hashes_are_public(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.o"
            path.write_bytes(synthetic_elf())
            public, private = elf_metadata(path)
            self.assertNotIn("PRIVATE_OBJECT_CONTENT", json.dumps(public))
            self.assertEqual(private[".data"], b"PRIVATE_OBJECT_CONTENT")
            self.assertEqual(public[".data"]["symbols"][0]["name"], "value")
            self.assertEqual(len(public[".data"]["symbols"][0]["sha256"]), 64)

    def test_elf_rejects_symbol_and_relocation_overruns_and_truncated_tables(self):
        invalid = [synthetic_elf(b"1234", symbol_size=5),
                   synthetic_elf(b"1234", nobits=True, symbol_size=5),
                   synthetic_elf(b"1234", relocation_offset=1),
                   synthetic_elf()[:-1]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.o"
            for index, blob in enumerate(invalid):
                with self.subTest(index=index), self.assertRaises(ValueError):
                    path.write_bytes(blob)
                    elf_metadata(path)

    def test_objdiff_bytes_and_disassembly_never_enter_public_result(self):
        private = "PRIVATE_ORIGINAL_PAYLOAD"
        raw = {side: {
            "sections": [
                {"name": ".data", "size": "4", "match_percent": 50,
                 "data_diff": [{"data": private}], "reloc_diff": [{"data": private}]},
                {"name": ".text", "data_diff": [{"data": private}]},
            ],
            "symbols": [
                {"name": "value", "size": "4", "address": "0", "match_percent": 50,
                 "data_diff": [{"data": private}],
                 "instructions": [{"instruction": {"formatted": private}}]},
                {"name": "function", "size": "4", "instructions": [private]},
            ],
        } for side in ("left", "right")}
        metadata = {side: {".data": {"symbols": [{"name": "value"}]}}
                    for side in ("target", "source")}
        result = sanitized_diff(raw, metadata)
        serialized = json.dumps(result)
        for forbidden in (private, "data_diff", "instructions", "reloc_diff", ".text", "function"):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(result["target"]["symbols"], [
            {"name": "value", "size": 4, "offset": 0, "match_percent": 50},
        ])

    def test_objdiff_score_cannot_smuggle_payload_into_metadata(self):
        for invalid in ("PRIVATE_BYTES", {"data": "PRIVATE_BYTES"}, float("nan"), 101):
            raw = {"left": {"sections": [{"name": ".data", "match_percent": invalid}]}}
            with self.subTest(invalid=repr(invalid)), self.assertRaises(ValueError):
                sanitized_diff(raw, {})

    def test_bss_zero_content_does_not_hide_symbol_order_or_alignment_errors(self):
        left = {".bss": {"size": 8, "alignment": 4, "nobits": True,
                          "symbols": [{"name": "a", "offset": 0, "size": 4},
                                      {"name": "b", "offset": 4, "size": 4}]}}
        right = {".bss": {"size": 8, "alignment": 8, "nobits": True,
                           "symbols": [{"name": "a", "offset": 4, "size": 4},
                                       {"name": "b", "offset": 0, "size": 4}]}}
        result = comparisons(left, right, {".bss": None}, {".bss": None})[".bss"]
        self.assertTrue(result["same_size"])
        self.assertFalse(result["same_alignment"])
        self.assertFalse(result["symbol_offsets_and_sizes_equal"])
        self.assertFalse(result["shared_symbol_offsets_and_sizes_equal"])
        self.assertNotIn("raw_bytes_equal", result)
        unit = {"sections": [{"name": ".bss", "metadata": {"virtual_address": "2147483652"}}]}
        self.assertFalse(source_alignment_at_original_address(unit, right)[".bss"]["compatible"])

    def test_addend_storage_equality_stays_separate_from_raw_byte_equality(self):
        def metadata(symbol):
            return {".data": {"size": 4, "alignment": 4,
                              "relocations": [{"offset": 0, "type": 1,
                                               "symbol": symbol, "addend": 20}]}}
        left, right = metadata("left_target"), metadata("different_target")
        result = comparisons(left, right, {".data": b"\0" * 4},
                             {".data": struct.pack(">I", 20)})[".data"]
        self.assertFalse(result["raw_bytes_equal"])
        self.assertTrue(result["bytes_equal_with_addr32_words_zeroed"])
        self.assertNotIn("matched_data", result)
        self.assertNotIn("relocations_equal", result)

    def test_resource_reuse_checks_hash_bounded_ranges_and_detect_changes(self):
        candidates = [(0x8027A500, 0x2D2C, 0x42D60),
                      (0x802BD260, 0x45A94, 0x3A50),
                      (0x802C0CB0, 0x494E4, 0xEB60),
                      (0x802CF810, 0x647B4, 0x124E0)]
        dol_base = candidates[0][0]
        dol_data = bytearray(candidates[-1][0] + candidates[-1][2] - dol_base)
        rel_data = bytearray(0x8BCB4)
        for number, (address, offset, size) in enumerate(candidates, start=1):
            # Synthetic non-retail payload; each candidate has one DOL location.
            data = bytes([number]) + b"\xA5" * (size - 2) + bytes([number + 10])
            dol_data[address - dol_base:address - dol_base + size] = data
            rel_data[offset:offset + size] = data
        struct.pack_into(">HBBI", rel_data, 0x45A8C, 0xFFFF, 0, 0, 0)
        dol = bytearray(0x100) + dol_data
        struct.pack_into(">I", dol, 7 * 4, 0x100)
        struct.pack_into(">I", dol, 0x48 + 7 * 4, dol_base)
        struct.pack_into(">I", dol, 0x90 + 7 * 4, len(dol_data))
        rel = bytearray(0x100) + rel_data
        struct.pack_into(">II", rel, 0xC, 5, 0x50)
        struct.pack_into(">II", rel, 0x50 + 4 * 8, 0x100, len(rel_data))
        with tempfile.TemporaryDirectory() as directory:
            orig = Path(directory)
            (orig / "sys").mkdir()
            (orig / "files").mkdir()
            (orig / "sys/main.dol").write_bytes(dol)
            (orig / "files/common_rel.rel").write_bytes(rel)
            result = resource_reuse_checks(orig)
            self.assertEqual(len(result["spans"]), 8)
            self.assertTrue(all(row["equal"] for row in result["known_candidates"]))
            self.assertEqual(result["spans"][0]["dol_addresses"], [dol_base])
            self.assertNotIn("data", result)
            self.assertEqual(result["font_dummy_header"], {
                "rel_offset": 0x45A8C, "size": 8,
                "font_id": 0xFFFF, "width": 0, "height": 0, "next_offset": 0,
                "is_font_open_terminator": True,
                "matches_empty_font_terminator": True,
            })
            struct.pack_into(">HBBI", rel, 0x100 + 0x45A8C, 3, 22, 18, 0x1234)
            (orig / "files/common_rel.rel").write_bytes(rel)
            dol[0x100 + 20] ^= 1
            (orig / "sys/main.dol").write_bytes(dol)
            result = resource_reuse_checks(orig)
            self.assertFalse(result["known_candidates"][0]["equal"])
            self.assertEqual(result["spans"][0]["dol_addresses"], [])
            self.assertTrue(all(row["equal"] for row in result["known_candidates"][1:]))
            self.assertEqual(result["font_dummy_header"], {
                "rel_offset": 0x45A8C, "size": 8,
                "font_id": 3, "width": 22, "height": 18, "next_offset": 0x1234,
                "is_font_open_terminator": False,
                "matches_empty_font_terminator": False,
            })


if __name__ == "__main__":
    unittest.main()
