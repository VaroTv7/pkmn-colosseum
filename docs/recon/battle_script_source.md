# Authored battle-sequence source

The remaining packed DOL battle programs are represented by named commands in
`src/game/battle_scripts/*.battle.json`. The 17 source owners retain all 195
original object names and exactly 13,500 physical data bytes. These are programs
for the game's battle interpreter, so they contribute to source-backed **data**.
They do not add decompiled C functions or native assembly functions.

The 17 owners are verified in the normal production build, contributing a
**13,500-byte gain in matched and complete source data**. Their physical
coverage remains unchanged. The integration evidence is recorded below.

`tools/battle_script_format.py` defines the supported commands and their typed
operands. Each command records the existing matching C handler and source path
used to establish its meaning, operand widths, and instruction stride. The
dispatch authority is `lbl_8027A00C` in
`src/game/data/rodata_80279B78.c`. The source language has 212 supported commands;
the reconstructed programs contain 3,182 command occurrences.

## Source and compilation

The authored files contain operations such as `calculate_damage`,
`apply_damage_and_update_hp`, `jump_if_condition`, `call_sequence`,
`copy_memory`, and `set_status_word`. They contain no opaque byte-array escape,
native instruction listing, or original-file path. Comparison, stat, battler,
and status-family operands have explicit domains. Status fields are checked
against the actual getter or setter switch for their family; read-only fields
are not silently accepted as setter fields.

For example, a fixed-damage transfer can be expressed as:

```json
{
  "command": "set_status_word",
  "family": "fight_floor",
  "context": null,
  "object_id": null,
  "field": 62,
  "index": null,
  "value": {"symbol": "lbl_80478D90", "encoding": "absolute"}
}
```

The existing `WS_STATUS_SET32` handler reads a 32-bit value through its value
operand and passes it to `statusSetStatus`. Family 7 selects
`fightFloorSetStatus`; field `0x3E` is the current damage transfer. The command
in `lbl_803767D1` references `lbl_80478D90`. Its operand is not word aligned in
the packed stream, so the old relocation scan missed this typed reference.
The analogous command in `lbl_80377531` references `lbl_80478D8C`. These uses
establish the two separate four-byte damage operands; no script reference was
found to the trailing alignment word at `0x80478D94`.

Branches name a script and a named entry, rather than an integer address or
offset. Entries inside the new sources are calculated from command widths.
`catalog.json` also declares 16 entries-owning script objects in 12 existing C
source files. During every build, the compiler reads those C initializers,
resolves their symbolic pointer words using the public symbol map, checks their
complete extents, and derives instruction boundaries. A catalog entry that
points inside an operand is rejected. Only the explicit constant `u8[]` and
`void*[]` initializer forms present in those sources are supported; unsupported
C syntax fails closed. Twelve additional handler strides are used for this
validation of neighboring C programs, without adding raw input to the new
source language.

Memory operands name data objects and optional nonnegative addends. Their
access widths must fit the declared symbol extents. Byte-copy and comparison
commands check the complete transfer count against both memory objects. That
count does not constrain an unrelated branch destination. Null is accepted
only in fields whose handlers provide a null case.

The compiler runs without original game files:

```sh
python tools/compile_battle_scripts.py \
  --source src/game/battle_scripts/scripts_80375E60.battle.json \
  --symbols config/GC6E01/symbols.txt \
  --assembler build/binutils/powerpc-eabi-as \
  --output build/GC6E01/battle-validation/scripts_80375E60.o
```

It emits generated GNU data assembly beside the output object and invokes the
normal PowerPC assembler. There are no native instructions. Each original
program becomes a global ELF object symbol with its actual byte-array extent.
The compiler requires contiguous ownership inside each owner and checks its
derived command sizes against the public map. It preserves each owner's
original section alignment: seven owners use four-byte alignment and ten use
eight-byte alignment. No internal alignment directives or object-byte patches
are needed.

Generated assembly and objects belong under the ignored build directory.
The authored JSON, compiler, source schema, neighboring C definitions, and
public symbol map are the build inputs. Private originals were used only to
reverse engineer and independently verify the authored source.

The generated object follows the existing GNU assembler build path through
`dtk elf fixup`. This source-only compatibility step sets the embedded PowerPC
ELF flag and removes empty sections and their section symbols. Independent
comparison of all 17 battle and 12 message objects verifies unchanged allocated
bytes, object symbols, relocations and section alignment. Their pinned objdiff
report remains 17,135 of 17,135 data bytes exact and 29 of 29 units complete.
No target object or original payload is an input to this fixup.

## Address encodings and relocation classification

The interpreter reads packed, big-endian wire addresses. The existing object
format represents some of those fields with normal `R_PPC_ADDR32` relocations
and leaves others as absolute wire addresses. Each source address explicitly
declares `reloc` or `absolute` encoding. Relocated fields are emitted as
ordinary assembler symbol expressions; absolute fields are resolved from the
public map. A field cannot request a relocation for an arbitrary scalar,
opcode, or byte span. GNU as emits the normal relocation records, including
unaligned relocations when requested by the format.

The field audit identified 1,590 semantic address operands in the new programs.
There are 299 genuine existing relocations. All their offsets, types, symbol
identities, addends, and local target offsets are preserved.

