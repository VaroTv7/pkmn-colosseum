# Complete small-data arrays and interior names

## Status and scope

Local checks with the pinned GC/1.2.5n compiler and objdiff 3.6.1 verify three
native source sections and their guarded comparison views: 200 of 200 data
bytes match across three complete units. The earlier source prefix accounted
for 172 of those bytes, so this proposal reconstructs another **28 physical
bytes**. The independent damage-operand investigation below also verifies
the remaining **12 physical bytes** as two separate scalar constants and
four bytes of linker alignment. Together, these local checks cover all 40
previously retained small-data bytes. Private CI also compiles all source
owners and retains all 8,677 exact function identities. An isolated link using
only source-derived alias copies with their `.comment` sections removed also
produces the exact canonical DOL hash. The normal production build and all
26 unchanged canonical output hashes are **pending private-input CI**. These
checks are not a completed project build or runtime test.

The native definitions retain complete C arrays. The existing symbol map
describes some of these arrays as smaller, adjacent historical fragments.
Defining one C object for each fragment would make existing array indexing
exceed the actual C object bounds. Keeping the complete objects and supplying
their original interior linker names resolves that problem without moving,
duplicating or removing storage.

| Source interval | Native storage newly reconstructed | Original interior names |
| --- | --- | --- |
| `0x804788CC–0x804788D8` | Two `s16[2]` coordinate arrays and one `u8[4]` filter-choice array | `lbl_804788CE` at coordinate-array offset 2; `lbl_804788D2` at coordinate-array offset 2 |
| `0x80478950–0x80478958` | One `u8[4]` controller-mask array and one `s8[4]` controller-order array | `lbl_80478951` and `lbl_80478955`, each at array offset 1 |
| `0x80478D78–0x80478D80` | One initialized `u8[8]` battle flag array | `lbl_80478D7B` at offset 3; `lbl_80478D7D` at offset 5 |

The first interval extends the existing `sdata_80478820.c` owner from 172 to
184 bytes. The other two owners each contain eight bytes. All original mapped
names and the full physical interval union remain present; the data
denominator is unchanged.

## Source evidence for the array bounds

`src/game/menu/pda_exact_800492CC_gc20.c` declares both coordinate arrays as
`s16[2]` and copies elements zero and one into the complete `lbl_804788C8`
coordinate pair. `src/game/menu/pda_exact_80040308.c` declares
`lbl_804788D4[4]` and indexes it by the selected PDA page. These declarations
and uses determine the source types independently of the original fragment
sizes. The private original bytes then verify the initializers and their
complete compiled layout.

`src/game/menu/cardesavedata.c` declares `lbl_80478950` as `u8[4]` and
`lbl_80478954` as `s8[4]`. Its controller-selection loops index the four mask
entries and iterate over `sizeof(lbl_80478954)` for the traversal order. The
definitions therefore retain both four-element arrays. Older unused scalar
declarations in other source carves do not establish smaller storage bounds.

`src/game/fight_seq.c` saves, clears and restores all eight elements of
`lbl_80478D78` in loops bounded by eight. The active battle-handler carves
also access its individual elements through index seven. The new definition
is one initialized `u8[8]`. Twenty-four stale `extern` declarations in 19
source files were corrected from `[1]` to `[8]`, without changing any function
computation or executable statement. These declaration-only changes require the full native
code-identity checks in CI.

The directly changed battle source owners are:

```text
game/fight_range_80211A00_exact_80214450.c
game/fight_range_80211A00_suffix_80216A58.c
game/fight_range_802128D0.c
game/fight_range_8021A338.c
game/fight_range_8022D6BC.c
game/fight_range_exact_80217018.c
game/fight_range_exact_80217E20.c
game/fight_range_exact_8021A6CC.c
game/fight_range_exact_8021C0F4.c
game/fight_range_exact_8021CB58.c
game/fight_range_exact_8021D9C0.c
game/fight_range_exact_80222110.c
game/fight_range_exact_80222C44.c
game/fight_range_exact_80223A24.c
game/fight_range_exact_802247D0.c
game/fight_range_exact_8022DCB8.c
game/fight_range_exact_8022FE20.c
game/fight_range_exact_80233DB0.c
```

