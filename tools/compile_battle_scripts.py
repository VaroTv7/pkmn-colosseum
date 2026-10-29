#!/usr/bin/env python3
"""Compile typed battle programs to a normal PowerPC data object.

Inputs are authored JSON programs, their source catalog, and the public symbol
map. No original executable, extracted section, target object, or byte dump is an
input. GNU as emits ordinary data symbols and R_PPC_ADDR32 relocations; there is
no binary patching or native instruction generation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

if __package__:
    from .battle_script_format import (BATTLERS, COMMANDS, COMPARISONS, EXTERNAL_COMMAND_STRIDES, FIELD_WIDTH,
                                       STATS, STATUS_FAMILIES, STATUS_GET_FIELDS, STATUS_SET_FIELDS)
else:
    from battle_script_format import (BATTLERS, COMMANDS, COMPARISONS, EXTERNAL_COMMAND_STRIDES, FIELD_WIDTH,
                                      STATS, STATUS_FAMILIES, STATUS_GET_FIELDS, STATUS_SET_FIELDS)


FORMAT = "colosseum-battle-source-v1"
CATALOG_FORMAT = "colosseum-battle-catalog-v1"
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")
SOURCE_FILENAME = re.compile(r"[A-Za-z_0-9]+\.battle\.json\Z")
MAP_ROW = re.compile(
    r"^(\S+) = ([^:]+):0x([0-9A-Fa-f]+);.*\btype:(\w+).*\bsize:0x([0-9A-Fa-f]+)"
)


class SourceError(ValueError):
    """Invalid program source; no output object should be installed."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise SourceError(reason)


def fields(value: Any, required: set[str], optional: set[str], what: str) -> dict:
    require(isinstance(value, dict), f"{what}: expected an object")
    require(required <= value.keys(), f"{what}: missing required fields {sorted(required)}")
    require(value.keys() <= required | optional, f"{what}: unexpected fields")
    return value


def integer(value: Any, what: str, low: int, high: int) -> int:
    require(type(value) is int and low <= value <= high,
            f"{what}: expected an integer in {low}..{high}")
    return value


def identifier(value: Any, what: str) -> str:
    require(isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None,
            f"{what}: invalid identifier")
    return value


def enum(value: Any, values: dict[str, int], what: str, numeric_domain: set[int]) -> int:
    if isinstance(value, str):
        require(value in values, f"{what}: unknown enum value {value!r}")
        return values[value]
    require(type(value) is int and value in numeric_domain, f"{what}: invalid enum value")
    return value


@dataclass(frozen=True)
class Symbol:
    address: int
    size: int
    section: str
    kind: str = "object"


def parse_symbols(text: str) -> dict[str, Symbol]:
    symbols = {}
    for line in text.splitlines():
        row = MAP_ROW.match(line)
        if row is None:
            continue
        name, section, address, kind, size = row.groups()
        # Compiler-local constants (@50, etc.) are deliberately not addressable
        # in this source language and can repeat in the public object map.
        if IDENTIFIER.fullmatch(name) is None or "scope:local" in line:
            continue
        require(name not in symbols, f"duplicate symbol map definition: {name}")
        symbols[name] = Symbol(int(address, 16), int(size, 16), section, kind)
    require(bool(symbols), "symbol map contains no sized definitions")
    return symbols


@dataclass
class Program:
    symbol: str
    body: list[dict]
    labels: dict[str, int]
    positions: list[int]
    size: int


@dataclass
class Owner:
    filename: str
    unit: str
    alignment: int
    programs: list[Program]
    size: int


