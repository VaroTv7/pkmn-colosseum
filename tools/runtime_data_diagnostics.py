#!/usr/bin/env python3
"""Describe two known runtime initializers without exporting raw game data.

The only accepted regions are the four MSL FILE records at 0x803138B0 and
MetroTRK's restore flags at 0x80313818. FILE offsets and bitfields come from
src/crt/stdio_range_800C7558.c; pointer values are represented exclusively by
their already-validated ELF relocation identities. This module neither emits
source nor changes the build/report. Unrecognized layouts fail closed.
"""

import re
import struct


FILE_ADDRESS = 0x803138B0
FILE_RECORD_SIZE = 0x50
FILE_RECORD_COUNT = 4
RESTORE_ADDRESS = 0x80313818

POINTER_FIELDS = {
    0x1C: "buffer",
    0x24: "buffer_ptr",
    0x38: "position_fn",
    0x3C: "read_fn",
    0x40: "write_fn",
    0x44: "close_fn",
    0x48: "idle_fn",
    0x4C: "next_file",
}
SCALAR_FIELDS = {
    0x00: "handle",
    0x18: "position",
    0x20: "buffer_size",
    0x28: "buffer_length",
    0x2C: "buffer_alignment",
    0x30: "save_buffer_length",
    0x34: "buffer_position",
}


def _validate_owner(section, data, symbol_name, symbol_size, section_size):
    if data is None or len(data) != section_size or section["size"] != section_size \
            or section["nobits"]:
        raise ValueError("Unexpected runtime data section extent")
    symbols = section["symbols"]
    owner = [symbol for symbol in symbols if symbol["name"] == symbol_name]
    if len(owner) != 1 or owner[0]["offset"] != 0 or owner[0]["size"] != symbol_size \
            or owner[0]["type"] != 1 or owner[0]["binding"] != 1:
        raise ValueError("Runtime initializer identity differs")
    padding = [symbol for symbol in symbols if symbol["name"] != symbol_name
               and symbol["size"]]
    allowed_gap = (symbol_name == "gTRKRestoreFlags" and len(padding) == 1
                   and padding[0]["name"] == "gap_05_80313821_data"
                   and padding[0]["offset"] == 9 and padding[0]["size"] == 3
                   and padding[0]["type"] == 1 and padding[0]["binding"] == 1
                   and padding[0].get("visibility") == 2)
    if padding and not allowed_gap:
        raise ValueError("Runtime initializer contains other storage")


def _pointer_identities(section, data):
    pointers = {}
    for relocation in section["relocations"]:
        offset = relocation["offset"]
        if relocation["type"] != 1 or not isinstance(relocation.get("addend"), int) \
                or not 0 <= offset < len(data) or offset % FILE_RECORD_SIZE not in POINTER_FIELDS:
            raise ValueError("Unexpected FILE initializer relocation")
        if offset in pointers or struct.unpack_from(">I", data, offset)[0] != 0:
            raise ValueError("FILE pointer is not an explicit normalized relocation")
        name = relocation["symbol"]
        if not re.fullmatch(r"[A-Za-z_.$@][A-Za-z_0-9.$@]*", name):
            raise ValueError("Unexpected FILE pointer symbol")
        identity = {"symbol": name, "addend": relocation["addend"]}
        for key in ("target_section", "target_symbol_offset", "target_section_offset"):
            if key in relocation and relocation[key] is not None:
                identity[key] = relocation[key]
        pointers[offset] = identity
    return pointers


