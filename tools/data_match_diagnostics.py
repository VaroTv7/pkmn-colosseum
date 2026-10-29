#!/usr/bin/env python3
"""Explain remaining data mismatches without exporting original payload bytes.

Run after ``ninja all_source build/GC6E01/report.json``. The JSON contains only
ELF metadata, section hashes, equality checks, and objdiff scores. Original
objects, data bytes, instruction text, and objdiff's raw JSON stay private.
This is a diagnostic; it does not modify objects, reports, or matching credit.
"""

import argparse
import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path

if __package__:
    from .resource_message_diagnostics import resource_message_reuse_checks
    from .runtime_data_diagnostics import runtime_structure
else:
    from resource_message_diagnostics import resource_message_reuse_checks
    from runtime_data_diagnostics import runtime_structure


DATA_SECTIONS = {".rodata", ".data", ".sdata", ".sdata2"}
BSS_SECTIONS = {".bss", ".sbss", ".sbss2"}
SHT_NOBITS = 8
SHT_SYMTAB = 2
SHT_RELA = 4
SHT_REL = 9
SHT_STRTAB = 3


def elf_metadata(path):
    """Return a JSON-safe description, plus private bytes for equality checks."""
    blob = path.read_bytes()
    if len(blob) < 52 or blob[:6] != b"\x7fELF\x01\x02":
        raise ValueError("expected big-endian ELF32")
    header = struct.unpack_from(">16sHHIIIIIHHHHHH", blob)
    if header[1:3] != (1, 20) or header[8] != 52 or header[11] != 40:
        raise ValueError("expected a relocatable PowerPC object")

    def bounded(offset, size):
        if offset < 0 or size < 0 or offset + size > len(blob):
            raise ValueError("ELF range exceeds file")
        return blob[offset:offset + size]

    table = bounded(header[6], header[12] * 40)
    records = list(struct.iter_unpack(">10I", table))
    if not 0 < header[13] < len(records) or records[header[13]][1] != SHT_STRTAB:
        raise ValueError("invalid section-name table")

    def payload(record):
        return bounded(record[4], record[5])

    def name(strings, offset):
        if offset >= len(strings):
            raise ValueError("invalid string-table offset")
        end = strings.find(b"\0", offset)
        if end < 0:
            raise ValueError("unterminated ELF metadata string")
        return strings[offset:end].decode("utf-8", errors="replace")

    section_names = payload(records[header[13]])
    names = [name(section_names, record[0]) for record in records]
    symbol_tables = {}
    for index, record in enumerate(records):
        if record[1] != SHT_SYMTAB:
            continue
        if record[9] != 16 or record[5] % 16 or record[6] >= len(records):
            raise ValueError("invalid ELF symbol table")
        if records[record[6]][1] != SHT_STRTAB:
            raise ValueError("invalid symbol-name table")
        strings = payload(records[record[6]])
        symbols = []
        for entry in struct.iter_unpack(">IIIBBH", payload(record)):
            symbol_name, value, size, info, other, section = entry
            if len(records) <= section < 0xFF00:
                raise ValueError("invalid symbol section index")
            symbols.append({
                "name": name(strings, symbol_name),
                "offset": value,
                "size": size,
                "type": info & 15,
                "binding": info >> 4,
                "visibility": other & 3,
                "section_index": section,
                "section": names[section] if 0 < section < len(names) else None,
            })
        symbol_tables[index] = symbols

    public = {}
    private = {}
    for index, record in enumerate(records):
        section_name = names[index]
        if section_name not in DATA_SECTIONS | BSS_SECTIONS:
            continue
        if section_name in public:
            raise ValueError("duplicate data section")
        symbols = [dict(symbol) for table in symbol_tables.values()
                   for symbol in table if symbol["section_index"] == index
                   and symbol["type"] != 3]
        for symbol in symbols:
            del symbol["section_index"]
            del symbol["section"]
            if symbol["offset"] + symbol["size"] > record[5]:
                raise ValueError("data symbol exceeds section")
        section = {
            "size": record[5],
            "alignment": record[8],
            "nobits": record[1] == SHT_NOBITS,
            "symbols": symbols,
            "relocations": [],
            "symbol_extent": max((s["offset"] + s["size"] for s in symbols
                                  if s["size"]), default=0),
        }
        data = None if record[1] == SHT_NOBITS else payload(record)
        if data is not None:
            section["sha256"] = hashlib.sha256(data).hexdigest()
        for reloc_record in records:
            if reloc_record[1] not in (SHT_REL, SHT_RELA) or reloc_record[7] != index:
                continue
            entry_size = 12 if reloc_record[1] == SHT_RELA else 8
            if reloc_record[9] != entry_size or reloc_record[5] % entry_size:
                raise ValueError("invalid ELF relocation table")
            symbols_for_relocs = symbol_tables.get(reloc_record[6])
            if symbols_for_relocs is None:
                raise ValueError("missing relocation symbol table")
            fmt = ">IIi" if entry_size == 12 else ">II"
            for entry in struct.iter_unpack(fmt, payload(reloc_record)):
                offset, info = entry[:2]
                relocation_type = info & 255
                width = 4 if relocation_type in (1, 24, 26, 33) else 1
                if relocation_type in (3, 4, 5, 6, 25, 32, 34, 35, 36):
                    width = 2
                if relocation_type and offset + width > record[5]:
                    raise ValueError("relocation exceeds section")
                symbol_index = info >> 8
                if symbol_index >= len(symbols_for_relocs):
                    raise ValueError("invalid relocation symbol index")
                symbol = symbols_for_relocs[symbol_index]
                addend = entry[2] if entry_size == 12 else None
                relocation = {
                    "offset": offset,
                    "type": relocation_type,
                    "symbol": symbol["name"],
                    "addend": addend,
                    "target_section": symbol["section"],
                    "target_symbol_offset": symbol["offset"],
                }
                if symbol["section"] is not None and addend is not None:
                    destination = symbol["offset"] + addend
                    relocation["target_section_offset"] = destination
                    functions = [s for s in symbols_for_relocs
                                 if s["type"] == 2 and s["size"]
                                 and s["section_index"] == symbol["section_index"]
                                 and s["offset"] <= destination < s["offset"] + s["size"]]
                    if len(functions) == 1:
                        relocation["target_function"] = functions[0]["name"]
                        relocation["target_function_offset"] = destination - functions[0]["offset"]
                if data is not None and relocation_type == 1:
                    word = struct.unpack_from(">I", data, offset)[0]
                    relocation["in_place_zero"] = word == 0
                    if addend is not None:
                        relocation["in_place_equals_explicit_addend"] = word == addend & 0xFFFFFFFF
                section["relocations"].append(relocation)
        if data is not None:
            for symbol in symbols:
                start, size = symbol["offset"], symbol["size"]
                end = start + size
                if not size:
                    continue
                if end > len(data):
                    raise ValueError("data symbol exceeds section")
                value = data[start:end]
                symbol["sha256"] = hashlib.sha256(value).hexdigest()
                normalized = bytearray(value)
                partial = False
                for relocation in section["relocations"]:
                    offset = relocation["offset"]
                    if relocation["type"] != 1 or relocation["addend"] is None:
                        continue
                    if start <= offset and offset + 4 <= end:
                        normalized[offset - start:offset - start + 4] = b"\0" * 4
                    elif offset < end and start < offset + 4:
                        partial = True
                if not partial:
                    symbol["sha256_addr32_zeroed"] = hashlib.sha256(normalized).hexdigest()
        public[section_name] = section
        private[section_name] = data
    return public, private


