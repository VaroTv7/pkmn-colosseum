"""Compare objdiff functions by module/address, not mutable names or TU paths.

This is a report audit, not a substitute for canonical binary hash checks.
"""
import argparse
import json
from bisect import bisect_right
from pathlib import Path
from typing import Any, Dict, Tuple

Key = Tuple[str, int]


def index_report(report: Dict[str, Any]) -> Dict[Key, Dict[str, Any]]:
    result = {}
    for unit in report.get("units", []):
        metadata = unit.get("metadata", {})
        module = metadata.get("module_name") or unit["name"].split("/", 1)[0]
        functions = list(unit.get("functions", []))
        for section in unit.get("sections", []):
            functions.extend(section.get("functions", []))
        for function in functions:
            address = function.get("metadata", {}).get("virtual_address")
            if address is None:
                raise ValueError(f"Missing address: {unit['name']}:{function['name']}")
            key = (module, int(address))
            if key in result:
                raise ValueError(f"Duplicate function identity: {key}")
            size = int(function["size"])
            score = float(function.get("fuzzy_match_percent", 0.0))
            if size <= 0 or not 0 <= score <= 100:
                raise ValueError(f"Invalid function size/score: {key}")
            result[key] = dict(name=function["name"], address=key[1],
                               module=module, size=size, score=score,
                               unit=unit["name"])
    expected = report.get("measures", {}).get("total_functions")
    if expected is not None and len(result) != int(expected):
        raise ValueError(f"Function count mismatch: {len(result)} != {expected}")
    if not result:
        raise ValueError("Empty function index is not validation evidence")
    return result


def compare_reports(base: Dict[str, Any], head: Dict[str, Any]) -> Dict[str, Any]:
    before, after = index_report(base), index_report(head)
    common = before.keys() & after.keys()
    regressions, renamed, boundaries = [], [], []
    for key in sorted(common):
        old, new = before[key], after[key]
        entry = dict(module=key[0], address=hex(key[1]),
                     before=old, after=new)
        if new["score"] < old["score"] - 0.01:
            regressions.append(entry)
        if old["name"] != new["name"]:
            renamed.append(entry)
        if old["size"] != new["size"]:
            boundaries.append(entry)
    missing, coalesced = [], []
    module_keys = {}
    for module, address in after:
        module_keys.setdefault(module, []).append(address)
    for addresses in module_keys.values():
        addresses.sort()
    for key in sorted(before.keys() - after.keys()):
        old = before[key]
        addresses = module_keys.get(key[0], [])
        pos = bisect_right(addresses, key[1]) - 1
        covering = after[(key[0], addresses[pos])] if pos >= 0 else None
        # A vanished identity is acceptable only when a 100%-matched replacement
        # demonstrably covers its full original address interval.
        if (covering and covering["score"] == 100.0
                and covering["address"] <= old["address"]
                and covering["address"] + covering["size"] >= old["address"] + old["size"]):
            coalesced.append(dict(before=old, covered_by=covering))
        else:
            missing.append(old)
    shrinking = [e for e in boundaries if e["after"]["size"] < e["before"]["size"]]
    return dict(
        scope="Report-level comparison only; canonical binary validation remains separate",
        base_functions=len(before), head_functions=len(after), compared_functions=len(common),
        regressions=regressions, missing_functions=missing,
        renamed_functions=renamed, boundary_changes=boundaries,
        coalesced_functions=coalesced,
        new_functions=[after[k] for k in sorted(after.keys() - before.keys())],
        base_measures=base.get("measures", {}), head_measures=head.get("measures", {}),
        passed=not (regressions or missing or shrinking),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("head", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = compare_reports(json.loads(args.base.read_text()), json.loads(args.head.read_text()))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"Report audit failed: {error}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Compared {result['compared_functions']} module/address identities: "
          f"{len(result['regressions'])} score regressions, "
          f"{len(result['missing_functions'])} unexplained removals, "
          f"{len(result['renamed_functions'])} renames, "
          f"{len(result['boundary_changes'])} boundary changes, "
          f"{len(result['coalesced_functions'])} exact interval coalescences.")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
