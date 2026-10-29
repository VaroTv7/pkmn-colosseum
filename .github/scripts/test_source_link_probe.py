#!/usr/bin/env python3
"""Synthetic checks for bounded link diagnostics; no original objects or payloads."""
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import probe_source_data_link as probe
from tools.source_data_aliases import comment_records, create_views
from tools.source_object_metadata import Elf
from test_source_data_aliases import GROUPS, fixture, symbol_patch


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


class AliasCandidateTests(unittest.TestCase):
    def setUp(self):
        self.link, _, _ = create_views(fixture(), fixture(False), GROUPS)

    def test_sorted_globals_preserve_native_bounds_and_paired_metadata(self):
        candidate, metadata = probe.sort_alias_globals(self.link)
        before, after = Elf(self.link), Elf(candidate)
        boundary = before.sections[before.symtab][7]
        self.assertEqual(after.symbols[:boundary], before.symbols[:boundary])
        self.assertEqual([name for name, _ in after.symbols[boundary:]],
                         ["flags", "status", "mode", "pointer", "external"])
        self.assertEqual(after.unique_symbol("flags")[1][2], 8)
        self.assertEqual(after.unique_symbol("status")[1][1:4], (3, 0, 0x10))
        self.assertEqual(after.unique_symbol("mode")[1][1:4], (5, 0, 0x10))
        old_comment, new_comment = comment_records(before)[1], comment_records(after)[1]
        for old_index, (name, _) in enumerate(before.symbols):
            index = old_index if old_index < boundary else after.unique_symbol(name)[0]
            self.assertEqual(old_comment[44 + 8*old_index:52 + 8*old_index],
                             new_comment[44 + 8*index:52 + 8*index])
        self.assertEqual(before.sections, after.sections)
        self.assertEqual(before.data_relocations(), after.data_relocations())
        self.assertEqual(metadata["relocation_indices_remapped"], 1)
        self.assertNotEqual(before.payload(2), after.payload(2))
        validation = probe.validate_alias_candidate(self.link, candidate, GROUPS)
        self.assertEqual(validation["allocated_bytes"], 12)
        self.assertEqual(validation["complete_array_hosts"], 1)
        self.assertEqual(validation["zero_size_interior_labels"], 2)
        self.assertEqual(validation["relocation_count"], 1)

    def test_equal_address_host_precedes_zero_size_label(self):
        # The ordering contract also covers an equal-address label; this
        # synthetic case is deliberately separate from registered interiors.
        source = symbol_patch(self.link, "status", 4, ">I", 0)
        candidate, _ = probe.sort_alias_globals(source)
        elf = Elf(candidate)
        self.assertLess(elf.unique_symbol("flags")[0], elf.unique_symbol("status")[0])

    def test_candidate_storage_or_alignment_changes_rejected(self):
        for field in ("byte", "alignment"):
            candidate = bytearray(self.link)
            elf = Elf(candidate)
            if field == "byte":
                candidate[elf.sections[1][4]] ^= 1
            else:
                struct.pack_into(">I", candidate, elf.header[6] + 40 + 32, 4)
            with self.subTest(field=field), self.assertRaises(probe.ProbeError):
                probe.validate_alias_candidate(self.link, bytes(candidate), GROUPS)

    def test_candidate_host_or_label_extent_changes_rejected(self):
        for name, size in (("flags", 7), ("status", 1)):
            candidate = symbol_patch(self.link, name, 8, ">I", size)
            with self.subTest(name=name), self.assertRaisesRegex(
                    probe.ProbeError, "symbol_identity_or_bounds"):
                probe.validate_alias_candidate(self.link, candidate, GROUPS)

    def test_candidate_relocation_semantics_change_rejected(self):
        candidate = bytearray(self.link)
        elf = Elf(candidate)
        struct.pack_into(">i", candidate, elf.sections[2][4] + 8, 13)
        with self.assertRaisesRegex(probe.ProbeError, "relocation_semantics"):
            probe.validate_alias_candidate(self.link, bytes(candidate), GROUPS)

    def test_full_array_and_alias_registration_bounds_are_checked(self):
        for field in ("host", "alias"):
            groups = copy.deepcopy(GROUPS)
            if field == "host":
                groups[0]["size"] = 7
            else:
                groups[0]["aliases"][0]["offset"] = 8
            with self.subTest(field=field), self.assertRaises(probe.ProbeError):
                probe.validate_alias_candidate(self.link, self.link, groups)

    def test_target_control_validates_data_without_claiming_native_bounds(self):
        result = probe.unchanged_data(Elf(self.link), Elf(fixture(False)))
        self.assertEqual(result["allocated_bytes"], 12)
        self.assertNotIn("complete_array_hosts", result)
        with self.assertRaisesRegex(probe.ProbeError, "symbol_identity_or_bounds"):
            probe.validate_alias_candidate(self.link, fixture(False), GROUPS)


if __name__ == "__main__":
    unittest.main()
