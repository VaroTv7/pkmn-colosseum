#!/usr/bin/env python3
"""Compare linked DOL data symbol addresses with the existing retail map.

Only complete, source-backed, data-only main units are selected. Incomplete
candidates still linked from originals are explicitly skipped. Output contains
symbol names, addresses, sizes and comparison status, never section payloads.
Missing/dead-stripped symbols are diagnostic observations, not matching credit.
"""

import argparse
import json
from pathlib import Path
import re
import struct


DATA_SECTIONS = {".ctors", ".dtors", ".rodata", ".data", ".bss",
                 ".sdata", ".sbss", ".sdata2", ".sbss2"}
SYMBOL = re.compile(r"^(\S+) = (\.[^:]+):0x([0-9A-Fa-f]+);\s*//\s*(.*)$")


def linked_symbols(blob):
    def bounded(offset, size):
        if offset < 0 or size < 0 or offset + size > len(blob):
            raise ValueError("Linked ELF range exceeds file")
        return blob[offset:offset + size]

    header = struct.unpack(">16sHHIIIIIHHHHHH", bounded(0, 52))
    if header[0][:7] != b"\x7fELF\x01\x02\x01" or header[1:4] != (2, 20, 1) \
            or header[8] != 52 or header[11] != 40 or not header[12]:
        raise ValueError("Expected a linked big-endian ELF32 PowerPC executable")
    sections = list(struct.iter_unpack(">10I", bounded(header[6], header[12] * 40)))
    tables = [section for section in sections if section[1] == 2]
    if len(tables) != 1:
        raise ValueError("Expected one linked symbol table")
    table = tables[0]
    if table[9] != 16 or table[5] % 16 or table[6] >= len(sections) \
            or sections[table[6]][1] != 3:
        raise ValueError("Invalid linked symbol table")
    names_section = sections[table[6]]
    names = bounded(names_section[4], names_section[5])
    output = {}
    for name_offset, address, size, info, _, section_index in struct.iter_unpack(
            ">IIIBBH", bounded(table[4], table[5])):
        if not section_index or info & 15 not in (0, 1):
            continue
        if section_index >= len(sections) and section_index != 0xFFF1:
            raise ValueError("Invalid linked data symbol section")
        if name_offset >= len(names):
            raise ValueError("Invalid linked symbol name")
        end = names.find(b"\0", name_offset)
        if end < 0:
            raise ValueError("Unterminated linked symbol name")
        name = names[name_offset:end].decode("utf-8")
        if name:
            definition = {"address": address, "size": size}
            definitions = output.setdefault(name, [])
            if definition not in definitions:
                definitions.append(definition)
    return output


def map_symbols(text):
    output = []
    for line in text.splitlines():
        match = SYMBOL.match(line)
        if not match:
            continue
        name, section, address, metadata = match.groups()
        fields = dict(re.findall(r"(\w+):([^\s]+)", metadata))
        if section not in DATA_SECTIONS or fields.get("type") != "object":
            continue
        address, size = int(address, 16), int(fields.get("size", "0"), 0)
        if not size:
            continue
        alias = name
        suffix = f"{address:08X}"
        if fields.get("scope") == "local" and not name.endswith(suffix):
            alias += "_" + suffix
        output.append({"name": name, "alias": alias, "section": section,
                       "address": address, "size": size})
    return output


def diagnose(report, expected, actual):
    result = {"schema_version": 1, "payload_bytes_included": False,
              "scope": "complete_source_data_only_main_units",
              "units": [], "skipped_incomplete_units": []}
    totals = {key: 0 for key in ("match", "address_mismatch", "size_mismatch",
                                "missing", "ambiguous")}
    for unit in report["units"]:
        measures, metadata = unit["measures"], unit.get("metadata", {})
        if not unit["name"].startswith("main/") or not metadata.get("source_path") \
                or int(measures.get("total_code", 0)) != 0 \
                or not int(measures.get("total_data", 0)):
            continue
        if not metadata.get("complete") or int(measures.get("complete_data", 0)) \
                != int(measures["total_data"]):
            result["skipped_incomplete_units"].append(unit["name"])
            continue
        rows = []
        for section in unit.get("sections", []):
            if section["name"] not in DATA_SECTIONS:
                continue
            start = int(section["metadata"]["virtual_address"])
            end = start + int(section["size"])
            for symbol in expected:
                if symbol["section"] != section["name"] or not start <= symbol["address"] < end:
                    continue
                if symbol["address"] + symbol["size"] > end:
                    raise ValueError("Reported owner bisects a mapped symbol")
                name = symbol["alias"]
                definitions = actual.get(name, [])
                # Source objects may retain a unique local basename while
                # extracted objects export DTK's address-qualified alias.
                if not definitions and name != symbol["name"]:
                    name = symbol["name"]
                    definitions = actual.get(name, [])
                row = {"name": symbol["name"], "expected_alias": symbol["alias"],
                       "section": symbol["section"],
                       "expected_address": symbol["address"],
                       "expected_size": symbol["size"],
                       "linked_name": name if definitions else None,
                       "actual_definitions": definitions}
                if not definitions:
                    status = "missing"
                elif len(definitions) != 1:
                    status = "ambiguous"
                elif definitions[0]["address"] != symbol["address"]:
                    status = "address_mismatch"
                elif definitions[0]["size"] != symbol["size"]:
                    status = "size_mismatch"
                else:
                    status = "match"
                row["status"] = status
                totals[status] += 1
                rows.append(row)
        result["units"].append({"name": unit["name"],
                                "source_path": metadata["source_path"], "symbols": rows})
    result["summary"] = {"complete_source_units": len(result["units"]),
                         "skipped_incomplete_units": len(result["skipped_incomplete_units"]),
                         "symbol_counts": totals}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elf", type=Path, default=Path("build/GC6E01/main.elf"))
    parser.add_argument("--report", type=Path, default=Path("build/GC6E01/report.json"))
    parser.add_argument("--symbols", type=Path, default=Path("config/GC6E01/symbols.txt"))
    parser.add_argument("--output", type=Path, default=Path("build/GC6E01/data_link_diagnostics.json"))
    args = parser.parse_args()
    try:
        result = diagnose(json.loads(args.report.read_text()),
                          map_symbols(args.symbols.read_text()), linked_symbols(args.elf.read_bytes()))
    except (OSError, ValueError, KeyError, TypeError, struct.error) as exc:
        result = {"schema_version": 1, "payload_bytes_included": False,
                  "error": type(exc).__name__}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result.get("summary", result), indent=2))
    # Address differences and absent/dead-stripped symbols are observations.
    # Canonical hashes and the independent object checks remain the gates.
    return 1 if "error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
