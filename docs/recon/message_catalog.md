# Completed message catalogue: readable source reconstruction

## Scope and verification status

[`src/rel/common_rel/message_catalog.json`](../../src/rel/common_rel/message_catalog.json)
represents the final **91,421 bytes** of message storage in **13 existing
`common_rel .data` owners**. It contains **4,018 indexed messages**, **three
retained strings without lookup entries**, **314 named formatting-control
operations**, and **41,093 ordinary BMP glyphs**. The original owner names,
symbols, boundaries, message keys and physical storage order are preserved.

A private authoring check parsed the original REL's section table and message
indices, encoded the readable source, and compared every complete owner
interval. A second reviewer, using a separate decoder and serializer, verified
all keys, offsets, first terminators, retained strings and alignment without
importing the authoring code or production encoder. Both comparisons matched
all **91,421 bytes**. All 13 production objects, including the normal object
fixup, also passed independent whole-owner comparisons, symbol/size checks,
alignment-1 checks and zero-relocation checks. The normal
[integrated Build](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40980024867/job/123817499088) at source revision
[`8c3c0d8845846b9b4b76e35d800cd2ff7cd8a486`](https://github.com/dougchansan/pkmn-colosseum/commit/8c3c0d8845846b9b4b76e35d800cd2ff7cd8a486)
then passed all **26 unchanged canonical output hashes and direct byte
comparisons**. Its complete report verifies the full **91,421-byte matched and
source-linked data gain**, completing all **3,565,996 tracked data bytes**.
Runtime gameplay testing is outside these checks.

## Provenance and maintainer authorization

On **2026-10-29**, the maintainer explicitly approved completing these remaining
91,421 bytes using the message content in their supplied original files. The
catalogue preserves that actual content as readable strings and named,
typed formatting controls. It is a content-preserving reconstruction of
**message data**; its dialogue and labels are not newly authored dialogue or
decompiled native program code.

That authorization is scoped to this catalogue. The tracked deliverable is
readable source, with no original binary, target object, compiler artifact,
opaque byte/hex array, binary include, or `.inc` change. Generated assembly
and objects remain build products. Original files are private validation
inputs and are not needed by the production catalogue encoder.

The 219 complete entries already implemented by
[`message_templates.json`](../../src/rel/common_rel/message_templates.json)
remain in their existing owners. The middle message group already represented
by shared DOL source also remains separate. Neither is counted again in this
91,421-byte contribution.

## Source representation

The `gs-message-catalog-v1` document groups entries under the existing
`message_storage_*` owner names. Each unit declares its original symbol,
section-relative start and complete size. Each indexed message has its
original `key` and an ordered `parts` list containing readable UTF-8 text and
named control operations.

The source retains **physical storage order**. Keys are not monotonically
ordered in that storage: the remaining owners contain 67 descending key
transitions. The existing typed message indices retain their own lookup order
and original offsets; sorting the catalogue by key would move message data.

Glyph strings preserve exact Unicode code points, punctuation, spacing and
case. There is no Unicode normalization. All 622 distinct glyphs are ordinary
BMP characters; the catalogue requires no surrogate, private-use, control-code
or noncharacter glyph escape. The encoder writes glyphs as big-endian
16-bit values and supplies each string's zero terminator.

The controls follow `GSmsgReadCode` and `GSmsgDispatchControl` in
[`src/game/gs_msg.c`](../../src/game/gs_msg.c), the `msgctrlcode` callback table
in [`data_80363774.c`](../../src/game/data/data_80363774.c), and the matching
control handlers. Control IDs are emitted from that named registry, not stored
as arbitrary opcode bytes in the catalogue.

| Source control | ID | Existing callback | Inline parameter | Uses |
|---|---:|---|---|---:|
| `line_break` | 0 | `msgctrlCR` | None | 28 |
| `key_end` | 2 | `msgctrlKeyEnd` | None | 8 |
| `font` | 7 | `msgctrlFont` | One unsigned byte | 233 |
| `color` | 8 | `msgctrlColor` | Red, green, blue and alpha unsigned bytes | 4 |
| `event_string_0` | 13 | `msgctrlEvStrBuf0` | None | 8 |
| `event_string_1` | 14 | `msgctrlEvStrBuf1` | None | 6 |
| `my_name` | 19 | `msgctrlMyName` | None | 8 |
| `my_pokemon` | 20 | `msgctrlMyMons` | None | 5 |
| `my_pokemon_2` | 21 | `msgctrlMyMons2` | None | 1 |
| `trainer_name` | 35 | `msgctrlTrainerName` | None | 1 |
| `move_name` | 40 | `msgctrlWazaName` | None | 1 |
| `item_name` | 41 | `msgctrlItemName` | None | 1 |
| `digit` | 47 | `msgctrlDigit` | None | 6 |
| `event_string_2` | 65 | `msgctrlEvStrBuf2` | None | 4 |
| **Total** | | | | **314** |

Font parameters use the existing unsigned-byte `value` field. Color parameters
use explicit `red`, `green`, `blue` and `alpha` fields, each constrained to
0–255. Substitution controls retain the dynamic names, numbers or strings
provided by the existing runtime handlers.

## Exact owner boundaries

Addresses are section-relative `common_rel .data` offsets, with exclusive
ends. The existing split and symbol declarations remain unchanged.

| Owner | Interval | Bytes | Indexed messages |
|---|---|---:|---:|
| `message_storage_5BF64` | `0x5BF64–0x5BFF4` | 144 | 6 |
| `message_storage_5C090` | `0x5C090–0x61A12` | 22,914 | 1,127 |
| `message_storage_61A40` | `0x61A40–0x61A5C` | 28 | 2 |
| `message_storage_61A7B` | `0x61A7B–0x61D8B` | 784 | 29 |
| `message_storage_61D94` | `0x61D94–0x61E46` | 178 | 9 |
| `message_storage_61E77` | `0x61E77–0x63069` | 4,594 | 369 |
| `message_storage_6306E` | `0x6306E–0x64102` | 4,244 | 352 |
| `message_storage_6410E` | `0x6410E–0x647B4` | 1,702 | 88 |
| `message_storage_7B268` | `0x7B268–0x80AB1` | 22,601 | 901 |
| `message_storage_810E1` | `0x810E1–0x811F1` | 272 | 25 |
| `message_storage_81609` | `0x81609–0x85FFD` | 18,932 | 697 |
| `message_storage_86014` | `0x86014–0x89788` | 14,196 | 377 |
| `message_storage_899BC` | `0x899BC–0x89CFC` | 832 | 36 |
| **Total** | **13 owners** | **91,421** | **4,018** |

These intervals cover the remaining storage in the groups based at `0x58044`
and `0x76C94`. Their existing typed headers and key/offset tables remain the
authoritative lookup definitions. The source includes each complete owner
extent, including the retained strings and alignment described below.

## Retained strings and real alignment padding

Three complete, zero-terminated strings follow an indexed message's first
terminator without having their own entries in either message index. They
are represented by named `retained` records on the preceding indexed message.
Each record contains readable text and receives its own terminator; no lookup
key is invented.

| Retained record | Interval | Bytes |
|---|---|---:|
| `unindexed_after_61271_1` | `0x82095–0x820AB` | 22 |
| `unindexed_after_61271_2` | `0x820AB–0x820C1` | 22 |
| `unindexed_after_61429_1` | `0x82895–0x828A5` | 16 |
| **Total** | **Within `message_storage_81609`** | **60** |

The ordinary message reader stops at the preceding message's first zero
terminator. These three records preserve storage only; their use through
other paths has not been established. Their content is not mislabeled as
padding or appended to the preceding visible message.

The only actual trailing padding is **two zero bytes at
`0x647B2–0x647B4`**, after the first group's final message, key 3177. The unit
declares `alignment_padding: 4`, so the encoder calculates the required
alignment from the absolute section position. It does not accept an arbitrary
padding-byte sequence.

Message streams must otherwise stay byte-packed: **1,525 indexed messages**
start at odd addresses. Native data owners therefore require alignment 1,
and neither glyphs nor control operations may acquire extra word padding.

## Production build path

[`tools/message_catalog_source.py`](../../tools/message_catalog_source.py)
reads the catalogue, the existing public symbol map, and the two existing
typed index sources:
[`message_index_58044.c`](../../src/rel/common_rel/message_index_58044.c) and
[`message_index_76C94.c`](../../src/rel/common_rel/message_index_76C94.c).
Those inputs define the owner extents, indexed keys and required addresses.
The production encoder accepts no original-file or target-object input.

`load_source(source, symbol_path, index_paths)` validates the source and
returns each unit's symbol, encoded payload, indexed entry extents, retained
record extents and alignment count. The pure `compile_document` operation
checks the parsed schema, symbols and indices. It rejects duplicate fields or
keys, undeclared controls, invalid parameter types, misplaced retained text,
incorrect owner extents and physical message offsets that disagree with the
typed indices.

The command-line interface accepts `--source`, `--unit`, `--symbols`, repeated
`--index-source`, `--assembler` and `--output` arguments. It emits data-only
assembly under the build directory, assembles with the repository's PowerPC
binutils, and reopens the object to check its complete section, alignment,
object symbol and absence of relocations. The generated file contains no
PowerPC instructions. Original files are used only by separate private
validation, outside this build path.

## Validation and progress accounting

The private comparison covers every original indexed key and offset, every
primary terminator, all three retained-string boundaries, the final alignment
and each complete owner extent. Independent verification then checked all 13
assembled objects after the normal object fixup against the original owner
intervals. Each is one exact global data object, aligned to one byte, with
zero relocations. The source and production build preserve exact code points
rather than normalizing or translating text.

The 15 focused catalogue tests and six existing template tests pass, as do
all 290 repository checker tests and 13 jump-table tests. The focused cases
cover physical/key order differences, odd glyph addresses, RGBA parameters,
exact Unicode preservation, malformed inputs, lookup extents, retained
strings and final bank alignment. A direct baseline comparison verifies that
the shared encoder changes leave all 12 existing template owners, 219 entries
and 3,635 bytes unchanged.

The pinned objdiff 3.6.1 subset report measures
`total_data = matched_data = complete_data = 91,421`, with all 13 units
complete and zero native functions or code bytes. Its SHA-256 is
`c5235df3ef3c83b05bfb43f8479156932d80e2e125762ee651da2308b2b738bc`.
The catalogue source SHA-256 is
`95307572fe153ad766045f119bb9fada92a8dde5243138307dc09350c3cce5cf`.

The normal integrated source build passed all 26 unchanged canonical output
hashes and direct byte comparisons. Its
[whole-project report](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40980024867/artifacts/12944233546) has SHA-256
`14bbb9b3f8e9099521db7d1f66b9527a4341a3786aa6d672b305e7380d958c39`.
The independent report audit preserves the exact physical interval union,
all 8,677 function identities and sizes, the 2,504,940-byte code denominator,
the **3,565,996-byte data denominator**, and the entire 2,272-unit topology.
There are no overlaps, omitted bytes or other source-status changes.

These 91,421 bytes contributed matched and source-linked **data**, bringing both
data measures to **100%**. They added no PowerPC functions or code credit and
did not shrink the denominator. At the PR #665 checkpoint, source-backed and
complete units rose from 2,258 to 2,271; the unchanged interrupt-vector template
was the sole incomplete owner outside the historical tracked-code denominator.
Its subsequent reconstruction completes the final scoring unit; see
[the vector evidence](../asm_evidence/interrupt_vectors.md). The initial
catalogue build's strict-freeze failure recorded its expected source-status
increase; the documentation/freeze refresh and final required checks are recorded in
[PR #665](https://github.com/dougchansan/pkmn-colosseum/pull/665).
