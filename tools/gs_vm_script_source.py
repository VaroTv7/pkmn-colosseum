#!/usr/bin/env python3
"""Compile authored GS VM statements and typed expressions to a C data object.

The input is program source, not an instruction listing. It contains named native
calls, local/global variables, if/while statements, returns and diagnostic strings.
There is deliberately no byte, opcode, address, or arbitrary binary escape.

Encoding and calling conventions follow the matching interpreter in gs_vm.c,
gs_vm_exact_800F10E8.c, gs_vm_exact_800F13D0.c, and gs_vm_exact_800F16C0.c.
Neither compilation nor the generated C needs an original game file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from typing import Any


FORMAT = "gs-vm-program-v1"
TYPES = {"int": 2, "float": 3}
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")

# Decimal indices of the existing cms_op* handler table. Descriptor bit 0x80
# means a computed value, 0x40 a frame variable; the low bits carry the type.
OP = {
    "exit": 1, "pop": 3, "return": 5, "jump": 6, "jump_false": 7,
    "immediate": 8, "load": 16, "logical_not": 17, "multiply": 20,
    "divide": 21, "subtract": 24, "equal": 29, "set": 31, "logical_and": 33,
    "log": 35, "wait": 36, "native": 37,
}
# Only operators used by the reconstructed program are accepted. Further VM
# handlers can be added after their descriptor/result-type rules are reviewed.
BINARY = {"multiply", "divide", "subtract", "equal", "logical_and"}
INTEGER_RESULT = {"equal", "logical_and"}


class SourceError(ValueError):
    """An invalid or unsupported source program, before any output is written."""


def integer(value: Any, what: str, low: int, high: int) -> int:
    if isinstance(value, str):
        try:
            value = int(value, 0)
        except ValueError as exc:
            raise SourceError(f"{what}: expected an integer") from exc
    if type(value) is not int or not low <= value <= high:
        raise SourceError(f"{what}: integer outside {low}..{high}")
    return value


def identifier(value: Any, what: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise SourceError(f"{what}: expected a source identifier")
    return value


def fields(value: Any, required: set[str], optional: set[str], what: str) -> dict:
    if not isinstance(value, dict) or not required <= value.keys():
        raise SourceError(f"{what}: missing required fields {sorted(required)}")
    extra = value.keys() - required - optional
    if extra:
        raise SourceError(f"{what}: unsupported fields {sorted(extra)}")
    return value


class Compiler:
    def __init__(self, program: dict):
        fields(program, {"format", "bank_id", "symbol", "start_offset", "globals",
                         "natives", "functions", "diagnostics"}, {"description"}, "program")
        if program["format"] != FORMAT:
            raise SourceError("Unsupported GS VM source format")
        self.program = program
        self.bank_id = integer(program["bank_id"], "bank_id", 0, 0xFFFF)
        self.symbol = identifier(program["symbol"], "output symbol")
        self.start = integer(program["start_offset"], "start_offset", 0, 0xFFFFFFFF)
        if self.start % 4:
            raise SourceError("The generated source owner must start on a word boundary")
        self.globals = self.variables(program["globals"], "globals")
        if not isinstance(program["natives"], dict):
            raise SourceError("natives must be a named declaration map")
        self.natives = {}
        native_ids = set()
        for name, native in program["natives"].items():
            identifier(name, "native name")
            fields(native, {"index", "parameters"}, {"ignored_extra_arguments", "description"}, name)
            index = integer(native["index"], "native index", 0, 0xFFFFFFFF)
            if index in native_ids:
                raise SourceError("Duplicate native index")
            native_ids.add(index)
            params = native["parameters"]
            if not isinstance(params, list) or len(params) > 8 or any(p not in TYPES for p in params):
                raise SourceError(f"{name}: invalid native parameter types")
            if "ignored_extra_arguments" in native and type(native["ignored_extra_arguments"]) is not bool:
                raise SourceError(f"{name}: ignored_extra_arguments must be boolean")
            self.natives[name] = {**native, "index": index}
        if not isinstance(program["functions"], list) or not 1 <= len(program["functions"]) <= 0xFFFF:
            raise SourceError("functions must be a nonempty list")
        self.function_ids = {}
        indices = set()
        for function in program["functions"]:
            fields(function, {"index", "name", "return_type", "locals", "body"},
                   {"description"}, "function")
            name = identifier(function["name"], "function name")
            index = integer(function["index"], "function index", 0, 0xFFFF)
            if name in self.function_ids or index in indices:
                raise SourceError("Duplicate function name or index")
            self.function_ids[name] = index
            indices.add(index)
            if function["return_type"] not in ("int", "void"):
                raise SourceError("Only the observed integer/void script return conventions are supported")
        if indices != set(range(len(indices))):
            raise SourceError("Function indices must completely cover the bank index")
        if not isinstance(program["diagnostics"], dict):
            raise SourceError("diagnostics must be a named string map")
        self.diagnostics = {}
        for name, text in program["diagnostics"].items():
            identifier(name, "diagnostic name")
            if not isinstance(text, str) or "\0" in text:
                raise SourceError("A diagnostic must be text without embedded NULs")
            if "%" in text:
                raise SourceError("Zero-argument diagnostics cannot contain format conversions")
            try:
                encoded = text.encode("ascii")
            except UnicodeError as exc:
                raise SourceError("This source format supports ASCII code diagnostics only") from exc
            self.diagnostics[name] = encoded + b"\0"
        self.data = bytearray()
        self.fixups: list[tuple[int, str]] = []
        self.function_offsets = {}
        self.runtime_relocations = []
        self.locals = {}
        self.return_type = "void"
        self.depth = 0

    @staticmethod
    def variables(values: Any, what: str) -> dict:
        if not isinstance(values, dict):
            raise SourceError(f"{what}: expected a named variable map")
        result = {}
        indices = set()
        for name, variable in values.items():
            identifier(name, f"{what} variable")
            fields(variable, {"index", "type"}, {"description"}, name)
            index = integer(variable["index"], "variable index", 0, 63)
            if variable["type"] not in TYPES or index in indices:
                raise SourceError(f"{what}: invalid variable type or duplicate index")
            indices.add(index)
            result[name] = (index, TYPES[variable["type"]])
        return result

    def emit(self, *values: int) -> None:
        self.data.extend(values)

    def word(self, value: int) -> None:
        self.data.extend(struct.pack(">I", value & 0xFFFFFFFF))

    def immediate(self, value: int, ty: int = 2) -> int:
        self.emit(OP["immediate"], ty)
        self.word(value)
        return ty

    def variable(self, expr: list) -> tuple[int, int]:
        if len(expr) != 2 or expr[0] not in ("local", "global"):
            raise SourceError("Expected a named local/global variable")
        values = self.locals if expr[0] == "local" else self.globals
        if expr[1] not in values:
            raise SourceError(f"Undeclared {expr[0]} variable {expr[1]!r}")
        index, ty = values[expr[1]]
        return index, ty | (0x40 if expr[0] == "local" else 0)

    def operand(self, expr: list) -> int:
        if isinstance(expr, list) and expr and expr[0] in ("local", "global"):
            index, desc = self.variable(expr)
            self.immediate(index)
            return desc
        return 0x80 | self.expression(expr)

    def expression(self, expr: Any) -> int:
        if not isinstance(expr, list) or not expr or not isinstance(expr[0], str):
            raise SourceError("Expected a typed expression")
        self.depth += 1
        if self.depth > 64:
            raise SourceError("Expression nesting exceeds the source compiler limit")
        try:
            return self._expression(expr)
        finally:
            self.depth -= 1

    def _expression(self, expr: list) -> int:
        kind = expr[0]
        if kind == "int" and len(expr) == 2:
            return self.immediate(integer(expr[1], "integer literal", -(1 << 31), 0xFFFFFFFF))
        if kind == "float" and len(expr) == 2:
            if type(expr[1]) not in (int, float) or not math.isfinite(expr[1]):
                raise SourceError("Expected a finite float literal")
            try:
                bits = struct.unpack(">I", struct.pack(">f", expr[1]))[0]
            except (OverflowError, struct.error) as exc:
                raise SourceError("Float literal is outside binary32 range") from exc
            return self.immediate(bits, 3)
        if kind == "script" and len(expr) == 2:
            if expr[1] not in self.function_ids:
                raise SourceError("Undeclared bank function")
            return self.immediate((self.bank_id << 16) | self.function_ids[expr[1]])
        if kind == "script_id" and len(expr) == 3:
            bank = integer(expr[1], "external script bank", 0, 0xFFFF)
            function = integer(expr[2], "external script function", 0, 0xFFFF)
            return self.immediate((bank << 16) | function)
        if kind in ("local", "global"):
            index, desc = self.variable(expr)
            self.immediate(index)
            self.emit(OP["load"], desc, 0, 1)
            return desc & 0x3F
        if kind == "call" and len(expr) >= 2:
            if expr[1] not in self.natives:
                raise SourceError(f"Undeclared native {expr[1]!r}")
            native = self.natives[expr[1]]
            args = expr[2:]
            count = len(native["parameters"])
            if len(args) != count and not (native.get("ignored_extra_arguments") and count < len(args) <= 8):
                raise SourceError(f"{expr[1]}: argument count disagrees with the native registry")
            # Calls reuse a copy of frame slot zero as their overwritten result
            # slot. The value loaded here is not an extra native argument.
            self.immediate(0)
            self.emit(OP["load"], 0x42, 0, 1)
            self.immediate(native["index"])
            for i, arg in enumerate(args):
                ty = self.expression(arg)
                if i < count and ty != TYPES[native["parameters"][i]]:
                    raise SourceError(f"{expr[1]}: argument {i + 1} has the wrong register type")
            self.emit(OP["native"], 0, 1, 0, len(args) + 1)
            return 2
        if kind == "set" and len(expr) == 3:
            index, dst = self.variable(expr[1])
            self.immediate(index)
            src = self.operand(expr[2])
            self.emit(OP["set"], src, dst)
            return dst & 0x3F
        if kind in BINARY and len(expr) == 3:
            lhs = self.operand(expr[1])
            rhs = self.operand(expr[2])
            self.emit(OP[kind], rhs, lhs)
            if kind in INTEGER_RESULT:
                return 2
            return 3 if (lhs & 0x3F) == 3 or (rhs & 0x3F) == 3 else 2
        if kind == "logical_not" and len(expr) == 2:
            operand = self.operand(expr[1])
            self.emit(OP[kind], operand)
            return 2
        raise SourceError(f"Unsupported expression {kind!r} or wrong arity")

    def discard(self, ty: int | None) -> None:
        self.emit(OP["pop"], 0x80 | (ty if ty is not None else 1), 0, int(ty is not None))

    def branch(self, conditional: bool) -> int:
        self.emit(OP["jump_false" if conditional else "jump"])
        pos = len(self.data)
        self.word(0)
        return pos

    def patch_branch(self, pos: int, target: int) -> None:
        struct.pack_into(">I", self.data, pos, self.start + target)

    def statements(self, body: Any, depth: int = 0) -> None:
        if not isinstance(body, list) or depth > 64:
            raise SourceError("Invalid statement block or excessive nesting")
        for statement in body:
            if not isinstance(statement, list) or not statement or not isinstance(statement[0], str):
                raise SourceError("Expected a semantic statement")
            kind = statement[0]
            if kind == "eval" and len(statement) == 2:
                self.discard(self.expression(statement[1]))
            elif kind == "return" and len(statement) == 2 and self.return_type == "int":
                self.immediate(0)
                src = self.operand(statement[1])
                self.emit(OP["set"], src, 0x42)
                self.discard(2)
                self.emit(OP["return"])
            elif kind == "if" and len(statement) in (3, 4):
                self.expression(statement[1])
                false = self.branch(True)
                self.statements(statement[2], depth + 1)
                if len(statement) == 4:
                    end = self.branch(False)
                    self.patch_branch(false, len(self.data))
                    self.statements(statement[3], depth + 1)
                    self.patch_branch(end, len(self.data))
                else:
                    self.patch_branch(false, len(self.data))
            elif kind == "while" and len(statement) == 3:
                start = len(self.data)
                self.expression(statement[1])
                end = self.branch(True)
                self.statements(statement[2], depth + 1)
                again = self.branch(False)
                self.patch_branch(again, start)
                self.patch_branch(end, len(self.data))
            elif kind == "wait_frames" and len(statement) == 2:
                if self.expression(statement[1]) != 2:
                    raise SourceError("wait_frames takes an integer frame count")
                self.emit(OP["wait"], 0, 0, 0, 1)
                self.discard(None)
            elif kind == "log" and len(statement) == 2:
                if statement[1] not in self.diagnostics:
                    raise SourceError("Undeclared code diagnostic")
                self.emit(OP["immediate"], 2)
                self.fixups.append((len(self.data), statement[1]))
                self.word(0)
                self.emit(OP["log"], 0, 0, 0, 1)
                self.discard(None)
            else:
                raise SourceError(f"Unsupported statement {kind!r} or wrong arity")

    def compile(self) -> tuple[bytes, dict]:
        for function in self.program["functions"]:
            self.locals = self.variables(function["locals"], function["name"])
            self.return_type = function["return_type"]
            self.function_offsets[self.function_ids[function["name"]]] = self.start + len(self.data)
            self.statements(function["body"])
            # The script compiler preserves its end-of-function return even
            # after an explicit return. No dead-code optimization is performed.
            self.emit(OP["return"])
        self.emit(OP["exit"])
        while (self.start + len(self.data)) % 4:
            self.emit(0)
        # The aligned empty string precedes named diagnostics in the pool.
        self.word(0)
        diagnostic_offsets = {}
        for name, value in self.diagnostics.items():
            diagnostic_offsets[name] = self.start + len(self.data)
            self.data.extend(value)
            while (self.start + len(self.data)) % 4:
                self.emit(0)
        if {name for _, name in self.fixups} != self.diagnostics.keys():
            raise SourceError("Every diagnostic declaration must have a logging use")
        for pos, name in self.fixups:
            target = diagnostic_offsets[name]
            struct.pack_into(">I", self.data, pos, target)
            self.runtime_relocations.append({"site": self.start + pos, "target": target})
        data = bytes(self.data)
        metadata = {
            "format": FORMAT, "symbol": self.symbol, "bank_id": self.bank_id,
            "start_offset": self.start, "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "function_offsets": [self.function_offsets[i] for i in range(len(self.function_ids))],
            "runtime_relocations": self.runtime_relocations,
            "diagnostics": {name: {"offset": diagnostic_offsets[name], "size_with_nul": len(value)}
                            for name, value in self.diagnostics.items()},
        }
        return data, metadata


def compile_program(program: dict) -> tuple[bytes, dict]:
    return Compiler(program).compile()


def c_source(data: bytes, symbol: str, source_name: str) -> str:
    # Keep arbitrary file names out of a C comment.
    safe_name = source_name.replace("*/", "* /").replace("\n", " ").replace("\r", " ")
    lines = [f"/* Generated from {safe_name}; edit the semantic source, not this file. */",
             '#include "dolphin/types.h"', "",
             f"u8 {symbol}[{len(data)}] __attribute__((aligned(4))) = {{"]
    for start in range(0, len(data), 16):
        lines.append("    " + ", ".join(f"0x{value:02X}" for value in data[start:start + 16]) + ",")
    lines.extend(["};", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()
    try:
        source = args.source.read_text(encoding="utf-8")
        data, metadata = compile_program(json.loads(source))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(c_source(data, metadata["symbol"], args.source.name), encoding="utf-8")
    if args.metadata:
        metadata["source_sha256"] = hashlib.sha256(source.encode("utf-8")).hexdigest()
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
