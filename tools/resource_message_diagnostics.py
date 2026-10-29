#!/usr/bin/env python3
"""Find message-storage reuse candidates without publishing message text.

MessageGroup and MessageEntry are defined by src/game/gs_msg.c. This module
reads only that bounded header and offset table. An entry's storage interval
ends at the next distinct entry offset or the resource boundary; it is not
claimed to be a decoded message. Interpreting control codes is deliberately
outside this diagnostic.

Searches are restricted to initialized DOL data owned by tracked source files
whose data is fully exact and source-linked in the supplied report. Returned
hashes and source locations are reuse candidates, not matching credit or proof
that a new source object has been built.
"""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
import subprocess


DATA_SECTIONS = {".data", ".rodata", ".sdata", ".sdata2"}
MESSAGE_SPANS = ((0x58044, 0x647B4), (0x647B4, 0x76C94), (0x76C94, 0x89CFC))


@dataclass(frozen=True)
class SourceRegion:
    unit: str
    source_path: str
    section: str
    address: int
    data: bytes


def _bounded(blob, offset, size):
    if offset < 0 or size < 0 or offset + size > len(blob):
        raise ValueError("range exceeds input")
    return blob[offset:offset + size]


def _dol_data_sections(blob):
    if len(blob) < 0x100:
        raise ValueError("truncated DOL header")
    offsets = struct.unpack_from(">18I", blob, 0)
    addresses = struct.unpack_from(">18I", blob, 0x48)
    sizes = struct.unpack_from(">18I", blob, 0x90)
    sections = []
    for offset, address, size in zip(offsets[7:], addresses[7:], sizes[7:]):
        if not size:
            continue
        if offset < 0x100 or address + size > 0x100000000:
            raise ValueError("invalid DOL data interval")
        sections.append((address, _bounded(blob, offset, size)))
    return sections


def _common_rel_data(blob):
    if len(blob) < 0x4C or struct.unpack_from(">I", blob)[0] != 125:
        raise ValueError("invalid common REL header")
    count, table = struct.unpack_from(">II", blob, 0xC)
    if count <= 4 or table < 0x4C:
        raise ValueError("invalid common REL section table")
    _bounded(blob, table, count * 8)
    offset, size = struct.unpack_from(">II", blob, table + 4 * 8)
    if offset & 1 or offset < table + count * 8:
        raise ValueError("invalid common REL data section")
    return _bounded(blob, offset, size)


def eligible_source_regions(report, dol_sections, tracked_sources):
    """Build private search regions from fully exact, linked source owners."""
    regions = []
    for unit in report.get("units", []):
        name = unit.get("name", "")
        source = unit.get("metadata", {}).get("source_path")
        measures = unit.get("measures", {})
        total = int(measures.get("total_data", 0))
        if (not name.startswith("main/") or source not in tracked_sources or total <= 0
                or int(measures.get("matched_data", 0)) != total
                or int(measures.get("complete_data", 0)) != total):
            continue
        for section in unit.get("sections", []):
            section_name = section.get("name")
            if section_name not in DATA_SECTIONS:
                continue
            size = int(section.get("size", 0))
            address = section.get("metadata", {}).get("virtual_address")
            if size <= 0 or address is None:
                continue
            address = int(address)
            if not 0 <= address < address + size <= 0x100000000:
                raise ValueError("invalid source data interval")
            candidates = [data[address - start:address - start + size]
                          for start, data in dol_sections
                          if start <= address and address + size <= start + len(data)]
            if len(candidates) != 1:
                raise ValueError("source data is not in one DOL section")
            regions.append(SourceRegion(name, source, section_name, address, candidates[0]))
    regions.sort(key=lambda region: region.address)
    for first, second in zip(regions, regions[1:]):
        if first.address + len(first.data) > second.address:
            raise ValueError("overlapping source data owners")
    return regions


def _locations(payload, regions, limit):
    matches = []
    for region in regions:
        offset = 0
        while True:
            offset = region.data.find(payload, offset)
            if offset < 0:
                break
            if len(matches) == limit:
                return matches, True
            matches.append({"unit": region.unit, "source_path": region.source_path,
                            "section": region.section, "dol_address": region.address + offset,
                            "offset_in_source_section": offset})
            offset += 1
    return matches, False


