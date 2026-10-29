#!/usr/bin/env python3
"""Preserve real C arrays while exposing their historical interior data names.

The native compiler object remains immutable. A link view adds zero-size ELF
labels inside explicitly registered arrays; every original C object keeps its
full extent. A separate comparison view describes the same source bytes using
the target's historical nonoverlapping fragments and verified zero gaps.
Only symbol/string/CodeWarrior-comment metadata changes in either view. No
target payload, code, relocation, section alignment or allocated byte is copied
or changed. Full native array bounds are validated before either view exists.
"""

import argparse
import json
from pathlib import Path
import re
import struct
import tempfile

if __package__:
    from .source_object_metadata import Elf
else:
    from source_object_metadata import Elf


def require(condition, message):
    if not condition:
        raise ValueError(message)


def comment_records(source):
    require(".comment" in source.names, "Missing native compiler metadata")
    index = source.names.index(".comment")
    data = source.payload(index)
    require(data[:11] == b"CodeWarrior" and len(data) == 44 + 8 * len(source.symbols)
            and data[11] in (8, 10, 11, 13, 14, 15) and data[20] == 44
            and data[16] in (0, 1) and data[17] in (0, 1, 2)
            and not data[21] & ~7 and not any(data[22:44]),
            "Unsupported native compiler metadata")
    for offset in range(44, len(data), 8):
        alignment, visibility, active, reserved = struct.unpack_from(">IBBH", data, offset)
        require(alignment in (0, 1, 2, 4, 8, 16, 32)
                and visibility in (0, 0xD, 0xE) and active in (0, 8, 16, 32)
                and not reserved, "Unsupported native symbol metadata")
    return index, data


def validate(source, target, groups):
    require(isinstance(groups, list) and groups, "Expected registered array aliases")
    require(set(source.allocated) == {".sdata"} == set(target.allocated),
            "Alias views require one initialized small-data section")
    si, ti = source.allocated[".sdata"], target.allocated[".sdata"]
    s, t = source.sections[si], target.sections[ti]
    require((s[1], s[2], s[5], s[8]) == (t[1], t[2], t[5], t[8])
            and s[1:3] == (1, 3), "Native and target section extents/flags/alignment differ")
    require(source.payload(si) == target.payload(ti), "Native source bytes differ")
    require(source.data_relocations() == target.data_relocations(),
            "Native source relocation semantics differ")
    allowed = {"", ".sdata", ".rela.sdata", ".symtab", ".strtab", ".shstrtab", ".comment"}
    require(set(source.names) <= allowed, "Unknown native symbol-indexed metadata")
    comment_records(source)

    originals, gaps = {}, {}
    target_spans = []
    for name, sym in target.symbols:
        if sym[5] != ti or sym[3] & 15 == 3:
            continue
        require(sym[2] > 0 and sym[3] == 0x11, "Unexpected target data symbol kind")
        require(name not in originals and name not in gaps, "Duplicate target object name")
        target_spans.append((sym[1], sym[1] + sym[2], name))
        if sym[4]:
            require(sym[4] == 2 and re.fullmatch(r"gap_\d+_[0-9A-Fa-f]{8}_sdata", name)
                    and not any(target.payload(ti)[sym[1]:sym[1] + sym[2]]),
                    "Target hidden symbol is not an independently verified zero gap")
            gaps[name] = sym
        else:
            originals[name] = sym
    cursor = 0
    for start, end, _ in sorted(target_spans):
        require(start == cursor, "Target fragments do not partition the physical section")
        cursor = end
    require(cursor == t[5], "Target section has uncovered trailing storage")

    plans, registered, group_spans = [], set(), []
    for group in groups:
        require(isinstance(group, dict) and set(group) == {"base", "size", "aliases"},
                "Unexpected array-alias registration fields")
        base, size, aliases = group["base"], group["size"], group["aliases"]
        require(isinstance(base, str) and re.fullmatch(r"[A-Za-z_]\w*", base)
                and type(size) is int and size > 0
                and isinstance(aliases, list) and aliases, "Invalid array-alias registration")
        index, host = source.unique_symbol(base)
        wanted = originals.get(base)
        require(wanted is not None and host[3:6] == (0x11, 0, si)
                and host[2] == size and host[1] == wanted[1]
                and 0 < wanted[2] < size, "Native host is not the complete registered C array")
        start, end = host[1], host[1] + size
        require(not any(a < end and start < b for a, b in group_spans),
                "Registered C arrays overlap")
        group_spans.append((start, end))
        members = {base: wanted}
        require(base not in registered, "Duplicate alias registration")
        registered.add(base)
        for alias in aliases:
            require(isinstance(alias, dict) and set(alias) == {"name", "offset", "size"},
                    "Unexpected interior-alias registration fields")
            name, offset, extent = alias["name"], alias["offset"], alias["size"]
            require(isinstance(name, str) and re.fullmatch(r"[A-Za-z_]\w*", name)
                    and name not in registered and type(offset) is int
                    and type(extent) is int and 0 < offset < size
                    and 0 < extent <= size - offset, "Alias exceeds or duplicates its C host")
            require(not any(n == name for n, _ in source.symbols),
                    "Alias name already exists in the native object")
            target_alias = originals.get(name)
            require(target_alias is not None
                    and target_alias[1:3] == (start + offset, extent),
                    "Interior alias differs from the original identity or extent")
            registered.add(name)
            members[name] = target_alias
        fragments = []
        for a, b, name in sorted(target_spans):
            if a >= end or b <= start:
                continue
            require(start <= a < b <= end and (name in members or name in gaps),
                    "Unregistered target storage intersects the C array")
            fragments.append((name, members.get(name, gaps.get(name))))
        cursor = start
        for _, sym in fragments:
            require(sym[1] == cursor, "Array fragments are not contiguous")
            cursor += sym[2]
        require(cursor == end, "Array fragments do not cover the full native C array")
        plans.append((index, base, host, fragments))

    for name, wanted in originals.items():
        if name in registered:
            continue
        _, actual = source.unique_symbol(name)
        require(actual[1:5] == wanted[1:5] and actual[5] == si,
                "Unrelated source object extent or identity differs")
    hosts = {base for _, base, _, _ in plans}
    for name, sym in source.symbols:
        if sym[5] != si or sym[3] & 15 == 3:
            continue
        if name in hosts or name in originals:
            continue
        if sym[3] == 0 and sym[1:3] == (0, 0) and name == "...sdata.0":
            continue
        require(sym[3:5] == (0x11, 0) and sym[2] > 0
                and any(g[1] <= sym[1] and sym[1] + sym[2] <= g[1] + g[2]
                        for g in gaps.values())
                and not any(a < sym[1] + sym[2] and sym[1] < b for a, b in group_spans)
                and not any(source.payload(si)[sym[1]:sym[1] + sym[2]]),
                "Unexpected native storage or alias inside a C array")
    return si, plans


