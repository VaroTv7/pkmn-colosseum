#!/usr/bin/env python3
"""Synthetic ELF tests; contains no original game bytes."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import link_vector_object as helper

SECTION_NAMES = ['', '.init', '.symtab', '.strtab', '.shstrtab', '.rela.init',
                 '.rel.init', '.comment', '.note.split']
MARKER_INDEX = 6
LOCAL_BOUNDARY = 4


def fixture():
    section_names = b'\0'.join(name.encode() for name in SECTION_NAMES) + b'\0'
    symbol_names = b'\0vector_fixture\0local_label\0gTRKInterruptVectorTable\0interior_label\0pad_00_800034AC_init\0gTRKInterruptVectorTableEnd\0'

    def symbol(name, value, size, info, other, section=1):
        offset = symbol_names.index(name + b'\0') if name else 0
        return struct.pack('>IIIBBH', offset, value, size, info, other, section)

    symbols = bytes(16)
    symbols += symbol(b'vector_fixture', 0, 0, 4, 0, 0xFFF1)
    symbols += symbol(b'', 0, 0, 3, 0)
    symbols += symbol(b'local_label', 8, 0, 0, 0)
    symbols += symbol(b'gTRKInterruptVectorTable', 0, 0, 0x10, 0)
    symbols += symbol(b'interior_label', 0xB54, 0, 0x10, 0)
    symbols += symbol(helper.MARKER.encode(), 0, helper.SIZE, 0x12, 2)
    symbols += symbol(b'gTRKInterruptVectorTableEnd', helper.SIZE, 0, 0x10, 0)
    comment_header = bytearray(helper.COMMENT_HEADER)
    comment_header[:11] = b'CodeWarrior'
    comment_header[11:21] = bytes([8, 2, 3, 0, 1, 1, 2, 0, 0x16, helper.COMMENT_HEADER])
    comments = bytes(comment_header) + b''.join(
        struct.pack('>IBBH', align, 0, active, 0)
        for align, active in [(0, 0), (1, 0), (4, 0), (0, 0),
                              (0, 0), (0, 0), (4, 8), (0, 0)])

    def note(kind, descriptor):
        return (struct.pack('>II4s', 6, len(descriptor), kind) + b'Split\0\0\0' +
                descriptor + bytes((-len(descriptor)) % 4))

    virtuals = [0, 0, 0x800034AC, 0x800034B4, 0x800034AC, 0x80004000,
                0x800034AC, 0x800053E0]
    notes = (note(b'GENR', b'synthetic DTK') + note(b'MODN', b'main') +
             note(b'MODI', struct.pack('>I', 0)) +
             note(b'VIRT', struct.pack('>8I', *virtuals)))
    rela = struct.pack('>IIi', 0x20, (MARKER_INDEX << 8) | 1, 4)
    rela += struct.pack('>IIi', 0x24, (5 << 8) | 10, -4)
    rel = struct.pack('>II', 0x28, (MARKER_INDEX << 8) | 1)
    rel += struct.pack('>II', 0x2C, (3 << 8) | 6)
    payloads = [b'', bytes((i * 37) % 256 for i in range(helper.SIZE)), symbols,
                symbol_names, section_names, rela, rel, comments, notes]
    kinds = [0, 1, 2, 3, 3, 4, 9, 1, helper.SHT_MWCATS]
    blob, headers = bytearray(52), []
    for i, data in enumerate(payloads):
        blob.extend(bytes((-len(blob)) % 4))
        offset = len(blob) if i else 0
        blob.extend(data)
        headers.append((section_names.index(SECTION_NAMES[i].encode() + b'\0'),
                        kinds[i], 6 if i == 1 else 0, 0, offset, len(data),
                        3 if i == 2 else 2 if i in (5, 6) else 0,
                        LOCAL_BOUNDARY if i == 2 else 1 if i in (5, 6) else 0,
                        4 if i else 0, 16 if i == 2 else 12 if i == 5 else 8 if i == 6 else 0))
    blob.extend(bytes((-len(blob)) % 4))
    shoff = len(blob)
    blob.extend(b''.join(struct.pack('>10I', *h) for h in headers))
    ident = b'\x7fELF\x01\x02\x01' + bytes(9)
    struct.pack_into('>16sHHIIIIIHHHHHH', blob, 0, ident, 1, 20, 1, 0, 0, shoff, 0,
                     52, 0, 0, 40, len(headers), 4)
    return bytes(blob), headers, shoff


def relocation_identities(blob, sections):
    """Independently resolve each fixture relocation to its named symbol."""
    table, strings = sections[2], sections[3]
    names = blob[strings[4]:strings[4]+strings[5]]
    result = []
    for i in (5, 6):
        section = sections[i]
        for offset in range(section[4], section[4]+section[5], section[9]):
            address, info = struct.unpack_from('>II', blob, offset)
            symbol = struct.unpack_from('>IIIBBH', blob, table[4] + (info >> 8) * 16)
            name = names[symbol[0]:names.index(b'\0', symbol[0])]
            addend = struct.unpack_from('>i', blob, offset+8)[0] if i == 5 else None
            result.append((i, address, info & 255, name, symbol[1], symbol[2], symbol[5], addend))
    return result


class LinkCopyTests(unittest.TestCase):
    def test_local_partition_layout_public_labels_and_per_symbol_metadata(self):
        before, sections, _ = fixture()
        after, summary = helper.local_link_copy(before)
        _, new_sections, names, new_symbols, table_index, marker = helper.read_vector(after, 0x02, 0)
        self.assertEqual((summary['old_marker'], summary['new_marker']), (6, 4))
        self.assertEqual((summary['old_boundary'], summary['new_boundary']), (4, 5))
        self.assertEqual((summary['symbol_records'], summary['comment_records'], summary['virt_records']), (3, 3, 3))
        self.assertEqual(marker, 4)
        self.assertEqual(new_sections[table_index][7], 5)
        self.assertTrue(all(s[1][3] >> 4 == 0 for s in new_symbols[:5]))
        self.assertTrue(all(s[1][3] >> 4 != 0 for s in new_symbols[5:]))
        for label in ('gTRKInterruptVectorTable', 'gTRKInterruptVectorTableEnd'):
            symbol = next(s for n, s in new_symbols if n == label)
            self.assertEqual(symbol[3:5], (0x10, 0))
        expected_order = [0, 1, 2, 3, 6, 4, 5, 7]
        old_comments = helper.comment_records(before, sections, names, 8)[1]
        new_comments = helper.comment_records(after, new_sections, names, 8)[1]
        self.assertEqual(new_comments, [old_comments[i] for i in expected_order])
        self.assertNotEqual(old_comments, new_comments)
        old_virtuals = helper.virtual_records(before, sections, names, 8)[1]
        new_virtuals = helper.virtual_records(after, new_sections, names, 8)[1]
        self.assertEqual(new_virtuals, [old_virtuals[i] for i in expected_order])
        self.assertNotEqual(old_virtuals, new_virtuals)
        self.assertEqual(len(before), len(after))
        self.assertEqual(before[:52], after[:52])
        for i, (old, new) in enumerate(zip(sections, new_sections)):
            expected = list(old)
            if i == 2:
                expected[7] += 1
            self.assertEqual(tuple(expected), new)
            if i in (0, 1, 3, 4):
                self.assertEqual(before[old[4]:old[4]+old[5]], after[new[4]:new[4]+new[5]])
        # Only the VIRT descriptor changes inside Split metadata.
        virt_offset, virt = helper.virtual_records(before, sections, names, 8)
        note_start, note_size = sections[8][4:6]
        self.assertEqual(before[note_start:virt_offset], after[note_start:virt_offset])
        self.assertEqual(before[virt_offset + 4*len(virt):note_start+note_size],
                         after[virt_offset + 4*len(virt):note_start+note_size])

    def test_rel_and_rela_keep_target_identity_type_offset_and_addend(self):
        before, sections, _ = fixture()
        after, summary = helper.local_link_copy(before)
        self.assertEqual(relocation_identities(before, sections), relocation_identities(after, sections))
        self.assertEqual(summary['relocations_checked'], 4)
        self.assertEqual(summary['relocation_records'], 3)
        for section_index in (5, 6):
            offset = sections[section_index][4]
            self.assertEqual(struct.unpack_from('>I', before, offset+4)[0] >> 8, 6)
            self.assertEqual(struct.unpack_from('>I', after, offset+4)[0] >> 8, 4)

    def test_original_and_other_objects_with_incoming_imports_are_untouched(self):
        before, sections, _ = fixture()
        incoming = bytearray(before)
        marker_offset = sections[2][4] + MARKER_INDEX * 16
        name_offset = struct.unpack_from('>I', incoming, marker_offset)[0]
        # Another ELF input imports the synthetic name. The copier must not
        # hide that dependency by changing its name or redirecting its target;
        # the ordinary full executable link must reject an unresolved import.
        struct.pack_into('>IIIBBH', incoming, marker_offset, name_offset, 0, 0, 0x10, 0, 0)
        with tempfile.TemporaryDirectory() as directory:
            source, dest = Path(directory)/'original.o', Path(directory)/'link'/'copy.o'
            other = Path(directory)/'other.o'
            source.write_bytes(before)
            other.write_bytes(incoming)
            helper.copy_file(source, dest)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(other.read_bytes(), incoming)
            self.assertEqual(dest.read_bytes(), helper.local_link_copy(before)[0])
            with self.assertRaises(ValueError):
                helper.copy_file(source, source)
            with self.assertRaises(ValueError):
                helper.local_link_copy(bytes(incoming))

    def test_invalid_identity_layout_and_metadata_are_rejected(self):
        original, sections, shoff = fixture()
        sym = sections[2][4] + MARKER_INDEX * 16
        virt, _ = helper.virtual_records(original, sections, SECTION_NAMES, 8)
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
            'duplicate_marker': (sections[2][4] + 4*16, original[sym:sym+4]),
            'bad_symbol_string': (sym, b'\xFF\xFF\xFF\xFF'),
            'bad_symbol_width': (shoff + 2*40 + 36, struct.pack('>I', 24)),
            'bad_string_link': (shoff + 2*40 + 24, struct.pack('>I', 100)),
            'overlapping_sections': (shoff + 7*40 + 16, struct.pack('>I', sections[2][4])),
            'extended_symbol_index': (sym + 14, b'\xFF\xFF'),
            'bad_local_boundary': (shoff + 2*40 + 28, struct.pack('>I', 3)),
            'unsupported_group': (shoff + 7*40 + 4, struct.pack('>I', 17)),
            'unsupported_note_type': (shoff + 8*40 + 4, struct.pack('>I', 7)),
            'unexpected_allocated_metadata': (shoff + 7*40 + 8, struct.pack('>I', 2)),
            'comment_version': (sections[7][4] + 11, b'\x0A'),
            'comment_count': (shoff + 7*40 + 20, struct.pack('>I', sections[7][5]-8)),
            'virt_count': (virt - 16, struct.pack('>I', 28)),
            'virt_address': (virt + 4*MARKER_INDEX, struct.pack('>I', 0x80000000)),
            'rela_symbol_index': (sections[5][4]+4, struct.pack('>I', (100 << 8)|1)),
            'rel_symbol_index': (sections[6][4]+4, struct.pack('>I', (100 << 8)|1)),
            'rel_bad_stride': (shoff + 6*40 + 36, struct.pack('>I', 12)),
        }
        for label, (offset, change) in variants.items():
            with self.subTest(label=label):
                altered = bytearray(original)
                altered[offset:offset+len(change)] = change
                with self.assertRaises((ValueError, struct.error)):
                    helper.local_link_copy(bytes(altered))

    def test_truncated_file_is_rejected_without_replacing_destination(self):
        before, _, _ = fixture()
        for length in (0, 4, 51, len(before)-1):
            with self.subTest(length=length), self.assertRaises((ValueError, struct.error)):
                helper.local_link_copy(before[:length])
        with tempfile.TemporaryDirectory() as directory:
            source, destination = Path(directory)/'bad.o', Path(directory)/'copy.o'
            source.write_bytes(before[:51])
            destination.write_bytes(b'unchanged')
            with self.assertRaises(ValueError):
                helper.copy_file(source, destination)
            self.assertEqual(destination.read_bytes(), b'unchanged')

    def test_cli_reports_only_canonicalization_metadata(self):
        before, _, _ = fixture()
        with tempfile.TemporaryDirectory() as directory:
            source, destination = Path(directory)/'original.o', Path(directory)/'copy.o'
            source.write_bytes(before)
            result = subprocess.run([sys.executable, str(ROOT/'tools/link_vector_object.py'),
                                     str(source), str(destination)], check=True, capture_output=True, text=True)
        self.assertEqual(result.stdout, 'Vector link copy: marker index 6->4; local boundary 4->5; '
                         'remapped 3 symbol, 3 comment, 3 VIRT, 3 relocation records '
                         '(4 relocations checked); allocated payloads unchanged.\n')
        self.assertEqual(result.stderr, '')


if __name__ == '__main__':
    unittest.main()
