#!/usr/bin/env python3
"""Report retail function spans associated with evidenced assembly.

Includes the evidence registry and the separate paired-single allowlist. These
are whole function spans, not assembly instruction bytes: mixed C/assembly and
inlined assembly cannot yield a pure-C percentage from an objdiff report.

    python3 .github/scripts/asm_evidence_summary.py [build/GC6E01/report.json]
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

from quality_scan import DOLPHIN_PAIRED_SINGLE_FUNCTIONS, DOLPHIN_PAIRED_SINGLE_PATH

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = REPO_ROOT / "docs" / "asm_evidence" / "registry.json"


def number(value) -> int:
    return int(value, 0) if isinstance(value, str) and value.startswith("0x") else int(value)


def report_functions(report: dict) -> list[dict]:
    result = []
    for unit in report.get("units", []):
        metadata = unit.get("metadata") or {}
        module = metadata.get("module_name") or unit["name"].split("/", 1)[0]
        sections = unit.get("sections") or []
        functions = [(fn, None) for fn in unit.get("functions") or []]
        for section in sections:
            functions.extend((fn, section["name"]) for fn in section.get("functions") or [])
        for fn, section_name in functions:
            address = (fn.get("metadata") or {}).get("virtual_address")
            # No address means no defensible interval, even if a name matches.
            if address is None or number(fn.get("size", 0)) <= 0:
                continue
            start, size = number(address), number(fn["size"])
            if section_name is None:
                enclosing = {s["name"] for s in sections
                             if (s.get("metadata") or {}).get("virtual_address") is not None
                             and number(s["metadata"]["virtual_address"]) <= start
                             and start + size <= number(s["metadata"]["virtual_address"]) + number(s["size"])}
                if len(enclosing) != 1:
                    continue
                section_name = enclosing.pop()
            result.append(dict(name=fn["name"], module=module, section=section_name,
                               start=start, end=start + size,
                               source=metadata.get("source_path"),
                               matched=float(fn.get("fuzzy_match_percent", 0)) == 100,
                               linked=bool(metadata.get("complete"))))
    return result


def resolve_entry(entry: dict, functions: list[dict]) -> list[dict]:
    """Resolve a standalone source owner; never select the first same-name hit."""
    path = entry.get("path", "")
    module = entry.get("module_name") or entry.get("module")
    if not module and path.startswith("src/"):
        module = path.split("/")[2] if path.startswith("src/rel/") else "main"
    candidates = [fn for fn in functions if fn["source"]
                  and (not module or fn["module"] == module)]
    address = entry.get("address")
    if address is not None:
        if isinstance(address, str) and address.startswith("fn_"):
            address = int(address[3:], 16)
        else:
            address = number(address)
        candidates = [fn for fn in candidates if fn["start"] == address]
    else:
        candidates = [fn for fn in candidates if fn["name"] == entry["function"]]
    same_source = [fn for fn in candidates if fn["source"] == path]
    if same_source:
        candidates = same_source
    # A unique name/address can survive a split into another source owner.
    identities = {(fn["module"], fn["section"], fn["start"], fn["end"])
                  for fn in candidates}
    return candidates if len(identities) == 1 else []


def span_totals(functions: list[dict]) -> dict:
    """Union intervals per module/section, including aliases and overlapping spans."""
    def byte_count(flag=None):
        groups = defaultdict(list)
        for fn in functions:
            if flag is None or fn[flag]:
                groups[(fn["module"], fn["section"])].append((fn["start"], fn["end"]))
        total = 0
        for intervals in groups.values():
            end = -1
            for start, stop in sorted(intervals):
                total += max(0, stop - max(start, end))
                end = max(end, stop)
        return total
    return dict(functions=len({(fn["module"], fn["section"], fn["start"], fn["end"])
                               for fn in functions}),
                bytes=byte_count(), matched_bytes=byte_count("matched"),
                linked_bytes=byte_count("linked"))


def summarize(entries: list[dict], report: dict) -> dict:
    functions = report_functions(report)
    tiers, all_resolved, unresolved = {}, [], []
    for entry in entries:
        tier = entry.get("tier", "library")
        group = tiers.setdefault(tier, dict(entries=0, resolved_entries=0, functions=[]))
        group["entries"] += 1
        resolved = resolve_entry(entry, functions)
        if resolved:
            group["resolved_entries"] += 1
            group["functions"].extend(resolved)
            all_resolved.extend(resolved)
        else:
            unresolved.append(dict(tier=tier, function=entry["function"],
                                   path=entry.get("path", "")))
    for group in tiers.values():
        group.update(span_totals(group.pop("functions")))
    return dict(tiers=tiers, combined=span_totals(all_resolved), unresolved=unresolved)


def main() -> int:
    report_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "build" / "GC6E01" / "report.json"
    entries = json.loads(REGISTRY.read_text(encoding="utf-8")).get("entries", [])
    entries += [dict(path=DOLPHIN_PAIRED_SINGLE_PATH, function=name,
                     tier="paired-single-allowlist")
                for name in sorted(DOLPHIN_PAIRED_SINGLE_FUNCTIONS)]
    if not report_path.is_file():
        print(f"{len(entries)} policy entries; no report at {report_path}. Function spans not measured.")
        return 0
    summary = summarize(entries, json.loads(report_path.read_text(encoding="utf-8")))
    print("Assembly-associated whole retail function spans (not assembly instruction bytes):")
    for tier, group in sorted(summary["tiers"].items()):
        print(f"{tier}: {group['resolved_entries']}/{group['entries']} entries resolved; "
              f"{group['functions']} unique spans, {group['bytes']} bytes "
              f"({group['matched_bytes']} matched, {group['linked_bytes']} linked)")
    total = summary["combined"]
    print(f"Combined, deduplicated: {total['functions']} spans, {total['bytes']} bytes "
          f"({total['matched_bytes']} matched, {total['linked_bytes']} linked).")
    missing = summary["unresolved"]
    print(f"Unresolved standalone entries: {len(missing)} (inline, inactive, or ambiguous; not counted).")
    if missing:
        print("  " + "; ".join(f"{e['function']} [{e['path']}]" for e in missing))
    print("Pure-C coverage is not derivable: mixed-function and inlined assembly is not measured separately.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