The remaining declaration is in the included `game/fight_seq.c`. Its current
registered wrappers are `fight_seq_candidate_80211170.c`,
`fight_seq_r54_80211810_prefix.c`, `fight_seq_r54_80211830_gc13_o4p.c` and
`fight_seq_r54_802118FC_suffix.c`; the appropriate conditional body is selected
by each wrapper. The full report must retain all original function identities.

### The byte at `0x80478D7C`

There is no original mapped symbol named `lbl_80478D7C`. The split target
describes this byte with the hidden generated zero-gap name
`gap_07_80478D7C_sdata`. A scan of all relocation sections in the 2,203 current
main target objects finds no named `lbl_80478D7C` reference. The two old scalar
references in `fight_seq.c` are inside
`#if !defined(PR424_FIGHT_SEQ_SPLIT)` and are excluded by the current candidate
includes. Active carved functions access this byte through the complete flag
array. The link view therefore adds only the original D7B and D7D names; D7C
remains part of the real eight-byte array, with generated gap metadata only in
the comparison view.

## Native object, link view and comparison view

`tools/source_data_aliases.py` creates two separate views from an immutable
native compiler object. The original target also remains immutable. Its
registrations are the three JSON files in `config/GC6E01/data_aliases/`.

Before producing either view, the helper requires:

1. A single initialized `.sdata` section in both objects, with equal section
   type, flags, size and alignment; all allocated bytes must already match.
2. Equal relocation semantics and supported native CodeWarrior symbol
   metadata. Unknown native section metadata is rejected.
3. The native host symbol to be one global object with the registered full
   C-array size at the correct offset.
4. Every original interior name to have exactly its registered offset and
   original extent, entirely inside its host array. Existing native aliases,
   duplicate registrations and overlapping host arrays are rejected.
5. Complete, nonoverlapping coverage of each host by original fragments and
   independently verified generated zero gaps. Unregistered storage or a
   nonzero gap is rejected. Unrelated original data objects must retain their
   identities and full extents.

The **link view** preserves every native C symbol's value, size, binding and
type. It adds the explicitly registered original interior names as global
`STT_NOTYPE` labels with size zero. These labels allocate no storage and do
not divide the host array. The final link copy has no CodeWarrior `.comment`
section. The native compiler object retains its original metadata and full
bounds; the comparison copy also retains its compiler metadata. The link-only
removal prevents MWLD's compiler-specific object processing from stalling on
complete arrays with interior labels, as established by the isolated CI
experiment below.

The **comparison view** describes the same native bytes using the target's
historical nonoverlapping object fragments and verified generated zero gaps.
Only the registered host symbols' comparison sizes are reduced to their
historical fragment sizes; the remaining fragment metadata is appended. Each
host's fragment union is exactly its complete native-array interval. This
metadata partition allows objdiff to compare the existing target identities
without counting overlapping aliases as additional data. It is not the
native C type layout and is not used for linking.

Both views leave allocated section bytes, section allocation and alignment,
existing symbol indices and relocation records unchanged. Only
symbol/string/CodeWarrior-comment metadata and its physical ELF file layout
change. The production CLI requires an explicit `--objcopy` tool and invokes
`objcopy --remove-section=.comment` on a temporary copy of the verified link
view. Before writing either output, it independently checks all allocated
bytes, every symbol record and full extent, section type/flags/size/alignment,
ELF identity and flags, and all relocation records and their meaning. The only
permitted section removal is `.comment`; section names and file offsets may
be reserialized, and GNU objcopy's string-table entry size changes from one
to zero are accepted. Symbol string offsets and string-table contents still
must be identical. The helper requires distinct input and output paths and
never imports target payload into an output object.

The linked-address diagnostic can consume the same three registrations through
`tools/data_link_diagnostics.py --array-aliases config/GC6E01/data_aliases`.
It retains each historical map fragment size in the result and adds an explicit
source-layout expectation: the full native array size for each of the five
hosts, or size zero for each of the six interior labels. The registered host
must fit wholly inside its named native source owner, and unrelated mapped
objects cannot be absorbed. Incorrect addresses, source bounds or unrelated
symbol sizes still report mismatches. Without this optional argument, the
diagnostic keeps its existing map-size comparison unchanged.

The pinned compiler rejects GNU alias attributes. A weak-alias pragma probe
did not create the required definition. With normal object detection enabled,
DTK 1.8.3 re-infers positive-sized objects for the interior labels even when
the map proposes zero-sized labels; those inferred fragments overlap a full
array symbol. Global object detection remains unchanged. The narrowly
registered views preserve both the actual C array bounds and the existing
target identities instead.

