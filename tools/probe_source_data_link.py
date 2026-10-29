#!/usr/bin/env python3
"""Metadata-only CI linker isolation. Never a progress/report build input.

Writes only below build/GC6E01/probe. No Ninja/DTK split or local wrapper probes.
ELF inspection reads only the header, bounded section headers and section names.
Tool output is discarded except strictly parsed elf2dol section-processing names.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shlex
import signal
import struct
import subprocess
import time

if __package__:
    from .source_data_aliases import comment_records
    from .source_object_metadata import Elf
else:
    from source_data_aliases import comment_records
    from source_object_metadata import Elf


class ProbeError(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise ProbeError(reason)


def digest(path, cap=128 * 1024 * 1024):
    require(path.stat().st_size <= cap, "hash_input_exceeds_cap")
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def elf_headers(path):
    """Return bounded ELF structural metadata, including malformed reasons."""
    result = {"exists": path.is_file(), "payload_read": False}
    if not result["exists"]:
        return result
    result["file_size"] = size = path.stat().st_size
    try:
        with path.open("rb") as f:
            def read(offset, length):
                require(0 <= offset <= size and 0 <= length <= 65536
                        and offset + length <= size, "metadata_range_outside_file")
                f.seek(offset)
                value = f.read(length)
                require(len(value) == length, "short_metadata_read")
                return value

            header = struct.unpack(">16sHHIIIIIHHHHHH", read(0, 52))
            require(header[0][:7] == b"\x7fELF\x01\x02\x01", "not_elf32_big_endian_v1")
            fields = ("type", "machine", "version", "entry", "program_table_offset",
                      "section_table_offset", "flags", "header_size",
                      "program_entry_size", "program_count", "section_entry_size",
                      "section_count", "section_names_index")
            result["header"] = dict(zip(fields, header[1:]))
            require(header[1:4] == (2, 20, 1) and header[8] == 52,
                    "not_powerpc_executable")
            require(header[11] == 40 and 0 < header[12] <= 512,
                    "invalid_or_excessive_section_table")
            require(header[13] < header[12], "invalid_section_name_index")
            sections = list(struct.iter_unpack(">10I", read(header[6], header[12] * 40)))
            shstr = sections[header[13]]
            require(shstr[1] == 3 and shstr[5] <= 65536, "invalid_or_excessive_section_names")
            names = read(shstr[4], shstr[5])
            rows, issues = [], []
            for index, s in enumerate(sections):
                end = names.find(b"\0", s[0]) if s[0] < len(names) else -1
                require(end >= 0, "invalid_section_name_offset")
                raw_name = names[s[0]:end]
                name = raw_name.decode("ascii") if re.fullmatch(rb"[A-Za-z0-9_.$-]{0,80}", raw_name) else "<nonstandard>"
                row = dict(zip(("name_offset", "type", "flags", "address", "offset",
                                "size", "link", "info", "alignment", "entry_size"), s))
                row.update(index=index, name=name)
                row["file_range_valid"] = s[1] == 8 or s[4] + s[5] <= size
                row["address_range_valid"] = s[3] + s[5] <= 0x100000000
                row["alignment_valid"] = s[8] == 0 or s[8] & (s[8] - 1) == 0
                rows.append(row)
                if not all(row[k] for k in ("file_range_valid", "address_range_valid", "alignment_valid")):
                    issues.append({"section": index, "reason": "invalid_section_bounds_or_alignment"})
                if s[2] & 2 and s[5] > 32 * 1024 * 1024:
                    issues.append({"section": index, "reason": "allocated_section_exceeds_probe_cap"})
            result["sections"] = rows
            result["issues"] = issues
            result["structurally_bounded"] = not issues and size <= 128 * 1024 * 1024
    except (OSError, ProbeError, struct.error) as exc:
        result["error_stage"] = "bounded_elf_headers"
        result["error_reason"] = str(exc) if isinstance(exc, ProbeError) else type(exc).__name__
        result["structurally_bounded"] = False
    return result


def ninja_plan(repo):
    text = (repo / "build.ninja").read_text()
    lines = re.sub(r"\$\r?\n[ \t]*", "", text).splitlines()
    globals_, rules, edge = {}, {}, None
    context = None
    for line in lines:
        if line.startswith("rule "):
            context = rules.setdefault(line[5:], {})
        elif line.startswith("build "):
            context = None
            if line.startswith("build build/GC6E01/main.elf ") and ": link " in line:
                require(edge is None, "multiple_main_link_edges")
                inputs = line.split(": link ", 1)[1].split(" |", 1)[0].split()
                edge = {"inputs": inputs}
                context = edge
        elif line and not line[0].isspace() and not line.startswith("#"):
            context = None
            match = re.fullmatch(r"([A-Za-z_]\w*) = (.*)", line)
            if match:
                globals_[match[1]] = match[2]
        elif context is not None:
            match = re.fullmatch(r"  ([A-Za-z_]\w*) = (.*)", line)
            if match:
                context[match[1]] = match[2]
    require(edge is not None and "link" in rules, "main_link_rule_missing")
    require(rules["link"].get("rspfile_content") == "$in_newline", "unsupported_response_template")
    token = re.compile(r"\$(\$|[ :]|\{[A-Za-z_]\w*\}|[A-Za-z_]\w*)")

    def expand(value, variables, depth=0):
        require(depth < 20, "recursive_ninja_variable")
        def replace(match):
            key = match[1]
            if key in ("$", " ", ":"):
                return key
            key = key.strip("{}")
            require(key in variables, "unknown_ninja_variable")
            return expand(variables[key], variables, depth + 1)
        return token.sub(replace, value)

    variables = dict(globals_)
    for key, value in edge.items():
        if key != "inputs":
            variables[key] = expand(value, globals_)
    variables["out"] = "build/GC6E01/main.elf"
    command = shlex.split(expand(rules["link"]["command"], variables))
    require(command.count("-o") == 1 and command.count("-map") == 1,
            "unsupported_link_output_flags")
    require(not any(x in command for x in (";", "&&", "||", "|", ">", "<")),
            "shell_link_rule_not_supported")
    require(command.count("@build/GC6E01/main.elf.rsp") == 1, "unexpected_response_argument")
    rsp = repo / "build/GC6E01/main.elf.rsp"
    if rsp.is_file():
        payload = rsp.read_text()
        require(shlex.split(payload) == edge["inputs"], "existing_response_differs_from_link_edge")
        origin = "existing_main_response_file"
    else:
        # Ninja removes a response file after a successful link. Reproduce only
        # its verified $in_newline template; this never changes the real edge.
        payload = "\n".join(edge["inputs"]) + "\n"
        origin = "verified_ninja_in_newline_template"
    require(all(re.fullmatch(r"[A-Za-z0-9_./+-]+\.o", p) for p in edge["inputs"]),
            "unsupported_response_input_path")
    return command, edge["inputs"], payload, origin


def substitutions(repo, inputs):
    cfg = json.loads((repo / "objdiff.json").read_text())
    alias_stems = {"sdata_80478820", "sdata_80478950", "sdata_80478D78"}
    alias = {}
    for unit in cfg["units"]:
        stem = unit["name"].rsplit("/", 1)[-1]
        if unit["name"].startswith("main/game/data/") and stem in alias_stems:
            alias[f"build/GC6E01/link/game/data/{stem}.o"] = unit["target_path"]
    require(len(alias) == 3, "unexpected_replacement_set_counts")
    for src, target in alias.items():
        require(inputs.count(src) == 1 and target not in inputs,
                "replacement_source_not_unique_or_target_already_linked")
        require(target.startswith("build/GC6E01/obj/") and target.endswith(".o"),
                "replacement_not_current_dtk_target")
    return alias


def unchanged_data(source, candidate):
    """Check storage independently of symbol-table order or metadata presence."""
    require(set(source.allocated) == {".sdata"} == set(candidate.allocated),
            "alias_candidate_requires_only_initialized_small_data")
    si, ci = source.allocated[".sdata"], candidate.allocated[".sdata"]
    before, after = source.sections[si], candidate.sections[ci]
    require((before[1], before[2], before[5], before[8]) ==
            (after[1], after[2], after[5], after[8]) and before[1:3] == (1, 3),
            "alias_candidate_changed_allocation_or_alignment")
    require(source.payload(si) == candidate.payload(ci), "alias_candidate_changed_storage_bytes")
    relocs = source.data_relocations()
    require(relocs == candidate.data_relocations(), "alias_candidate_changed_relocation_semantics")
    return {"allocated_bytes": before[5], "alignment": before[8],
            "data_sha256": hashlib.sha256(source.payload(si)).hexdigest(),
            "relocation_count": len(relocs), "allocated_bytes_changed": 0,
            "relocation_semantics_changed": 0}


def symbol_identities(elf):
    # File and section symbols may be regenerated by an ELF serializer; every
    # actual named definition/reference, including zero-size labels, must stay.
    return sorted((name, s[1], s[2], s[3], s[4],
                   elf.names[s[5]] if 0 < s[5] < len(elf.sections) else f"reserved:{s[5]}")
                  for name, s in elf.symbols[1:] if s[3] & 15 not in (3, 4))


def validate_alias_candidate(source_blob, candidate_blob, groups):
    source, candidate = Elf(source_blob), Elf(candidate_blob)
    result = unchanged_data(source, candidate)
    require(source.header[7] == candidate.header[7], "alias_candidate_changed_elf_flags")
    require(symbol_identities(source) == symbol_identities(candidate),
            "alias_candidate_changed_symbol_identity_or_bounds")
    require(isinstance(groups, list) and groups, "alias_groups_missing")
    labels = 0
    for group in groups:
        require(isinstance(group, dict) and set(group) == {"base", "size", "aliases"},
                "malformed_alias_group")
        _, host = candidate.unique_symbol(group["base"])
        require(type(group["size"]) is int and group["size"] > 0
                and host[2] == group["size"] and host[3:6] ==
                (0x11, 0, candidate.allocated[".sdata"]), "incomplete_native_array_host")
        require(isinstance(group["aliases"], list) and group["aliases"], "alias_group_has_no_labels")
        for alias in group["aliases"]:
            require(isinstance(alias, dict) and set(alias) == {"name", "offset", "size"}
                    and type(alias["offset"]) is int and 0 < alias["offset"] < host[2]
                    and type(alias["size"]) is int and 0 < alias["size"] <= host[2] - alias["offset"],
                    "malformed_or_out_of_bounds_alias_label")
            _, label = candidate.unique_symbol(alias["name"])
            require(label[1:6] == (host[1] + alias["offset"], 0, 0x10, 0, host[5]),
                    "alias_candidate_lost_zero_size_interior_label")
            labels += 1
    result.update(complete_array_hosts=len(groups), zero_size_interior_labels=labels,
                  all_symbol_identities_preserved=True,
                  codewarrior_comment_present=".comment" in candidate.names)
    return result


def sort_alias_globals(blob):
    """Reorder only global metadata, preserving paired CW and relocation refs."""
    source = Elf(blob)
    require(set(source.names) <= {"", ".sdata", ".rela.sdata", ".symtab", ".strtab",
                                  ".shstrtab", ".comment"},
            "unknown_alias_symbol_indexed_metadata")
    source.data_relocations()  # Validate every relocation before changing indices.
    comment_index, comment = comment_records(source)
    table = source.sections[source.symtab]
    boundary = table[7]

    def key(index):
        s = source.symbols[index][1]
        return (s[5] not in source.allocated.values(), s[5], s[1],
                not (s[3] & 15 == 1 and s[2] > 0), index)

    order = list(range(boundary)) + sorted(range(boundary, len(source.symbols)), key=key)
    indices = {old: new for new, old in enumerate(order)}
    output = bytearray(blob)
    raw = source.payload(source.symtab)
    output[table[4]:table[4] + table[5]] = b"".join(raw[16*i:16*i + 16] for i in order)
    cs = source.sections[comment_index]
    output[cs[4] + 44:cs[4] + cs[5]] = b"".join(comment[44 + 8*i:52 + 8*i] for i in order)
    remapped = 0
    for section in source.sections:
        if section[1] != 4:
            continue
        for offset in range(section[4], section[4] + section[5], 12):
            info = struct.unpack_from(">I", output, offset + 4)[0]
            old_index, kind = info >> 8, info & 255
            require(old_index in indices, "invalid_alias_relocation_symbol_index")
            struct.pack_into(">I", output, offset + 4, indices[old_index] << 8 | kind)
            remapped += indices[old_index] != old_index
    output = bytes(output)
    checked = Elf(output)
    require(source.header == checked.header and source.sections == checked.sections,
            "alias_sort_changed_elf_layout")
    require(checked.symbols == [source.symbols[i] for i in order],
            "alias_sort_changed_symbol_record")
    require(comment_records(checked)[1] == comment[:44] +
            b"".join(comment[44 + 8*i:52 + 8*i] for i in order),
            "alias_sort_changed_paired_compiler_records")
    changed = {source.symtab, comment_index}
    changed.update(i for i, s in enumerate(source.sections) if s[1] == 4)
    require(all(source.payload(i) == checked.payload(i)
                for i in range(len(source.sections)) if i not in changed),
            "alias_sort_changed_unrelated_bytes")
    unchanged_data(source, checked)
    require(symbol_identities(source) == symbol_identities(checked), "alias_sort_changed_symbol_identity")
    return output, {"symbol_records_reordered": sum(i != old for i, old in enumerate(order)),
                    "relocation_indices_remapped": remapped, "local_prefix_unchanged": True}


SOURCE_VARIANTS = ("alias_no_comment", "alias_sorted", "alias_sorted_no_comment")


def prepare_alias_candidates(repo, out, aliases,
                             objcopy=Path("build/binutils/powerpc-eabi-objcopy")):
    """Build source-only variants; original targets are used only as controls."""
    root = out / "candidate_objects"
    require(not root.exists(), "candidate_directory_already_exists")
    root.mkdir()
    replacements = {mode: {} for mode in SOURCE_VARIANTS}
    metadata, source_metadata = [], []
    for src, target in sorted(aliases.items()):
        stem = Path(src).stem
        source_blob = (repo / src).read_bytes()
        groups = json.loads((repo / "config/GC6E01/data_aliases" / (stem + ".json")).read_text())
        proof = validate_alias_candidate(source_blob, source_blob, groups)
        target_proof = unchanged_data(Elf(source_blob), Elf((repo / target).read_bytes()))
        source_metadata.append({"owner": stem, "current": proof, "target_control": target_proof})
        sorted_blob, sorted_proof = sort_alias_globals(source_blob)
        paths = {}
        for mode in SOURCE_VARIANTS:
            directory = root / mode
            directory.mkdir(exist_ok=True)
            paths[mode] = directory / (stem + ".o")
        paths["alias_sorted"].write_bytes(sorted_blob)
        for mode in SOURCE_VARIANTS:
            row = {"owner": stem, "variant": mode}
            if "sorted" in mode:
                row["sorting"] = sorted_proof
            if mode != "alias_sorted":
                before = paths["alias_sorted"] if "sorted" in mode else repo / src
                row["objcopy"] = bounded_command(
                    [str(objcopy), "--remove-section=.comment",
                     str(before.relative_to(repo)), str(paths[mode].relative_to(repo))], repo, 15)
                require(row["objcopy"]["exit_code"] == 0, "alias_comment_removal_failed")
            blob = paths[mode].read_bytes()
            row["invariants"] = validate_alias_candidate(source_blob, blob, groups)
            require(row["invariants"]["codewarrior_comment_present"] == (mode == "alias_sorted"),
                    "alias_candidate_comment_mode_incorrect")
            row["object_sha256"] = hashlib.sha256(blob).hexdigest()
            replacements[mode][src] = str(paths[mode].relative_to(repo))
            metadata.append(row)
    return replacements, {"controls": source_metadata, "source_derived_candidates": metadata}


def bounded_command(command, cwd, timeout, conversion=False):
    start = time.monotonic()
    result = {"timeout_seconds": timeout, "timed_out": False,
              "captured_payload": False, "processing_sections": []}
    p = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, start_new_session=True)
    os.set_blocking(p.stdout.fileno(), False)
    selector = selectors.DefaultSelector()
    selector.register(p.stdout, selectors.EVENT_READ)
    tail, total, kill_at = b"", 0, None
    while selector.get_map() or p.poll() is None:
        now = time.monotonic()
        if now - start >= timeout and kill_at is None:
            result["timed_out"] = True
            kill_at = now + 3
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        if kill_at is not None and now >= kill_at:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            # Bound inherited pipes too; do not wait forever for a descendant.
            if now >= kill_at + 2:
                break
        for key, _ in selector.select(0.1):
            chunk = os.read(key.fd, 8192)
            if not chunk:
                selector.unregister(key.fileobj)
                continue
            total += len(chunk)
            if conversion:
                data = tail + chunk
                lines = data.split(b"\n")
                tail = lines.pop()[-512:]
                for line in lines:
                    match = re.search(rb"Processing (text|data) section:? ['\"]?([A-Za-z0-9_.$-]{1,80})(?:['\"]|\s|$)", line)
                    if match and len(result["processing_sections"]) < 128:
                        result["processing_sections"].append({"kind": match[1].decode(), "name": match[2].decode()})
    selector.close()
    p.stdout.close()
    try:
        result["exit_code"] = p.wait(timeout=2)
    except subprocess.TimeoutExpired:
        result["exit_code"] = None
    result["duration_seconds"] = round(time.monotonic() - start, 3)
    result["discarded_tool_output_bytes"] = total
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--out", default="build/GC6E01/probe/link-isolation")
    parser.add_argument("--link-timeout", type=int, default=60)
    parser.add_argument("--convert-timeout", type=int, default=30)
    parser.add_argument("--objcopy", type=Path,
                        default=Path("build/binutils/powerpc-eabi-objcopy"))
    parser.add_argument("--inspect-only", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = (repo / args.out).resolve()
    require(out.is_relative_to(repo / "build/GC6E01/probe"), "output_outside_private_probe_tree")
    require(1 <= args.link_timeout <= 300 and 1 <= args.convert_timeout <= 120,
            "timeout_outside_probe_bounds")
    out.mkdir(parents=True, exist_ok=True)
    summary = {"schema_version": 1, "diagnostic_only": True,
               "fallbacks_never_feed_normal_build": True, "payload_bytes_included": False,
               "existing_main_elf": elf_headers(repo / "build/GC6E01/main.elf"),
               "variants": []}
    output = out / "summary.json"

    def save():
        output.write_text(json.dumps(summary, indent=2) + "\n")

    save()
    if args.inspect_only:
        print(json.dumps(summary, indent=2))
        return 0
    command, inputs, rsp, origin = ninja_plan(repo)
    alias = substitutions(repo, inputs)
    summary.update(response_origin=origin, response_sha256=hashlib.sha256(rsp.encode()).hexdigest(),
                   input_count=len(inputs), alias_replacements=len(alias))
    if args.plan_only:
        summary["planned_variants"] = [{"name": name, "replacement_count": 0 if name == "current" else 3}
                                       for name in ("current", "target_aliases", *SOURCE_VARIANTS)]
        save()
        print(json.dumps(summary, indent=2))
        return 0
    # Hash every read-only linker input, alias targets, linker script, and
    # generated metadata configs before/after. This never reads section payloads
    # into output; only a combined manifest hash is published.
    immutable = set(inputs) | set(alias.values())
    immutable.update(("build.ninja", "objdiff.json"))
    immutable.update("config/GC6E01/data_aliases/" + Path(src).stem + ".json" for src in alias)
    immutable.update("build/GC6E01/src/game/data/" + Path(src).name for src in alias)
    immutable.update("build/GC6E01/compare/game/data/" + Path(src).name for src in alias)
    immutable.add(command[command.index("-lcf") + 1])
    if origin == "existing_main_response_file":
        immutable.add("build/GC6E01/main.elf.rsp")
    before = {p: digest(repo / p) for p in sorted(immutable)}
    candidates, summary["alias_candidate_validation"] = prepare_alias_candidates(
        repo, out, alias, args.objcopy)
    # Validation completes for all current/control/candidate data before any
    # MWLD command can consume a diagnostic response file.
    save()
    plan = (("current", {}), ("target_aliases", alias),
            *((mode, candidates[mode]) for mode in SOURCE_VARIANTS))
    for name, replacements in plan:
        variant = out / name
        require(not variant.exists(), "probe_variant_already_exists")
        variant.mkdir()
        elf = variant / "main.elf"
        dol = variant / "main.dol"
        response = variant / "main.elf.rsp"
        response.write_text(rsp if not replacements else "\n".join(replacements.get(p, p) for p in inputs) + "\n")
        argv = list(command)
        argv[argv.index("-o") + 1] = str(elf.relative_to(repo))
        argv[argv.index("-map") + 1] = str((variant / "main.elf.MAP").relative_to(repo))
        argv[argv.index("@build/GC6E01/main.elf.rsp")] = "@" + str(response.relative_to(repo))
        row = {"name": name, "replacement_count": len(replacements),
               "response_sha256": digest(response)}
        row["link"] = bounded_command(argv, repo, args.link_timeout)
        row["elf"] = elf_headers(elf)
        if row["link"]["exit_code"] == 0 and row["elf"].get("structurally_bounded"):
            row["convert"] = bounded_command(["build/tools/dtk", "-L", "debug", "elf2dol",
                                              str(elf.relative_to(repo)), str(dol.relative_to(repo))],
                                             repo, args.convert_timeout, conversion=True)
            if dol.is_file():
                row["dol_file_size"] = dol.stat().st_size
                if row["dol_file_size"] <= 32 * 1024 * 1024:
                    row["dol_sha256"] = digest(dol)
        summary["variants"].append(row)
        save()
        print(json.dumps(row), flush=True)
    after = {p: digest(repo / p) for p in sorted(immutable)}
    summary["input_files_unchanged"] = before == after
    summary["input_manifest_sha256"] = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
    save()
    require(before == after, "readonly_input_changed_during_probe")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ProbeError, OSError, KeyError, ValueError, struct.error) as exc:
        print(json.dumps({"diagnostic_only": True, "error_stage": "probe_setup_or_execution",
                          "error_reason": str(exc) if isinstance(exc, ProbeError) else type(exc).__name__,
                          "payload_bytes_included": False}))
        raise SystemExit(1)
