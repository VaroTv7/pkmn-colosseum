#!/usr/bin/env python3
"""Give only the original vector padding marker native local linker metadata.

The primary DTK target remains untouched for progress reporting. This separate
link copy preserves allocated bytes and section offsets. It moves the synthetic
marker to the end of the local symbol prefix, remapping the symbol-indexed
metadata emitted by pinned DTK. Public vector labels stay global. Any other
object importing the synthetic marker is left unchanged; the normal full link
must reject unresolved imports rather than silently retargeting them.
"""
import argparse
from pathlib import Path
import struct
import tempfile

MARKER = 'pad_00_800034AC_init'
SIZE = 0x1F34
COMMENT_HEADER = 0x2C
SHT_MWCATS = 0xCA2A82C2


def chunk(blob, offset, size):
    if offset < 0 or size < 0 or offset + size > len(blob):
        raise ValueError('ELF record extends beyond the file')
    return blob[offset:offset + size]


def string_at(table, offset):
    if offset < 0 or offset >= len(table):
        raise ValueError('ELF string offset is outside its table')
    end = table.find(b'\0', offset)
    if end < 0:
        raise ValueError('Unterminated ELF string')
    return table[offset:end].decode('ascii')


def payload(blob, section):
    return chunk(blob, section[4], section[5])


def read_vector(blob, marker_info=0x12, marker_visibility=2):
    header = struct.unpack('>16sHHIIIIIHHHHHH', chunk(blob, 0, 52))
    if header[0][:7] != b'\x7fELF\x01\x02\x01' or header[1:4] != (1, 20, 1):
        raise ValueError('Expected a big-endian ELF32 PowerPC relocatable object')
    if header[8] != 52 or header[10] != 0 or header[11] != 40:
        raise ValueError('Unsupported ELF header layout')
    if not 0 < header[12] < 0xFF00 or header[13] >= header[12]:
        raise ValueError('Unsupported section table layout')
    sections = [struct.unpack('>10I', chunk(blob, header[6] + i * 40, 40))
                for i in range(header[12])]
    names_header = sections[header[13]]
    if names_header[1] != 3:
        raise ValueError('Section names are not a string table')
    strings = payload(blob, names_header)
    names = [string_at(strings, section[0]) for section in sections]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate section names')
    expected_types = {'': 0, '.init': 1, '.symtab': 2, '.strtab': 3,
                      '.shstrtab': 3, '.comment': 1, '.rel.init': 9,
                      '.rela.init': 4, '.note.split': SHT_MWCATS}
    for name, section in zip(names, sections):
        if name not in expected_types or section[1] != expected_types[name]:
            raise ValueError(f'Unsupported section or symbol-indexed metadata: {name}')
        payload(blob, section)
        if section[2] & 2 and name != '.init':
            raise ValueError('Unexpected allocated section in vector fallback')
    occupied = [(0, 52), (header[6], header[6] + 40 * len(sections))]
    occupied += [(section[4], section[4] + section[5]) for section in sections if section[5]]
    previous_end = 0
    for start, end in sorted(occupied):
        if start < previous_end:
            raise ValueError('Overlapping ELF sections or headers')
        previous_end = end
    if '.init' not in names or '.symtab' not in names:
        raise ValueError('Expected the vector section and its symbol table')
    init_index, table_index = names.index('.init'), names.index('.symtab')
    init, table = sections[init_index], sections[table_index]
    if (init[1], init[3], init[5]) != (1, 0, SIZE) or init[2] & 6 != 6:
        raise ValueError('Expected only the 0x1F34-byte vector .init owner')
    if table[9] != 16 or table[5] % 16 or table[6] >= len(sections):
        raise ValueError('Invalid symbol table layout')
    strings_header = sections[table[6]]
    if strings_header[1] != 3:
        raise ValueError('Symbol names are not a string table')
    strings = payload(blob, strings_header)
    symbols = []
    for offset in range(0, table[5], 16):
        symbol = struct.unpack('>IIIBBH', chunk(blob, table[4] + offset, 16))
        if symbol[3] >> 4 not in (0, 1, 2) or \
                (symbol[5] not in (0, 0xFFF1) and symbol[5] >= len(sections)):
            raise ValueError('Unsupported symbol binding or section index')
        symbols.append((string_at(strings, symbol[0]), symbol))
    if not symbols or symbols[0][1] != (0, 0, 0, 0, 0, 0):
        raise ValueError('Invalid null symbol')
    boundary = table[7]
    if not 1 <= boundary <= len(symbols) or any(
            (symbol[3] >> 4 == 0) != (i < boundary)
            for i, (_, symbol) in enumerate(symbols)):
        raise ValueError('Symbol table ordering disagrees with sh_info')
    targets = [i for i, (name, _) in enumerate(symbols) if name == MARKER]
    if len(targets) != 1:
        raise ValueError('Expected exactly one synthetic vector marker')
    marker_index = targets[0]
    if symbols[marker_index][1][1:] != (0, SIZE, marker_info, marker_visibility, init_index):
        raise ValueError('Marker does not have the expected binding, visibility, or extent')
    for label, value in [('gTRKInterruptVectorTable', 0), ('gTRKInterruptVectorTableEnd', SIZE)]:
        matches = [symbol for name, symbol in symbols if name == label]
        if len(matches) != 1 or matches[0][1:] != (value, 0, 0x10, 0, init_index):
            raise ValueError('Public vector boundary labels do not match the expected owner')
    return header, sections, names, symbols, table_index, marker_index


