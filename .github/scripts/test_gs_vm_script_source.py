#!/usr/bin/env python3
"""Synthetic semantic checks; no original game bytes or instruction fixtures."""

from copy import deepcopy
import json
from pathlib import Path
import re
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from gs_vm_script_source import SourceError, compile_program  # noqa: E402


def program(body, natives=None, diagnostics=None):
    return {
        "format": "gs-vm-program-v1", "bank_id": 7, "symbol": "test_script",
        "start_offset": 64,
        "globals": {"count": {"index": 0, "type": "int"},
                    "seconds": {"index": 1, "type": "float"}},
        "natives": natives or {},
        "functions": [{"index": 0, "name": "main", "return_type": "int",
                       "locals": {"remaining": {"index": 1, "type": "int"}}, "body": body}],
        "diagnostics": diagnostics or {},
    }


def execute(data, metadata, argument=0, natives=None):
    """Small independent operand-stack evaluator for the synthetic programs."""
    stack = [0, argument, 0, 0, 1]
    globals_ = [0, 0]
    frame = 0
    pc = metadata["function_offsets"][0] - metadata["start_offset"]
    calls = []
    natives = natives or {}

    def word():
        nonlocal pc
        result = int.from_bytes(data[pc:pc + 4], "big")
        pc += 4
        return result

    def signed(value):
        return value - (1 << 32) if value & (1 << 31) else value

    def number(value, desc):
        return signed(value) if desc & 0x3F == 2 else struct.unpack(">f", struct.pack(">I", value))[0]

    def operand(desc):
        value = stack.pop()
        if desc & 0x80:
            return value
        return stack[frame + value] if desc & 0x40 else globals_[value]

    for _ in range(10000):
        op = data[pc]
        pc += 1
        if op == 8:
            pc += 1
            stack.append(word())
        elif op == 16:
            desc = data[pc]
            count = int.from_bytes(data[pc + 1:pc + 3], "big")
            pc += 3
            start = stack.pop()
            values = stack if desc & 0x40 else globals_
            base = frame if desc & 0x40 else 0
            stack.extend(values[base + start:base + start + count])
        elif op in (20, 21, 24, 29, 33):
            rhs_desc, lhs_desc = data[pc:pc + 2]
            pc += 2
            rhs, lhs = number(operand(rhs_desc), rhs_desc), number(operand(lhs_desc), lhs_desc)
            if op == 20:
                value = lhs * rhs
            elif op == 21:
                value = lhs / rhs
            elif op == 24:
                value = lhs - rhs
            elif op == 29:
                value = int(lhs == rhs)
            else:
                value = int(bool(lhs) and bool(rhs))
            if op not in (29, 33) and (lhs_desc & 0x3F == 3 or rhs_desc & 0x3F == 3):
                stack.append(struct.unpack(">I", struct.pack(">f", value))[0])
            else:
                stack.append(int(value) & 0xFFFFFFFF)
        elif op == 17:
            desc = data[pc]
            pc += 1
            stack.append(int(not number(operand(desc), desc)))
        elif op == 31:
            src, dst = data[pc:pc + 2]
            pc += 2
            value = operand(src)
            index = stack.pop()
            if src & 0x3F != dst & 0x3F:
                if dst & 0x3F == 3:
                    value = struct.unpack(">I", struct.pack(">f", signed(value)))[0]
                else:
                    value = int(number(value, src)) & 0xFFFFFFFF
            (stack if dst & 0x40 else globals_)[frame + index if dst & 0x40 else index] = value
            stack.append(value)
        elif op == 3:
            count = int.from_bytes(data[pc + 1:pc + 3], "big")
            pc += 3
            if count:
                del stack[-count:]
        elif op in (6, 7):
            target = word() - metadata["start_offset"]
            if op == 6 or stack.pop() == 0:
                pc = target
        elif op == 37:
            count = int.from_bytes(data[pc + 2:pc + 4], "big")
            pc += 4
            values = stack[-count:]
            del stack[-count:]
            native_id = values[0]
            signature, result = natives[native_id]
            args = tuple(number(v, 3 if ty == "float" else 2) for v, ty in zip(values[1:], signature))
            calls.append((native_id, args))
            stack[-1] = result
        elif op == 5:
            argc = stack.pop()
            frame = stack.pop()
            return_ip = stack.pop()
            for _ in range(argc):
                stack.pop()
            if return_ip:
                raise AssertionError("Synthetic test unexpectedly called another script function")
            return signed(stack.pop()), globals_, calls
        else:
            raise AssertionError(f"Unexpected synthetic instruction {op}")
    raise AssertionError("Synthetic program did not terminate")


