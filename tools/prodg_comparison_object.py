#!/usr/bin/env python3
"""Make a comparison-only view of a ProDG data object.

SN's assembler duplicates explicit RELA addends in the relocated data words.
DTK's extracted comparison objects zero those words. The native source object
must keep them for the retail REL link, so this tool writes a separate copy.
It never reads target bytes into the output. Every relocation must have the
same site, type and resolved section/offset (or external symbol/addend), and
every remaining byte must already be equal. Compiler-local literal labels
receive source-derived sizes so objdiff can compare the whole literal pool.

Only data-only, big-endian ELF32 PowerPC objects with explicit ADDR32 RELA
relocations are supported. Unsupported layouts and differences fail closed.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import tempfile


def chunk(blob, offset, size):
    if offset < 0 or size < 0 or offset + size > len(blob):
        raise ValueError("ELF record extends beyond the file")
    return blob[offset:offset + size]


def string_at(table, offset):
    if not 0 <= offset < len(table):
        raise ValueError("ELF string offset is outside its table")
    end = table.find(b"\0", offset)
    if end < 0:
        raise ValueError("Unterminated ELF string")
    return table[offset:end].decode("ascii")


class Elf:
    def __init__(self, blob):
        self.blob = blob
        h = struct.unpack(">16sHHIIIIIHHHHHH", chunk(blob, 0, 52))
        if h[0][:7] != b"\x7fELF\x01\x02\x01" or h[1:4] != (1, 20, 1):
            raise ValueError("Expected a big-endian ELF32 PowerPC relocatable object")
        if h[8] != 52 or h[9] or h[10] or h[11] != 40 or not 0 < h[12] < 0xFF00:
            raise ValueError("Unsupported ELF header layout")
        self.sections = [struct.unpack(">10I", chunk(blob, h[6] + i * 40, 40))
                         for i in range(h[12])]
        if h[13] >= len(self.sections) or self.sections[h[13]][1] != 3:
            raise ValueError("Invalid section-name table")
        strings = self.payload(h[13])
        self.names = [string_at(strings, s[0]) for s in self.sections]
        if len(set(self.names)) != len(self.names):
            raise ValueError("Duplicate section names")
        if self.sections[0] != (0,) * 10:
            raise ValueError("Invalid null section")
        spans = [(0, 52), (h[6], h[6] + h[12] * 40)]
        for s in self.sections:
            if s[1] != 8:
                chunk(blob, s[4], s[5])
                if s[5]:
                    spans.append((s[4], s[4] + s[5]))
            if s[3] != 0:
                raise ValueError("Object sections must use section-relative addresses")
        previous = 0
        for start, end in sorted(spans):
            if start < previous:
                raise ValueError("Overlapping ELF records")
            previous = end
        self.allocated = {}
        for i, s in enumerate(self.sections):
            if s[2] & 2 and s[5]:
                name = self.names[i]
                if name not in (".data", ".rodata") or s[1] != 1 or s[2] & 4:
                    raise ValueError("Expected only nonempty .data and .rodata sections")
                self.allocated[name] = i
        if set(self.allocated) != {".data", ".rodata"}:
            raise ValueError("Expected a data table and its literal pool")
        tables = [i for i, s in enumerate(self.sections) if s[1] == 2]
        if len(tables) != 1:
            raise ValueError("Expected one symbol table")
        self.table_index = tables[0]
        table = self.sections[self.table_index]
        if table[9] != 16 or table[5] % 16 or table[6] >= len(self.sections) or \
                self.sections[table[6]][1] != 3:
            raise ValueError("Invalid symbol-table layout")
        strings = self.payload(table[6])
        self.symbols = []
        for offset in range(0, table[5], 16):
            fields = struct.unpack(">IIIBBH", chunk(blob, table[4] + offset, 16))
            name = string_at(strings, fields[0])
            section = fields[5]
            if fields[3] >> 4 not in (0, 1, 2) or \
                    section not in (0, 0xFFF1) and not 0 < section < len(self.sections):
                raise ValueError("Unsupported symbol binding or section index")
            if 0 < section < len(self.sections) and \
                    fields[1] + fields[2] > self.sections[section][5]:
                raise ValueError("Symbol extends beyond its section")
            self.symbols.append((name, fields))
        if not self.symbols or self.symbols[0][1] != (0,) * 6:
            raise ValueError("Invalid null symbol")
        if not 1 <= table[7] <= len(self.symbols) or any(
                (s[3] >> 4 == 0) != (i < table[7])
                for i, (_, s) in enumerate(self.symbols)):
            raise ValueError("Symbol ordering disagrees with sh_info")

    def payload(self, index):
        s = self.sections[index]
        return chunk(self.blob, s[4], s[5])

    def relocations(self):
        result = {}
        for index, s in enumerate(self.sections):
            if s[1] == 9 and s[5]:
                raise ValueError("Implicit REL relocations are unsupported")
            if s[1] != 4:
                continue
            if s[9] != 12 or s[5] % 12 or s[6] != self.table_index or \
                    s[7] not in self.allocated.values():
                raise ValueError("Unsupported relocation-table layout")
            site_section = self.sections[s[7]]
            for at in range(0, s[5], 12):
                offset, info, addend = struct.unpack_from(">IIi", self.payload(index), at)
                symbol_index, kind = info >> 8, info & 255
                if kind != 1 or offset % 4 or offset + 4 > site_section[5] or \
                        not 0 < symbol_index < len(self.symbols):
                    raise ValueError("Expected aligned R_PPC_ADDR32 data relocations")
                symbol_name, symbol = self.symbols[symbol_index]
                if symbol[5] == 0:
                    identity = ("external", symbol_name, addend)
                    in_place = addend & 0xFFFFFFFF
                elif symbol[5] in self.allocated.values():
                    address = symbol[1] + addend
                    if not 0 <= address < self.sections[symbol[5]][5]:
                        raise ValueError("Relocation target is outside allocated data")
                    identity = ("section", self.names[symbol[5]], address)
                    in_place = address
                else:
                    raise ValueError("Unsupported relocation target")
                key = (self.names[s[7]], offset)
                if key in result:
                    raise ValueError("Duplicate relocation site")
                result[key] = (kind, identity, in_place)
        if not result:
            raise ValueError("Expected explicit data relocations")
        return result


def comparison_copy(source_blob, target_blob):
    source, target = Elf(source_blob), Elf(target_blob)
    for name, index in source.allocated.items():
        a, b = source.sections[index], target.sections[target.allocated[name]]
        if (a[1], a[2] & 7, a[5]) != (b[1], b[2] & 7, b[5]):
            raise ValueError(f"Allocated section layout differs: {name}")
    before_relocations, target_relocations = source.relocations(), target.relocations()
    if before_relocations != target_relocations:
        raise ValueError("Source and target relocation semantics differ")
    output = bytearray(source_blob)
    normalized = []
    for (name, offset), (_, identity, expected) in before_relocations.items():
        source_at = source.sections[source.allocated[name]][4] + offset
        target_at = target.sections[target.allocated[name]][4] + offset
        word = struct.unpack_from(">I", source_blob, source_at)[0]
        if struct.unpack_from(">I", target_blob, target_at)[0] != 0:
            raise ValueError("Target relocation word is not normalized")
        if word not in (0, expected):
            raise ValueError("Source relocation word is not its explicit addend")
        if word:
            if identity[0] != "section":
                raise ValueError("Only section-relative duplicate addends are normalized")
            output[source_at:source_at + 4] = bytes(4)
            normalized.append((name, offset))
    # No bytes are copied from the target: compare the independently normalized
    # source against it and reject all other differences, including padding.
    for name, index in source.allocated.items():
        s = source.sections[index]
        actual = bytes(output[s[4]:s[4] + s[5]])
        if actual != target.payload(target.allocated[name]):
            raise ValueError(f"Non-relocation bytes differ: {name}")

    # GCC's .LC labels have no size/type. objdiff intentionally excludes these
    # labels from size inference, making an otherwise equal pool unmeasurable.
    # Give those existing source labels extents bounded by the next label or
    # section end. The native object, label values and relocation indices stay.
    rodata = source.allocated[".rodata"]
    labels = [(i, s) for i, (name, s) in enumerate(source.symbols)
              if s[5] == rodata and re.fullmatch(r"\.LC\d+", name)]
    named = [(i, s) for i, (_, s) in enumerate(source.symbols)
             if s[5] == rodata and s[2] and s[3] & 15 == 1]
    if not labels and not named:
        raise ValueError("Literal pool needs source-owned literal extents")
    if labels and min(s[1] for _, s in labels) != 0:
        raise ValueError("Literal pool needs compiler-local .LC labels starting at zero")
    if named:
        if labels:
            raise ValueError("Mixed sized and compiler-local literal metadata")
        pool = source.payload(rodata)
        cursor = 0
        for _, symbol in sorted(named, key=lambda row: row[1][1]):
            start, size = symbol[1:3]
            if start < cursor or any(pool[cursor:start]):
                raise ValueError("Named literal extents overlap or leave nonzero gaps")
            value = pool[start:start + size]
            if not value or value[-1] != 0 or 0 in value[:-1]:
                raise ValueError("Named literal extent is not one terminated source string")
            cursor = start + size
        if any(pool[cursor:]):
            raise ValueError("Named literal extents leave nonzero trailing data")
    if any(s[2] or s[3] != 0 or s[4] != 0 for _, s in labels):
        raise ValueError("Unexpected compiler-local literal metadata")
    ends = sorted({s[1] for _, s in labels} | {source.sections[rodata][5]})
    table_at = source.sections[source.table_index][4]
    for index, s in labels:
        next_offset = next((x for x in ends if x > s[1]), None)
        if next_offset is None:
            raise ValueError("Literal label does not own any source bytes")
        struct.pack_into(">IIIBBH", output, table_at + index * 16,
                         s[0], s[1], next_offset - s[1], 1, s[4], s[5])
    after = Elf(bytes(output))
    if after.relocations() != before_relocations:
        raise ValueError("Comparison copy changed relocation semantics")
    allowed = set()
    for name, offset in normalized:
        start = source.sections[source.allocated[name]][4] + offset
        allowed.update(range(start, start + 4))
    for index, _ in labels:
        allowed.update(range(table_at + index * 16 + 8, table_at + index * 16 + 13))
    if len(output) != len(source_blob) or any(
            a != b and i not in allowed for i, (a, b) in enumerate(zip(source_blob, output))):
        raise ValueError("Comparison copy changed unrelated object bytes")
    return bytes(output), {
        "source_sha256": hashlib.sha256(source_blob).hexdigest(),
        "target_sha256": hashlib.sha256(target_blob).hexdigest(),
        "comparison_sha256": hashlib.sha256(output).hexdigest(),
        "relocations_verified": len(before_relocations),
        "duplicate_addend_words_normalized": len(normalized),
        "literal_labels_sized": len(labels),
        "named_literal_objects_verified": len(named),
        "data_bytes_verified": sum(source.sections[i][5] for i in source.allocated.values()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in (args.source.resolve(), args.target.resolve()):
        parser.error("comparison output must not replace either input")
    output, summary = comparison_copy(args.source.read_bytes(), args.target.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as temporary:
        temporary.write(output)
        temporary_path = Path(temporary.name)
    temporary_path.replace(args.output)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