def make_view(source, si, plans, comparison):
    output = bytearray(source.blob)
    table = source.sections[source.symtab]
    strings_index = table[6]
    strings = bytearray(source.payload(strings_index))
    symbols = bytearray(source.payload(source.symtab))
    comment_index, comment = comment_records(source)
    comment = bytearray(comment)
    additions = 0
    for host_index, base, host, fragments in plans:
        for name, target in fragments:
            if name == base:
                if comparison:
                    struct.pack_into(">I", symbols, host_index * 16 + 8, target[2])
                continue
            if target[4] and not comparison:
                continue  # A generated zero gap has no original public alias.
            offset = len(strings)
            strings.extend(name.encode("ascii") + b"\0")
            symbols.extend(struct.pack(">IIIBBH", offset, target[1],
                                       target[2] if comparison else 0,
                                       0x11 if comparison else 0x10,
                                       target[4] if comparison else 0, si))
            # Added labels require only byte alignment. They describe an
            # existing array/subrange, never separately allocated C storage.
            comment.extend(struct.pack(">IBBH", 1, 0, 8, 0))
            additions += 1
    for index, data in ((strings_index, strings), (source.symtab, symbols),
                        (comment_index, comment)):
        alignment = max(1, source.sections[index][8])
        output.extend(bytes(-len(output) % alignment))
        offset = len(output)
        output.extend(data)
        struct.pack_into(">II", output, source.header[6] + index * 40 + 16,
                         offset, len(data))
    result = bytes(output)
    checked = Elf(result)
    changed = {strings_index, source.symtab, comment_index}
    for index, section in enumerate(source.sections):
        before, after = section, checked.sections[index]
        if index not in changed:
            require(before == after and source.payload(index) == checked.payload(index),
                    "Alias view changed unrelated source content")
        else:
            require(before[:4] == after[:4] and before[6:] == after[6:],
                    "Alias view changed unrelated section metadata")
    permitted_sizes = {i: next(s[2] for n, s in parts if n == base)
                       for i, base, _, parts in plans} if comparison else {}
    for index, ((name, before), (after_name, after)) in enumerate(
            zip(source.symbols, checked.symbols)):
        expected = list(before)
        if index in permitted_sizes:
            expected[2] = permitted_sizes[index]
        require(name == after_name and tuple(expected) == after,
                "Alias view changed an original symbol beyond its registered comparison size")
    require(source.data_relocations() == checked.data_relocations(),
            "Alias view changed relocation semantics")
    return result, additions


def create_views(source_blob, target_blob, groups):
    source, target = Elf(source_blob), Elf(target_blob)
    si, plans = validate(source, target, groups)
    link, link_count = make_view(source, si, plans, False)
    comparison, comparison_count = make_view(source, si, plans, True)
    return link, comparison, {
        "native_array_bounds": [{"name": base, "offset": sym[1], "size": sym[2]}
                                for _, base, sym, _ in plans],
        "link_labels_added": link_count,
        "comparison_fragment_symbols_added": comparison_count,
        "allocated_bytes_verified": source.sections[si][5],
        "allocated_bytes_changed": 0,
        "relocation_records_changed": 0,
        "native_and_target_inputs_modified": False,
    }


def write_output(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--groups", required=True, type=Path)
    parser.add_argument("--link-output", required=True, type=Path)
    parser.add_argument("--comparison-output", required=True, type=Path)
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()
    paths = [args.source, args.target, args.groups, args.link_output,
             args.comparison_output] + ([args.metadata] if args.metadata else [])
    require(len({p.resolve() for p in paths}) == len(paths),
            "Inputs and output views must be distinct paths")
    link, comparison, metadata = create_views(args.source.read_bytes(),
                                            args.target.read_bytes(),
                                            json.loads(args.groups.read_text()))
    write_output(args.link_output, link)
    write_output(args.comparison_output, comparison)
    if args.metadata:
        write_output(args.metadata, (json.dumps(metadata, indent=2) + "\n").encode())
    print(json.dumps(metadata))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
