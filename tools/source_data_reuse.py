#!/usr/bin/env python3
"""Find missing DOL data in native compiled objects of active tracked sources.

Matches must lie inside a defined source symbol, or equal an entire initialized
source section, and neither matched interval may contain relocations. Results
are reuse leads, not matching credit. Original and compiled bytes stay private.
"""

from functools import lru_cache
import hashlib
from pathlib import Path
import subprocess


DATA_SECTIONS = {".data", ".rodata", ".sdata", ".sdata2"}
MAX_OBJECT_BYTES = 16 * 1024 * 1024
MAX_TARGET_BYTES = 2 * 1024 * 1024
MAX_TARGET_SYMBOLS = 4096
MATCH_LIMIT = 8


def _inside(root, path):
    result = (root / path).resolve()
    result.relative_to(root)
    return result


def _has_relocation(section, start, end):
    # All data relocations occupy at most four bytes in these PPC objects.
    # Conservatively reserve four even for halfword forms.
    return any(relocation["offset"] < end and start < relocation["offset"] + 4
               for relocation in section["relocations"])


def matching_intervals(section, data, needle):
    """Yield bounded locations; never treat anonymous section padding as source."""
    if data is None or not needle or section["nobits"]:
        return
    seen = set()
    for symbol in section["symbols"]:
        start, size = symbol["offset"], symbol["size"]
        if symbol["type"] not in (0, 1) or size < len(needle) \
                or start < 0 or start + size > len(data):
            continue
        at = data.find(needle, start, start + size)
        emitted = 0
        while at >= 0 and emitted < MATCH_LIMIT:
            blocked_to = max((relocation["offset"] + 4
                              for relocation in section["relocations"]
                              if relocation["offset"] < at + len(needle)
                              and at < relocation["offset"] + 4), default=0)
            if blocked_to:
                at = data.find(needle, blocked_to, start + size)
                continue
            if at not in seen:
                seen.add(at)
                emitted += 1
                yield {"source_symbol": symbol["name"], "offset": at,
                       "symbol_offset": at - start}
            at = data.find(needle, at + 1, start + size)
    if not seen and len(data) == len(needle) and data == needle \
            and not _has_relocation(section, 0, len(data)):
        yield {"source_symbol": None, "offset": 0, "symbol_offset": None}


def find_source_reuse(config, report, root, build_dir, elf_reader, tracked_paths=None):
    root, build_dir = root.resolve(), build_dir.resolve()
    build_dir.relative_to(root)
    if tracked_paths is None:
        proc = subprocess.run(["git", "ls-files", "-z", "--", "src"], cwd=root,
                              capture_output=True, check=True)
        tracked_paths = set(proc.stdout.decode().split("\0"))
    else:
        tracked_paths = set(tracked_paths)
    config_units = {unit["name"]: unit for unit in config["units"]}
    output = {"schema_version": 1, "payload_bytes_included": False,
              "match_limit_per_target": MATCH_LIMIT, "targets": [], "errors": []}

    @lru_cache(maxsize=4)
    def read(path):
        if path.stat().st_size > MAX_OBJECT_BYTES:
            raise ValueError("Object exceeds bounded diagnostic size")
        return elf_reader(path)

    patterns = {}
    target_bytes = 0
    for unit in report["units"]:
        if not unit["name"].startswith("main/") or unit.get("metadata", {}).get("source_path"):
            continue
        if not any(section["name"] in DATA_SECTIONS for section in unit.get("sections", [])):
            continue
        try:
            settings = config_units[unit["name"]]
            path = _inside(root, Path(config.get("target_dir") or "") / settings["target_path"])
            metadata, private = read(path)
            for section_name, section in metadata.items():
                if section_name not in DATA_SECTIONS or section["nobits"]:
                    continue
                data = private[section_name]
                for symbol in section["symbols"]:
                    start, size = symbol["offset"], symbol["size"]
                    if symbol["type"] != 1 or not size or symbol["name"].startswith("gap_") \
                            or _has_relocation(section, start, start + size):
                        continue
                    if start < 0 or start + size > len(data):
                        raise ValueError("Target symbol exceeds initialized data")
                    needle = data[start:start + size]
                    target_bytes += size
                    if target_bytes > MAX_TARGET_BYTES or len(output["targets"]) >= MAX_TARGET_SYMBOLS:
                        raise ValueError("Target search exceeds bounded diagnostic size")
                    matches = patterns.setdefault(needle, [])
                    output["targets"].append({"unit": unit["name"], "symbol": symbol["name"],
                                              "section": section_name, "offset": start, "size": size,
                                              "sha256": hashlib.sha256(needle).hexdigest(),
                                              "matches": matches})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            output["errors"].append({"unit": unit["name"], "kind": "target",
                                     "error": type(exc).__name__})
    considered = scanned = 0
    seen_objects = set()
    for settings in config["units"]:
        source = settings.get("metadata", {}).get("source_path")
        if source not in tracked_paths or not settings.get("base_path"):
            continue
        considered += 1
        try:
            _inside(root, source)
            base = _inside(root, Path(config.get("base_dir") or "") / settings["base_path"])
            relative = base.relative_to(build_dir)
            if relative.parts[0] not in ("src", "compare"):
                raise ValueError("Expected a configured native source-object path")
            # Comparison views are deliberately not scanned: read their native
            # compiler object so stripped/normalized bytes cannot be mistaken
            # for newly generated source data.
            native = build_dir / "src" / Path(*relative.parts[1:])
            if native in seen_objects:
                continue
            seen_objects.add(native)
            metadata, private = read(native)
            scanned += 1
            for section_name, section in metadata.items():
                if section_name not in DATA_SECTIONS or section["nobits"]:
                    continue
                data = private[section_name]
                for needle, matches in patterns.items():
                    if len(matches) >= MATCH_LIMIT:
                        continue
                    for found in matching_intervals(section, data, needle):
                        matches.append({"owner": settings["name"], "source_path": source,
                                        "object": native.relative_to(root).as_posix(),
                                        "section": section_name, **found, "size": len(needle),
                                        "sha256": hashlib.sha256(needle).hexdigest()})
                        if len(matches) >= MATCH_LIMIT:
                            break
        except (OSError, ValueError, KeyError, TypeError) as exc:
            output["errors"].append({"unit": settings["name"], "kind": "source",
                                     "error": type(exc).__name__})
    output["summary"] = {"source_objects_considered": considered, "source_objects_scanned": scanned,
                         "target_symbols": len(output["targets"]),
                         "target_symbols_with_matches": sum(bool(row["matches"]) for row in output["targets"]),
                         "errors": len(output["errors"])}
    read.cache_clear()
    return output
