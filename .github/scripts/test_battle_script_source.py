#!/usr/bin/env python3
"""Synthetic wire-format tests and source-only interpreter/schema checks."""

import copy
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import battle_script_format as fmt
from tools.compile_battle_scripts import (
    CATALOG_FORMAT, FORMAT, Compiler, SourceError, Symbol, load_source,
    no_duplicate_keys, parse_symbols,
)
from tools.data_match_diagnostics import elf_metadata
from tools.small_data_reference_diagnostics import (
    _balanced_body, _field_cases, _without_comments, source_schema,
)


def address(symbol="state", encoding="absolute", **extra):
    return {"symbol": symbol, "encoding": encoding, **extra}


def branch(symbol="script_entry", entry="entry", encoding="absolute"):
    return {"script": symbol, "entry": entry, "encoding": encoding}


def fixture(body, size, name="script_entry", base=0x80000000, alignment=4):
    documents = {"synthetic.battle.json": {
        "format": FORMAT, "catalog": "catalog.json", "unit": "main/synthetic",
        "alignment": alignment, "programs": [{"symbol": name, "body": body}],
    }}
    catalog = {"format": CATALOG_FORMAT, "sources": list(documents), "external_entries": []}
    symbols = {name: Symbol(base, size, ".data"),
               "state": Symbol(0x80400000, 8, ".bss"),
               "other_state": Symbol(0x80400020, 8, ".sdata")}
    return documents, catalog, symbols


def c_function(path, name):
    text = _without_comments(path.read_text())
    definitions = list(re.finditer(r"(?m)^(?!asm\b)[A-Za-z_][^;{}]*\b" + re.escape(name)
                                  + r"\s*\([^;{}]*\)\s*\{", text))
    if len(definitions) != 1:
        raise AssertionError(f"ambiguous C handler: {name}")
    return _balanced_body(text, definitions[0].end() - 1)


