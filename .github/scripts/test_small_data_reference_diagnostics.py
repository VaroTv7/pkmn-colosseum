#!/usr/bin/env python3
"""Synthetic checks for the five-site metadata-only small-data diagnostic."""

import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "small_data_reference_diagnostics", ROOT / "tools/small_data_reference_diagnostics.py")
DIAG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIAG)


def fixture(schema):
    objects = {}
    for unit, (size, name, offset, extent) in DIAG.SCRIPT_OWNERS.items():
        data = bytearray(size)
        data[:19] = b"private-script-data"
        section = {"size": size, "nobits": False,
                   "symbols": [{"name": name, "offset": offset, "size": extent,
                                "type": 1, "binding": 1}], "relocations": []}
        objects[unit] = ({".data": section}, {".data": data})
    indices = {name: index for index, name in schema["dispatch"].items()}
    for unit, relative, operand, extent in DIAG.SITES:
        public, private = objects[unit]
        pointer = DIAG.SCRIPT_OWNERS[unit][2] + relative
        start = pointer - 16
        name = "WS_STATUS_SET16" if extent == 2 else "WS_STATUS_SET32"
        private[".data"][start] = indices[name]
        private[".data"][start + 1] = 7
        struct.pack_into(">H", private[".data"], start + 10, 0x3B)
        public[".data"]["relocations"].append(
            {"offset": pointer, "type": 1, "symbol": operand, "addend": 0,
             "target_section": None, "target_symbol_offset": 0})
    return objects


class ReferenceSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = DIAG.source_schema(ROOT)

    def test_output_is_limited_to_five_typed_roles_and_inputs_are_unchanged(self):
        objects = fixture(self.schema)
        before = copy.deepcopy(objects)
        result = DIAG.diagnose(objects, self.schema)
        self.assertEqual(objects, before)
        self.assertEqual(result["status"], "verified")
        self.assertFalse(result["payload_bytes_included"])
        self.assertEqual(len(result["references"]), 5)
        allowed = {"script_symbol", "reference_offset", "operand_symbol", "handler_symbol",
                   "status_kind", "status_family", "status_field_id", "operand_width_bits",
                   "operand_access"}
        for row in result["references"]:
            self.assertEqual(set(row), allowed)
            self.assertEqual(row["status_field_id"], 0x3B)
            self.assertEqual(row["status_family"], "fight_floor")
        rendered = json.dumps(result)
        self.assertNotIn("private-script-data", rendered)
        self.assertNotIn("opcode", rendered)
        self.assertNotIn("payload", rendered.replace("payload_bytes_included", ""))

    def test_handler_read_write_direction_comes_from_existing_source(self):
        objects = fixture(self.schema)
        unit, relative, _, _ = DIAG.SITES[0]
        start = DIAG.SCRIPT_OWNERS[unit][2] + relative - 16
        index = next(i for i, name in self.schema["dispatch"].items() if name == "WS_STATUS_GET16")
        objects[unit][1][".data"][start] = index
        row = DIAG.diagnose(objects, self.schema)["references"][0]
        self.assertEqual(row["operand_access"], "write")
        self.assertEqual(row["operand_width_bits"], 16)

    def test_unknown_handler_family_field_and_oversized_operand_are_rejected(self):
        unit, relative, _, _ = DIAG.SITES[0]
        start = DIAG.SCRIPT_OWNERS[unit][2] + relative - 16
        wide = next(i for i, name in self.schema["dispatch"].items() if name == "WS_STATUS_SET32")
        unknown = next(i for i in range(256) if i not in self.schema["dispatch"])
        for offset, data in [(start, bytes([unknown])), (start, bytes([wide])),
                             (start + 1, b"\xff"), (start + 1, b"\x02"),
                             (start + 10, b"\xff\xff")]:
            with self.subTest(offset=offset, data=data):
                objects = fixture(self.schema)
                objects[unit][1][".data"][offset:offset + len(data)] = data
                with self.assertRaises(ValueError):
                    DIAG.diagnose(objects, self.schema)

    def test_operand_relocation_identity_type_addend_and_normalization_are_required(self):
        unit = DIAG.SITES[0][0]
        for key, value in [("symbol", "unrelated_name"), ("type", 2), ("addend", 1),
                           ("target_section", ".data"), ("target_symbol_offset", 4)]:
            with self.subTest(key=key):
                objects = fixture(self.schema)
                objects[unit][0][".data"]["relocations"][0][key] = value
                with self.assertRaises(ValueError):
                    DIAG.diagnose(objects, self.schema)
        for mode in ("missing", "duplicate", "in_place"):
            with self.subTest(mode=mode):
                objects = fixture(self.schema)
                relocs = objects[unit][0][".data"]["relocations"]
                if mode == "missing":
                    del relocs[0]
                elif mode == "duplicate":
                    relocs.append(dict(relocs[0]))
                else:
                    objects[unit][1][".data"][relocs[0]["offset"]] = 1
                with self.assertRaises(ValueError):
                    DIAG.diagnose(objects, self.schema)

    def test_opaque_context_pointers_and_relocations_over_scalar_fields_are_rejected(self):
        unit, relative, _, _ = DIAG.SITES[0]
        start = DIAG.SCRIPT_OWNERS[unit][2] + relative - 16
        for mode in ("pointer", "field_relocation", "overlapping_relocation"):
            objects = fixture(self.schema)
            relocs = objects[unit][0][".data"]["relocations"]
            if mode == "pointer":
                objects[unit][1][".data"][start + 2:start + 6] = b"\x80\x00\x00\x01"
            else:
                relocs.append(dict(relocs[0], offset=start + 10 if mode == "field_relocation" else start - 1))
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                DIAG.diagnose(objects, self.schema)

    def test_unrelated_reference_is_not_exported(self):
        objects = fixture(self.schema)
        unit = DIAG.SITES[0][0]
        objects[unit][0][".data"]["relocations"].append(
            {"offset": 40, "type": 1, "symbol": "private_unrelated_symbol", "addend": 0})
        self.assertNotIn("private_unrelated_symbol", json.dumps(DIAG.diagnose(objects, self.schema)))

    def test_wrong_section_symbol_extent_and_object_scope_are_rejected(self):
        unit = DIAG.SITES[0][0]
        for mode in ("size", "nobits", "symbol_offset", "symbol_size", "symbol_type",
                     "symbol_binding", "extra_section", "extra_object", "truncated"):
            objects = fixture(self.schema)
            public, private = objects[unit]
            section = public[".data"]
            if mode == "size":
                section["size"] -= 1
            elif mode == "nobits":
                section["nobits"] = True
            elif mode.startswith("symbol_"):
                field = mode.removeprefix("symbol_")
                section["symbols"][0][field] += 1
            elif mode == "extra_section":
                public[".sdata"] = dict(section)
            elif mode == "extra_object":
                objects["unknown"] = objects[unit]
            else:
                private[".data"] = private[".data"][:-1]
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                DIAG.diagnose(objects, self.schema)

    def test_source_schema_drift_fails_closed(self):
        original = Path.read_text
        def changed(path, *args, **kwargs):
            text = original(path, *args, **kwargs)
            if path.name == "fight_range_80211A00.c":
                return text.replace("pVar9 = *(u16 **)(iVar1 + 0x10);",
                                    "pVar9 = *(u32 **)(iVar1 + 0x10);")
            return text
        with patch.object(Path, "read_text", changed), self.assertRaises(ValueError):
            DIAG.source_schema(ROOT)

    def test_cli_does_not_clobber_an_input_when_later_input_validation_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            native = root / "original.o"
            native.write_bytes(b"synthetic original must survive")
            config = root / "objdiff.json"
            config.write_text(json.dumps({"units": [{"name": next(iter(DIAG.SCRIPT_OWNERS)),
                                                     "target_path": "original.o"}]}))
            for output in (native, config):
                before = output.read_bytes()
                result = subprocess.run([sys.executable, str(ROOT / "tools/small_data_reference_diagnostics.py"),
                                         "--config", str(config), "--output", str(output)],
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(output.read_bytes(), before)
                self.assertNotIn("synthetic original must survive", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
