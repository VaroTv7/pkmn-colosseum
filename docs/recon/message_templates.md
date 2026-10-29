# Packed message controls and generated labels

## Verified scope and acceptance status

`src/rel/common_rel/message_templates.json` reconstructs **219 complete message
entries totaling 3,635 bytes** in 12 `common_rel .data` owners. Independent
local verification established that every authored entry has the original
key, starting offset, complete storage extent and bytes. All 12 generated
native objects also match their entire original intervals, with **alignment
1**, one correctly sized exported data symbol and **zero relocations**.

**Full integrated canonical CI is pending for this checkpoint.** The local
source/native comparisons described here do not claim that the complete
DOL/REL build, canonical hashes, topology or metric-integrity gates have
passed with the new owners. Final acceptance must retain those checks and
the full physical data denominator.

This reconstruction covers formatting controls, simple UI states, complete
entries already represented by existing source, and regular counter-label
families. It does not publish a decoded catalog of the remaining message
resources. Unreconstructed intervals remain adjacent fallback and receive
no source credit.

## Source provenance and entry counts

| Source category | Complete entries | Basis |
|---|---:|---|
| Typed control-only messages | 33 | Existing control dispatch table and matching handlers; 32 entries in the first group and one combined event/string/digit template in the second |
| `ON` and `OFF` | 2 | Explicit simple state labels |
| Existing `????` and `FIGHT` entries | 2 | Complete existing source-backed DOL entries, totaling 22 bytes |
| `TEST01` through `TEST06` | 6 | One counter template with a font prefix |
| D2 member labels | 100 | One template over member numbers 1–100 |
| M4 set/member labels | 36 | Five under-sets of four members, four bottom-sets of three members, and a fifth bottom-set of four |
| Scenario and eight-person-doubles labels | 40 | Two 1–20 counter families with fullwidth decimal digits |
| **Total** | **219** | **3,635 exact bytes** |

The counter families account for **182 entries**. Their source specifies the
fixed label format, counter axes, iteration order and first key; it does not
store a separate decoded original string for every member. Fullwidth
conversion applies to the interpolated decimal digits. The fixed prefix
remains explicit readable text.

The two reused text entries already occur in the DOL message definitions
owned by `src/game/data/data_8027A500.c`, in the group at `lbl_802CF810`:

| REL entry key | Existing DOL entry key | Complete extent | Source meaning |
|---:|---:|---:|---|
| 2,356 | 11,119 | 10 bytes | `????`, including its GSchar terminator |
| 3,007 | 316 | 12 bytes | `FIGHT`, including its GSchar terminator |

These were verified as complete entries, rather than substrings found in
unrelated DOL storage. The existing DOL owner was already native-source
verified at the preceding canonical checkpoint. Two additional five-byte
whole-entry matches are represented here by their understood controls:
REL key 207 / DOL key 408 is the menu-message substitution, and REL key
4,426 / DOL key 6,035 is the hero-name substitution. Those two entries are
already included in the 33 control-only entries; they are not counted again
as text reuse.

## Complete source intervals

All addresses below are **section-relative `common_rel .data` offsets**, with
exclusive ends. Each boundary is a complete message-storage boundary, and
the 12 intervals do not overlap.

| Generated owner | Interval | Bytes | Entries |
|---|---|---:|---:|
| `message_templates_5BFF4` | `0x5BFF4–0x5C090` | 156 | 20 |
| `message_templates_61A12` | `0x61A12–0x61A40` | 46 | 5 |
| `message_templates_61A5C` | `0x61A5C–0x61A7B` | 31 | 3 |
| `message_templates_61D8B` | `0x61D8B–0x61D94` | 9 | 1 |
| `message_templates_61E46` | `0x61E46–0x61E77` | 49 | 5 |
| `message_templates_63069` | `0x63069–0x6306E` | 5 | 1 |
| `message_templates_64102` | `0x64102–0x6410E` | 12 | 1 |
| `message_templates_7B1FC` | `0x7B1FC–0x7B268` | 108 | 6 |
| `message_templates_80AB1` | `0x80AB1–0x810E1` | 1,584 | 100 |
| `message_templates_811F1` | `0x811F1–0x81609` | 1,048 | 36 |
| `message_templates_85FFD` | `0x85FFD–0x86014` | 23 | 1 |
| `message_templates_89788` | `0x89788–0x899BC` | 564 | 40 |
| **Total** | **12 owners** | **3,635** | **219** |