class Compiler:
    """Validate a source catalog before serializing any selected owner.

    A branch names an entry label, never a numeric offset. Labels in authored
    programs are computed from command widths. External entries are declarations
    for already source-backed scripts, with their independently checked offsets
    recorded in the catalog; they cannot be invented in an operand.
    """

    def __init__(self, documents: dict[str, dict], catalog: dict,
                 symbols: dict[str, Symbol]):
        fields(catalog, {"format", "sources", "external_entries"}, {"description"}, "catalog")
        require(catalog["format"] == CATALOG_FORMAT, "unsupported battle catalog format")
        require(isinstance(catalog["sources"], list) and catalog["sources"], "empty source catalog")
        require(all(isinstance(name, str) and SOURCE_FILENAME.fullmatch(name)
                    for name in catalog["sources"]), "invalid catalog source filename")
        require(len(set(catalog["sources"])) == len(catalog["sources"]), "duplicate catalog source")
        require(set(documents) == set(catalog["sources"]), "catalog/source set differs")
        self.symbols = symbols
        self.owners: dict[str, Owner] = {}
        self.programs: dict[str, Program] = {}
        self.entries: dict[str, dict[str, int]] = {}
        self.external_sources: set[str] = set()
        self.external_entries: list[dict] = []
        occupied = []
        for filename in catalog["sources"]:
            doc = documents[filename]
            fields(doc, {"format", "catalog", "unit", "alignment", "programs"},
                   {"description"}, filename)
            require(doc["format"] == FORMAT, f"{filename}: unsupported source format")
            require(doc["catalog"] == "catalog.json", "source must use its sibling catalog.json")
            require(isinstance(doc["unit"], str) and
                    re.fullmatch(r"main/[A-Za-z_0-9]+", doc["unit"]), "invalid source unit name")
            require(doc["unit"] not in {o.unit for o in self.owners.values()}, "duplicate source unit")
            alignment = integer(doc["alignment"], "section alignment", 1, 32)
            require(alignment & (alignment - 1) == 0, "alignment must be a power of two")
            require(isinstance(doc["programs"], list) and doc["programs"], "empty program owner")
            programs = []
            start = None
            cursor = None
            for source in doc["programs"]:
                fields(source, {"symbol", "body"}, {"description"}, "program")
                name = identifier(source["symbol"], "program symbol")
                require(name not in self.programs, f"duplicate program definition: {name}")
                symbol = self.symbol(name)
                require(symbol.section == ".data" and symbol.kind == "object" and symbol.size > 0,
                        f"{name}: script must be a nonempty .data object")
                if start is None:
                    start = cursor = symbol.address
                    require(start % alignment == 0, f"{name}: section start violates alignment")
                require(symbol.address == cursor, f"{name}: source ownership has a gap or overlap")
                require(isinstance(source["body"], list) and source["body"], f"{name}: empty body")
                labels = {"entry": 0}
                positions = []
                position = 0
                for node in source["body"]:
                    require(isinstance(node, dict) and "command" in node, f"{name}: expected a command")
                    require(isinstance(node["command"], str) and node["command"] in COMMANDS,
                            f"{name}: unknown command")
                    command = COMMANDS[node["command"]]
                    fields(node, {"command", *(name for name, _ in command.fields)},
                           {"label", "note"}, f"{name}/{command.name}")
                    if "note" in node:
                        require(isinstance(node["note"], str), "command note must be text")
                    if "label" in node:
                        label = identifier(node["label"], "entry label")
                        require(label not in labels, f"{name}: duplicate/reserved entry label {label}")
                        labels[label] = position
                    positions.append(position)
                    position += command.size
                require(position == symbol.size,
                        f"{name}: command extent {position} differs from mapped object size {symbol.size}")
                program = Program(name, source["body"], labels, positions, position)
                self.programs[name] = program
                self.entries[name] = labels
                programs.append(program)
                occupied.append((symbol.address, symbol.address + symbol.size, name))
                cursor += symbol.size
            self.owners[filename] = Owner(filename, doc["unit"], alignment, programs, cursor - start)
        occupied.sort()
        require(all(left[1] <= right[0] for left, right in zip(occupied, occupied[1:])),
                "source program owners overlap")
        require(isinstance(catalog["external_entries"], list), "external entries must be a list")
        for entry in catalog["external_entries"]:
            fields(entry, {"symbol", "source", "labels"}, {"description"}, "external script")
            name = identifier(entry["symbol"], "external script symbol")
            require(name not in self.entries, f"duplicate external/defined script: {name}")
            symbol = self.symbol(name)
            require(symbol.kind == "object" and symbol.section == ".data" and symbol.size > 0,
                    "external script must name a nonempty data object")
            path = entry["source"]
            require(isinstance(path, str) and re.fullmatch(r"src/game/[A-Za-z_0-9/]+\.c", path),
                    "external entry requires an existing C source path")
            self.external_sources.add(path)
            self.external_entries.append(entry)
            require(isinstance(entry["labels"], dict) and entry["labels"], "empty external entry set")
            labels = {}
            for label, offset in entry["labels"].items():
                identifier(label, "external label")
                labels[label] = integer(offset, "external entry offset", 0, symbol.size - 1)
            require(labels.get("entry") == 0, "external script must declare its entry at zero")
            require(len(set(labels.values())) == len(labels), "duplicate external entry offset")
            self.entries[name] = labels
        # Check operands in every catalog member, including cross-owner branches,
        # before an object for any one owner can be emitted.
        for owner in self.owners.values():
            self.assembly(owner.filename)

    def verify_external_entries(self, root: Path) -> list[Path]:
        """Check entry declarations against the existing, source-owned C arrays.

        This intentionally recognizes only the explicit u8[] and void*[] constant
        initializer forms used by those owners. It never reads a target object.
        Symbolic pointer initializers are evaluated with the public map, after
        which the handler-derived strides locate valid instruction boundaries.
        Unsupported C syntax fails closed instead of approximating its bytes.
        """
        root = root.resolve()
        paths = set()
        lengths = {c.opcode: c.size for c in COMMANDS.values()}
        lengths.update({opcode: row[0] for opcode, row in EXTERNAL_COMMAND_STRIDES.items()})
        for entry in self.external_entries:
            path = (root / entry["source"]).resolve()
            require(path.is_relative_to(root) and path.is_file(), "external script source is missing")
            paths.add(path)
            text = re.sub(r"/\*.*?\*/|//[^\n]*", " ", path.read_text(), flags=re.S)
            name = entry["symbol"]
            pattern = (r"(?m)^(u8|void\*)\s+" + re.escape(name)
                       + r"\s*\[([0-9]+)\]\s*(?:__attribute__\s*\(\(aligned\([0-9]+\)\)\)\s*)?"
                       + r"=\s*\{([^{}]*)\}\s*;")
            definitions = list(re.finditer(pattern, text))
            require(len(definitions) == 1, f"{name}: unsupported or ambiguous external C definition")
            definition = definitions[0]
            width = 1 if definition[1] == "u8" else 4
            count = int(definition[2])
            require(count * width == self.symbol(name).size, f"{name}: external C extent differs")
            tokens = [re.sub(r"\s+", "", token) for token in definition[3].split(",")]
            if tokens and not tokens[-1]:
                tokens.pop()
            require(len(tokens) <= count and all(tokens), f"{name}: invalid C initializer extent")
            wire = bytearray()
            for token in tokens:
                literal = re.fullmatch(r"(?:\(void\*\))?(0x[0-9A-Fa-f]+|[0-9]+)", token)
                pointer = re.fullmatch(r"\(void\*\)\(\(u8\*\)([A-Za-z_][A-Za-z_0-9]*)"
                                       r"(?:\+(0x[0-9A-Fa-f]+|[0-9]+))?\)", token)
                if literal:
                    require(width == 4 or not token.startswith("("), "pointer initializer in byte array")
                    value = int(literal[1], 0)
                elif pointer and width == 4:
                    value = self.symbol(pointer[1]).address + (int(pointer[2], 0) if pointer[2] else 0)
                else:
                    raise SourceError(f"{name}: unsupported external C initializer expression")
                integer(value, "external initializer", 0, (1 << (8 * width)) - 1)
                wire.extend(value.to_bytes(width, "big"))
            wire.extend(bytes((count - len(tokens)) * width))
            boundaries = set()
            cursor = 0
            while cursor < len(wire):
                boundaries.add(cursor)
                require(wire[cursor] in lengths, f"{name}: unknown external instruction")
                cursor += lengths[wire[cursor]]
                require(cursor <= len(wire), f"{name}: external instruction overruns its object")
            require(set(entry["labels"].values()) <= boundaries,
                    f"{name}: external entry points inside an operand")
        return sorted(paths)

    def symbol(self, name: str) -> Symbol:
        identifier(name, "symbol reference")
        require(name in self.symbols, f"unresolved symbol: {name}")
        return self.symbols[name]

    def scalar(self, kind: str, value: Any, what: str) -> int:
        if kind == "comparison":
            return enum(value, COMPARISONS, what, set(COMPARISONS.values()))
        if kind == "stat":
            return enum(value, STATS, what, set(STATS.values()))
        if kind == "family":
            return enum(value, STATUS_FAMILIES, what, set(STATUS_FAMILIES.values()))
        if kind == "battler":
            return enum(value, BATTLERS, what, set(range(30)))
        if kind == "zero32":
            return integer(value, what, 0, 0)
        return integer(value, what, 0, (1 << (FIELD_WIDTH[kind] * 8)) - 1)

    def address(self, value: Any, kind: str, nullable: bool, program: Program,
                position: int, field: str, required_width: int) -> tuple[str, bool, dict | None]:
        what = f"{program.symbol}+{position}/{field}"
        if value is None:
            require(nullable, f"{what}: required address cannot be null")
            return "0", False, None
        require(isinstance(value, dict), f"{what}: address must be symbolic")
        if "legacy_address" in value:
            fields(value, {"legacy_address"}, set(), what)
            # This single original command actually asks wsCmd46 to dereference
            # address ten. Preserve its wire behavior; do not reinterpret it as
            # an immediate animation id or generalize it into a raw-byte escape.
            require((program.symbol, self.symbol(program.symbol).address, position,
                     kind, field, value["legacy_address"]) ==
                    ("lbl_80378AF1", 0x80378AF1, 0, "mem8", "animation", "wsCmd46_pointer_ten"),
                    f"{what}: unsupported legacy address")
            return "10", False, None
        if kind in {"branch", "ignored_branch"}:
            fields(value, {"script", "entry", "encoding"}, set(), what)
            target = identifier(value["script"], "branch script")
            label = identifier(value["entry"], "branch label")
            require(target in self.entries and label in self.entries[target],
                    f"{what}: branch does not name an instruction entry")
            offset = self.entries[target][label]
        else:
            fields(value, {"symbol", "encoding"}, {"addend"}, what)
            target = identifier(value["symbol"], "memory symbol")
            offset = integer(value.get("addend", 0), "memory addend", 0, 0xFFFFFFFF)
        symbol = self.symbol(target)
        require(symbol.kind == "object" and symbol.section in
                {".data", ".rodata", ".sdata", ".sdata2", ".bss", ".sbss", ".sbss2"},
                f"{what}: address must refer to a data object")
        require(0 <= offset < symbol.size and offset + required_width <= symbol.size,
                f"{what}: operand access exceeds the named object")
        encoding = value["encoding"]
        require(encoding in {"absolute", "reloc"}, f"{what}: unknown address encoding")
        address = symbol.address + offset
        require(address <= 0xFFFFFFFF, f"{what}: wire address overflows")
        expression = target + (f"+{offset}" if offset else "") if encoding == "reloc" else str(address)
        edge = None
        if kind == "branch":
            edge = {"source": program.symbol, "offset": position, "field": field,
                    "target": target, "entry": value["entry"]}
        return expression, encoding == "reloc", edge

    def assembly(self, filename: str) -> tuple[str, dict]:
        require(filename in self.owners, "source is not in the battle catalog")
        owner = self.owners[filename]
        lines = ["# Generated from typed battle source; do not edit.",
                 '.section .data,"aw",@progbits', f".balign {owner.alignment}"]
        relocations = []
        edges = []
        command_count = 0
        section_offset = 0
        for program in owner.programs:
            lines.extend((f".global {program.symbol}", f".type {program.symbol},@object",
                          program.symbol + ":"))
            for position, node in zip(program.positions, program.body):
                command = COMMANDS[node["command"]]
                command_count += 1
                lines.extend((f"# {command.name}", f".byte {command.opcode}"))
                field_offset = 1
                if command.opcode >= 0xF8:
                    family = self.scalar("family", node["family"], "status family")
                    field_id = self.scalar("status_field", node["field"], "status field")
                    domains = STATUS_GET_FIELDS if command.opcode <= 0xFA else STATUS_SET_FIELDS
                    require(field_id in domains[family], "unknown field for status family/direction")
                for name, wire_kind in command.fields:
                    kind = wire_kind.rstrip("?")
                    width = FIELD_WIDTH[kind]
                    if kind.startswith("mem") or kind in {"branch", "ignored_branch"}:
                        access = int(kind[3:]) // 8 if kind.startswith("mem") else 1
                        if kind.startswith("mem") and command.name in {"copy_memory", "jump_if_memory_equal", "jump_if_memory_different"}:
                            access = integer(node["count"], "memory transfer count", 0, 255)
                        expression, relocated, edge = self.address(
                            node[name], kind, wire_kind.endswith("?"), program, position, name, access)
                        lines.append(f".long {expression}")
                        if relocated:
                            relocations.append({"offset": section_offset + position + field_offset,
                                                "expression": expression, "type": 1})
                        if edge is not None:
                            edges.append(edge)
                    else:
                        scalar = self.scalar(kind, node[name], f"{program.symbol}/{command.name}/{name}")
                        directive = {1: ".byte", 2: ".short", 4: ".long"}[width]
                        lines.append(f"{directive} {scalar}")
                    field_offset += width
            lines.append(f".size {program.symbol}, .-{program.symbol}")
            section_offset += program.size
        return "\n".join(lines) + "\n", {
            "unit": owner.unit, "size": owner.size, "alignment": owner.alignment,
            "symbols": [{"name": p.symbol, "size": p.size} for p in owner.programs],
            "commands": command_count, "relocations": relocations, "edges": edges,
        }