def file_initializer(section, data):
    """Decode only the existing 80-byte FILE ABI and symbolic pointer fields."""
    _validate_owner(section, data, "__files", 0x140, 0x140)
    pointers = _pointer_identities(section, data)
    records = []
    for index in range(FILE_RECORD_COUNT):
        start = index * FILE_RECORD_SIZE
        record = data[start:start + FILE_RECORD_SIZE]
        modes = struct.unpack_from(">I", record, 4)[0]
        # The 13 declared mode bits occupy the high bits of this big-endian
        # word. The remainder is reserved. The initial mutable FILE state,
        # character/ungetc buffers, and their alignment padding must be zero.
        if modes & 0x7FFFF or any(record[0x08:0x18]):
            raise ValueError("Unexpected FILE reserved bits or initial state")
        file_mode = {
            "open_mode": modes >> 30 & 3,
            "io_mode": modes >> 27 & 7,
            "buffer_mode": modes >> 25 & 3,
            "file_kind": modes >> 22 & 7,
            "file_orientation": modes >> 20 & 3,
            "binary_io": bool(modes >> 19 & 1),
        }
        if file_mode["buffer_mode"] > 2 or file_mode["file_kind"] > 3 \
                or file_mode["file_orientation"] > 2:
            raise ValueError("Unknown FILE mode enum value")
        result = {"index": index, "offset": start, "file_mode": file_mode,
                  "mutable_state_and_character_buffers_zero": True,
                  "reserved_bits_and_padding_zero": True}
        for offset, name in SCALAR_FIELDS.items():
            result[name] = struct.unpack_from(">I", record, offset)[0]
        result["pointers"] = {}
        for offset, name in POINTER_FIELDS.items():
            if start + offset in pointers:
                result["pointers"][name] = pointers[start + offset]
            elif struct.unpack_from(">I", record, offset)[0] == 0:
                result["pointers"][name] = None
            else:
                raise ValueError("Non-null FILE pointer has no symbolic relocation")
        records.append(result)
    return {"kind": "msl_file_initializer", "symbol": "__files",
            "address": FILE_ADDRESS, "record_size": FILE_RECORD_SIZE,
            "record_count": FILE_RECORD_COUNT,
            "layout_source": "src/crt/stdio_range_800C7558.c",
            "records": records, "relocations_verified": len(pointers)}


def restore_initializer(section, data):
    """Describe the existing nine boolean restore flags and three padding bytes."""
    _validate_owner(section, data, "gTRKRestoreFlags", 9, 12)
    if section["relocations"] or any(value not in (0, 1) for value in data[:9]) \
            or any(data[9:]):
        raise ValueError("Unexpected MetroTRK restore-flag initializer")
    return {"kind": "metrotrk_restore_flags", "symbol": "gTRKRestoreFlags",
            "address": RESTORE_ADDRESS, "size": 9,
            "flags": [bool(value) for value in data[:9]],
            "padding_size": 3, "padding_zero": True,
            "layout_source": "src/trk/TRKSaveState.c"}


def runtime_structure(unit, metadata, private):
    """Return a description for an allowlisted original region, otherwise None."""
    if not unit["name"].startswith("main/"):
        return None
    recognized = []
    for section in unit.get("sections", []):
        if section["name"] != ".data":
            continue
        address = int(section.get("metadata", {}).get("virtual_address", 0))
        if address in (FILE_ADDRESS, RESTORE_ADDRESS):
            recognized.append((address, int(section["size"])))
    if not recognized:
        return None
    if len(recognized) != 1:
        raise ValueError("Multiple runtime regions in one owner")
    address, size = recognized[0]
    expected = 0x140 if address == FILE_ADDRESS else 12
    section, data = metadata[".data"], private[".data"]
    if size != expected:
        # Restore flags may share an aligned owner with the following existing
        # MetroTRK data. Inspect only the same twelve-byte prefix; never decode
        # unrelated storage using this known runtime ABI.
        if address != RESTORE_ADDRESS or size < expected or data is None \
                or len(data) != size or section["size"] != size:
            raise ValueError("Runtime report extent differs")
        if any(symbol["offset"] < expected < symbol["offset"] + symbol["size"]
               for symbol in section["symbols"]):
            raise ValueError("Runtime prefix bisects another symbol")
        section = dict(section, size=expected,
                       symbols=[symbol for symbol in section["symbols"]
                                if symbol["offset"] < expected],
                       relocations=[relocation for relocation in section["relocations"]
                                    if relocation["offset"] < expected])
        data = data[:expected]
    if address == FILE_ADDRESS:
        return file_initializer(section, data)
    return restore_initializer(section, data)
