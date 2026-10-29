# Shared GS VM bank 0x0596: semantic source reconstruction

## Verified local result and CI status

The authored program in
`src/rel/common_rel/common_script_0596.json` reconstructs the **7,964 bytes**
at `common_rel .data 0x89D98–0x8BCB4`. Together with the existing 156-byte
typed header in `script_structure_89CFC.c`, it reproduces the complete
**8,120-byte** bank at `0x89CFC–0x8BCB4`.

Both generated program data and the existing header were compiled locally
with **ProDG 3.5**, using the repository's `-O0 -G0` REL options and the
normal binutils object conversion. The native sections were compared with
the maintainer's private original input; no comparison-only rewrite was
needed.

| Native source object/interval | Size | Alignment | ELF relocations | Verified SHA-256 |
|---|---:|---:|---:|---|
| Program, `lbl_125_data_89D98` | 7,964 | 4 | 0 | `f645e6df3ce90b4c31208a2703a0cf60b68867ec87c0794ecda7df8bfb1d65f7` |
| Complete header + program bank | 8,120 | 4 | 0 | `97da7bebacaa9c0485092349eda2d06ed8d7a0515c7fb5cd9c5ab7647fa2ef85` |

The program object contains one nonempty allocated `.data` section and one
global object symbol of size 7,964. The header object likewise contains only
its 156-byte `.data` definition. Their native section bytes concatenate to
the original bank exactly. All 27 generated entry offsets agree with the
already reconstructed header.

**Full canonical CI is pending for this reconstruction.** These local results
establish the source bytes, layout and native object contents; they do not
claim that the complete DOL/REL build, report-integrity checks or runtime
testing have passed for the new checkpoint. Final acceptance also requires
the repository's unchanged canonical hashes and full physical denominator.

## Program, rather than an instruction transcript

`tools/gs_vm_script_source.py` compiles semantic JSON source into C under the
build directory. The authored source contains structured `if` and `while`
statements, returns, typed expressions, named native calls, named frame/global
variables, script identifiers and one named code diagnostic. It contains no
opcode list, original byte array, binary include, fixed branch address, or
escape that accepts arbitrary instruction bytes.

The encoder reads only its source input. It does not read a retail executable,
target object, disassembly, fixture or private analysis file. Generated C and
native objects are build products and must not be committed. No `.inc` file
is used. The public source can be compiled without the original game files;
the originals are required only for matching validation.

The schema and lowering rules come from the existing matching implementation:

- `include/game/gs_vm.h` defines values, script headers and call frames.
- `src/game/gs_vm.c` defines expression descriptors, assignments, control flow,
  script returns and the opcode table.
- `gs_vm_exact_800F10E8.c` implements native calls;
  `gs_vm_exact_800F13D0.c` and `gs_vm_exact_800F16C0.c` implement waits and logs.
- `lbl_802E1CF0` in `src/game/data/data_8027A500.c` supplies the native indices,
  function identities and argument-register types.

Only the expression operators needed by this program are accepted. Unknown
statements, raw/opcode escapes, undeclared variables/natives, inconsistent
argument types, invalid indices and unsupported diagnostic formats fail
before output is written.

## Reconstructed behavior

The bank has **27 script entry points**, **41 distinct native bindings**, and
**176 native-call sites**. The five bank globals are the current room,
previous floor, elevator duration in centiseconds, its converted duration in
seconds, and saved background-music ID. Their initial zero storage remains
owned by the typed header.

| Entry indices | Source behavior |
|---|---|
| 0–2 | Default callbacks returning success |
| 3 | Hero movement update and a one-frame yield in a loop |
| 4–7, 12–13 | Floor changes, doors, elevator departure/arrival, and a menu-room return path |
| 8–9, 22–23 | Half-second fade callbacks with explicit native fade modes |
| 10 | Per-frame treasure-actor visibility controlled by event and hide flags |
| 11 | Open and close a caller-selected field message while hero movement is suspended |
| 14 | Wait for an actor's motion and close that actor |
| 15 | Sleep for 0.6 times frame slot zero, preserving that explicit calling convention |
| 16–18, 20, 26 | Cologne, evolution, mail, GBA communication and evolution-finalization wrappers |
| 19 | Story-selected TV news with per-room cameras, actor visibility, music restoration and a failure diagnostic |
| 21 | Story-flag conditions selecting duplicate-aware mail notifications |
| 24–25 | Clear the two story-selected TV-news flags |