One previous relocation was a scanner false positive. In `lbl_80378F8C`, the
`set_status_halfword` command begins at `0x80378FE1` and occupies 20 bytes. Its
four-byte value-address field begins at `0x80378FF1` and references
`lbl_80478D80`. The next `play_animation` command begins at `0x80378FF5`, with
separate one-byte battler and animation operands. The aligned word beginning
at `0x80378FF4` therefore crosses the last byte of the value pointer, the next
command, and those two scalar operands. It is not a reference to
`lbl_80451217`. The narrowly scoped `block_relocations` entry at that source
site corrects the object metadata; the program's physical bytes, symbol names,
and behavior remain unchanged. Neither target hashes nor progress denominators
are changed to accommodate it.

## Preserved interpreter compatibility behavior

The source preserves the existing interpreter and programs, including unusual
wire behavior. It does not repair game logic as a side effect of reconstruction.

| Source command | Existing behavior preserved |
| --- | --- |
| `print_selection_message_legacy` | `wsCmd11` advances three bytes but loads a 32-bit message at offset one. Its two stored operand bytes are followed by two bytes of lookahead into subsequent commands. The source retains this three-byte stride and does not invent a 16-bit handler load. |
| `animate_selected_condition` | `wsCmd66` ignores the byte at offset two and compares the following 32-bit number with seven. The number is not treated as a pointer. |
| `copy_target_stat_stages` | `WS_JIKOANJI` occupies five bytes but does not read its four-byte compatibility target. The encoded address and its relocation remain, while the control-flow audit excludes it as an executable branch edge. |
| `apply_intimidate` | The handler ignores its four-byte compatibility operand. The source retains its zero scalar and full command stride. |
| `play_animation_indirect` in `lbl_80378AF1` | `wsCmd46` reads a pointer at offset two, dereferences a byte when non-null, and advances ten bytes. This one existing command encodes address ten. The scoped `wsCmd46_pointer_ten` legacy operand preserves that pointer interpretation; it is not changed into an immediate animation ID. The compiler rejects this exception in every other program, position, or field. |

No new C out-of-bounds array definition is introduced to emulate packed data.
The generated objects are byte-array storage; the matching interpreter's
existing access and control-flow behavior remain the authority. The low-address
legacy operand is an observation of the original program, not evidence that
executing that path is safe or that it is reachable in normal play.

## Validation and limits

The complete surrounding script range, `0x80375E48` through `0x80379BFE`, was
decoded using handler-derived strides. All 262 script symbols decode to their
declared boundaries. The new programs contain 628 executable branch/call
operands targeting 201 distinct instruction entries. Every non-null target
falls on an instruction boundary; ignored compatibility addresses are excluded
from that control-flow count. This is a structural audit, not a runtime
reachability or termination proof.

Local native-object validation assembled all 17 authored owners and compared
them with the canonical private DOL and object metadata. A separate independent
review regenerated DTK target objects from the current configuration and symbol
map, assembled every source owner again, and compared the resulting objects
directly. Both checks passed all 13,500 physical bytes, all 195 symbol
names/offsets/sizes/types/bindings, all 299 relocation records, and every section
alignment. The direct comparison with regenerated targets required no manual
exclusion or data normalization beyond the target's ordinary relocation
representation. No non-data storage was emitted. No original payload, target
object, or generated object is committed as evidence.

The focused suite is:

```sh
python .github/scripts/test_battle_script_source.py
```

Its 27 tests cover packed byte/halfword/word encoding, real unaligned GNU
relocations and addends, symbol metadata, legacy lookahead and ignored operands,
the tightly scoped low-address operand, memory bounds, branch labels, external
C entry boundaries, status getter/setter domains, duplicate keys, unsupported
fields, ownership gaps/overlaps, and rejection of numeric/raw address escapes.
Source-only tests also verify the dispatch identities, status field switches,
the complete 17-owner extent, and dependency coverage. Assembler-dependent
synthetic cases explicitly skip when the assembler has not been downloaded;
they ran locally with the project's PowerPC assembler.

[Normal Build 40968205519](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40968205519/job/123777997002)
at [source commit 456efababa4448e5b66c1c8ac336531c1e669536](https://github.com/dougchansan/pkmn-colosseum/commit/456efababa4448e5b66c1c8ac336531c1e669536)
passed all **26 unchanged canonical DOL/REL hashes and direct binary
comparisons**. The normal build ran no diagnostic target-substitution variants.
It also passed the 34 zero-data layout checks, assembly-branch checks,
metric-integrity checks, strict freeze, and README metric table check.

The full source report confirms all 17 battle owners complete, with
`total_data = matched_data = complete_data = 13,500`. This is a verified
13,500-byte source-data gain. The independent audit preserves all **8,677
function identities**, all 2,504,940 native code bytes, and the exact physical
interval union across all 26 modules, with no overlaps, removed bytes or added
bytes. The full data denominator remains 3,565,996 bytes; no native functions
or physical storage were reclassified out of scope to obtain this result.

The [report artifact from that build](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40968205519/artifacts/12939685347)
has report SHA-256
`c4e3995c1d8155a5b9536a4de02dae2580ff2b9a8a265cdcf4426e897680e09b`.
These integrated checks establish source accounting and binary identity.
Runtime gameplay was not tested, and the structural control-flow audit does
not claim that every branch is reachable or terminates.
