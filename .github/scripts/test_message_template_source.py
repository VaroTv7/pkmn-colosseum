#!/usr/bin/env python3
"""Verify the message-source contract with synthetic messages and source APIs."""

import copy
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import message_template_source as compiler


class MessageTemplateTests(unittest.TestCase):
    def test_packed_control_and_glyph_widths_follow_the_reader(self):
        # A three-byte control leaves the following 16-bit glyph unaligned.
        self.assertEqual(compiler.encode_parts([
            {'control': 'menu_digit'}, 'A', {'control': 'font', 'value': 3}]),
            bytes.fromhex('ffff340041ffff07030000'))
        self.assertEqual(compiler.encode_parts([
            {'control': 'baseline_bias', 'value': -2}, {'control': 'hero_name'}]),
            bytes.fromhex('ffff5cfeffff2b0000'))

    def test_control_ids_are_bound_to_the_existing_callback_table(self):
        text = (ROOT / 'src/game/data/data_80363774.c').read_text()
        table = text.split('void* msgctrlcode[190] = {', 1)[1].split('};', 1)[0]
        entries = re.findall(r'\(void\*\)([^,]+),', table)[1::2]
        self.assertEqual(len(entries), 95)
        for code, callback, _ in compiler.CONTROLS.values():
            self.assertIn(callback, entries[code])

    def test_parameter_types_and_reserved_bytes_are_rejected(self):
        invalid = [
            [{'control': 'font', 'value': -1}],
            [{'control': 'font', 'value': 256}],
            [{'control': 'font', 'value': True}],
            [{'control': 'baseline_bias', 'value': 128}],
            [{'control': 'baseline_bias', 'value': -129}],
            [{'control': 'menu_digit', 'value': 0}],
            [{'control': 'unknown'}], [{'raw': '0000'}],
            ['\0'], ['\uffff'], ['\ud800'], ['\U00010000'],
        ]
        for parts in invalid:
            with self.subTest(parts=repr(parts)), self.assertRaises(ValueError):
                compiler.encode_parts(parts)

    def test_counter_order_keys_and_fullwidth_decimal(self):
        messages = compiler.expand_messages([{
            'first_key': 100, 'template': '{row}_{column}',
            'axes': [{'name': 'row', 'values': [1, 3]},
                     {'name': 'column', 'values': {'start': 8, 'stop': 10}}],
            'fullwidth': True,
        }])
        self.assertEqual([key for key, _ in messages], [100, 101, 102, 103])
        self.assertEqual([data.hex() for _, data in messages], [
            'ff11005fff180000', 'ff11005fff190000',
            'ff13005fff180000', 'ff13005fff190000',
        ])

    def test_unknown_format_fields_and_duplicate_keys_fail(self):
        base = {'first_key': 1, 'template': '{n}',
                'axes': [{'name': 'n', 'values': [1, 2]}]}
        for changes in ({'template': '{n.__class__}'}, {'template': '{n:02}'},
                        {'template': '{n!s}'}, {'fullwidth': 1},
                        {'axes': [{'name': 'n', 'values': [1, 1]}]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                compiler.expand_messages([{**base, **changes}])
        with self.assertRaises(ValueError):
            compiler.expand_messages([base, {'key': 2, 'parts': []}])

    def test_unit_extent_and_symbol_are_checked_before_assembly(self):
        source = {'schema': 'gs-message-templates-v1', 'units': {
            'synthetic': {'symbol': 'synthetic_message', 'start': 37, 'size': 5,
                          'messages': [{'key': 1, 'parts': [{'control': 'menu_digit'}]}]}}}
        symbol, payload, entries = compiler.compile_unit(source, 'synthetic')
        self.assertEqual((symbol, payload), ('synthetic_message', bytes.fromhex('ffff340000')))
        self.assertEqual(entries, [{'key': 1, 'start': 37, 'size': 5}])
        for changes in ({'size': 6}, {'symbol': 'label\n.byte 1'}, {'raw': []}):
            broken = copy.deepcopy(source)
            broken['units']['synthetic'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                compiler.compile_unit(broken, 'synthetic')


if __name__ == '__main__':
    unittest.main()