These names describe the behavior established by existing native routines
and callers. Uncertain native identities retain their existing address-based
names, such as `fn_80088428`; the reconstruction does not rename engine
symbols. Integer mode/resource IDs remain explicit where the source does not
justify a more specific semantic name. The three source-resource comparisons
in entry 12 also appear in the already committed callback records in
`src/rel/common_rel/misc_data.c`.

Entry 19 uses real decimal float literals for camera positions and rotations.
The encoder rounds them to binary32. It preserves the original arithmetic,
call order and branches; it does not simplify the program or invent a new
camera policy.

## Calling convention and control-flow details

Native calls reserve a result by loading frame slot zero, push the named
native index and typed argument values, then enter the existing native-call
handler. The handler writes its raw return register into that reserved slot.
Standalone expressions discard their result; waits and logs use the distinct
void cleanup convention. The source compiler preserves both conventions.

The native registry determines integer versus float register arguments. C
prototype spelling elsewhere in the decompilation is not substituted for
that runtime table. One entry-12 call deliberately supplies a sixth argument
to `heroMoveAddAutoEvent`: the runtime type table ends after five arguments,
so the sixth value is ignored by native dispatch. The source documents this
case and enables extra arguments only for that declared native.

GS `logical_and` evaluates both expressions. The 11 such operations stay eager;
nested `if` statements retain their separate conditional evaluation. The
encoder does not convert either form into the other. Likewise, the original
compiler's implicit end-of-function returns remain after explicit returns,
and the terminal bank exit guard is retained.

An independent review checked all **74 branch targets** against instruction
boundaries, the complete program interval, native bindings, operand access,
assignment conversions, nested conditionals and eager logical AND. This
review found no unresolved instruction format or opaque program interval.

## Runtime relocation and the final diagnostic

There are no linker relocations in the generated object. The bank's one
**runtime** relocation is different: `cms_RegisterScript` adds the loaded
bank address to the word named by the header's relocation index.

| Bank-relative field | Verified value |
|---|---:|
| Relocation-table entry | 6,976 |
| Initial word at that site | 8,096 |
| Diagnostic string begins | 8,096 |
| Diagnostic extent including NUL | 23 bytes |
| Final alignment suffix | 1 zero byte |

The encoder calculates that string position and emits the initial
bank-relative word. It reports the same `6976 → 8096` pair as the existing
header and private original. The four zero bytes preceding the named
diagnostic represent the aligned empty-string storage.

The readable `unsupported_tv_room` literal is an internal, zero-argument ASCII
log. Its only caller is entry 19's unsupported-room branch, which restores
actor visibility and returns failure when no TV camera case applies. It is
not a localized message-group entry or an opaque text resource. Its readable
source, explicit NUL terminator and alignment suffix are included in the
7,964-byte reconstruction.

## Focused validation

The seven tests in `.github/scripts/test_gs_vm_script_source.py` pass:

- An independent synthetic stack evaluator checks loop/branch behavior,
  variables, mixed integer/float expressions, native argument registers and
  the return value.
- An eager-AND case checks that both native calls run even when the first
  result is false, including their separate result slots.
- A synthetic diagnostic checks the calculated bank-relative runtime fixup,
  string extent, NUL and alignment.
- Rejection cases cover raw/opcode escapes, unresolved symbols, invalid
  literal values, native argument types, duplicate indices, undeclared extra
  arguments and unsupported diagnostic formatting.
- Source-only cross-checks verify all 41 native bindings against the existing
  C registry and the generated layout against the existing typed header.

The tests contain no original program-byte fixtures. The separate private
native-object comparison supplies whole-region equality evidence. Source data
credit must come from this generated native object when it is actually linked;
the original fallback is not credited, and reconstructed script data does not
change the PowerPC function/code denominator.