def sanitized_diff(raw, metadata):
    """Use an allowlist: never copy data_diff, instructions, or raw stderr."""
    def percentage(value):
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("invalid objdiff score")
        if not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError("invalid objdiff score")
        return value

    result = {}
    for side, key in (("left", "target"), ("right", "source")):
        value = raw.get(side) or {}
        known = metadata.get(key) or {}
        data_names = {s["name"] for section in known.values()
                      for s in section["symbols"]}
        result[key] = {
            "sections": [{"name": s["name"], "size": int(s.get("size", 0)),
                          "match_percent": percentage(s.get("match_percent"))}
                         for s in value.get("sections", [])
                         if s.get("name") in DATA_SECTIONS | BSS_SECTIONS],
            "symbols": [{"name": s["name"], "offset": int(s.get("address", 0)),
                         "size": int(s.get("size", 0)),
                         "match_percent": percentage(s.get("match_percent"))}
                        for s in value.get("symbols", [])
                        if s.get("name") in data_names],
        }
    return result


def comparisons(target, source, target_bytes, source_bytes):
    result = {}
    for name in sorted(target.keys() & source.keys()):
        left, right = target[name], source[name]
        row = {"same_size": left["size"] == right["size"],
               "same_alignment": left["alignment"] == right["alignment"],
               "same_nobits": left.get("nobits") == right.get("nobits")}
        layouts = []
        for section in (left, right):
            by_name = {}
            for symbol in section.get("symbols", []):
                by_name.setdefault(symbol["name"], []).append((symbol["offset"], symbol["size"]))
            layouts.append({key: sorted(value) for key, value in by_name.items()})
        shared = layouts[0].keys() & layouts[1].keys()
        row["symbol_offsets_and_sizes_equal"] = layouts[0] == layouts[1]
        row["shared_symbol_offsets_and_sizes_equal"] = (
            all(layouts[0][key] == layouts[1][key] for key in shared) if shared else None)
        row["target_symbols_without_source_name"] = sorted(layouts[0].keys() - layouts[1].keys())
        row["source_symbols_without_target_name"] = sorted(layouts[1].keys() - layouts[0].keys())
        a, b = target_bytes[name], source_bytes[name]
        if a is not None and b is not None:
            row["raw_bytes_equal"] = a == b
            # This boolean diagnoses explicit-addend storage differences. It
            # cannot establish a relocation match or grant matching credit.
            normalized = []
            for data, section in ((a, left), (b, right)):
                data = bytearray(data)
                for reloc in section["relocations"]:
                    offset = reloc["offset"]
                    if reloc["type"] == 1 and reloc["addend"] is not None:
                        if offset + 4 > len(data):
                            raise ValueError("relocation exceeds section")
                        data[offset:offset + 4] = b"\0" * 4
                normalized.append(data)
            row["bytes_equal_with_addr32_words_zeroed"] = normalized[0] == normalized[1]
            row["target_size_prefix_equal"] = len(b) >= len(a) and a == b[:len(a)]
        result[name] = row
    return result


