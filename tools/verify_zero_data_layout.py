#!/usr/bin/env python3
"""Verify zero-data symbol layouts; identical zero bytes alone are insufficient.

Expectations come from the existing symbol map and named splits, not from the
candidate declarations. The compact unit list selects the new zero-data owners
and existing zero-data owners proposed for source linking. This checker never
modifies objects or grants matching credit.
"""

import argparse
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.import_constant_symbol import parse_symbols, read_elf

ZERO_SECTIONS = {".bss", ".sbss", ".sbss2"}
SYMBOL = re.compile(r"^(\S+) = (\.[^:]+):0x([0-9A-Fa-f]+);\s*//\s*(.*)$")
SPLIT = re.compile(r"^\s+(\.\S+)\s+start:0x([0-9A-Fa-f]+)\s+end:0x([0-9A-Fa-f]+)(.*)$")


def expectations(manifest_path, symbols_path, splits_path):
    manifest = json.loads(manifest_path.read_text())
    units = manifest["units"]
    if manifest.get("version") != 1 or not units or len(units) != len(set(units)):
        raise ValueError("invalid or duplicate zero-data units")
    for unit in units:
        path = Path(unit)
        if path.is_absolute() or ".." in path.parts or path.suffix != ".c":
            raise ValueError("unsafe zero-data unit path")
    ranges = {unit: [] for unit in units}
    all_ranges = []
    owner = None
    for line in splits_path.read_text().splitlines():
        if line and not line[0].isspace() and line.endswith(":"):
            owner = line[:-1]
        match = SPLIT.match(line)
        if match:
            section, begin, end, extra = match.groups()
            span = (section, int(begin, 16), int(end, 16))
            all_ranges.append((owner, *span))
            if owner in ranges:
                if extra.strip() or span[1] >= span[2]:
                    raise ValueError("unsupported zero-data split attributes")
                ranges[owner].append(span)
    symbols = []
    for line in symbols_path.read_text().splitlines():
        match = SYMBOL.match(line)
        if match:
            name, section, address, metadata = match.groups()
            fields = dict(re.findall(r"(\w+):([^\s]+)", metadata))
            symbols.append((name, section, int(address, 16), fields))
    result = []
    for unit, spans in ranges.items():
        if len(spans) != 1 or spans[0][0] not in ZERO_SECTIONS:
            raise ValueError("zero-data owner must have one zero-init section")
        section, start, end = spans[0]
        for other, other_section, a, b in all_ranges:
            if other != unit and other_section == section and a < end and start < b:
                raise ValueError("zero-data split overlaps another owner")
        selected = []
        for name, symbol_section, address, fields in symbols:
            if symbol_section != section:
                continue
            size = int(fields.get("size", "0"), 0)
            if address < start and address + size > start:
                raise ValueError("split bisects an existing symbol")
            if not start <= address < end:
                continue
            if fields.get("type") != "object" or size <= 0 or address + size > end:
                raise ValueError("unsupported or bisected zero-data symbol")
            suffix = f"{address:08X}"
            if fields.get("scope") == "local" and not name.endswith(suffix):
                name += "_" + suffix
            selected.append({"name": name, "offset": address - start, "size": size})
        if not selected:
            raise ValueError("zero-data owner has no existing symbols")
        selected.sort(key=lambda row: row["offset"])
        cursor = 0
        expected = []
        for row in selected:
            if row["offset"] < cursor:
                raise ValueError("zero-data symbols overlap")
            if row["offset"] > cursor:
                expected.append({"name": f"padding_{start + cursor:08X}",
                                 "offset": cursor, "size": row["offset"] - cursor})
            expected.append(row)
            cursor = row["offset"] + row["size"]
        if cursor < end - start:
            expected.append({"name": f"padding_{start + cursor:08X}",
                             "offset": cursor, "size": end - start - cursor})
        if len({row["name"] for row in expected}) != len(expected):
            raise ValueError("duplicate zero-data symbol name")
        result.append({"unit": unit, "section": section, "start": start,
                       "size": end - start, "symbols": expected,
                       "existing_symbols": len(selected)})
    return result


def check_object(blob, expected):
    _, sections = read_elf(blob)
    _, symbols = parse_symbols(sections)
    errors = []
    indices = [i for i, section in enumerate(sections)
               if section["name"] == expected["section"]]
    if len(indices) != 1:
        return ["expected exactly one declared zero-init section"]
    index = indices[0]
    fields = sections[index]["fields"]
    if fields[1] != 8 or not fields[2] & 2 or fields[2] & 4:
        errors.append("expected allocated non-executable SHT_NOBITS storage")
    if fields[5] != expected["size"]:
        errors.append(f"section size {fields[5]} != {expected['size']}")
    alignment = fields[8]
    if not alignment or alignment & (alignment - 1) or expected["start"] % alignment:
        errors.append("compiled section alignment cannot occupy the retail start")
    for i, section in enumerate(sections):
        f = section["fields"]
        if i != index and f[2] & 2 and f[5]:
            errors.append("unexpected additional allocated section")
        if f[1] in (4, 9) and f[7] == index and f[5]:
            errors.append("zero-init section unexpectedly has relocations")
    names = {row["name"] for row in expected["symbols"]}
    for row in expected["symbols"]:
        found = [symbol for symbol in symbols if symbol["name"] == row["name"]
                 and symbol["shndx"] != 0]
        if len(found) != 1:
            errors.append(f"{row['name']}: expected one definition")
            continue
        symbol = found[0]
        actual = (symbol["shndx"], symbol["value"], symbol["size"], symbol["info"])
        wanted = (index, row["offset"], row["size"], 0x11)
        if actual != wanted:
            errors.append(f"{row['name']}: section/offset/size/binding {actual} != {wanted}")
    for symbol in symbols:
        if (symbol["shndx"] == index and symbol["size"]
                and symbol["info"] & 15 != 3 and symbol["name"] not in names):
            errors.append(f"unexpected storage symbol: {symbol['name']}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "config/GC6E01/zero_data_units.json")
    parser.add_argument("--symbols", type=Path, default=ROOT / "config/GC6E01/symbols.txt")
    parser.add_argument("--splits", type=Path, default=ROOT / "config/GC6E01/splits.txt")
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build/GC6E01")
    parser.add_argument("--metadata-only", action="store_true",
                        help="Validate declared ownership only; no compiler/layout proof")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    expected = expectations(args.manifest, args.symbols, args.splits)
    result = {"metadata_valid": True, "objects_verified": 0,
              "compiled_layout_valid": None, "units": [],
              "total_bytes": sum(row["size"] for row in expected)}
    if not args.metadata_only:
        for row in expected:
            path = args.build_dir / "src" / Path(row["unit"]).with_suffix(".o")
            try:
                errors = check_object(path.read_bytes(), row)
            except (OSError, ValueError, IndexError, struct.error) as exc:
                errors = [type(exc).__name__]
            result["units"].append({"unit": row["unit"], "errors": errors})
            result["objects_verified"] += not errors
        result["compiled_layout_valid"] = result["objects_verified"] == len(expected)
    summary = {key: value for key, value in result.items() if key != "units"}
    summary["expected_units"] = len(expected)
    print(json.dumps(summary, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    else:
        for row in result["units"]:
            if row["errors"]:
                print(row["unit"], row["errors"][:8])
    return 1 if result["compiled_layout_valid"] is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
