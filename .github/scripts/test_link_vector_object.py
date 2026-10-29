#!/usr/bin/env python3
"""Focused synthetic ELF tests; contains no original game bytes."""
import sys
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import link_vector_object as helper


def fixture():
    section_names = b'\0.init\0.symtab\0.strtab\0.shstrtab\0.rela.init\0.comment\0.note.split\0'
    names = [b'', b'.init', b'.symtab', b'.strtab', b'.shstrtab', b'.rela.init', b'.comment', b'.note.split']
    symbol_names = b'\0gTRKInterruptVectorTable\0pad_00_800034AC_init\0gTRKInterruptVectorTableEnd\0'
    def symbol(name, value, size, info, other):
        return struct.pack('>IIIBBH', symbol_names.index(name + b'\0'), value, size, info, other, 1)
    symbols = bytes(16)
    symbols += symbol(b'gTRKInterruptVectorTable', 0, 0, 0x10, 0)
    symbols += symbol(helper.MARKER.encode(), 0, helper.SIZE, 0x12, 2)
    symbols += symbol(b'gTRKInterruptVectorTableEnd', helper.SIZE, 0, 0x10, 0)
    payloads = [b'', bytes((i * 37) % 256 for i in range(helper.SIZE)), symbols,
                symbol_names, section_names, struct.pack('>IIi', 0x20, (2 << 8) | 1, 4),
                b'synthetic compiler comment\0', b'synthetic split metadata\0']
    # SHT_NULL, PROGBITS, SYMTAB, STRTAB, STRTAB, RELA, PROGBITS, NOTE.
    kinds = [0, 1, 2, 3, 3, 4, 1, 7]
    blob, headers = bytearray(52), []
    for i, data in enumerate(payloads):
        blob.extend(bytes((-len(blob)) % 4))
        offset = len(blob) if i else 0
        blob.extend(data)
        headers.append((section_names.index(names[i] + b'\0'), kinds[i], 6 if i == 1 else 0,
                        0, offset, len(data), 3 if i == 2 else 2 if i == 5 else 0,
                        1 if i in (2, 5) else 0, 4 if i else 0,
                        16 if i == 2 else 12 if i == 5 else 0))
    blob.extend(bytes((-len(blob)) % 4))
    shoff = len(blob)
    blob.extend(b''.join(struct.pack('>10I', *h) for h in headers))
    ident = b'\x7fELF\x01\x02\x01' + bytes(9)
    struct.pack_into('>16sHHIIIIIHHHHHH', blob, 0, ident, 1, 20, 1, 0, 0, shoff, 0,
                     52, 0, 0, 40, len(headers), 4)
    return bytes(blob), headers, shoff


class LinkCopyTests(unittest.TestCase):
    def test_only_visibility_byte_changes_and_every_other_payload_is_identical(self):
        before, sections, _ = fixture()
        after, offset = helper.default_visibility_copy(before)
        expected = sections[2][4] + 2 * 16 + 13
        self.assertEqual(offset, expected)
        self.assertEqual([i for i, (a, b) in enumerate(zip(before, after)) if a != b], [expected])
        self.assertEqual((before[expected], after[expected]), (2, 0))
        for i, s in enumerate(sections):
            if i != 2:
                self.assertEqual(before[s[4]:s[4]+s[5]], after[s[4]:s[4]+s[5]])
        self.assertEqual(len(before), len(after))

    def test_original_is_unchanged_and_destination_is_separate(self):
        before, _, _ = fixture()
        with tempfile.TemporaryDirectory() as directory:
            source, dest = Path(directory)/'original.o', Path(directory)/'link'/'copy.o'
            source.write_bytes(before)
            helper.copy_file(source, dest)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(dest.read_bytes(), helper.default_visibility_copy(before)[0])
            with self.assertRaises(ValueError):
                helper.copy_file(source, source)

    def test_invalid_identity_layout_and_marker_are_rejected(self):
        original, sections, shoff = fixture()
        sym = sections[2][4] + 2 * 16
        variants = {
            'ELF64': (4, b'\x02'), 'little_endian': (5, b'\x01'),
            'executable': (16, b'\0\x02'), 'x86': (18, b'\0\x03'),
            'init_size': (shoff + 40 + 20, struct.pack('>I', helper.SIZE - 4)),
            'marker_value': (sym + 4, struct.pack('>I', 4)),
            'marker_size': (sym + 8, struct.pack('>I', helper.SIZE - 4)),
            'local_marker': (sym + 12, b'\x02'),
            'object_marker': (sym + 12, b'\x11'),
            'default_visibility': (sym + 13, b'\0'),
            'protected_visibility': (sym + 13, b'\x03'),
            'undefined_marker': (sym + 14, b'\0\0'),
            'missing_marker': (sym, b'\0\0\0\0'),
            'duplicate_marker': (sections[2][4] + 16, original[sym:sym+4]),
            'bad_symbol_string': (sym, b'\xFF\xFF\xFF\xFF'),
            'bad_symbol_width': (shoff + 2*40 + 36, struct.pack('>I', 24)),
            'bad_string_link': (shoff + 2*40 + 24, struct.pack('>I', 100)),
            'payload_overlap': (shoff + 6*40 + 16, struct.pack('>I', sym)),
        }
        for label, (offset, change) in variants.items():
            with self.subTest(label=label):
                altered = bytearray(original)
                altered[offset:offset+len(change)] = change
                with self.assertRaises((ValueError, struct.error)):
                    helper.default_visibility_copy(bytes(altered))

    def test_truncated_file_is_rejected(self):
        before, _, _ = fixture()
        for length in (0, 4, 51, len(before)-1):
            with self.subTest(length=length), self.assertRaises((ValueError, struct.error)):
                helper.default_visibility_copy(before[:length])


if __name__ == '__main__':
    unittest.main()