def selected_units(report, include_units=(), include_data_only=False):
    """Include explicit units and retain visibility into exact unlinked data."""
    names = {unit["name"]: unit for unit in report["units"]}
    requested = set(include_units)
    if requested - names.keys():
        raise ValueError("explicit unit is missing from the report")
    if any(int(names[name]["measures"].get("total_data", 0)) <= 0 for name in requested):
        raise ValueError("explicit unit has no reported data")
    for unit in report["units"]:
        measures = unit["measures"]
        total = int(measures.get("total_data", 0))
        if not total:
            continue
        source = unit.get("metadata", {}).get("source_path")
        unmatched = int(measures.get("matched_data", 0)) < total
        data_only_source = source and int(measures.get("total_code", 0)) == 0
        unlinked = int(measures.get("complete_data", 0)) < total
        default_mismatch = unmatched and (source or (
            unit["name"].startswith("main/") and
            any(s["name"] in DATA_SECTIONS for s in unit.get("sections", []))))
        if (unit["name"] in requested or default_mismatch or
                data_only_source and (unlinked or include_data_only)):
            yield unit


def source_alignment_at_original_address(unit, source):
    result = {}
    for section in unit.get("sections", []):
        address = section.get("metadata", {}).get("virtual_address")
        if address is None or section["name"] not in source:
            continue
        alignment = source[section["name"]]["alignment"] or 1
        result[section["name"]] = {
            "address": int(address), "source_alignment": alignment,
            "compatible": int(address) % alignment == 0,
        }
    return result