## Reproduced local checks

The local probes compile the actual three source files with GC/1.2.5n,
`-sdata 8`, `-sdata2 0`, `-align powerpc` and the ordinary Gekko C settings.
The wrapper used to run the unchanged Windows compiler was a temporary local
wibo 1.2.0 executable because the repository-pinned wrapper could not start in
this environment. No repository tool version was changed.

| Native source section | Bytes | `.sdata` alignment | SHA-256 of the complete `.sdata` section |
| --- | ---: | ---: | --- |
| `sdata_80478820.c` | 184 | 8 | `fd48d9f551ba53562b58726b83157bab0f29af460d6b83c3e16ad5aa1f4eb4df` |
| `sdata_80478950.c` | 8 | 8 | `2493124f87133fdb86070e9695a17f043e93cf706caa9e0a8ef3e9f2f1820d72` |
| `sdata_80478D78.c` | 8 | 8 | `af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc` |

Each native section passed the strict byte, symbol-bound and relocation
checks against its private split target. Each comparison view then achieved
100% `.sdata` matching with the pinned objdiff CLI. A normal three-unit objdiff
report measures `total_data = matched_data = complete_data = 200`, with all
three units complete. This verifies the physical accounting and the 28-byte
gain without adding credit for overlapping link labels.

The helper's 19 synthetic tests cover complete native bounds, zero-sized
link aliases, exact comparison partitions, unchanged allocated bytes and
relocations, input-path protection, and rejection of incorrect bytes,
relocations, extents, alias registrations, gaps or compiler metadata. The
tests also check that intermediate link labels have all-zero CodeWarrior
records, positive-sized comparison fragments retain their active-object
records, and all pre-existing native records remain unchanged. The production
normalization tests permit only compiler-metadata removal and ELF metadata
serialization. They reject altered data, full host bounds, alias sizes or
offsets, relocations, alignment and ELF flags. A failed normalization leaves
both output files unchanged. The tests contain synthetic objects only:

```sh
python3 -m unittest discover -s .github/scripts -p test_source_data_aliases.py
python3 -m py_compile tools/source_data_aliases.py
git diff --check
```

### First full-link integration and label metadata correction

Private CI compiled all source owners and retained all 8,677 exact function
identities. The first final-output attempts stalled. A bounded four-variant
link probe isolated the problem to the three array-alias link copies:

| Private diagnostic variant | MWLD result | DOL result |
| --- | --- | --- |
| All current source inputs | Timed out after 30 seconds; zero-byte ELF | Not convertible |
| Replace only the three alias link copies with their original targets | Completed in 3.59 seconds | Exact canonical hash |
| Replace only the 17 battle-script source objects with original targets | Timed out after 30 seconds; zero-byte ELF | Not convertible |
| Replace both diagnostic groups with original targets | Completed in 3.57 seconds | Exact canonical hash |

Both successful diagnostic DOLs have SHA-256
`7e6c00a3bd632126d5466cbab856c63ac3c52a5da20b60dba7e756538152c9f4`.
These substitutions were isolated diagnostic files and never entered a
normal link or source-progress report. Their result isolates the alias
metadata failure; it does not validate the original alias link copies.

The first helper gave each added zero-size label the CodeWarrior record
`(alignment=1, visibility=0, active=8, reserved=0)`. That is an active-storage
record appropriate for the positive-sized comparison fragments. The existing
successfully linked `gTRKInterruptVectorTable`, `lbl_80003FF0`, `lbl_80004000`
and `gTRKInterruptVectorTableEnd` labels instead use `(0, 0, 0, 0)`.
Pinned DTK 1.8.3's `CommentSym::from` likewise gives unknown/label symbols
zero default alignment and does not set their active bit through `export_all`.

Changing only those six records to zero retained every symbol, byte and
relocation, but the next bounded CI run still stalled. A second experiment
therefore compared three source-derived representations in one run:

| Source representation | MWLD result | DOL result |
| --- | --- | --- |
| Original symbol order and zero label comment records | Timed out after 30 seconds | Not convertible |
| Remove only `.comment` | Completed in 4.331 seconds | Exact canonical hash |
| Order globals by offset, with paired comment records and remapped relocation indices | Timed out after 30 seconds | Not convertible |
| Reorder globals and remove `.comment` | Completed in 4.320 seconds | Exact canonical hash |