class BattleSourceTests(unittest.TestCase):
    def compile(self, data):
        return Compiler(*data)

    def assemble(self, compiler):
        assembler = ROOT / "build/binutils/powerpc-eabi-as"
        if not assembler.is_file():
            self.skipTest("PowerPC assembler is not downloaded; source validation remains active")
        assembly, summary = compiler.assembly("synthetic.battle.json")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.s"
            obj = path.with_suffix(".o")
            path.write_text(assembly)
            subprocess.run([str(assembler), "-mgekko", "-o", str(obj), str(path)], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            metadata, payload = elf_metadata(obj)
        return metadata, payload, summary

    def test_real_unaligned_relocation_and_big_endian_wire_address(self):
        data = fixture([
            {"command": "set_byte", "destination": address(encoding="reloc"), "value": 7},
            {"command": "jump", "target": branch("script_tail")},
        ], 11)
        data[0]["synthetic.battle.json"]["programs"].append(
            {"symbol": "script_tail", "body": [{"command": "return_sequence"}]})
        data[2]["script_tail"] = Symbol(0x8000000B, 1, ".data")
        metadata, payload, summary = self.assemble(self.compile(data))
        self.assertEqual(payload[".data"], b"\x2e\0\0\0\0\x07\x28\x80\0\0\x0b\x3c")
        section = metadata[".data"]
        self.assertEqual((section["size"], section["alignment"]), (12, 4))
        self.assertEqual([(s["name"], s["offset"], s["size"], s["type"], s["binding"])
                          for s in section["symbols"]],
                         [("script_entry", 0, 11, 1, 1), ("script_tail", 11, 1, 1, 1)])
        self.assertEqual([(r["offset"], r["type"], r["symbol"], r["addend"])
                          for r in section["relocations"]], [(1, 1, "state", 0)])
        self.assertEqual(summary["size"], 12)
        self.assertTrue(all(s["size"] == 0 for n, s in metadata.items() if n != ".data"))

    def test_relocated_address_addend_is_native_rela(self):
        data = fixture([{"command": "set_byte", "destination": address(encoding="reloc", addend=3),
                         "value": 42}], 6)
        metadata, payload, _ = self.assemble(self.compile(data))
        self.assertEqual(payload[".data"], b"\x2e\0\0\0\0\x2a")
        relocation = metadata[".data"]["relocations"][0]
        self.assertEqual((relocation["offset"], relocation["symbol"], relocation["addend"]),
                         (1, "state", 3))

    def test_byte_and_halfword_fields_have_packed_widths(self):
        data = fixture([{"command": "jump_if_halfword", "comparison": "less",
                         "address": address(), "value": 0x1234, "target": branch()}], 12)
        _, payload, _ = self.assemble(self.compile(data))
        self.assertEqual(payload[".data"], b"\x2a\x03\x80\x40\0\0\x12\x34\x80\0\0\0")

    def test_message_legacy_stride_preserves_u32_lookahead(self):
        data = fixture([{"command": "print_selection_message_legacy", "message_prefix": 0x1234}], 3)
        data[0]["synthetic.battle.json"]["programs"].append({"symbol": "following_commands", "body": [
            {"command": "end_move"}, {"command": "end_sequence"}]})
        data[2]["following_commands"] = Symbol(0x80000003, 2, ".data")
        _, payload, _ = self.assemble(self.compile(data))
        self.assertEqual(payload[".data"], b"\x11\x12\x34\x3d\x3e")
        self.assertEqual(struct.unpack_from(">I", payload[".data"], 1)[0], 0x12343D3E)

    def test_ignored_target_keeps_relocation_without_a_branch_edge(self):
        data = fixture([{"command": "copy_target_stat_stages",
                         "ignored_failure_target": branch(encoding="reloc")},
                        {"command": "end_sequence"}], 6)
        metadata, payload, summary = self.assemble(self.compile(data))
        self.assertEqual(payload[".data"], b"\xbd\0\0\0\0\x3e")
        self.assertEqual(len(metadata[".data"]["relocations"]), 1)
        self.assertEqual(summary["edges"], [])

    def test_ignored_condition_byte_is_separate_from_numeric_word(self):
        data = fixture([{"command": "animate_selected_condition", "battler": "attacker",
                         "ignored_condition_kind": 1, "condition": 7}], 7)
        metadata, payload, _ = self.assemble(self.compile(data))
        self.assertEqual(payload[".data"], b"\x66\x11\x01\0\0\0\x07")
        self.assertEqual(metadata[".data"]["relocations"], [])

    def test_ignored_zero_word_is_still_four_bytes(self):
        data = fixture([{"command": "apply_intimidate", "ignored_operand": 0}], 5)
        _, payload, _ = self.assemble(self.compile(data))
        self.assertEqual(payload[".data"], b"\xe1\0\0\0\0")
        data[0]["synthetic.battle.json"]["programs"][0]["body"][0]["ignored_operand"] = 1
        with self.assertRaises(SourceError):
            self.compile(data)

    def test_scoped_legacy_pointer_is_not_an_immediate_animation(self):
        node = {"command": "play_animation_indirect", "battler": "attacker",
                "animation": {"legacy_address": "wsCmd46_pointer_ten"}, "argument": None}
        data = fixture([node], 10, "lbl_80378AF1", 0x80378AF1, 1)
        metadata, payload, _ = self.assemble(self.compile(data))
        self.assertEqual(payload[".data"], b"\x46\x11\0\0\0\x0a\0\0\0\0")
        self.assertEqual(metadata[".data"]["relocations"], [])
        with self.assertRaises(SourceError):
            self.compile(fixture([node], 10))

    def test_no_numeric_address_or_general_legacy_escape(self):
        for invalid in (10, 0x80400000, {"legacy_address": 10},
                        {"legacy_address": "wsCmd46_pointer_ten"}, {"raw_bytes": [1, 2, 3, 4]}):
            with self.subTest(invalid=invalid), self.assertRaises(SourceError):
                self.compile(fixture([{"command": "set_byte", "destination": invalid, "value": 1}], 6))

    def test_unknown_command_or_payload_field_rejected(self):
        for node in ({"command": "RAW_BYTES", "data": [0]},
                     {"command": "return_sequence", "raw": 0},
                     {"command": "set_byte", "destination": address(), "value": 3, "opcode": 46}):
            with self.subTest(node=node), self.assertRaises(SourceError):
                self.compile(fixture([node], 1))

    def test_scalar_bounds_and_enum_domains_rejected(self):
        for invalid in (-1, 256, True, "0x12"):
            with self.subTest(invalid=invalid), self.assertRaises(SourceError):
                self.compile(fixture([{"command": "set_byte", "destination": address(), "value": invalid}], 6))
        for invalid in (-1, 6, "approximately"):
            with self.subTest(invalid=invalid), self.assertRaises(SourceError):
                self.compile(fixture([{"command": "jump_if_byte", "comparison": invalid,
                                       "address": address(), "value": 3, "target": branch()}], 11))

    def test_symbol_extent_and_kind_are_enforced(self):
        data = fixture([{"command": "set_word_bits", "destination": address(addend=6), "mask": 1}], 9)
        with self.assertRaises(SourceError):
            self.compile(data)
        data[0]["synthetic.battle.json"]["programs"][0]["body"][0]["destination"] = address()
        data[2]["state"] = Symbol(0x80400000, 8, ".text", "function")
        with self.assertRaises(SourceError):
            self.compile(data)

    def test_transfer_bounds_apply_only_to_memory_not_branch_target(self):
        data = fixture([{"command": "jump_if_memory_equal", "left": address(),
                         "right": address("other_state"), "count": 8,
                         "target": branch("one_byte_tail")}], 14)
        data[0]["synthetic.battle.json"]["programs"].append({"symbol": "one_byte_tail", "body": [
            {"command": "return_sequence"}]})
        data[2]["one_byte_tail"] = Symbol(0x8000000E, 1, ".data")
        self.compile(data)
        data[2]["state"] = Symbol(0x80400000, 7, ".bss")
        with self.assertRaises(SourceError):
            self.compile(data)

    def test_null_only_for_optional_address_fields(self):
        self.compile(fixture([{"command": "play_animation", "battler": "defender",
                               "animation": 7, "argument": None}], 7))
        with self.assertRaises(SourceError):
            self.compile(fixture([{"command": "set_byte", "destination": None, "value": 0}], 6))

    def test_branch_must_name_an_existing_command_label(self):
        data = fixture([{"command": "jump", "target": branch(entry="inside_operand")}], 5)
        with self.assertRaises(SourceError):
            self.compile(data)
        data[0]["synthetic.battle.json"]["programs"][0]["body"][0]["target"] = {
            "script": "script_entry", "entry": "entry", "encoding": "absolute", "addend": 1}
        with self.assertRaises(SourceError):
            self.compile(data)

    def test_local_branch_label_comes_from_command_widths(self):
        data = fixture([{"command": "jump", "target": branch(entry="finished")},
                        {"label": "finished", "command": "return_sequence"}], 6)
        _, payload, _ = self.assemble(self.compile(data))
        self.assertEqual(payload[".data"], b"\x28\x80\0\0\x05\x3c")

    def test_duplicate_labels_and_extent_mismatch_rejected(self):
        for body, size in (([{"label": "entry", "command": "end_move"}], 1),
                           ([{"label": "same", "command": "end_move"},
                             {"label": "same", "command": "end_sequence"}], 2),
                           ([{"command": "end_sequence"}], 2)):
            with self.subTest(body=body), self.assertRaises(SourceError):
                self.compile(fixture(body, size))

    def test_owner_gaps_and_overlaps_rejected(self):
        for offset in (0, 2):
            data = fixture([{"command": "end_move"}], 1)
            data[0]["synthetic.battle.json"]["programs"].append(
                {"symbol": "second", "body": [{"command": "end_sequence"}]})
            data[2]["second"] = Symbol(0x80000000 + offset, 1, ".data")
            with self.subTest(offset=offset), self.assertRaises(SourceError):
                self.compile(data)

    def test_status_getter_and_setter_domains_are_distinct(self):
        node = {"command": "get_status_word", "family": "fight_floor", "context": None,
                "object_id": None, "field": 93, "index": None, "value": address()}
        self.compile(fixture([node], 20))
        node["command"] = "set_status_word"
        with self.assertRaises(SourceError):
            self.compile(fixture([node], 20))
        node["field"] = 62
        self.compile(fixture([node], 20))
        node["field"] = 65535
        with self.assertRaises(SourceError):
            self.compile(fixture([node], 20))

    def external_fixture(self, offset):
        data = fixture([{"command": "jump", "target": branch("external_script", "resume")}], 5)
        data[1]["external_entries"] = [{"symbol": "external_script",
                                        "source": "src/game/external.c",
                                        "labels": {"entry": 0, "resume": offset}}]
        data[2]["external_script"] = Symbol(0x80001000, 7, ".data")
        return data

    def test_external_entry_inside_operand_is_rejected_from_actual_c_source(self):
        for offset, accepted in ((6, True), (1, False)):
            compiler = self.compile(self.external_fixture(offset))
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "src/game/external.c"
                source.parent.mkdir(parents=True)
                source.write_text("u8 external_script[7] = {0x2e, 0x80, 0x40, 0, 0, 5, 0x3c};\n")
                if accepted:
                    self.assertEqual(compiler.verify_external_entries(root), [source.resolve()])
                else:
                    with self.assertRaises(SourceError):
                        compiler.verify_external_entries(root)

    def test_external_source_missing_or_unsupported_c_rejected(self):
        compiler = self.compile(self.external_fixture(6))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(SourceError):
                compiler.verify_external_entries(root)
            source = root / "src/game/external.c"
            source.parent.mkdir(parents=True)
            for text in ("u8 wrong_name[7] = {0};", "u8 external_script[6] = {0};",
                         "u8 external_script[7] = {DYNAMIC_VALUE};"):
                source.write_text(text)
                with self.subTest(text=text), self.assertRaises(SourceError):
                    compiler.verify_external_entries(root)

    def test_duplicate_json_keys_and_catalog_path_escape_rejected(self):
        with self.assertRaises(SourceError):
            json.loads('{"command":"end_move","command":"end_sequence"}',
                       object_pairs_hook=no_duplicate_keys)
        data = fixture([{"command": "end_move"}], 1)
        data[1]["sources"] = ["../synthetic.battle.json"]
        with self.assertRaises(SourceError):
            self.compile(data)

    def test_symbol_parser_excludes_repeated_compiler_locals(self):
        symbols = parse_symbols("state = .data:0x80000000; // type:object size:0x4 scope:global\n"
                                "@2 = .data:0x80000100; // type:object size:0x4 scope:local\n"
                                "@2 = .data:0x80000200; // type:object size:0x4 scope:local\n")
        self.assertEqual(set(symbols), {"state"})
        with self.assertRaises(SourceError):
            parse_symbols("state = .data:0x80000000; // type:object size:0x4\n"
                          "state = .data:0x80000004; // type:object size:0x4\n")


class ExistingInterpreterTests(unittest.TestCase):
    def test_dispatch_identity_for_every_supported_command(self):
        text = _without_comments((ROOT / "src/game/data/rodata_80279B78.c").read_text())
        table = re.search(r"lbl_8027A00C\[255\]\s*=\s*\{([^{}]+)\}", text)
        self.assertIsNotNone(table)
        entries = [re.sub(r"^\(void\*\)\s*", "", x.strip()) for x in table[1].split(",") if x.strip()]
        self.assertEqual(len(entries), 255)
        for command in fmt.COMMANDS.values():
            with self.subTest(command=command.name):
                self.assertEqual(entries[command.opcode], command.handler)
                self.assertEqual(command.size, 1 + sum(fmt.FIELD_WIDTH[k.rstrip("?")]
                                                       for _, k in command.fields))
        for opcode, (_, handler, _) in fmt.EXTERNAL_COMMAND_STRIDES.items():
            self.assertEqual(entries[opcode], handler)

    def test_status_schema_matches_existing_getter_and_setter_field_switches(self):
        schema = source_schema(ROOT)
        self.assertEqual({kind: set(row[1]) for kind, row in schema["families"].items()},
                         {kind: set(values) for kind, values in fmt.STATUS_SET_FIELDS.items()})
        for kind, (name, path) in fmt.STATUS_GET_SOURCES.items():
            with self.subTest(getter=name):
                body = c_function(ROOT / path, name)
                self.assertEqual(_field_cases(body), set(fmt.STATUS_GET_FIELDS[kind]))

    def test_compatibility_quirks_remain_in_matching_c(self):
        body = re.sub(r"\s+", "", c_function(ROOT / "src/game/fight_range_exact_80226134.c", "wsCmd11"))
        self.assertIn("*(u32*)(lbl_8047B610+1)", body)
        self.assertRegex(body, r"lbl_8047B610(?:\+=3|=lbl_8047B610\+3);")
        body = re.sub(r"\s+", "", c_function(ROOT / "src/game/fight_range_exact_80222110.c", "wsCmd46"))
        self.assertIn("ptr1=*(void**)(pc+2);", body)
        self.assertIn("uVar1=*(u8*)ptr1;", body)
        self.assertIn("lbl_8047B610+=10;", body)

    def test_complete_source_catalog_preserves_physical_extent_and_dependencies(self):
        compiler, inputs = load_source(ROOT / "src/game/battle_scripts/scripts_80375E60.battle.json",
                                       ROOT / "config/GC6E01/symbols.txt")
        summaries = [compiler.assembly(name)[1] for name in compiler.owners]
        self.assertEqual(len(summaries), 17)
        self.assertEqual(sum(s["size"] for s in summaries), 13500)
        self.assertEqual(sum(len(s["symbols"]) for s in summaries), 195)
        self.assertEqual(sum(s["commands"] for s in summaries), 3182)
        self.assertEqual(sum(len(s["relocations"]) for s in summaries), 299)
        self.assertEqual(len(compiler.external_entries), 16)
        self.assertTrue({(ROOT / p).resolve() for p in compiler.external_sources} <= set(inputs))


if __name__ == "__main__":
    unittest.main()
