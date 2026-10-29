#!/usr/bin/env python3
"""Make narrowly verified metadata views of compiled PowerPC source objects.

``names`` changes only anonymous data-symbol names for comparison. objdiff
v3.6.1's report command does not apply project symbol_mappings. The native
object remains the linker input; no symbol size, value, binding, relocation,
code or data changes in this view.

``align`` makes a source-link copy for independently carved data owners.
MWCC emits an eight-byte section alignment even when every source object
requires at most four. A four-byte section boundary is accepted only after
checking all bytes, symbol extents and relocation semantics against the
immutable target, and the compiler's own per-symbol alignment records. Only
the section header and its section/section-base alignment records change. The
native source object remains the comparison input.

No target payload is ever copied to either output.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import tempfile

DATA = {".rodata", ".data", ".sdata", ".sdata2"}
ZERO = {".bss", ".sbss", ".sbss2"}


def bounded(blob, start, size):
    if start < 0 or size < 0 or start + size > len(blob):
        raise ValueError("ELF record extends beyond the file")
    return blob[start:start + size]


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
        h = struct.unpack(">16sHHIIIIIHHHHHH", bounded(blob, 0, 52))
        if h[0][:7] != b"\x7fELF\x01\x02\x01" or h[1:4] != (1, 20, 1):
            raise ValueError("Expected big-endian ELF32 PowerPC relocatable object")
        if h[8] != 52 or h[9] or h[10] or h[11] != 40 or not 0 < h[12] < 0xFF00:
            raise ValueError("Unsupported ELF header layout")
        self.header = h
        self.sections = [struct.unpack(">10I", bounded(blob, h[6] + i * 40, 40))
                         for i in range(h[12])]
        if self.sections[0] != (0,) * 10 or not 0 < h[13] < len(self.sections):
            raise ValueError("Invalid ELF null section or section-name table")
        if self.sections[h[13]][1] != 3:
            raise ValueError("Invalid section-name string table")
        strings = self.payload(h[13])
        self.names = [string_at(strings, s[0]) for s in self.sections]
        if len(set(self.names)) != len(self.names):
            raise ValueError("Duplicate section names")
        spans = [(0, 52), (h[6], h[6] + h[12] * 40)]
        self.allocated = {}
        for i, s in enumerate(self.sections):
            if s[3] or s[8] and s[8] & (s[8] - 1):
                raise ValueError("Invalid section-relative address or alignment")
            if s[1] != 8:
                bounded(blob, s[4], s[5])
                if s[5]:
                    spans.append((s[4], s[4] + s[5]))
            if s[2] & 2 and s[5]:
                self.allocated[self.names[i]] = i
        end = 0
        for a, b in sorted(spans):
            if a < end:
                raise ValueError("Overlapping ELF records")
            end = b
        tables = [i for i, s in enumerate(self.sections) if s[1] == 2]
        if len(tables) != 1:
            raise ValueError("Expected one symbol table")
        self.symtab = tables[0]
        table = self.sections[self.symtab]
        if table[9] != 16 or table[5] % 16 or not 0 < table[6] < len(self.sections) \
                or self.sections[table[6]][1] != 3:
            raise ValueError("Invalid symbol table")
        strings = self.payload(table[6])
        self.symbols = []
        for at in range(0, table[5], 16):
            s = struct.unpack_from(">IIIBBH", self.payload(self.symtab), at)
            if s[3] >> 4 not in (0, 1, 2) or s[5] not in (0, 0xFFF1) \
                    and not 0 < s[5] < len(self.sections):
                raise ValueError("Unsupported symbol binding or section index")
            if 0 < s[5] < len(self.sections) and s[1] + s[2] > self.sections[s[5]][5]:
                raise ValueError("Symbol extends beyond its section")
            self.symbols.append((string_at(strings, s[0]), s))
        if not self.symbols or self.symbols[0][1] != (0,) * 6:
            raise ValueError("Invalid null symbol")
        if not 1 <= table[7] <= len(self.symbols) or any(
                (s[3] >> 4 == 0) != (i < table[7])
                for i, (_, s) in enumerate(self.symbols)):
            raise ValueError("Symbol ordering disagrees with sh_info")

    def payload(self, index):
        s = self.sections[index]
        if s[1] == 8:
            raise ValueError("NOBITS section has no file payload")
        return bounded(self.blob, s[4], s[5])

    def unique_symbol(self, name):
        found = [(i, s) for i, (n, s) in enumerate(self.symbols) if n == name]
        if len(found) != 1:
            raise ValueError(f"Expected exactly one symbol named {name}")
        return found[0]

    def data_relocations(self):
        result = {}
        for index, s in enumerate(self.sections):
            if s[1] == 9 and s[5]:
                raise ValueError("Implicit relocations are unsupported")
            if s[1] != 4 or not s[5]:
                continue
            if s[9] != 12 or s[5] % 12 or s[6] != self.symtab \
                    or s[7] not in self.allocated.values():
                raise ValueError("Invalid data relocation table")
            site = self.sections[s[7]]
            for at in range(0, s[5], 12):
                offset, info, addend = struct.unpack_from(">IIi", self.payload(index), at)
                symbol_index, kind = info >> 8, info & 255
                if kind != 1 or offset % 4 or offset + 4 > site[5] \
                        or not 0 < symbol_index < len(self.symbols):
                    raise ValueError("Expected aligned ADDR32 data relocations")
                name, symbol = self.symbols[symbol_index]
                if symbol[5] == 0:
                    identity = ("external", name, addend)
                elif symbol[5] in self.allocated.values():
                    address = symbol[1] + addend
                    if not 0 <= address <= self.sections[symbol[5]][5]:
                        raise ValueError("Relocation target is outside data")
                    identity = ("section", self.names[symbol[5]], address)
                else:
                    raise ValueError("Unsupported data relocation target")
                key = (self.names[s[7]], offset)
                if key in result:
                    raise ValueError("Duplicate data relocation site")
                result[key] = (kind, identity)
        return result


def comparison_names(source_blob, target_blob, mappings):
    source, target = Elf(source_blob), Elf(target_blob)
    if not isinstance(mappings, dict) or not mappings \
            or any(not isinstance(k, str) or not k or not isinstance(v, str) or not v
                   for k, v in mappings.items()) \
            or len(set(mappings.values())) != len(mappings):
        raise ValueError("Expected unambiguous target-to-source symbol mappings")
    output = bytearray(source_blob)
    table = source.sections[source.symtab]
    strings_index = table[6]
    strings = bytearray(source.payload(strings_index))
    for target_name, source_name in mappings.items():
        if not re.fullmatch(r"@\d+", source_name):
            raise ValueError("Only anonymous compiler data symbols may be named")
        index, s = source.unique_symbol(source_name)
        _, t = target.unique_symbol(target_name)
        if any(n == target_name for n, _ in source.symbols):
            raise ValueError(f"Source already defines comparison name {target_name}")
        if s[3] != 1 or t[3] & 15 != 1 or not s[2] or s[2] != t[2] \
                or s[4] or t[4] or s[5] not in source.allocated.values() \
                or t[5] not in target.allocated.values():
            raise ValueError("Comparison names require equal, defined data-object extents")
        section_name = source.names[s[5]]
        section_type = 8 if section_name in ZERO else 1
        if section_name not in DATA | ZERO or section_name != target.names[t[5]] \
                or source.sections[s[5]][1] != section_type \
                or target.sections[t[5]][1] != section_type:
            raise ValueError("Comparison names require the same data section and kind")
        offset = len(strings)
        strings.extend(target_name.encode("ascii") + b"\0")
        struct.pack_into(">I", output, table[4] + index * 16, offset)
    # Append a fresh string table without moving or rewriting any source data,
    # relocation, symbol index, section index or other metadata record.
    new_offset = len(output)
    output.extend(strings)
    struct.pack_into(">II", output, source.header[6] + strings_index * 40 + 16,
                     new_offset, len(strings))
    result = bytes(output)
    checked = Elf(result)
    for i, section in enumerate(source.sections):
        if i not in (source.symtab, strings_index) and section[1] != 8 \
                and source.payload(i) != checked.payload(i):
            raise AssertionError("Comparison naming changed an unrelated section")
    for (_, before), (_, after) in zip(source.symbols, checked.symbols):
        if before[1:] != after[1:]:
            raise AssertionError("Comparison naming changed symbol identity or extent")
    return result, {"mode": "comparison_names", "symbols_named": len(mappings),
                    "allocated_bytes_changed": 0, "relocation_records_changed": 0}


def data_alignment(source_blob, target_blob, alignment):
    if alignment != 4:
        raise ValueError("Only the verified eight-to-four data alignment is supported")
    source, target = Elf(source_blob), Elf(target_blob)
    if len(source.allocated) != 1 or source.allocated.keys() != target.allocated.keys():
        raise ValueError("Alignment copies require one matching data-only section")
    name, index = next(iter(source.allocated.items()))
    ti = target.allocated[name]
    s, t = source.sections[index], target.sections[ti]
    if name not in (".data", ".rodata") or s[1] != 1 or t[1] != 1 \
            or s[2] & 4 or (s[1], s[2], s[5]) != (t[1], t[2], t[5]) \
            or s[8] != 8 or t[8] != 4:
        raise ValueError("Expected equal data extents with source alignment eight and target four")
    if source.payload(index) != target.payload(ti):
        raise ValueError("Source data bytes differ from target")
    relocations = source.data_relocations()
    if relocations != target.data_relocations():
        raise ValueError("Source data relocation semantics differ from target")
    expected = {n: sym for n, sym in target.symbols
                if sym[5] == ti and sym[2] and sym[3] & 15 != 3 and not sym[4] & 2}
    if not expected:
        raise ValueError("Target has no independent data-object extents")
    for n, wanted in expected.items():
        _, actual = source.unique_symbol(n)
        if wanted[3] & 15 != 1 or actual[3] & 15 != 1 or actual[5] != index \
                or actual[1:3] != wanted[1:3]:
            raise ValueError(f"Source symbol extent differs: {n}")
    gaps = []
    for n, sym in target.symbols:
        if sym[5] != ti or not sym[2] or not sym[4] & 2:
            continue
        if sym[4] != 2 or sym[3] & 15 != 1 or not re.fullmatch(
                r"gap_\d+_[0-9A-Fa-f]{8}_" + re.escape(name[1:]), n) \
                or any(target.payload(ti)[sym[1]:sym[1] + sym[2]]):
            raise ValueError("Hidden target object is not a generated zero-padding gap")
        gaps.append((sym[1], sym[1] + sym[2]))
    gaps.sort()
    cursor = 0
    for start, end in sorted([(x[1], x[1] + x[2]) for x in expected.values()] + gaps):
        if start != cursor:
            raise ValueError("Data section contains storage without independent extents")
        cursor = end
    if cursor != s[5]:
        raise ValueError("Data section contains uncovered trailing storage")
    for n, sym in source.symbols:
        if sym[5] != index or not sym[2] or sym[3] & 15 == 3 or n in expected:
            continue
        if sym[3] & 15 != 1 or not any(a <= sym[1] and sym[1] + sym[2] <= b
                                                      for a, b in gaps) \
                or any(source.payload(index)[sym[1]:sym[1] + sym[2]]):
            raise ValueError(f"Unexpected source storage symbol: {n}")
    if ".comment" not in source.names:
        raise ValueError("Missing compiler per-symbol alignment records")
    ci = source.names.index(".comment")
    comment = source.payload(ci)
    if comment[:11] != b"CodeWarrior" or len(comment) != 44 + 8 * len(source.symbols) \
            or comment[11] not in (8, 10, 11, 13, 14, 15) or comment[20] != 44 \
            or comment[16] not in (0, 1) or comment[17] not in (0, 1, 2) \
            or comment[21] & ~7 or any(comment[22:44]):
        raise ValueError("Unsupported CodeWarrior alignment metadata")
    output = bytearray(source_blob)
    struct.pack_into(">I", output, source.header[6] + index * 40 + 32, alignment)
    section_records = 0
    pool_records = 0
    object_records = 0
    for i, (n, sym) in enumerate(source.symbols):
        at = 44 + i * 8
        required, visibility, active, padding = struct.unpack_from(">IBBH", comment, at)
        if visibility not in (0, 0xD, 0xE) or active not in (0, 8, 16, 32) or padding:
            raise ValueError("Unknown CodeWarrior symbol alignment record")
        if sym[5] != index:
            continue
        if sym[3] & 15 == 3:
            if required != 8 or sym[1] or sym[2]:
                raise ValueError("Unsupported section-symbol alignment record")
            struct.pack_into(">I", output, source.sections[ci][4] + at, alignment)
            section_records += 1
        elif sym[3] == 0 and sym[1] == 0 and sym[2] == 0 \
                and n == "..." + name[1:] + ".0":
            # MWCC's untyped, zero-sized pool marker aliases the section base;
            # it is not a C storage object. All real objects in the pool must
            # independently pass the <=4 requirement below. Preserve smaller
            # requirements; lower a duplicated section alignment explicitly.
            if required not in (1, 2, 4, 8):
                raise ValueError("Unsupported compiler pool-base alignment")
            if required == 8:
                struct.pack_into(">I", output, source.sections[ci][4] + at, alignment)
                pool_records += 1
        else:
            if sym[3] & 15 != 1 or required not in (1, 2, 4) or sym[1] % required:
                raise ValueError(f"Source symbol requires unsupported alignment: {n} ({required})")
            object_records += 1
    if section_records != 1 or not object_records:
        raise ValueError("Missing independent section/object alignment evidence")
    result = bytes(output)
    checked = Elf(result)
    if source.symbols != checked.symbols or source.data_relocations() != checked.data_relocations() \
            or source.payload(index) != checked.payload(index):
        raise AssertionError("Alignment copy changed source content")
    return result, {"mode": "source_link_alignment", "section": name,
                    "from_alignment": 8, "to_alignment": 4,
                    "data_bytes_verified": s[5], "symbol_extents_verified": len(expected),
                    "compiler_alignments_verified": object_records,
                    "section_pool_alignments_adjusted": pool_records,
                    "relocations_verified": len(relocations), "allocated_bytes_changed": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("names", "align"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mappings", type=Path)
    parser.add_argument("--alignment", type=int)
    args = parser.parse_args()
    if args.output.resolve() in (args.source.resolve(), args.target.resolve()):
        parser.error("Output must be separate from native source and target")
    source, target = args.source.read_bytes(), args.target.read_bytes()
    if args.mode == "names":
        if args.mappings is None or args.alignment is not None:
            parser.error("names requires --mappings only")
        output, summary = comparison_names(source, target, json.loads(args.mappings.read_text()))
    else:
        if args.alignment is None or args.mappings is not None:
            parser.error("align requires --alignment only")
        output, summary = data_alignment(source, target, args.alignment)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(output)
    temporary.replace(args.output)
    summary.update(source_sha256=hashlib.sha256(source).hexdigest(),
                   output_sha256=hashlib.sha256(output).hexdigest())
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