def resource_reuse_checks(orig):
    """Compare public-address resource candidates; return hashes/addresses only."""
    dol = (orig / "sys/main.dol").read_bytes()
    rel = (orig / "files/common_rel.rel").read_bytes()
    if len(dol) < 0x100 or len(rel) < 0x4C:
        raise ValueError("truncated original header")
    offsets = struct.unpack_from(">18I", dol, 0)
    addresses = struct.unpack_from(">18I", dol, 0x48)
    sizes = struct.unpack_from(">18I", dol, 0x90)
    dol_data = []
    for offset, address, size in zip(offsets[7:], addresses[7:], sizes[7:]):
        if not size:
            continue
        if offset < 0x100 or offset + size > len(dol) or address + size > 0x100000000:
            raise ValueError("DOL data exceeds file")
        dol_data.append((address, dol[offset:offset + size]))
    section_count, section_table = struct.unpack_from(">II", rel, 0xC)
    if section_count <= 4 or section_table < 0x4C or section_table + section_count * 8 > len(rel):
        raise ValueError("invalid REL section table")
    rel_offset, rel_size = struct.unpack_from(">II", rel, section_table + 4 * 8)
    rel_offset &= ~1
    if rel_offset < section_table + section_count * 8 or rel_offset + rel_size > len(rel):
        raise ValueError("REL data exceeds file")
    rel_data = rel[rel_offset:rel_offset + rel_size]

    def region(start, end):
        if not 0 <= start < end <= len(rel_data):
            raise ValueError("resource range exceeds REL data")
        return rel_data[start:end]

    boundaries = [0x2D2C, 0x45A8C, 0x45A94, 0x494E4, 0x58044,
                  0x647B4, 0x76C94, 0x89CFC, 0x8BCB4]
    # This one eight-byte resource is the FontFileHeader consumed by
    # GSmsgFontOpen, not a glyph or message payload. Record only its four
    # structural scalar fields so a typed terminator can be reconstructed.
    # Keep this allowlist tied to its known address; do not expose arbitrary
    # resource bytes or decode the remaining opaque resource contents.
    font_id, width, height, next_offset = struct.unpack(
        ">HBBI", region(0x45A8C, 0x45A94))
    result = {"rel_section_index": 4, "spans": [], "known_candidates": [],
              "font_dummy_header": {
                  "rel_offset": 0x45A8C, "size": 8,
                  "font_id": font_id, "width": width, "height": height,
                  "next_offset": next_offset,
                  "is_font_open_terminator": font_id == 0xFFFF,
                  "matches_empty_font_terminator":
                      (font_id, width, height, next_offset) == (0xFFFF, 0, 0, 0),
              }}
    for start, end in zip(boundaries, boundaries[1:]):
        data = region(start, end)
        row = {"rel_offset": start, "size": len(data),
               "sha256": hashlib.sha256(data).hexdigest(), "dol_addresses": []}
        if len(data) > 8:
            for address, section in dol_data:
                at = 0
                while True:
                    at = section.find(data, at)
                    if at < 0:
                        break
                    if len(row["dol_addresses"]) >= 32:
                        row["search_truncated"] = True
                        break
                    row["dol_addresses"].append(address + at)
                    at += 1
        result["spans"].append(row)
    candidates = [(0x8027A500, 0x2D2C, 0x42D60),
                  (0x802BD260, 0x45A94, 0x3A50),
                  (0x802C0CB0, 0x494E4, 0xEB60),
                  (0x802CF810, 0x647B4, 0x124E0)]
    for address, start, size in candidates:
        a = region(start, start + size)
        matches = [section[address - base:address - base + size]
                   for base, section in dol_data
                   if base <= address and address + size <= base + len(section)]
        if len(matches) != 1:
            raise ValueError("candidate DOL range is not in one data section")
        b = matches[0]
        result["known_candidates"].append({
            "dol_address": address, "rel_offset": start, "size": size,
            "equal": a == b, "rel_sha256": hashlib.sha256(a).hexdigest(),
            "dol_sha256": hashlib.sha256(b).hexdigest(),
        })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("build/GC6E01/report.json"))
    parser.add_argument("--config", type=Path, default=Path("objdiff.json"))
    parser.add_argument("--objdiff", type=Path, default=Path("build/tools/objdiff-cli"))
    parser.add_argument("--output", type=Path, default=Path("build/GC6E01/data_match_diagnostics.json"))
    parser.add_argument("--orig", type=Path, help="Optional verified original-input root for resource equality checks")
    parser.add_argument("--include-unit", action="append", default=[], metavar="UNIT",
                        help="Also inspect this exact report unit name (repeatable; unknown units fail)")
    parser.add_argument("--include-data-only", action="store_true",
                        help="Inspect every source-backed data-only unit, including exact promoted units")
    args = parser.parse_args()
    root = args.config.resolve().parent
    config = json.loads(args.config.read_text())
    report = json.loads(args.report.read_text())
    configs = {unit["name"]: unit for unit in config["units"]}
    output = {"schema_version": 1, "payload_bytes_included": False,
              "include_data_only": args.include_data_only,
              "explicit_units": sorted(set(args.include_unit)), "units": []}
    failures = 0
    try:
        selection = list(selected_units(report, args.include_unit, args.include_data_only))
    except ValueError:
        # Unit names are supplied by the caller; do not echo unvalidated inputs.
        parser.error("include-unit selectors must name report units with data")
    for unit in selection:
        item = {"name": unit["name"], "source_path": unit.get("metadata", {}).get("source_path"),
                "measures": {key: unit["measures"].get(key, 0)
                             for key in ("total_data", "matched_data", "complete_data")}}
        try:
            paths = configs[unit["name"]]
            metadata = {}
            private = {}
            for kind, path_key in (("target", "target_path"), ("source", "base_path")):
                path = paths.get(path_key)
                if path:
                    prefix = config.get("target_dir" if kind == "target" else "base_dir") or ""
                    metadata[kind], private[kind] = elf_metadata(root / prefix / path)
            item.update(metadata)
            if "target" in metadata:
                runtime = runtime_structure(unit, metadata["target"], private["target"])
                if runtime is not None:
                    item["runtime_structure"] = runtime
            if "source" in metadata:
                item["source_alignment_at_original_address"] = source_alignment_at_original_address(
                    unit, metadata["source"])
            if "target" in metadata and "source" in metadata:
                item["comparisons"] = comparisons(metadata["target"], metadata["source"],
                                                  private["target"], private["source"])
                if int(item["measures"]["matched_data"]) == int(item["measures"]["total_data"]):
                    item["objdiff_skipped_reason"] = "report_data_already_exact"
                else:
                    proc = subprocess.run([str(args.objdiff.resolve()), "diff", "-p", str(root),
                                           "-u", unit["name"], "-o", "-", "--format", "json"],
                                          capture_output=True, timeout=120, check=False)
                    if proc.returncode:
                        item["objdiff_error"] = {"returncode": proc.returncode}
                        failures += 1
                    else:
                        item["objdiff"] = sanitized_diff(json.loads(proc.stdout), metadata)
        except (OSError, ValueError, KeyError, struct.error, subprocess.TimeoutExpired) as exc:
            # Exception messages can contain private input. Expose only type.
            item["error"] = type(exc).__name__
            failures += 1
        output["units"].append(item)
        measures = item["measures"]
        remaining = int(measures["total_data"]) - int(measures["matched_data"])
        if remaining or "error" in item or "objdiff_error" in item:
            print(f"{unit['name']}: {remaining} unmatched data bytes; "
                  f"source={'yes' if item['source_path'] else 'no'}; "
                  f"metadata={'error' if 'error' in item else 'recorded'}")
    if args.orig:
        try:
            output["resource_reuse"] = resource_reuse_checks(args.orig)
            equal = sum(candidate["equal"] for candidate in output["resource_reuse"]["known_candidates"])
            print(f"Resource candidates: {equal}/4 equal (hashes and addresses only).")
        except (OSError, ValueError, struct.error) as exc:
            output["resource_reuse"] = {"error": type(exc).__name__}
            failures += 1
        try:
            output["resource_messages"] = resource_message_reuse_checks(args.orig, report, root)
        except (OSError, ValueError, KeyError, struct.error, subprocess.CalledProcessError) as exc:
            output["resource_messages"] = {"error": type(exc).__name__}
            failures += 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    skipped = sum("objdiff_skipped_reason" in unit for unit in output["units"])
    print(f"Wrote metadata for {len(output['units'])} units ({failures} failures); "
          f"skipped {skipped} already-exact objdiff runs.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