class ScriptSourceTests(unittest.TestCase):
    def test_loop_variables_float_native_and_return(self):
        p = program([
            ["while", ["logical_not", ["equal", ["local", "remaining"], ["int", 0]]], [
                ["eval", ["set", ["global", "count"], ["subtract", ["global", "count"], ["int", -1]]]],
                ["eval", ["set", ["local", "remaining"], ["subtract", ["local", "remaining"], ["int", 1]]]],
            ]],
            ["eval", ["set", ["global", "seconds"], ["divide", ["global", "count"], ["float", 2.0]]]],
            ["if", ["equal", ["global", "count"], ["int", 3]],
                [["eval", ["call", "record", ["global", "count"], ["global", "seconds"]]]],
                [["eval", ["call", "record", ["int", -9], ["float", 0.0]]]]],
            ["return", ["global", "count"]],
        ], {"record": {"index": 9, "parameters": ["int", "float"]}})
        data, metadata = compile_program(p)
        result, globals_, calls = execute(data, metadata, 3, {9: (["int", "float"], 19)})
        self.assertEqual(result, 3)
        self.assertEqual(globals_[0], 3)
        self.assertEqual(calls, [(9, (3, 1.5))])
        self.assertEqual(execute(data, metadata, 0, {9: (["int", "float"], 19)})[2], [(9, (-9, 0.0))])

    def test_logical_and_is_eager_and_preserves_nested_call_frames(self):
        p = program([["if", ["logical_and", ["call", "first"], ["call", "second"]],
                      [["return", ["int", 7]]]], ["return", ["int", 4]]],
                    {"first": {"index": 1, "parameters": []}, "second": {"index": 2, "parameters": []}})
        data, metadata = compile_program(p)
        result, _, calls = execute(data, metadata, natives={1: ([], 0), 2: ([], 1)})
        self.assertEqual(result, 4)
        self.assertEqual(calls, [(1, ()), (2, ())])

    def test_diagnostic_pointer_is_a_bank_relative_runtime_fixup(self):
        p = program([["log", "missing_case"], ["return", ["int", 0]]],
                    diagnostics={"missing_case": "synthetic case missing\\n"})
        data, metadata = compile_program(p)
        relocation, = metadata["runtime_relocations"]
        source_offset = relocation["site"] - metadata["start_offset"]
        target_offset = relocation["target"] - metadata["start_offset"]
        self.assertEqual(int.from_bytes(data[source_offset:source_offset + 4], "big"), relocation["target"])
        expected = b"synthetic case missing\\n\0"
        self.assertEqual(data[target_offset:target_offset + len(expected)], expected)
        self.assertEqual(len(data) % 4, 0)
        self.assertEqual(data[-1], 0)

    def test_rejects_binary_escapes_unknown_symbols_and_wrong_native_types(self):
        invalid = [
            ["bytes", "00ff"], ["opcode", 8], ["goto", 17],
            ["eval", ["int", 1 << 32]], ["eval", ["float", float("nan")]],
            ["eval", ["global", "unknown"]], ["eval", ["call", "unknown"]],
            ["eval", ["call", "takes_float", ["int", 1]]],
        ]
        for statement in invalid:
            with self.subTest(statement=statement[0]):
                p = program([statement], {"takes_float": {"index": 1, "parameters": ["float"]}})
                with self.assertRaises(SourceError):
                    compile_program(p)
        for diagnostic in ("embedded\0suffix", "unprovided %d argument"):
            with self.subTest(diagnostic=diagnostic):
                with self.assertRaises(SourceError):
                    compile_program(program([["log", "bad"]], diagnostics={"bad": diagnostic}))
        p = program([["return", ["int", 0]]])
        p["original_bytes"] = "00"
        with self.assertRaises(SourceError):
            compile_program(p)

    def test_duplicate_indices_and_implicit_native_arguments_are_rejected(self):
        p = program([["return", ["int", 0]]])
        p["functions"].append(deepcopy(p["functions"][0]))
        with self.assertRaises(SourceError):
            compile_program(p)
        p = program([["eval", ["call", "one", ["int", 1], ["int", 2]]]],
                    {"one": {"index": 1, "parameters": ["int"]}})
        with self.assertRaises(SourceError):
            compile_program(p)
        p["natives"]["one"]["ignored_extra_arguments"] = True
        compile_program(p)

    def test_authored_native_bindings_match_existing_runtime_registry(self):
        p = json.loads((ROOT / "src/rel/common_rel/common_script_0596.json").read_text())
        source = (ROOT / "src/game/data/data_8027A500.c").read_text()
        body = source.split("void* lbl_802E1CF0[742] = {", 1)[1].split("};", 1)[0]
        words = [word.strip() for word in body.split(",") if word.strip()]
        for name, declaration in p["natives"].items():
            with self.subTest(native=name):
                start = declaration["index"] * 3
                symbol, types_a, types_b = words[start:start + 3]
                self.assertEqual(symbol, f"(void*)((u8*){name})")
                values = [int(word.removeprefix("(void*)"), 0) for word in (types_a, types_b)]
                signature = struct.pack(">II", *values).split(b"\0", 1)[0]
                self.assertEqual(declaration["parameters"], ["float" if value == 2 else "int" for value in signature])

    def test_authored_layout_agrees_with_existing_typed_header(self):
        p = json.loads((ROOT / "src/rel/common_rel/common_script_0596.json").read_text())
        data, metadata = compile_program(p)
        header = (ROOT / "src/rel/common_rel/script_structure_89CFC.c").read_text()
        definition = header.split("__attribute__((aligned(4))) = {", 1)[1]
        groups = re.findall(r"\{([^{}]*)\}", definition)
        offsets = [int(value) for value in re.findall(r"\d+", groups[0])]
        sites = [int(value) for value in re.findall(r"\d+", groups[1])]
        self.assertEqual(metadata["function_offsets"], offsets)
        self.assertEqual([r["site"] for r in metadata["runtime_relocations"]], sites)
        self.assertEqual(len(data), 0x8BCB4 - 0x89D98)


if __name__ == "__main__":
    unittest.main()
