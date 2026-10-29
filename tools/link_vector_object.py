#!/usr/bin/env python3
"""Make a link-only visibility copy of the original interrupt-vector object.

The original DTK target remains untouched for progress reporting.  A separate
copy is passed to the legacy MW linker to isolate hidden-symbol handling.
No allocated bytes, relocations, symbol identity, or binding are changed.
Deliberately accepts only this specific ELF32/PPC fallback.
"""
import argparse
from pathlib import Path
import struct
import tempfile

MARKER = 'pad_00_800034AC_init'
SIZE = 0x1F34


def default_visibility_copy(blob):
    def chunk(offset, size):
        if offset < 0 or size < 0 or offset + size > len(blob):
            raise ValueError('ELF record extends beyond the file')
        return blob[offset:offset + size]

    def name(table, offset):
        if offset < 0 or offset >= len(table):
            raise ValueError('ELF string offset is outside its table')
        end = table.find(b'\0', offset)
        if end < 0:
            raise ValueError('Unterminated ELF string')
        return table[offset:end].decode('ascii')

    header = struct.unpack('>16sHHIIIIIHHHHHH', chunk(0, 52))
    if header[0][:7] != b'\x7fELF\x01\x02\x01' or header[1:4] != (1, 20, 1):
        raise ValueError('Expected a big-endian ELF32 PowerPC relocatable object')
    if header[8] != 52 or header[10] != 0 or header[11] != 40:
        raise ValueError('Unsupported ELF header layout')
    if not 0 < header[12] < 0xFF00 or header[13] >= header[12]:
        raise ValueError('Unsupported section table layout')
    sections = [struct.unpack('>10I', chunk(header[6] + i * 40, 40))
                for i in range(header[12])]
    for section in sections:
        if section[1] != 8:
            chunk(section[4], section[5])
    names_header = sections[header[13]]
    if names_header[1] != 3:
        raise ValueError('Section names are not a string table')
    section_names = chunk(names_header[4], names_header[5])
    init = [(i, s) for i, s in enumerate(sections)
            if name(section_names, s[0]) == '.init']
    if len(init) != 1:
        raise ValueError('Expected exactly one .init section')
    init_index, init_header = init[0]
    if (init_header[1], init_header[3], init_header[5]) != (1, 0, SIZE) or init_header[2] & 6 != 6:
        raise ValueError('Expected only the 0x1F34-byte vector .init owner')
    tables = [s for s in sections if s[1] == 2]
    if len(tables) != 1:
        raise ValueError('Expected exactly one symbol table')
    table = tables[0]
    if table[9] != 16 or table[5] % 16 or table[6] >= len(sections):
        raise ValueError('Invalid symbol table layout')
    strings_header = sections[table[6]]
    if strings_header[1] != 3:
        raise ValueError('Symbol names are not a string table')
    strings = chunk(strings_header[4], strings_header[5])
    symbols = []
    for offset in range(0, table[5], 16):
        symbol = struct.unpack('>IIIBBH', chunk(table[4] + offset, 16))
        symbols.append((name(strings, symbol[0]), symbol, table[4] + offset))
    targets = [(s, offset) for n, s, offset in symbols if n == MARKER]
    if len(targets) != 1:
        raise ValueError('Expected exactly one synthetic vector marker')
    target, offset = targets[0]
    if target[1:] != (0, SIZE, 0x12, 2, init_index):
        raise ValueError('Marker must be the exact global hidden Function at .init+0')
    for label, value in [('gTRKInterruptVectorTable', 0), ('gTRKInterruptVectorTableEnd', SIZE)]:
        matches = [s for n, s, _ in symbols if n == label]
        if len(matches) != 1 or matches[0][1] != value or matches[0][5] != init_index:
            raise ValueError('Vector boundary labels do not match the expected owner')
    changed_offset = offset + 13  # Elf32_Sym.st_other, after st_info.
    output = bytearray(blob)
    output[changed_offset] = 0  # STV_HIDDEN -> STV_DEFAULT; STB_GLOBAL stays unchanged.
    if len(output) != len(blob) or [i for i, (a, b) in enumerate(zip(blob, output)) if a != b] != [changed_offset]:
        raise ValueError('The copy changed more than the one visibility byte')
    for section in sections:
        if section[1] != 2 and section[1] != 8:
            start, size = section[4], section[5]
            if output[start:start + size] != blob[start:start + size]:
                raise ValueError('Visibility byte overlaps another section payload')
    return bytes(output), changed_offset


def copy_file(source, destination):
    if source.resolve() == destination.resolve():
        raise ValueError('The report target and link copy must be distinct files')
    before = source.read_bytes()
    output, offset = default_visibility_copy(before)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        temporary.write(output)
    try:
        temporary_path.replace(destination)
    finally:
        temporary_path.unlink(missing_ok=True)
    if source.read_bytes() != before:
        raise ValueError('The original report target changed during the copy')
    return offset


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    offset = copy_file(args.source, args.destination)
    print(f'Link copy: only {MARKER} st_other changed 2->0 at file offset 0x{offset:X}')