def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON field: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(), object_pairs_hook=no_duplicate_keys)


def load_source(source: Path, symbols_path: Path) -> tuple[Compiler, list[Path]]:
    source = source.resolve()
    catalog_path = source.parent / "catalog.json"
    catalog = read_json(catalog_path)
    require(isinstance(catalog, dict) and isinstance(catalog.get("sources"), list), "invalid catalog")
    require(all(isinstance(name, str) and SOURCE_FILENAME.fullmatch(name)
                for name in catalog["sources"]), "invalid source filename")
    documents = {}
    inputs = [catalog_path, symbols_path.resolve()]
    for name in catalog["sources"]:
        path = (source.parent / name).resolve()
        require(path.parent == source.parent, "catalog source leaves source directory")
        documents[name] = read_json(path)
        inputs.append(path)
    require(source in inputs, "requested source is not catalogued")
    compiler = Compiler(documents, catalog, parse_symbols(symbols_path.read_text()))
    inputs.extend(compiler.verify_external_entries(Path(__file__).resolve().parents[1]))
    return compiler, inputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--symbols", type=Path, required=True)
    parser.add_argument("--assembler", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assembly", type=Path)
    args = parser.parse_args()
    compiler, inputs = load_source(args.source, args.symbols)
    assembly, _ = compiler.assembly(args.source.name)
    output = args.output.resolve()
    assembly_path = (args.assembly or output.with_suffix(".s")).resolve()
    require(output.suffix == ".o" and assembly_path.suffix == ".s", "expected .o/.s output paths")
    require(output not in inputs and assembly_path not in inputs and output != assembly_path,
            "output would overwrite a source input")
    output.parent.mkdir(parents=True, exist_ok=True)
    assembly_path.parent.mkdir(parents=True, exist_ok=True)
    # Install only after the full source catalog validates and GNU as succeeds.
    with tempfile.TemporaryDirectory(prefix="battle-source-", dir=output.parent) as directory:
        temporary_asm = Path(directory) / "program.s"
        temporary_obj = Path(directory) / "program.o"
        temporary_asm.write_text(assembly)
        subprocess.run([str(args.assembler.resolve()), "-mgekko", "-o", str(temporary_obj),
                        str(temporary_asm)], check=True)
        temporary_obj.replace(output)
        assembly_path.write_text(assembly)


if __name__ == "__main__":
    main()