Both successful source-derived DOLs have the canonical SHA-256 listed above.
All candidate objects were checked before linking: 200 allocated bytes,
five complete native arrays, six global zero-size labels, all symbol
identities and bounds, `.sdata` flags and alignment, ELF flags and relocation
meaning were unchanged. The isolated original-target control also matched.
The experiment identifies removal of `.comment` as sufficient; production
therefore does **not** reorder any symbols.

The production CLI now applies this exact link-only normalization using an
explicit PowerPC objcopy path. A local run of that CLI on all three actual
pinned-compiler objects passes its strict validation, preserves all native
and original target inputs, and produces comparison objects byte-identical
to the existing 200/200 matching report. The five array hosts and six original
interior names remain in the existing `FORCEACTIVE` retention list. No
diagnostic substitution is used by the production build. Normal production
linking and all 26 unchanged canonical output hashes remain **pending
private-input CI**.

## Two independent damage constants and linker padding

The previously retained `0x80478D8C–0x80478D98` interval required a separate
investigation. The ELF relocation scan identified a leading 32-bit damage
operand but missed a second pointer encoded at an unaligned position in the
battle scripts. Decoding the typed memory operands across all 262 surrounding
script symbols identifies exactly two reads in this interval:

| Script instruction | Typed operand location | Referenced word | Established use |
| --- | --- | --- | --- |
| `lbl_80377531 + 259` (`0x80377634`) | `0x80377644` | `lbl_80478D8C` | `WS_STATUS_SET32`, fight-floor status kind 7, field `0x3E`: read one 32-bit damage value |
| `lbl_803767D1 + 149` (`0x80376866`) | `0x80376876` | `lbl_80478D90` | The same typed 32-bit damage read; this encoded pointer lacks an ELF relocation |

Existing status routing leads from fight-floor field `0x3E` through the
Pokemon status entry to the move's damage field. Each consumer reads one
word. The source therefore defines **two independent `u32` constants**, with
values 20 and 40, in `sdata_80478D80.c`. No relationship requiring a new C
array or a third element is inferred. The historical D8C object extent is
refined from 12 to four bytes, and the second proven word receives the
traceable address name `lbl_80478D90` with size four. No consumer operation or
encoded address changes.

No decoded typed operand in the 262-symbol scan refers to D94 or another
interior address. The last four original bytes, `0x80478D94–0x80478D98`, are
zero and contain no relocation. They form the alignment gap before the
existing D98 source owner's eight-byte-aligned `.sdata` section. As with the
earlier linker-padding ownership merges, the D80 source split extends through
the next unchanged owner start at D98. There is no additional C padding
object or initializer for this gap.

The pinned compiler emits a 20-byte `.sdata` section for the complete D80
source, at alignment eight. Its symbols retain these exact offsets and sizes:

| Symbol | Offset from D80 | Native size |
| --- | ---: | ---: |
| `lbl_80478D80` | 0 | 6 |
| `lbl_80478D86` | 6 | 2 |
| `lbl_80478D88` | 8 | 2 |
| `padding_80478D8A` | 10 | 2 |
| `lbl_80478D8C` | 12 | 4 |
| `lbl_80478D90` | 16 | 4 |

The separately compiled D98 source section also has alignment eight.
Consequently, the 20 native bytes followed by four linker zero bytes occupy
exactly D80 through D98 and match all 24 private original bytes. Their complete
physical-interval SHA-256 is
`da8d716c87b0b3022cd681ed70299ecb719c149d7783bcfa34153d782968a793`.

A private DTK split using the refined map and merged interval produces a
24-byte target section, including the hidden generated D94 padding gap. The
pinned objdiff CLI compares that target directly with the unmodified
20-byte native compiler object and reports
`total_data = matched_data = complete_data = 24`, with one complete unit.
No comparison metadata view or artificial storage is used for this owner.
The previous D80 source accounted for 12 bytes, so this owner contributes
another 12 physical bytes: eight bytes of independently typed constants and
four bytes of verified linker alignment.

Together with the three array owners, the four isolated reports account for
224 matched bytes, previously 184 source bytes, for a proposed 40-byte gain.
The physical denominator is unchanged. Full project CI must still verify
the new linked layout, native consumers and canonical hashes before this is
reported as a verified project-wide result.