def comment_records(blob, sections, names, count):
    if '.comment' not in names:
        raise ValueError('Missing CodeWarrior symbol metadata')
    section = sections[names.index('.comment')]
    data = payload(blob, section)
    if len(data) != COMMENT_HEADER + 8 * count or data[:11] != b'CodeWarrior' or \
            data[11] != 8 or data[20] != COMMENT_HEADER:
        raise ValueError('Unexpected CodeWarrior per-symbol metadata layout')
    return section[4] + COMMENT_HEADER, [data[COMMENT_HEADER + 8*i:COMMENT_HEADER + 8*(i+1)]
                                        for i in range(count)]


def virtual_records(blob, sections, names, count):
    if '.note.split' not in names:
        raise ValueError('Missing DTK split metadata')
    section = sections[names.index('.note.split')]
    data = payload(blob, section)
    position, found = 0, []
    while position < len(data):
        name_size, desc_size, kind = struct.unpack('>III', chunk(data, position, 12))
        note_name = chunk(data, position + 12, name_size)
        desc_start = (position + 12 + name_size + 3) & ~3
        desc = chunk(data, desc_start, desc_size)
        if note_name != b'Split\0' or kind.to_bytes(4, 'big') not in (b'GENR', b'MODN', b'MODI', b'VIRT'):
            raise ValueError('Unsupported DTK split note')
        if kind == int.from_bytes(b'VIRT', 'big'):
            if desc_size != 4 * count:
                raise ValueError('VIRT metadata does not match the symbol count')
            found.append((section[4] + desc_start, [desc[4*i:4*(i+1)] for i in range(count)]))
        position = (desc_start + desc_size + 3) & ~3
        if position > len(data):
            raise ValueError('Truncated DTK split note padding')
    if len(found) != 1:
        raise ValueError('Expected exactly one VIRT symbol-address table')
    return found[0]


def relocations(blob, sections, names, symbols, table_index):
    result = []
    for name, section in zip(names, sections):
        if section[1] not in (4, 9):
            if section[6] == table_index and name != '.symtab':
                raise ValueError('Unsupported reference to the symbol table')
            continue
        stride = 12 if section[1] == 4 else 8
        if section[9] != stride or section[5] % stride or section[6] != table_index or \
                section[7] != names.index('.init'):
            raise ValueError('Unsupported relocation table layout')
        for offset in range(0, section[5], stride):
            file_offset = section[4] + offset
            record = chunk(blob, file_offset, stride)
            address, info = struct.unpack('>II', record[:8])
            symbol_index = info >> 8
            if symbol_index >= len(symbols) or address >= SIZE:
                raise ValueError('Invalid relocation target or source offset')
            result.append((file_offset + 4, symbol_index, info & 0xFF,
                           (name, address, record[8:], symbols[symbol_index])))
    return result


