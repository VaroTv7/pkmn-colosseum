#!/usr/bin/env python3
"""Synthetic source/index/layout checks for authored message catalogues."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import message_catalog_source as compiler
from tools import message_template_source as templates


UNIT = "message_storage_10028"
INDEX_TEXT = """
typedef struct MessageResourceIndex_10000 {
    RelMessageHeader header;
    RelMessageIndex entries[3];
} MessageResourceIndex_10000;
MessageResourceIndex_10000 synthetic_index __attribute__((aligned(4))) = {
    { 0, 0, 1, 3, 0x5553, NULL, NULL },
    { { 10, 0x30 }, { 20, 0x28 }, { 30, 0x34 }, }
};
"""
SYMBOL_TEXT = """
synthetic_index = .data:0x00010000; // type:object size:0x28
synthetic_messages = .data:0x00010028; // type:object size:0x13
"""


def fixture():
    symbols = compiler.parse_symbol_map(SYMBOL_TEXT)
    index = compiler.parse_message_index(INDEX_TEXT, symbols)
    document = {"schema": "gs-message-catalog-v1", "units": {UNIT: {
        "symbol": "synthetic_messages", "start": 0x10028, "size": 19,
        "messages": [
            {"key": 20, "parts": [{"control": "font", "value": 3}, "A"]},
            {"key": 10, "parts": ["B"]},
            {"key": 30, "parts": [{"control": "event_string_2"}, "é"]},
        ]}}}
    return document, symbols, [index]


class MessageCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.document, self.symbols, self.indexes = fixture()

    def compile(self, document=None):
        return compiler.compile_document(document or self.document, self.symbols, self.indexes)[UNIT]

    def test_physical_order_and_odd_address_glyphs_preserve_index_offsets(self):
        unit = self.compile()
        self.assertEqual(unit["payload"], bytes.fromhex("ffff07030041000000420000ffff4100e90000"))
        self.assertEqual([e["key"] for e in unit["entries"]], [20, 10, 30])
        self.assertEqual([e["start"] for e in unit["entries"]], [0x10028, 0x10030, 0x10034])
        self.assertEqual(unit["payload"][15:17], bytes.fromhex("00e9"))

    def test_rgba_parameter_has_four_named_big_endian_byte_channels(self):
        parts = [{"control": "color", "red": 60, "green": 180, "blue": 255, "alpha": 255}, "A"]
        self.assertEqual(compiler.encode_catalog_parts(parts), bytes.fromhex("ffff083cb4ffff00410000"))
        for edit in ({"value": 0x3CB4FFFF}, {"red": True}, {"alpha": -1}, {"blue": 256},
                     {"raw": [60, 180, 255, 255]}):
            malformed = {**parts[0], **edit}
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                compiler.encode_catalog_parts([malformed])
        missing = dict(parts[0]); missing.pop("alpha")
        with self.assertRaises(ValueError):
            compiler.encode_catalog_parts([missing])

    def test_new_controls_agree_with_matching_reader_implementations(self):
        handler = (ROOT / "src/game/msgctrl_candidate_80131FF4.c").read_text()
        color = handler.split("s32 msgctrlColor(", 1)[1].split("\ns32 ", 1)[0]
        self.assertIn("obj->colorRgba = *(u32*)obj->stream", color)
        self.assertIn("obj->stream += 4", color)
        font = handler.split("s32 msgctrlFont(", 1)[1].split("\ns32 ", 1)[0]
        self.assertIn("obj->commandValue = obj->stream[0]", font)
        self.assertIn("obj->stream++", font)
        self.assertEqual(templates.CONTROLS["color"], (8, "msgctrlColor", 4))
        self.assertEqual(templates.CONTROLS["font"], (7, "msgctrlFont", 1))

    def test_unicode_is_not_normalized(self):
        self.assertEqual(compiler.encode_catalog_parts(["é"]), bytes.fromhex("00e90000"))
        self.assertEqual(compiler.encode_catalog_parts(["e\u0301"]), bytes.fromhex("006503010000"))
        self.assertEqual(compiler.encode_catalog_parts(["Ａ"]), bytes.fromhex("ff210000"))

    def test_non_readable_glyphs_and_raw_operations_are_rejected(self):
        for parts in (["\0"], ["\uffff"], ["\n"], ["\ue000"], ["\ufdd0"], ["\ud800"],
                      ["\U00010000"], [{"raw": "0000"}], [{"hex": "ffff00"}], [65],
                      [{"control": 8}], [{"control": "unknown"}]):
            with self.subTest(parts=repr(parts)), self.assertRaises(ValueError):
                compiler.encode_catalog_parts(parts)

    def test_stale_reordered_missing_and_duplicate_lookup_keys_fail(self):
        for change in ("reorder", "missing", "duplicate", "unknown", "wrong_width"):
            document = copy.deepcopy(self.document)
            messages = document["units"][UNIT]["messages"]
            if change == "reorder":
                messages.reverse()
            elif change == "missing":
                messages.pop()
            elif change == "duplicate":
                messages[1]["key"] = 20
            elif change == "unknown":
                messages[1]["key"] = 999
            else:
                messages[0]["parts"].append("X")
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.compile(document)

    def test_owner_identity_and_full_public_extent_are_required(self):
        for changes in ({"size": 18}, {"size": True}, {"start": 0x10029},
                        {"symbol": "absent"}, {"symbol": "synthetic_index"}):
            document = copy.deepcopy(self.document)
            document["units"][UNIT].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.compile(document)

    def test_unknown_fields_are_rejected_at_every_authored_level(self):
        for level in ("document", "unit", "message"):
            document = copy.deepcopy(self.document)
            target = document if level == "document" else document["units"][UNIT]
            if level == "message":
                target = target["messages"][0]
            target["original_file"] = "resource.bin"
            with self.subTest(level=level), self.assertRaises(ValueError):
                self.compile(document)

    def test_every_document_unit_is_validated(self):
        document = copy.deepcopy(self.document)
        document["units"]["message_storage_20000"] = {"raw": []}
        with self.assertRaises(ValueError):
            self.compile(document)

    def test_retained_plain_string_has_its_own_terminator_and_no_lookup_key(self):
        message = self.document["units"][UNIT]["messages"][0]
        message["parts"] = ["A"]
        message["retained"] = [{"name": "unindexed_after_20_1", "parts": ["Z"]}]
        unit = self.compile()
        self.assertEqual(unit["payload"][:8], bytes.fromhex("00410000005a0000"))
        self.assertEqual(unit["entries"][0]["size"], 4)
        self.assertEqual(unit["retained"], [{"name": "unindexed_after_20_1", "start": 0x1002C, "size": 4}])
        self.assertEqual([entry["key"] for entry in unit["entries"]], [20, 10, 30])

    def test_retained_strings_reject_controls_keys_names_and_index_overlap(self):
        for retained in ([{"name": "unindexed_after_20_1", "parts": [{"control": "key_end"}]}],
                         [{"name": "unindexed_after_20_1", "parts": ["Z"], "key": 25}],
                         [{"name": "unindexed_after_20_2", "parts": ["Z"]}],
                         [{"name": "unindexed_after_20_1", "parts": ["ZZ"]}]):
            document = copy.deepcopy(self.document)
            message = document["units"][UNIT]["messages"][0]
            message["parts"], message["retained"] = ["A"], retained
            with self.subTest(retained=retained), self.assertRaises(ValueError):
                self.compile(document)

    def test_only_final_bank_padding_to_the_public_boundary_is_accepted(self):
        self.document["units"][UNIT].update(size=20, alignment_padding=4)
        self.symbols["synthetic_messages"]["size"] = 20
        unit = self.compile()
        self.assertEqual(unit["padding"], 1)
        self.assertEqual(len(unit["payload"]), 20)
        for alignment in (True, 1, 2, 8):
            document = copy.deepcopy(self.document)
            document["units"][UNIT]["alignment_padding"] = alignment
            with self.subTest(alignment=alignment), self.assertRaises(ValueError):
                self.compile(document)
        # Another index entry exists beyond this shortened owner: its end
        # cannot be described as final resource padding.
        self.document["units"][UNIT]["messages"].pop()
        self.document["units"][UNIT]["size"] = 12
        self.symbols["synthetic_messages"]["size"] = 12
        with self.assertRaisesRegex(ValueError, "final indexed bank"):
            self.compile()

    def test_index_parser_rejects_expressions_counts_duplicates_and_wrong_extent(self):
        for text in (INDEX_TEXT.replace("{ 10, 0x30 }", "{ 10, 0x2F + 1 }"),
                     INDEX_TEXT.replace("1, 3, 0x5553", "1, 2, 0x5553"),
                     INDEX_TEXT.replace("{ 20, 0x28 }", "{ 10, 0x28 }"),
                     INDEX_TEXT.replace("{ 20, 0x28 }", "{ 20, 0x30 }"),
                     INDEX_TEXT.replace("{ 20, 0x28 }", "{ 20, 0x10 }")):
            with self.subTest(text=text), self.assertRaises(ValueError):
                compiler.parse_message_index(text, self.symbols)
        self.symbols["synthetic_index"]["size"] = 32
        with self.assertRaisesRegex(ValueError, "extent"):
            compiler.parse_message_index(INDEX_TEXT, self.symbols)

    def test_duplicate_json_keys_and_index_sources_fail(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            json.loads('{"schema":"a","schema":"b"}', object_pairs_hook=compiler.unique_fields)
        with self.assertRaisesRegex(ValueError, "Duplicate message-index"):
            compiler.compile_document(self.document, self.symbols, self.indexes * 2)

    def test_current_catalogue_has_exact_registered_counts_and_source_coverage(self):
        source = ROOT / "src/rel/common_rel"
        compiled = compiler.load_source(source / "message_catalog.json",
            ROOT / "config/GC6E01/common_rel/symbols.txt",
            [source / "message_index_58044.c", source / "message_index_76C94.c"])
        self.assertEqual(len(compiled), 13)
        self.assertEqual(sum(len(unit["payload"]) for unit in compiled.values()), 91421)
        self.assertEqual(sum(len(unit["entries"]) for unit in compiled.values()), 4018)
        self.assertEqual(sum(len(unit["retained"]) for unit in compiled.values()), 3)
        self.assertEqual(sum(unit["padding"] for unit in compiled.values()), 2)
        self.assertEqual([name for name, unit in compiled.items() if unit["padding"]],
                         ["message_storage_6410E"])


if __name__ == "__main__":
    unittest.main()
