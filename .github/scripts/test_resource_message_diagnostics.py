#!/usr/bin/env python3
"""Synthetic checks for bounded, source-owned message reuse diagnostics."""

import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.resource_message_diagnostics import (
    SourceRegion, analyze_message_group, analyze_script_bank, eligible_source_regions,
    resource_range_integrity,
)


def message_group(entries, payload):
    return (struct.pack(">HBBHHII", 3, 0, 1, len(entries), 0, 0, 0)
            + b"".join(struct.pack(">II", *entry) for entry in entries) + payload)


def script_bank():
    return (struct.pack(">HHHHHBBIiI", 7, 0x1234, 3, 2, 0x5678, 0, 0, 64, 56, 0)
            + struct.pack(">III", 36, 44, 36)
            + b"FUNC_ONE" + b"SECOND_FUNC!" + b"GLOBAL!!"
            + struct.pack(">II", 36, 44))


class ResourceMessageDiagnosticTests(unittest.TestCase):
    def test_complete_resource_hash_includes_original_fallback_storage(self):
        original = b"HEADER_INDEX_PRIVATE_STORAGE"
        result = resource_range_integrity(original, original, 0, len(original))
        self.assertTrue(result["bytes_equal"])
        changed = original[:-1] + b"!"
        self.assertTrue(resource_range_integrity(original, changed, 0, 12)["bytes_equal"])
        self.assertFalse(resource_range_integrity(original, changed, 0, len(original))["bytes_equal"])
        self.assertNotIn("PRIVATE_STORAGE", json.dumps(result))
        for start, end in ((-1, 2), (0, len(original) + 1), (3, 3)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                resource_range_integrity(original, original, start, end)

    def test_script_metadata_bounds_and_hashes_do_not_expose_instructions(self):
        regions = [SourceRegion("main/shared", "src/shared.c", ".data", 0x80200000,
                                b"PREFIXFUNC_ONE")]
        result = analyze_script_bank(script_bank(), regions, 0x89CFC)
        self.assertEqual(result["resource_type"], "gs_vm_script_bank")
        self.assertEqual(result["function_offsets"], [36, 44, 36])
        self.assertEqual(result["relocation_sites"], [36, 44])
        self.assertEqual(result["structural_bytes"], 44)
        self.assertEqual(result["non_table_storage_bytes"], 28)
        self.assertEqual(result["reusable_storage_bytes"], 8)
        self.assertEqual(result["unique_function_offsets"], 2)
        self.assertEqual(result["intervals"][2]["function_indices"], [0, 2])
        serialized = json.dumps(result)
        for private in (b"FUNC_ONE", b"SECOND_FUNC!", b"GLOBAL!!"):
            self.assertNotIn(private.decode(), serialized)
            self.assertNotIn(private.hex(), serialized)
        invalid = [script_bank()[:23]]
        for offset, fmt, value in ((4, ">H", 0xFFFF), (24, ">I", 72),
                                   (12, ">I", 70), (64, ">I", 70),
                                   (16, ">i", -1), (68, ">I", 36)):
            changed = bytearray(script_bank())
            struct.pack_into(fmt, changed, offset, value)
            invalid.append(changed)
        for number, data in enumerate(invalid):
            with self.subTest(number=number), self.assertRaises(ValueError):
                analyze_script_bank(data, [], 0x89CFC)

    def test_offset_metadata_and_source_locations_do_not_expose_text(self):
        first, second = b"PRIVATE_SYNTHETIC_TEXT_1", b"PRIVATE_SYNTHETIC_TEXT_2"
        start = 16 + 3 * 8
        group = message_group([(5, start), (6, start), (9, start + len(first))], first + second)
        regions = [SourceRegion("main/shared", "src/shared.c", ".data", 0x80200000,
                                b"PREFIX" + first + b"OTHER")]
        result = analyze_message_group(group, regions, 0x58044)
        self.assertEqual((result["group_id"], result["font_id"], result["entry_count"]), (3, 1, 3))
        self.assertEqual(result["unique_storage_intervals"], 2)
        self.assertEqual(result["reusable_storage_bytes"], len(first))
        self.assertEqual(result["entries_with_source_locations"], 2)
        self.assertEqual(result["entries"][0]["source_locations"], [{
            "unit": "main/shared", "source_path": "src/shared.c", "section": ".data",
            "dol_address": 0x80200006, "offset_in_source_section": 6,
        }])
        self.assertEqual(result["entries"][2]["source_locations"], [])
        serialized = json.dumps(result)
        for payload in (first, second):
            self.assertNotIn(payload.decode(), serialized)
            self.assertNotIn(payload.hex(), serialized)
        repeated = [SourceRegion("main/repeated", "src/repeated.c", ".data", 0x80200000,
                                 first * 3)]
        capped = analyze_message_group(message_group([(1, 24)], first), repeated, 0,
                                       max_matches=2)
        self.assertEqual(len(capped["entries"][0]["source_locations"]), 2)
        self.assertTrue(capped["entries"][0]["locations_truncated"])
        self.assertEqual(capped["reusable_storage_bytes"], len(first))

    def test_truncated_tables_bad_offsets_and_unordered_keys_fail(self):
        invalid = [b"\0" * 15,
                   message_group([(1, 24)], b"AB")[:20],
                   message_group([(1, 23)], b"AB"),
                   message_group([(1, 26)], b"AB"),
                   message_group([(0x100000, 24)], b"AB"),
                   message_group([(2, 32), (1, 34)], b"ABCD"),
                   message_group([(1, 32), (2, 33)], b"ABCD")]
        for number, data in enumerate(invalid):
            with self.subTest(number=number), self.assertRaises(ValueError):
                analyze_message_group(data, [], 0)

    def test_only_tracked_exact_linked_initialized_source_regions_are_searched(self):
        def unit(name, source, address, *, matched=4, linked=4, section=".data"):
            return {"name": name, "metadata": {"source_path": source},
                    "measures": {"total_data": "4", "matched_data": str(matched),
                                 "complete_data": str(linked)},
                    "sections": [{"name": section, "size": "4",
                                  "metadata": {"virtual_address": str(address)}}]}
        base = 0x80200000
        report = {"units": [unit("main/exact", "src/exact.c", base),
                            unit("main/untracked", "src/untracked.c", base + 4),
                            unit("main/unmatched", "src/exact.c", base + 8, matched=0),
                            unit("main/fallback", "src/exact.c", base + 12, linked=0),
                            unit("common_rel/exact", "src/exact.c", base + 16),
                            unit("main/bss", "src/exact.c", base + 20, section=".bss")]}
        regions = eligible_source_regions(report, [(base, b"ABC" * 8)], {"src/exact.c"})
        self.assertEqual(len(regions), 1)
        self.assertEqual(regions[0].unit, "main/exact")
        self.assertEqual(regions[0].data, b"ABCA")
        report["units"] = [unit("main/invalid", "src/exact.c", base + 22)]
        with self.assertRaises(ValueError):
            eligible_source_regions(report, [(base, b"A" * 24)], {"src/exact.c"})


if __name__ == "__main__":
    unittest.main()
