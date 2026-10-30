#!/usr/bin/env python3
"""Compile readable indexed message source into packed data-only objects.

Inputs are authored text/typed controls, the existing typed C indices, and the
public symbol map. There is no original-resource input or raw-byte escape.
Every unit and lookup offset is validated before any selected object is built.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unicodedata

if __package__:
    from .message_template_source import assembly_source, encode_parts, require
    from .source_object_metadata import Elf
else:
    from message_template_source import assembly_source, encode_parts, require
    from source_object_metadata import Elf


IDENTIFIER = r"[A-Za-z_][A-Za-z_0-9]*"
INTEGER = r"(?:0x[0-9A-Fa-f]+|[0-9]+)"


def unique_fields(pairs):
    output = {}
    for key, value in pairs:
        require(key not in output, "Duplicate message-source JSON field")
        output[key] = value
    return output


def encode_catalog_parts(parts):
    require(isinstance(parts, list), "Message parts must be a list")
    for part in parts:
        if isinstance(part, str):
            require(all(not unicodedata.category(character).startswith("C") for character in part),
                    "Catalogue text must use readable glyphs; formatting requires typed controls")
    return encode_parts(parts)


def parse_symbol_map(text):
    output = {}
    pattern = re.compile(r"^(" + IDENTIFIER + r") = (\.[^:]+):0x([0-9A-Fa-f]+);\s*//\s*(.*)$")
    for line in text.splitlines():
        match = pattern.fullmatch(line)
        if not match:
            continue
        name, section, address, metadata = match.groups()
        require(name not in output, "Duplicate public message symbol")
        fields = dict(re.findall(r"(\w+):([^\s]+)", metadata))
        output[name] = {"section": section, "start": int(address, 16),
                        "size": int(fields.get("size", "0"), 0),
                        "type": fields.get("type"), "scope": fields.get("scope", "global")}
    return output


def parse_message_index(text, symbols):
    """Read only the existing explicit RelMessageHeader/RelMessageIndex form."""
    clean = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    declaration = re.search(
        r"typedef\s+struct\s+(MessageResourceIndex_[0-9A-Fa-f]+)\s*\{\s*"
        r"RelMessageHeader\s+header\s*;\s*RelMessageIndex\s+entries\[([0-9]+)\]\s*;\s*"
        r"\}\s*\1\s*;", clean)
    require(declaration is not None, "Unsupported typed message-index declaration")
    typename, count = declaration[1], int(declaration[2])
    pattern = re.compile(
        r"\b" + re.escape(typename) + r"\s+(" + IDENTIFIER + r")\s+"
        r"__attribute__\s*\(\(aligned\(4\)\)\)\s*=\s*\{\s*"
        r"\{([^{}]*)\}\s*,\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*,?\s*\}\s*;", re.S)
    matches = list(pattern.finditer(clean))
    require(len(matches) == 1, "Expected one explicit typed message-index initializer")
    match = matches[0]
    name = match[1]
    require(name in symbols, "Message index is absent from the public map")
    mapped = symbols[name]
    require(mapped["section"] == ".data" and mapped["type"] == "object"
            and mapped["scope"] == "global" and mapped["size"] == 16 + 8 * count,
            "Typed message-index extent differs from its public symbol")
    header = [field.strip() for field in match[2].split(",")]
    require(len(header) == 7 and header[-2:] == ["NULL", "NULL"]
            and all(re.fullmatch(INTEGER, field) for field in header[:5]),
            "Unsupported message resource header initializer")
    header = [int(field, 0) for field in header[:5]]
    require(header[0] == 0 and 0 <= header[1] <= 255 and 0 <= header[2] <= 255
            and header[3] == count and 0 < count <= 65535 and 0 <= header[4] <= 65535,
            "Typed message resource header fields are invalid")
    pair = re.compile(r"\{\s*(" + INTEGER + r")\s*,\s*(" + INTEGER + r")\s*\}")
    pairs = list(pair.finditer(match[3]))
    require(not pair.sub("", match[3]).strip(" \t\r\n,"),
            "Unsupported expression in typed message index")
    entries = [(int(p[1], 0), int(p[2], 0)) for p in pairs]
    require(len(entries) == count and all(0 < key <= 0xFFFFF and
            mapped["size"] <= offset <= 0xFFFFFFFF - mapped["start"]
            for key, offset in entries), "Invalid typed message-index entry")
    require(all(a[0] < b[0] for a, b in zip(entries, entries[1:]))
            and len({offset for _, offset in entries}) == count,
            "Message index requires ascending unique keys and unique offsets")
    return {"symbol": name, "base": mapped["start"],
            "entries": [(key, mapped["start"] + offset) for key, offset in entries],
            "last_start": mapped["start"] + max(offset for _, offset in entries)}


def compile_document(document, symbols, indexes):
    require(isinstance(document, dict) and set(document) == {"schema", "units"}
            and document["schema"] == "gs-message-catalog-v1"
            and isinstance(document["units"], dict) and document["units"],
            "Unknown message catalogue schema")
    require(isinstance(indexes, list) and indexes, "Message catalogue needs typed source indices")
    lookups, banks = {}, {}
    for bank in indexes:
        require(bank["symbol"] not in banks, "Duplicate message-index source")
        banks[bank["symbol"]] = bank
        for key, address in bank["entries"]:
            require(key not in lookups, "Duplicate key across message-index sources")
            lookups[key] = (address, bank["symbol"])
    compiled, intervals, seen_keys, seen_symbols = {}, [], set(), set()
    for unit_name, unit in document["units"].items():
        match = re.fullmatch(r"message_storage_([0-9A-Fa-f]{5,8})", unit_name)
        require(match is not None and isinstance(unit, dict)
                and {"symbol", "start", "size", "messages"} <= set(unit)
                and set(unit) <= {"symbol", "start", "size", "messages", "alignment_padding"},
                "Invalid message source unit fields")
        name, start, size = unit["symbol"], unit["start"], unit["size"]
        require(isinstance(name, str) and re.fullmatch(IDENTIFIER, name)
                and name not in seen_symbols and type(start) is int
                and start == int(match[1], 16) and type(size) is int and size > 0
                and start + size <= 0x100000000, "Invalid message source unit identity or bounds")
        require(name in symbols and symbols[name] ==
                {"section": ".data", "start": start, "size": size, "type": "object", "scope": "global"},
                "Message source owner differs from its public symbol")
        seen_symbols.add(name)
        end = start + size
        require(not any(a < end and start < b for a, b in intervals), "Message source owners overlap")
        intervals.append((start, end))
        messages = unit["messages"]
        require(isinstance(messages, list) and messages, "Message source unit has no indexed entries")
        payload, entries, retained_rows = bytearray(), [], []
        bank_name = None
        for message in messages:
            require(isinstance(message, dict) and {"key", "parts"} <= set(message)
                    and set(message) <= {"key", "parts", "retained"}, "Unknown indexed message fields")
            key = message["key"]
            require(type(key) is int and key in lookups and key not in seen_keys,
                    "Unknown or duplicate authored message key")
            address, owner_bank = lookups[key]
            require(address == start + len(payload), "Authored message offset differs from its typed index")
            require(bank_name is None or bank_name == owner_bank, "Message owner crosses resource banks")
            bank_name = owner_bank
            seen_keys.add(key)
            data = encode_catalog_parts(message["parts"])
            entries.append({"key": key, "start": address, "size": len(data)})
            payload.extend(data)
            if "retained" in message:
                retained = message["retained"]
                require(isinstance(retained, list) and retained, "Retained strings must be a nonempty list")
                for ordinal, item in enumerate(retained, 1):
                    require(isinstance(item, dict) and set(item) == {"name", "parts"}
                            and item["name"] == f"unindexed_after_{key}_{ordinal}"
                            and isinstance(item["parts"], list) and item["parts"]
                            and all(isinstance(part, str) and part for part in item["parts"]),
                            "Retained strings require named readable text without controls or lookup keys")
                    data = encode_catalog_parts(item["parts"])
                    retained_rows.append({"name": item["name"], "start": start + len(payload),
                                          "size": len(data)})
                    payload.extend(data)
        expected = sorted((address, key) for key, (address, _) in lookups.items() if start <= address < end)
        require([(entry["start"], entry["key"]) for entry in entries] == expected,
                "Authored unit does not cover exactly its indexed message entries")
        padding = 0
        if "alignment_padding" in unit:
            require(type(unit["alignment_padding"]) is int and unit["alignment_padding"] == 4
                    and entries[-1]["start"] == banks[bank_name]["last_start"],
                    "Alignment padding is permitted only after the final indexed bank entry")
            padding = -(start + len(payload)) % 4
            require(0 < padding < 4 and start + len(payload) + padding == end,
                    "Final message padding does not reach its mapped four-byte boundary")
            payload.extend(bytes(padding))
        require(len(payload) == size, "Authored messages do not fill the mapped source interval")
        compiled[unit_name] = {"symbol": name, "payload": bytes(payload), "entries": entries,
                               "retained": retained_rows, "padding": padding}
    return compiled


def load_source(source, symbol_path, index_paths):
    document = json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=unique_fields)
    symbols = parse_symbol_map(symbol_path.read_text(encoding="utf-8"))
    indexes = [parse_message_index(path.read_text(encoding="utf-8"), symbols) for path in index_paths]
    return compile_document(document, symbols, indexes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--index-source", required=True, action="append", type=Path)
    parser.add_argument("--assembler", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assembly = args.output.with_suffix(".s")
    inputs = [args.source, args.symbols, args.assembler, *args.index_source]
    require(args.output.resolve() != assembly.resolve()
            and not {args.output.resolve(), assembly.resolve()}.intersection(path.resolve() for path in inputs),
            "Generated message output would overwrite a source input")
    units = load_source(args.source, args.symbols, args.index_source)
    require(args.unit in units, "Unknown message catalogue unit")
    unit = units[args.unit]
    symbol, payload = unit["symbol"], unit["payload"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    assembly.write_text(assembly_source(symbol, payload), encoding="ascii")
    subprocess.run([str(args.assembler), "-mgekko", "-o", str(args.output), str(assembly)], check=True)
    obj = Elf(args.output.read_bytes())
    require(set(obj.allocated) == {".data"}, "Message object must contain only initialized data")
    section = obj.allocated[".data"]
    require(obj.payload(section) == payload and obj.sections[section][1:3] == (1, 3)
            and obj.sections[section][8] == 1, "Assembler changed packed message storage")
    _, native = obj.unique_symbol(symbol)
    require(native[1:6] == (0, len(payload), 0x11, 0, section)
            and not obj.data_relocations(), "Message symbol or relocations differ from source")
    print(json.dumps({"unit": args.unit, "bytes": len(payload), "messages": len(unit["entries"]),
                      "retained_strings": len(unit["retained"]), "alignment_padding": unit["padding"],
                      "sha256": hashlib.sha256(payload).hexdigest()}))


if __name__ == "__main__":
    main()