def local_link_copy(blob):
    header, sections, names, symbols, table_index, marker = read_vector(blob)
    table = sections[table_index]
    boundary, count = table[7], len(symbols)
    order = list(range(boundary)) + [marker] + [i for i in range(boundary, count) if i != marker]
    old_to_new = {old: new for new, old in enumerate(order)}
    comment_offset, comments = comment_records(blob, sections, names, count)
    virtual_offset, virtuals = virtual_records(blob, sections, names, count)
    if virtuals[marker] != struct.pack('>I', 0x800034AC):
        raise ValueError('Vector marker has an unexpected original address')
    before_relocations = relocations(blob, sections, names, symbols, table_index)
    raw_symbols = [chunk(blob, table[4] + 16*i, 16) for i in range(count)]
    local_marker = bytearray(raw_symbols[marker])
    local_marker[12:14] = b'\x02\x00'  # STB_LOCAL|STT_FUNC, STV_DEFAULT.
    raw_symbols[marker] = bytes(local_marker)
    patches = [
        (table[4], b''.join(raw_symbols[i] for i in order)),
        (header[6] + table_index * 40 + 28, struct.pack('>I', boundary + 1)),
        (comment_offset, b''.join(comments[i] for i in order)),
        (virtual_offset, b''.join(virtuals[i] for i in order)),
    ]
    for offset, old_index, kind, _ in before_relocations:
        patches.append((offset, struct.pack('>I', (old_to_new[old_index] << 8) | kind)))
    output = bytearray(blob)
    previous_end = 52
    for offset, data in sorted(patches):
        if offset < previous_end:
            raise ValueError('Overlapping symbol metadata or ELF header')
        chunk(blob, offset, len(data))
        output[offset:offset + len(data)] = data
        previous_end = offset + len(data)
    output = bytes(output)
    after_header, after_sections, after_names, after_symbols, after_table_index, after_marker = \
        read_vector(output, marker_info=0x02, marker_visibility=0)
    if len(output) != len(blob) or header != after_header or names != after_names or table_index != after_table_index:
        raise ValueError('ELF structure changed while localizing the marker')
    for i, (before, after) in enumerate(zip(sections, after_sections)):
        expected = list(before)
        if i == table_index:
            expected[7] = boundary + 1
        if tuple(expected) != after:
            raise ValueError('Section layout changed while localizing the marker')
        if before[2] & 2 or names[i] not in ('.symtab', '.comment', '.note.split', '.rel.init', '.rela.init'):
            if payload(blob, before) != payload(output, after):
                raise ValueError('Allocated or unrelated section payload changed')
    expected_symbols = [(symbols[i][0], struct.unpack('>IIIBBH', raw_symbols[i])) for i in order]
    if after_symbols != expected_symbols or after_marker != boundary:
        raise ValueError('Symbol identities changed while localizing the marker')
    if comment_records(output, after_sections, after_names, count)[1] != [comments[i] for i in order] or \
            virtual_records(output, after_sections, after_names, count)[1] != [virtuals[i] for i in order]:
        raise ValueError('Per-symbol metadata was not preserved')
    after_relocations = relocations(output, after_sections, after_names, after_symbols, after_table_index)
    normalized_before = []
    for offset, old_index, kind, (name, address, addend, target) in before_relocations:
        target = (target[0], struct.unpack('>IIIBBH', raw_symbols[old_index]))
        normalized_before.append((offset, kind, name, address, addend, target))
    normalized_after = [(offset, kind, *identity) for offset, _, kind, identity in after_relocations]
    if normalized_before != normalized_after:
        raise ValueError('Relocation semantics changed while localizing the marker')
    moved = sum(new != old for new, old in enumerate(order))
    return output, dict(old_marker=marker, new_marker=after_marker,
                        old_boundary=boundary, new_boundary=boundary + 1,
                        symbol_records=moved, comment_records=moved, virt_records=moved,
                        relocation_records=sum(old_to_new[index] != index for _, index, _, _ in before_relocations),
                        relocations_checked=len(before_relocations))


def copy_file(source, destination):
    if source.resolve() == destination.resolve():
        raise ValueError('The report target and link copy must be distinct files')
    before = source.read_bytes()
    output, summary = local_link_copy(before)
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
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    summary = copy_file(args.source, args.destination)
    print('Vector link copy: marker index {old_marker}->{new_marker}; local boundary '
          '{old_boundary}->{new_boundary}; remapped {symbol_records} symbol, '
          '{comment_records} comment, {virt_records} VIRT, {relocation_records} relocation '
          'records ({relocations_checked} relocations checked); allocated payloads unchanged.'
          .format(**summary))
