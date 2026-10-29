#!/usr/bin/env python3
"""Measure pinned MWCC alignment using only small, synthetic C declarations.

No original inputs or project source files are read. Each case runs in a fresh
scratch directory; only section/symbol metadata and bounded compiler diagnostics
are written to the requested JSON output. These probes neither modify objects
used by the game build nor grant matching credit.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.import_constant_symbol import parse_symbols, read_elf


def cases():
    plain = "unsigned char tail[7];\nunsigned char head[5];\n"
    initialized = "unsigned char head[5] = {1};\nunsigned char tail[7] = {2};\n"
    yield "zero_plain_arrays", plain, []
    yield "initialized_plain_arrays", initialized, []
    for alignment in (1, 2, 4):
        attr = f" __attribute__((aligned({alignment})))"
        declspec = f"__declspec(align({alignment})) "
        yield f"zero_gnu_aligned_{alignment}", (
            f"unsigned char tail[7]{attr};\nunsigned char head[5]{attr};\n"), []
        yield f"initialized_gnu_aligned_{alignment}", (
            f"unsigned char head[5]{attr} = {{1}};\n"
            f"unsigned char tail[7]{attr} = {{2}};\n"), []
        yield f"zero_declspec_align_{alignment}", (
            f"{declspec}unsigned char tail[7];\n"
            f"{declspec}unsigned char head[5];\n"), []
        yield f"initialized_declspec_align_{alignment}", (
            f"{declspec}unsigned char head[5] = {{1}};\n"
            f"{declspec}unsigned char tail[7] = {{2}};\n"), []
    aggregate = ("struct Byte7 { unsigned char bytes[7]; };\n"
                 "struct Byte5 { unsigned char bytes[5]; };\n"
                 "struct Byte7 tail;\nstruct Byte5 head;\n")
    yield "zero_byte_structs", aggregate, []
    yield "zero_packed_structs", aggregate.replace("struct Byte", "struct __attribute__((packed)) Byte", 2), []
    yield "zero_pragma_pack_structs", "#pragma pack(1)\n" + aggregate + "#pragma pack()\n", []
    yield "zero_pragma_align_packed_structs", "#pragma options align=packed\n" + aggregate + "#pragma options align=reset\n", []
    yield "zero_align_array_members_off", "#pragma align_array_members off\n" + plain, []
    yield "initialized_align_array_members_off", "#pragma align_array_members off\n" + initialized, []
    for alignment in ("mac68k", "mac68k4byte"):
        yield f"zero_align_{alignment}", plain, ["-align", alignment]
        yield f"initialized_align_{alignment}", initialized, ["-align", alignment]
    yield "zero_scalar_halfwords", "unsigned short tail;\nunsigned short head;\n", []
    small = ["-sdata", "16", "-sdata2", "8"]
    yield "small_zero_plain_arrays", plain, small
    yield "small_zero_gnu_aligned_1", (
        "unsigned char tail[7] __attribute__((aligned(1)));\n"
        "unsigned char head[5] __attribute__((aligned(1)));\n"), small
    yield "small_const_zero_gnu_aligned_1", (
        "const unsigned char tail[7] __attribute__((aligned(1)));\n"
        "const unsigned char head[5] __attribute__((aligned(1)));\n"), small


def metadata(blob):
    _, sections = read_elf(blob)
    _, symbols = parse_symbols(sections)
    result = []
    for index, section in enumerate(sections):
        fields = section["fields"]
        if not fields[2] & 2 or not fields[5]:
            continue
        result.append({
            "name": section["name"], "type": fields[1], "flags": fields[2],
            "size": fields[5], "alignment": fields[8],
            "symbols": [{"name": symbol["name"], "offset": symbol["value"],
                         "size": symbol["size"], "info": symbol["info"]}
                        for symbol in symbols if symbol["shndx"] == index
                        and symbol["info"] & 15 != 3 and symbol["name"]],
        })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--wrapper", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    compiler = args.compiler.resolve()
    if not compiler.is_file():
        parser.error("compiler file is missing")
    wrapper = args.wrapper.resolve() if args.wrapper else None
    if wrapper and not wrapper.is_file():
        parser.error("compiler wrapper is missing")
    command = ([str(wrapper)] if wrapper else []) + [str(compiler)]
    flags = ["-nodefaults", "-proc", "gekko", "-align", "powerpc", "-enum", "int",
             "-fp", "hard", "-Cpp_exceptions", "off", "-O4,p", "-inline", "auto",
             "-nosyspath", "-RTTI", "off", "-sdata", "0", "-sdata2", "0"]
    results = []
    for name, source, extra in cases():
        with tempfile.TemporaryDirectory(prefix="mwcc-alignment-") as directory:
            scratch = Path(directory)
            input_path, output_path = scratch / "probe.c", scratch / "probe.o"
            input_path.write_text("#pragma force_active on\n" + source)
            call = command + flags + extra + ["-c", str(input_path), "-o", str(output_path)]
            row = {"case": name, "source": source, "extra_flags": extra}
            try:
                process = subprocess.run(call, cwd=scratch, capture_output=True,
                                         text=True, errors="replace", timeout=30)
                row["returncode"] = process.returncode
                diagnostics = (process.stdout + process.stderr).replace(str(scratch), "<scratch>")
                row["diagnostics"] = diagnostics[:4000]
                row["diagnostics_truncated"] = len(diagnostics) > 4000
                if process.returncode == 0 and output_path.exists():
                    row["sections"] = metadata(output_path.read_bytes())
            except (OSError, ValueError, IndexError, struct.error, subprocess.TimeoutExpired) as error:
                row["error"] = type(error).__name__
            results.append(row)
    result = {"schema_version": 1, "synthetic_inputs_only": True,
              "compiler_sha256": hashlib.sha256(compiler.read_bytes()).hexdigest(),
              "base_flags": flags, "cases": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"cases": len(results), "compiled_cases": sum("sections" in row for row in results),
                      "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
