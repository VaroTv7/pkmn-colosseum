#!/usr/bin/env python3
"""Exercise allowlisting, ABI decoding and pointer privacy with synthetic data."""

import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.runtime_data_diagnostics import (
    FILE_ADDRESS, RESTORE_ADDRESS, file_initializer, restore_initializer,
    runtime_structure,
)


def file_fixture():
    data = bytearray(0x140)
    relocations = []
    for index in range(4):
        start = index * 0x50
        struct.pack_into(">I", data, start, index)
        mode = 1 << 27 | 1 << 25 | 2 << 22
        struct.pack_into(">I", data, start + 4, mode)
        struct.pack_into(">I", data, start + 0x20, 0x100)
        relocations.append({"offset": start + 0x40, "type": 1,
                            "symbol": "__write_console", "addend": 0,
                            "target_section": None, "target_symbol_offset": 0})
    section = {"size": 0x140, "nobits": False,
               "symbols": [{"name": "__files", "offset": 0, "size": 0x140,
                            "type": 1, "binding": 1}],
               "relocations": relocations}
    return section, data


def restore_fixture():
    return {"size": 12, "nobits": False,
            "symbols": [{"name": "gTRKRestoreFlags", "offset": 0, "size": 9,
                         "type": 1, "binding": 1},
                        {"name": "gap_05_80313821_data", "offset": 9, "size": 3,
                         "type": 1, "binding": 1, "visibility": 2}],
            "relocations": []}, bytearray(12)


def report_unit(address, size, name="main/known_runtime"):
    return {"name": name, "sections": [{"name": ".data", "size": str(size),
             "metadata": {"virtual_address": str(address)}}]}


class RuntimeDataDiagnosticTests(unittest.TestCase):
    def test_decodes_fields_and_preserves_symbolic_pointer_identity(self):
        section, data = file_fixture()
        result = file_initializer(section, data)
        self.assertEqual(result["record_count"], 4)
        self.assertEqual(result["relocations_verified"], 4)
        self.assertEqual(result["records"][2]["handle"], 2)
        self.assertEqual(result["records"][2]["buffer_size"], 0x100)
        self.assertEqual(result["records"][2]["file_mode"], {
            "open_mode": 0, "io_mode": 1, "buffer_mode": 1, "file_kind": 2,
            "file_orientation": 0, "binary_io": False})
        pointer = result["records"][2]["pointers"]["write_fn"]
        self.assertEqual(pointer["symbol"], "__write_console")
        self.assertEqual(pointer["addend"], 0)
        self.assertIsNone(result["records"][2]["pointers"]["idle_fn"])
        # JSON has only the fixed ABI fields; there is no original byte buffer.
        self.assertNotIn("payload", json.dumps(result))

    def test_accepts_only_two_known_main_ranges(self):
        section, data = file_fixture()
        for address, name in ((FILE_ADDRESS + 4, "main/unknown"),
                              (FILE_ADDRESS, "common_rel/runtime")):
            self.assertIsNone(runtime_structure(report_unit(address, 0x140, name),
                                               {".data": section}, {".data": data}))
        self.assertEqual(runtime_structure(report_unit(FILE_ADDRESS, 0x140),
                         {".data": section}, {".data": data})["symbol"], "__files")

    def test_wrong_extent_or_owner_rejected(self):
        section, data = file_fixture()
        with self.assertRaises(ValueError):
            runtime_structure(report_unit(FILE_ADDRESS, 0x13C),
                              {".data": section}, {".data": data})
        section["symbols"][0]["name"] = "different_initializer"
        with self.assertRaises(ValueError):
            file_initializer(section, data)

    def test_nonzero_unknown_state_and_reserved_mode_bits_rejected(self):
        section, data = file_fixture()
        for offset in (7, 0x09, 0x0C, 0x11, 0x17):
            mutated = data[:]
            mutated[offset] |= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                file_initializer(section, mutated)

    def test_nonnull_pointer_without_relocation_rejected(self):
        section, data = file_fixture()
        struct.pack_into(">I", data, 0x1C, 0x81234567)
        with self.assertRaises(ValueError):
            file_initializer(section, data)

    def test_relocation_to_scalar_or_duplicate_site_rejected(self):
        section, data = file_fixture()
        invalid = copy.deepcopy(section)
        invalid["relocations"][0]["offset"] = 0x20
        with self.assertRaises(ValueError):
            file_initializer(invalid, data)
        invalid = copy.deepcopy(section)
        invalid["relocations"].append(dict(invalid["relocations"][0]))
        with self.assertRaises(ValueError):
            file_initializer(invalid, data)

    def test_restore_flags_are_boolean_and_padding_is_retained(self):
        section, data = restore_fixture()
        data[1] = 1
        result = runtime_structure(report_unit(RESTORE_ADDRESS, 12),
                                   {".data": section}, {".data": data})
        self.assertEqual(result["flags"], [False, True] + [False] * 7)
        self.assertEqual(result["size"] + result["padding_size"], 12)
        self.assertTrue(result["padding_zero"])

    def test_restore_rejects_nonboolean_values_padding_and_relocations(self):
        section, data = restore_fixture()
        for offset in (0, 8, 9, 11):
            mutated = data[:]
            mutated[offset] = 2
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                restore_initializer(section, mutated)
        section["relocations"] = [{"offset": 0}]
        with self.assertRaises(ValueError):
            restore_initializer(section, data)


if __name__ == "__main__":
    unittest.main()
