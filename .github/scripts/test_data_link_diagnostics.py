#!/usr/bin/env python3
"""Ensure address diagnostics never credit fallback or export payloads."""

import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.data_link_diagnostics import diagnose, linked_symbols, map_symbols


def executable_fixture():
    names = b"\0shifted\0local_80001004\0"
    payload = b"PRIVATE_GAME_BYTES"
    symbols = bytes(16) + struct.pack(">IIIBBH", 1, 0x80001004, 4, 0x11, 0, 1) \
        + struct.pack(">IIIBBH", 9, 0x80001004, 4, 0x11, 0, 1)
    blob = bytearray(52)
    records = [(0,) * 10]
    for kind, value, address, link, info, width in (
            (1, payload, 0x80001000, 0, 0, 0),
            (3, names, 0, 0, 0, 0), (2, symbols, 0, 2, 1, 16)):
        offset = len(blob)
        blob += value
        records.append((0, kind, 3 if kind == 1 else 0, address, offset,
                        len(value), link, info, 4, width))
    at = len(blob)
    for record in records:
        blob += struct.pack(">10I", *record)
    struct.pack_into(">16sHHIIIIIHHHHHH", blob, 0,
                     b"\x7fELF\x01\x02\x01" + bytes(9), 2, 20, 1, 0, 0, at,
                     0, 52, 0, 0, 40, len(records), 0)
    return blob


class DataLinkDiagnosticTests(unittest.TestCase):
    def test_address_shift_alias_missing_and_incomplete_selection(self):
        def unit(name, start, complete):
            return {"name": "main/" + name,
                    "measures": {"total_data": "12", "total_code": "0",
                                 "complete_data": "12" if complete else "0"},
                    "metadata": {"source_path": "src/" + name + ".c", "complete": complete},
                    "sections": [{"name": ".data", "size": "12",
                                  "metadata": {"virtual_address": str(start)}}]}
        expected = map_symbols("\n".join([
            "shifted = .data:0x80001000; // type:object size:0x4",
            "local = .data:0x80001004; // type:object size:0x4 scope:local",
            "stripped = .data:0x80001008; // type:object size:0x4",
            "candidate = .data:0x80002000; // type:object size:0x4",
        ]))
        result = diagnose({"units": [unit("linked", 0x80001000, True),
                                     unit("candidate", 0x80002000, False)]},
                          expected, linked_symbols(executable_fixture()))
        self.assertEqual(result["skipped_incomplete_units"], ["main/candidate"])
        self.assertEqual([r["status"] for r in result["units"][0]["symbols"]],
                         ["address_mismatch", "match", "missing"])
        self.assertEqual(result["units"][0]["symbols"][1]["linked_name"], "local_80001004")

    def test_payload_is_not_returned_and_truncated_elf_is_rejected(self):
        blob = executable_fixture()
        result = linked_symbols(blob)
        self.assertNotIn("PRIVATE_GAME_BYTES", json.dumps(result))
        self.assertEqual(set(result), {"shifted", "local_80001004"})
        with self.assertRaises(ValueError):
            linked_symbols(blob[:-1])
        struct.pack_into(">H", blob, 16, 1)
        with self.assertRaises(ValueError):
            linked_symbols(blob)


if __name__ == "__main__":
    unittest.main()
