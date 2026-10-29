#!/usr/bin/env python3
"""Compile authored message controls and counter templates into data objects.

GSmsgReadCode reads big-endian 16-bit glyphs and a zero terminator. The FFFF
escape introduces a one-byte control ID; msgctrlcode selects its callback.
These source templates describe formatting operations and generated labels.
This compiler has no original-resource input or opaque-byte escape.
"""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import string
import subprocess


# IDs and parameter widths follow msgctrlcode and the respective callbacks.
CONTROLS = {
    "line_break": (0, "msgctrlCR", 0),
    "font": (7, "msgctrlFont", 1),
    "event_string_0": (13, "msgctrlEvStrBuf0", 0),
    "event_string_1": (14, "msgctrlEvStrBuf1", 0),
    "hero_name": (43, "msgctrlHero", 0),
    "digit": (47, "msgctrlDigit", 0),
    "menu_digit": (52, "msgctrlMenuDigit", 0),
    "menu_message": (55, "msgctrlMenuMsg", 0),
    "menu_unsigned": (69, "msgctrlMenuUDigit", 0),
    "menu_hex": (71, "msgctrlMenuHex", 0),
    "menu_zero_digit": (73, "msgctrlMenuZDigit", 0),
    "string": (77, "msgctrlString", 0),
    "menu_money": (80, "msgctrlMenuMoney", 0),
    "menu_message_2": (81, "msgctrlMenuMsg2", 0),
    "align": (83, "msgctrlAlign", 1),
    "baseline_bias": (92, "msgctrlBaseLineBias", -1),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encode_parts(parts):
    require(isinstance(parts, list), "Message parts must be a list")
    out = bytearray()
    for part in parts:
        if isinstance(part, str):
            require(all(0 < ord(ch) < 0xFFFF and not 0xD800 <= ord(ch) <= 0xDFFF
                        for ch in part),
                    "Text must contain ordinary 16-bit glyphs, not terminators or escapes")
            out.extend(part.encode("utf-16-be"))
            continue
        require(isinstance(part, dict) and "control" in part
                and set(part) <= {"control", "value"}, "Unknown message operation")
        require(part["control"] in CONTROLS, "Unknown message control")
        code, _, width = CONTROLS[part["control"]]
        out.extend((0xFF, 0xFF, code))
        if width:
            lower, upper = (-128, 127) if width < 0 else (0, 255)
            require(type(part.get("value")) is int and lower <= part["value"] <= upper,
                    "Control byte parameter is missing or outside its declared type")
            out.append(part["value"] & 255)
        else:
            require("value" not in part, "This control has no parameter")
    return bytes(out) + b"\0\0"


def axis_values(axis):
    require(isinstance(axis, dict) and set(axis) == {"name", "values"}
            and isinstance(axis["name"], str)
            and re.fullmatch(r"[a-z][a-z_]*", axis["name"]), "Invalid counter axis")
    values = axis["values"]
    if isinstance(values, dict):
        require(set(values) == {"start", "stop"}
                and all(type(values[k]) is int for k in values)
                and 0 <= values["start"] < values["stop"] <= 10001,
                "Invalid counter range")
        values = list(range(values["start"], values["stop"]))
    require(isinstance(values, list) and 0 < len(values) <= 10000
            and all(type(v) is int and 0 <= v <= 10000 for v in values)
            and len(set(values)) == len(values), "Invalid or duplicate counter values")
    return axis["name"], values


def expand_messages(specs):
    require(isinstance(specs, list) and specs, "Expected authored message templates")
    result = []
    for spec in specs:
        require(isinstance(spec, dict), "Message definition must be an object")
        if "key" in spec:
            require(set(spec) == {"key", "parts"}, "Unknown message fields")
            result.append((spec["key"], encode_parts(spec["parts"])))
        else:
            require({"first_key", "template", "axes"} <= set(spec)
                    and set(spec) <= {"first_key", "template", "axes", "prefix", "fullwidth"},
                    "Unknown counter-template fields")
            require(type(spec["first_key"]) is int
                    and isinstance(spec["template"], str)
                    and isinstance(spec["axes"], list) and 1 <= len(spec["axes"]) <= 3
                    and type(spec.get("fullwidth", False)) is bool, "Invalid counter template")
            axes = [axis_values(axis) for axis in spec["axes"]]
            require(len({name for name, _ in axes}) == len(axes), "Duplicate counter axes")
            fields = []
            for _, field, fmt, conversion in string.Formatter().parse(spec["template"]):
                require(not fmt and not conversion, "Formatting modifiers are not supported")
                if field is not None:
                    fields.append(field)
            require(set(fields) == {name for name, _ in axes},
                    "Template fields must name exactly the declared counter axes")
            prefix = spec.get("prefix", [])
            require(isinstance(prefix, list) and all(isinstance(p, dict) for p in prefix),
                    "Counter prefixes must contain formatting controls")
            for index, row in enumerate(itertools.product(*(values for _, values in axes))):
                require(index < 10000, "Counter expansion is too large")
                values = {name: str(value) for (name, _), value in zip(axes, row)}
                if spec.get("fullwidth", False):
                    values = {name: value.translate(str.maketrans("0123456789", "０１２３４５６７８９"))
                              for name, value in values.items()}
                text = spec["template"].format(**values)
                result.append((spec["first_key"] + index, encode_parts([*prefix, text])))
    require(all(type(key) is int and 0 < key <= 0xFFFFF for key, _ in result)
            and len({key for key, _ in result}) == len(result),
            "Message keys must be unique nonzero 20-bit identifiers")
    return result


def compile_unit(document, unit_name):
    require(isinstance(document, dict) and set(document) == {"schema", "units"}
            and document["schema"] == "gs-message-templates-v1"
            and isinstance(document["units"], dict), "Unknown message source schema")
    require(unit_name in document["units"], "Unknown message source unit")
    unit = document["units"][unit_name]
    require(isinstance(unit, dict) and set(unit) == {"symbol", "start", "size", "messages"}
            and isinstance(unit["symbol"], str)
            and re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", unit["symbol"])
            and type(unit["start"]) is int and unit["start"] >= 0
            and type(unit["size"]) is int and unit["size"] > 0,
            "Invalid message source unit")
    messages = expand_messages(unit["messages"])
    payload = b"".join(data for _, data in messages)
    require(len(payload) == unit["size"], "Authored messages do not fill the declared source interval")
    offsets = []
    cursor = unit["start"]
    for key, data in messages:
        offsets.append({"key": key, "start": cursor, "size": len(data)})
        cursor += len(data)
    return unit["symbol"], payload, offsets


def assembly_source(symbol, payload):
    # Packed GSchar streams need byte alignment, including after control bytes.
    lines = ['.section .data,"aw",@progbits', '.balign 1',
             f'.global {symbol}', f'.type {symbol},@object', f'{symbol}:']
    for offset in range(0, len(payload), 16):
        lines.append('.byte ' + ', '.join(str(v) for v in payload[offset:offset + 16]))
    lines.append(f'.size {symbol},.-{symbol}')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--unit', required=True)
    parser.add_argument('--assembler', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(args.source.resolve() != args.output.resolve(), "Source and output must differ")
    document = json.loads(args.source.read_text(encoding='utf-8'))
    symbol, payload, messages = compile_unit(document, args.unit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    assembly = args.output.with_suffix('.s')
    require(assembly.resolve() != args.source.resolve(), "Assembly output would replace source")
    assembly.write_text(assembly_source(symbol, payload), encoding='ascii')
    subprocess.run([str(args.assembler), '-mgekko', '-o', str(args.output), str(assembly)], check=True)
    from source_object_metadata import Elf
    obj = Elf(args.output.read_bytes())
    require(set(obj.allocated) == {'.data'}, "Message object must contain only initialized data")
    section = obj.allocated['.data']
    require(obj.payload(section) == payload and obj.sections[section][8] == 1,
            "Assembler changed the packed source layout")
    _, native = obj.unique_symbol(symbol)
    require(native[1:4] == (0, len(payload), 0x11)
            and native[5] == section and not obj.data_relocations(),
            "Message array symbol or relocations differ from source")
    print(json.dumps({'unit': args.unit, 'bytes': len(payload), 'messages': len(messages),
                      'sha256': hashlib.sha256(payload).hexdigest()}))


if __name__ == '__main__':
    main()