The existing typed message headers and key/offset tables remain unchanged.
Entry offsets still refer to their original group bases at `0x58044` and
`0x76C94`, as required by `GSmsgFindMessage`. Keys in the template source
describe which existing index entries own the generated storage; the
payload generator does not replace or renumber the index tables.

## Encoding follows the existing reader and handlers

`tools/message_template_source.py` implements the packed representation
already consumed by `GSmsgReadCode` and `GSmsgDispatchControl` in
`src/game/gs_msg.c`:

- Ordinary glyphs are big-endian 16-bit values; a zero halfword terminates
  an entry.
- The `0xFFFF` escape is followed by a one-byte control ID.
- A control's inline parameter width comes from its matching callback.
  The next glyph can consequently begin at an odd byte address.

Control identities are bound to `msgctrlcode` in
`src/game/data/data_80363774.c`. The typed parameter cases used here are:

| Authored control | Callback | Inline parameter |
|---|---|---|
| `font` | `msgctrlFont` | One unsigned byte |
| `align` | `msgctrlAlign` | One unsigned byte |
| `baseline_bias` | `msgctrlBaseLineBias` | One signed byte |

The baseline handler reads its parameter as `s8` and advances the stream by
one byte. The source therefore writes the semantic value `-2`, with the
encoder performing the signed-byte representation. Font and alignment
parameters retain their unsigned ranges. The other controls used here take
no inline parameter: they invoke existing line-break, name, string or
number-substitution callbacks.

All 16 control declarations in the compiler agree with the existing callback
table. The current authored entries use 15 of them; the declared second
menu-message control is not needed by this selection. The controls themselves
do not duplicate the dynamic names, numbers or messages supplied at runtime.

## Source-only build path and native layout

The compiler accepts named control operations, readable text and bounded
counter templates. It has **no original-file input, binary include, raw-byte
operation or original-object fallback escape**. It rejects reserved glyphs,
embedded terminators, unsupported parameter types, undeclared formatting
fields, duplicate keys and source intervals that are not filled exactly.

After expanding the authored source, it emits a data-only assembly file under
the build directory and assembles that file with the repository's PowerPC
binutils. The generated file contains only initialized data directives,
symbol metadata and `.balign 1`; it contains no PowerPC instructions.
Generated assembly and object files are build products and must not be
committed. No `.inc` file is involved.

Byte alignment is necessary here. Several message starts and owner sizes are
odd, and inserting native word-alignment padding would move subsequent
messages. The compiler reopens the assembled object and requires exactly the
authored `.data` payload, alignment 1, the expected object symbol and size,
and no data relocations. These checks preserve the packed storage used by
the original message reader.

When the objects are linked and accepted, they contribute source-linked
**data**. They do not add decompiled PowerPC functions or assembly-code
credit, and the original fallback cannot supply their source credit.

## Validation evidence

The six focused tests in `.github/scripts/test_message_template_source.py`
cover packed glyph/control widths, callback-table identities, signed and
unsigned parameter validation, counter order and fullwidth decimal digits,
duplicate/unknown template fields, and symbol/extent rejection before
assembly. Their examples are synthetic; they do not contain original
message catalogs or retail payload fixtures.

The independent private-input review additionally passed all of these
checks for the actual source selection:

- Parsed the two original `MessageGroup` indices independently and verified
  every one of the 219 keys, starting offsets and complete storage extents.
- Walked every selected entry according to glyph and control widths,
  confirming that its zero terminator ends exactly at the next storage
  boundary.
- Compared all 3,635 authored bytes with their original intervals.
- Built all 12 native objects and independently checked their section
  contents, alignment, symbol sizes and absence of relocations.
- Confirmed that the source-owner intervals do not overlap and that every
  native section remains byte-identical to its complete original interval.

Only counts, boundaries, identities, hashes and equality results are suitable
as public verification metadata. Private originals and decoded catalogs are
not documentation or build inputs. The final integrated build must still
prove that these source owners preserve the unchanged complete resources,
canonical outputs and physical progress scope.