def analyze_message_group(data, regions, rel_offset, *, max_matches=8):
    """Return bounded offset-table metadata and exact storage-span matches."""
    if max_matches < 1 or max_matches > 32:
        raise ValueError("invalid match limit")
    if len(data) < 16:
        raise ValueError("truncated message header")
    group_id, reserved_byte, font_id, count, reserved_word, next_ptr, previous_ptr = (
        struct.unpack_from(">HBBHHII", data))
    table_end = 16 + count * 8
    table = _bounded(data, 16, count * 8)
    entries = list(struct.iter_unpack(">II", table))
    if any(key > 0xFFFFF or not table_end <= offset < len(data)
           for key, offset in entries):
        raise ValueError("invalid message key or offset")
    if any(left[0] >= right[0] for left, right in zip(entries, entries[1:])):
        raise ValueError("message keys are not strictly increasing")
    offsets = sorted({offset for _, offset in entries})
    spans = {}
    for start, end in zip(offsets, offsets[1:] + [len(data)]):
        if end - start < 2:
            raise ValueError("message storage interval is too short")
        payload = data[start:end]
        matches, truncated = _locations(payload, regions, max_matches)
        spans[start] = {"storage_size": len(payload),
                        "storage_sha256": hashlib.sha256(payload).hexdigest(),
                        "source_locations": matches, "locations_truncated": truncated}
    return {
        "rel_offset": rel_offset, "size": len(data),
        "resource_sha256": hashlib.sha256(data).hexdigest(),
        "group_id": group_id, "font_id": font_id, "entry_count": count,
        "reserved_header_fields_zero": reserved_byte == 0 and reserved_word == 0,
        "runtime_link_fields_zero": next_ptr == 0 and previous_ptr == 0,
        "table_end_offset": table_end,
        "header_and_table_sha256": hashlib.sha256(data[:table_end]).hexdigest(),
        "gap_after_table_size": (offsets[0] if offsets else len(data)) - table_end,
        "unique_storage_intervals": len(spans),
        "unique_storage_bytes": sum(span["storage_size"] for span in spans.values()),
        "reusable_storage_bytes": sum(span["storage_size"] for span in spans.values()
                                      if span["source_locations"]),
        "entries_with_source_locations": sum(bool(spans[offset]["source_locations"])
                                              for _, offset in entries),
        "entries": [{"key": key, "offset": offset, **spans[offset]}
                    for key, offset in entries],
    }


def resource_message_reuse_checks(orig, report, repository_root):
    """Inspect only the three known resource slots; never return payloads."""
    tracked = subprocess.run(
        ["git", "-C", str(repository_root), "ls-files", "-z", "--", "src"],
        check=True, capture_output=True).stdout.decode("utf-8").split("\0")
    dol_sections = _dol_data_sections((orig / "sys/main.dol").read_bytes())
    rel_data = _common_rel_data((orig / "files/common_rel.rel").read_bytes())
    regions = eligible_source_regions(report, dol_sections, set(tracked))
    result = {"schema_version": 1, "payload_bytes_included": False,
              "text_decoded": False,
              "interval_rule": "entry offset through next distinct offset or resource end",
              "source_eligibility": "tracked source with all data report-exact and source-linked",
              "eligible_source_regions": len(regions),
              "eligible_source_bytes": sum(len(region.data) for region in regions),
              "groups": []}
    for start, end in MESSAGE_SPANS:
        data = _bounded(rel_data, start, end - start)
        try:
            group = analyze_message_group(data, regions, start)
            group["valid_message_table"] = True
        except ValueError:
            # A suspected resource type may be wrong. Do not echo bytes or
            # arbitrary exception text; preserve the other groups' results.
            group = {"rel_offset": start, "size": end - start,
                     "valid_message_table": False, "error": "invalid_message_table"}
        result["groups"].append(group)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orig", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = resource_message_reuse_checks(
            args.orig, json.loads(args.report.read_text()), args.source_root)
    except (OSError, ValueError, KeyError, struct.error, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Message metadata diagnostic failed: {type(exc).__name__}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Recorded metadata for {len(result['groups'])} message resource candidates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
