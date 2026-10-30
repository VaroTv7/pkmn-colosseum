# Remaining data matching

## Approved message-catalogue completion

On 2026-10-29 the maintainer explicitly approved completing the remaining
91,421 message-data bytes. This continuation represents their actual content
as readable UTF-8 text and named, typed formatting controls in
`src/rel/common_rel/message_catalog.json`, using the supplied private originals
for comparison. It is reconstructed message **data**, not newly authored
dialogue or additional native program code. The source compiler has no
original-file input or opaque byte-array escape.

The catalogue retains the same 13 physical owners, all 4,018 indexed entries,
three complete strings stored after indexed terminators, and two bytes of
final bank alignment. The existing 219 template entries are not counted
again. All 3,565,996 data bytes remain in scope. Independent source/native
comparisons and the pinned 13-owner report verify all 91,421 bytes exact and
source-complete. All 290 checker tests and 13 jump-table tests pass locally.
Full canonical build and fresh whole-project report acceptance are pending;
the verified 97.44% checkpoint below remains the baseline until those checks pass.
See [the catalogue evidence](recon/message_catalog.md).

## Verified script and small-data continuation

The normal private-input
[Build job](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40968205519/job/123777997002)
at source revision
[`456efababa4448e5b66c1c8ac336531c1e669536`](https://github.com/dougchansan/pkmn-colosseum/commit/456efababa4448e5b66c1c8ac336531c1e669536)
passes all **26 unchanged canonical hashes and direct original/rebuilt byte
comparisons**. It compiles and links the reconstructed programs, small C data
and message templates through the normal production path, with no diagnostic
input substitutions. All 34 zero-data layout checks, registered assembly
branch checks, metric integrity, strict topology freeze and README/report
checks pass.

The fresh report verifies **3,474,575 of 3,565,996 data bytes matched and linked
from source (97.43632%)**, with 2,258 complete units out of 2,272. All 8,677
tracked functions and all 2,504,940 tracked code bytes remain exact and
source-linked. This continuation adds **25,139 data bytes** beyond the merged
[PR #663](https://github.com/dougchansan/pkmn-colosseum/pull/663) baseline,
master `4cf5494422955e6f383b8470ae5e46dd5362fc4f`. That baseline's final checks
and [post-merge Build](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40953799950)
also passed at 3,449,436 matched and source-linked data bytes.

The same source revision's
[Regression Guard](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40968205600)
compiled the complete project and verified all 8,677 existing function
identities with no score regressions, removals, renames or boundary changes.
Quality Lint also passes. The normal Build report is byte-identical to the
earlier compiler report from
[Regression Guard 40960309403](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40960309403).
The build separates compilation from a bounded final-output step while
preserving all canonical checks. All 275 local checker tests pass.

### Linker compatibility evidence

The direct GNU data-object path initially omitted the ordinary assembler
path's `dtk elf fixup` compatibility step. The corrected path applies the same
source-only fixup. Independent validation of all 29 affected objects confirms
that all 17,135 data bytes, 207 object symbols, 299 relocations and section
alignments remain unchanged; the pinned subset report remains fully exact.

The [bounded link-isolation report](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40963988506/artifacts/12935439809)
identified the separate final-link failure. With the three new array-alias
views, MWLD timed out and left a zero-byte `main.elf`. Replacing only those
three inputs with original targets made MWLD finish in 3.59 seconds; keeping
all 17 generated battle owners and the other native source changes produced a
DOL with the canonical SHA-256
`7e6c00a3bd632126d5466cbab856c63ac3c52a5da20b60dba7e756538152c9f4`.
Replacing the battle owners alone did not resolve the timeout. These private
fallback variants are diagnostics only and never feed the normal build,
report or source credit.

Giving the six zero-size labels the zero CodeWarrior records used by existing
vector labels did not resolve the timeout. The
[source-derived representation experiment](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40966529539/artifacts/12938023071)
then tested explicit `.comment` removal, paired symbol/metadata reordering,
and both transformations. Removing only `.comment` linked in 4.331 seconds
and produced the canonical DOL hash above with all new source owners intact.
Reordering alone still timed out; combining it with metadata removal yielded
the same canonical result, so reordering is unnecessary.

The normal alias helper now removes that compiler-specific section only from
the source-derived link copy, using the configured GNU objcopy. It verifies
every allocated byte, full array and alias identity, relocation, alignment
and ELF flag before writing. The immutable native compiler object and the
comparison view retain their existing metadata and bounds. Temporary probe
steps and tooling have been removed from the final tree; their committed
history and metadata-only artifacts retain the experiment. The successful
normal Build above independently verifies this exact representation and all
26 canonical outputs. Its linked-data diagnostic verifies all five complete
array hosts and six zero-size interior labels at their expected addresses.
All 209 added symbols match: 195 battle-script symbols and 14 small-data
symbols. The 31 size mismatches and 19 missing symbols elsewhere in that
diagnostic are unchanged from the preceding verified build; there are no new
residual issues, address mismatches or ambiguities.

### Source gain and remaining data

| Reconstructed source | Additional bytes | Evidence |
| --- | ---: | --- |
| Semantic GS VM bank `0x0596` | 7,964 | [Structured programs, native signatures and runtime fixup](recon/common_script_0596.md) |
| Seventeen packed battle-script owners | 13,500 | [Typed commands, symbol extents and 299 real relocations](recon/battle_script_source.md) |
| Complete small-data arrays and damage constants | 40 | [Native object bounds, interior labels and natural alignment](recon/small_data_array_aliases.md) |
| Message controls, counter templates and existing-source reuse | 3,635 | [219 complete entries from semantic templates](recon/message_templates.md) |
| **Verified matched and source-linked gain** | **25,139** | **Full denominator retained** |

The pinned objdiff subset report verifies all 30 generated script/template
owners: 25,099 of 25,099 data bytes exact and source-complete, with no native
code or functions. Separate native-object reports verify all 40 small-data
bytes. The generated-source report SHA-256 is
`568f498367d1032a507365edcfc81ef5d48b5726e090b4a1ccbd5af4031001a7`.
Generated C, data assembly and objects remain ignored build outputs; authored
source and source-only compilers are the tracked inputs.

The measured residual is 91,421 message-content bytes in 13 explicit original
fallback intervals. Reconstructing a message decoder or its formatting rules
does not reconstruct the unique message contents. Those bytes remain in the
3,565,996-byte scope and receive no source or matching credit. README progress
and the topology freeze describe the verified normal Build report, whose
SHA-256 is
`c4e3995c1d8155a5b9536a4de02dae2580ff2b9a8a265cdcf4426e897680e09b`.
The [normal Build report artifact](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40968205519/artifacts/12939685347)
contains this report; its archive SHA-256 is
`5aaeaec12cf7377291735cafdca1893862d7dcd8288f8e8206d9814ffe9104a2`.
The [metadata-only diagnostics](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40968205519/artifacts/12937999603)
record the canonical output comparisons, zero-data layouts and linked symbols.
An independent audit of this fresh report verifies all 8,677 function
identities and the same physical interval union across all 26 modules: no
overlapping intervals, removed physical bytes, added physical bytes or renamed
functions. The code, function and data denominators are unchanged. The
separate 7,992-byte physical interrupt-vector fallback remains disclosed
below and receives no tracked-code or source credit.

## Verified PR #663 source result

The ninth private-input build verifies source revision
[`dcdfc947cd77221ff38159679f07e704be77d9e4`](https://github.com/dougchansan/pkmn-colosseum/commit/dcdfc947cd77221ff38159679f07e704be77d9e4).
Its [Build job](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40950775953/job/123717998521)
passes all 26 unchanged canonical output hashes and all 26 direct
original/rebuilt comparisons. All 34 zero-data layout checks, assembly branch
checks and metric-integrity checks pass. The
[report artifact](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40950775953/artifacts/12931237166)
contains `report.json` with SHA-256
`b4153fe0b68fdfdb1bb658bfeaa455c51d3514d1617fd4845a10b2a876b2c7e2`.

| Measure | Verified baseline | Verified continuation | Change |
| --- | ---: | ---: | ---: |
| Matched code | 2,504,940 / 2,504,940 bytes | 2,504,940 / 2,504,940 bytes | Unchanged |
| Exact functions | 8,677 / 8,677 | 8,677 / 8,677 | Unchanged |
| Source-linked code | 2,504,940 bytes | 2,504,940 bytes | Unchanged |
| Matched data | 2,970,480 / 3,565,996 bytes (83.30%) | 3,449,436 / 3,565,996 bytes (96.731346%) | +478,956 bytes |
| Source-linked data | 1,897,440 / 3,565,996 bytes (53.21%) | 3,449,436 / 3,565,996 bytes (96.731346%) | +1,551,996 bytes |

The verified report has 2,226 complete units out of 2,251. The baseline is
master `e354ba3f0475ac50af3b7d9dccc1f2855be8369c`, merged through
[PR #662](https://github.com/dougchansan/pkmn-colosseum/pull/662), whose
[master build](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40835427934)
also passes all 26 outputs. Its report SHA-256 is
`898380a43cce0515e7936ccc2fbf6c4a0cf2d8d3d058196242b83e769a646114`.

An independent audit of the baseline and new reports verifies all 8,677 function
identities and the physical interval union unchanged across all 26 modules: no overlapping
intervals, removed physical bytes, added physical bytes or renamed functions.
The 3,565,996-byte data denominator is unchanged. The historical tracked-code
denominator remains 2,504,940 bytes; the separate 7,988-byte interrupt-vector
template and four-byte alignment padding remain explicit original fallback
outside that tracked-code denominator. Those 7,992 physical bytes are retained
and receive no function, matching-code or source-linked credit.

The ninth Build established the source result above. The subsequent
documentation and topology-freeze refresh passed all required checks on the
final PR #663 head, `2e2b83e8ee7e6d67ada2923d0fd7c76d6f98e387`.
The merged master tree is identical to that tested tree, and its post-merge
Build also passed.

## Remaining data at the PR #663 baseline

All 116,560 remaining data bytes use original fallback and receive no matching
or source-link credit. They remain in completion scope and the denominator.

| Remaining group | Bytes | Location or next reconstruction requirement |
| --- | ---: | --- |
| Message storage | 95,056 | Two `common_rel` message groups; typed headers and indices already reconstructed |
| GS VM script storage | 7,964 | `common_rel` bank `0x0596`; typed structural prefix already reconstructed |
| DOL script data | 13,500 | Remaining packed battle-script owners; preserve instruction and relocation semantics |
| Small-data objects with interior names or unresolved extents | 40 | Four complete fallback intervals listed below |
| **Total** | **116,560** | **Full original data scope retained** |

| Remaining small-data interval | Bytes | Reason for fallback |
| --- | ---: | --- |
| `0x804788CC–0x804788D8` | 12 | Complete coordinate arrays with interior labels, plus following aligned storage |
| `0x80478950–0x80478958` | 8 | Four-element controller-mask and port-order arrays with interior labels |
| `0x80478D78–0x80478D80` | 8 | One eight-element battle flag array with interior labels |
| `0x80478D8C–0x80478D98` | 12 | Leading damage operand understood; complete mapped extent unresolved |

## PR #663 build history

The continuation is tracked in
[PR #663](https://github.com/dougchansan/pkmn-colosseum/pull/663). Its private-input
builds distinguish exact source objects from complete output verification:

| Checkpoint | Established evidence | Remaining integration issue at that checkpoint |
| --- | --- | --- |
| First build | All 8,677 functions remained exact; four complete resource spans matched existing source definitions. | Canonical outputs and 32 of 34 zero-owner layout checks failed. |
| Third build | All 34 zero-data owners passed native symbol-layout checks, covering 655,080 bytes; 423,928 shared resource bytes matched from native ProDG source. | DOL linker layout and complete outputs still required correction. |
| Fifth build | Both typed message prefixes matched and linked; the complete 561,032-byte resource region was byte-identical, including fallback. | `main.dol` and `common_rel.rel` failed; the other 24 outputs passed. |
| Sixth build | The 156-byte GS VM prefix matched and linked; `main.dol` and 24 REL outputs passed canonical hashes and direct comparisons. | Only `common_rel.rel` differed: 149 byte positions in 84 sound-table pointer addend words. |
| Seventh build | No fresh compiler/report measurement. | A split at `0x80478D86` required two-byte alignment before compilation could proceed. |
| Eighth build | All 25 REL outputs, including `common_rel.rel`, passed canonical hashes and direct comparisons. All 8,677 code functions remained exact. | `main.dol` differed in the new `sdata_80478D08.c` owner; a subsequent consumer audit also identified incomplete source object extents. |
| Ninth build | All 26 outputs, all 34 zero-data layouts and the report-integrity audit passed. Corrected source object bounds preserve all function identities and physical coverage. | Source matching is verified; the final documentation/freeze revision still needs its required PR checks. |

Earlier partial builds were diagnostic checkpoints. The leading result uses
the ninth report and complete-output evidence, including the corrected object
boundaries and explicit fallback intervals.

## Work remaining at the baseline

| Group | Units | Unmatched data | Data still linked from originals |
| --- | ---: | ---: | ---: |
| Original `common_rel` resource region | 1 | 561,032 | 561,032 |
| DOL units without source | 53 | 28,948 | 28,948 |
| Existing partly matched source | 10 | 5,536 | 1,264 |
| Exact but unlinked source | 67 | 0 | 1,077,312 |
| Total | 131 | 595,516 | 1,668,556 |

The initialized DOL gaps contain SDK assertions and runtime state, small
initialized globals, and packed battle bytecode. Embedded bytecode pointers
must retain their relocation semantics; these regions must not be interpreted
as arbitrary string pools.

## Source ownership and zero-storage reconstruction

The initial proposal selected 66 already exact data candidates, totaling
1,077,180 bytes, for source linking. Isolated section equality did not prove
their final layout. Native compiler and linked-address diagnostics identified
the necessary retention, declaration-order and alignment corrections.

The initially deferred 132-byte `game/data/data_802EE06C.c` switch table starts four
bytes past an eight-byte boundary. Its existing definition is now included
after the generated tables in `menu_middle_r59_8006CCC0_o1.c`, at that owner's
`.data + 0xBC`. This retains the original `0x802EE06C–0x802EE0F0` interval and
relocation targets without introducing a separately aligned section.

Fourteen newly reconstructed zero-storage owners cover 13,168 bytes using
existing symbol-map boundaries. The first build exposed reversed existing BSS
declarations and redundant explicit padding. Corrected declaration order,
scalar or natural padding, and explicit byte alignment preserve the recorded
placements. Together with twenty existing BSS owners, all 34 owners passed
the third build's native layout checks and pass again in the ninth after the
consumer-bound corrections described below.

`lbl_8047C9E4` retains its recorded five-byte string extent; the following
seven zero bytes remain section padding. Four separate unnamed alignment gaps
are accounted for in the ownership table below. These changes preserve every
physical byte in the original denominator.

## Validation requirements

All-zero bytes can compare exactly even when variables have moved. Each
zero-storage owner therefore needs a compiled-symbol address and size check,
in addition to the ordinary report. `tools/verify_zero_data_layout.py` derives
these expectations independently from `symbols.txt` and `splits.txt`; it checks
all 1,440 existing symbol boundaries and the intervening zero-padding ranges in
the fourteen new owners. It also checks the twenty existing BSS owners now
linked from source, covering another 641,904 bytes and 136 existing symbols.
The same offset, size, binding, section and alignment requirements apply to both
groups. Other candidates need actual source and target section, symbol,
relocation and alignment comparison.

The full acceptance sequence is:

1. Configure and build all source objects and a fresh report with the private
   original inputs.
2. Verify zero-storage symbol layouts and investigate remaining data
   differences using the metadata diagnostics.
3. Build all outputs and pass all 26 unchanged canonical hashes and direct byte
   comparisons.
4. Preserve every baseline code/function identity and all physical data
   intervals; explain every intentional split change without reducing the
   code, function or data denominators.
5. Refresh the strict topology freeze, README and this work record from the
   verified report, then pass Build, Quality Lint and Regression Guard on the
   final PR head before merging.

The ninth source build and its integrity audit established steps 1–4 for
PR #663. Its final head and post-merge Build also passed step 5. The normal
source-continuation Build above independently passes steps 1–4 with the
measured topology freeze and README table. All required checks continue to
apply to the final PR #664 head before merging.

## Source metadata and linker layout

`source_data_exports.txt` retains only the source definitions introduced by
this continuation. Packed boundaries retain explicit byte-array alignment;
section starts retain the original linker alignment.

The initial audit found 21 initialized data owners starting four bytes past
an eight-byte boundary. MWCC emits eight-byte section alignment even though
their actual C objects require at most four. The same issue applies to some
later reconstructed owners. `tools/source_object_metadata.py align`
creates a separate source-link object after requiring identical section
bytes, every original data-symbol extent, and relocation semantics. It reads
the compiler's per-symbol alignment records and rejects any real object that
requires more than four-byte alignment. Only the section alignment and its
section metadata change. The native object remains the report input, and
the original target remains untouched.

One pointer-array owner also has MWCC's local, untyped, zero-sized
`...data.0` section-base marker. A duplicated eight-byte alignment on that
marker may be lowered with the section alignment only when real object
extents and verified zero gaps cover the entire section. It is explicitly a
section marker, not an additional reconstructed C object. No code, data,
symbol offset, symbol size, symbol binding, or relocation record is changed
by the link view. This is compiled source with a documented linker-layout
adjustment, and remains subject to all canonical hashes and byte comparisons.
The metadata format follows the pinned toolkit's
[`MWComment`/`CommentSym` definitions](https://github.com/encounter/decomp-toolkit/blob/v1.8.3/src/util/comment.rs).

The pinned objdiff v3.6.1
[`report_object` implementation](https://github.com/encounter/objdiff/blob/v3.6.1/objdiff-cli/src/cmd/report.rs)
constructs a default symbol mapping instead of using each unit's configured
mapping. Six comparison-only views therefore give existing anonymous or
compiler-disambiguated function-local data objects their established target names. This
changes only symbol-name/string-table metadata. All source bytes, symbol
values and sizes, bindings, and relocation records remain unchanged; native
objects remain linker inputs. The standard report generator still performs
the actual byte/relocation comparison, with its full original denominators.

## Unnamed linker-alignment gaps

Four previously separate fallback intervals contain only alignment padding.
Their ownership is extended from the preceding source section to the unchanged
start of the next source section. No C object, initializer, symbol name, symbol
size, or next-owner address is added or changed.

| Padding interval | Bytes | Preceding source owner | Alignment of the next owner |
| --- | ---: | --- | --- |
| `.data` `0x803634EC–0x803634F0` | 4 | `hero_savedata_exact_80129280.c` | Eight-byte compiler data-section alignment for `hero_bios_exact_8012A450.c` |
| `.data` `0x8036BFA4–0x8036BFC0` | 28 | `particle.c` | `psdisp.c` declares `lbl_8036BFC0` with `aligned(32)` |
| `.bss` `0x804657AC–0x804657C0` | 20 | `hsd/tev.c` | `hsd/video.c` declares `lbl_804657C0` with `aligned(32)` |
| `.sbss` `0x8047B490–0x8047B4A0` | 16 | `THPVideoDecode.c` | `THPDec.c` includes the `Ydchuff` declaration with `ATTRIBUTE_ALIGN(32)` |

The fifth private-input diagnostic verifies zero bytes and no relocations in
both initialized gaps. The other two gaps are zero-initialized section storage.
A symbol-map audit finds no real object intersecting any of the four intervals;
all adjacent objects already match in that build. The nonexistent
`game/data/data_803634EC.c` registration is removed because its entire four-byte
interval now belongs to its preceding source owner. The other three intervals
were automatically generated fallback units.

All 68 physical bytes remain in scope. This is linker-generated padding owned
by the surrounding compiled source. The sixth build's canonical main executable
verified that layout after `-sdata 0` restored a two-byte padding array in the
merged developer-string owner to its original initialized-data section. Later
DOL additions remain subject to the same complete-output check.

## Native sound tables and their comparison view

The first private build established exact source literal-pool hashes and
explicit relocation destinations for `snd_song_table.c` and
`snd_sample_table.c`. An intermediate attempt gave the existing literals named
definitions so objdiff could measure them. That approach changed SN's stored
pointer addends, even with local `static` linkage. The sixth build isolated
the resulting REL mismatch to 149 byte positions in 84 pointer words. That
source change was abandoned.

Both sound C files are restored byte-for-byte to the verified baseline.
`tools/prodg_comparison_object.py` creates a separate source-comparison copy;
the native compiler object remains the actual linker input. Before creating
the copy, the tool requires identical section extents and relocation semantics,
normalizes only duplicated explicit section-relative RELA addend words, and
requires every remaining allocated byte, including padding, to equal the target.

For unlabeled native pools, literal starts come exclusively from source
`R_PPC_ADDR32` relocation destinations. They must cover the pool from offset
zero, and each interval must contain one terminated source string followed by
at most three zero alignment bytes. Generated names and sized object symbols
are appended only to the comparison copy. Existing symbol indices, symbol
records and relocation records remain unchanged. No target payload or target
symbol names supply the new metadata.

The eighth build verifies both complete source owners through this view
(2,400 song-table bytes and 376 sample-table bytes), while the untouched native
objects reproduce the canonical `common_rel.rel`. The comparison view neither
changes linker inputs nor promotes an incomplete owner. Synthetic checks cover
unlabeled pools, symbol-index preservation, invalid padding and missing
terminators, name collisions, and separate report/link paths.

## SDK diagnostics and small OS state

Three additional source owners reconstruct five SDK strings, covering 308
initialized bytes with their padding. `DVDRead` and `DVDSeekAsyncPrio` already
reference the two diagnostics in `dvd/dvdfs_range_800A4D28.c`; their wording
follows the existing adjacent `DVDReadAsync` diagnostic. The DVD, PAD and ARQ
version pointers already identify the relevant SDK components. Their build
stamps are recorded in `config/GC6E01/symbolmap/strings.json`, and follow the
same version format as the existing OS, SI, AI, AR and DSP source definitions.

| Original interval | Reconstructed definitions | Complete SHA-256 |
| --- | --- | --- |
| `.data` `0x80311A24–0x80311AC8` | DVD read/seek diagnostics and DVD build version | `affdfd28135a877801c76d43f1c74d98d40463db2f181e30b239fbb44ad3f1b2` |
| `.data` `0x803124B8–0x80312500` | PAD build version | `19561f5dbc84f3239f5f4deb8dde4c603d8b3fbb2945bd7d91c7e172cf44e015` |
| `.data` `0x803125A0–0x803125E8` | ARQ build version | `5fd17a9ea3f19b12b48fd826603a9e67049e1cab2f198568750a1ce4267fe810` |

The literal lengths, individual hashes, zero-padding ranges and absence of
relocations agree with the fifth private-input diagnostic. The DVD owner
uses the strict source-only four-byte alignment view. The four-byte gap before
ARQ's eight-byte-aligned start is assigned to the preceding existing AR version
source owner; no extra variable is invented for that linker padding.

The German and Dutch DVD fatal-error strings are reconstructed from text
already recorded in `config/GC6E01/symbolmap/strings.json`, following the
existing English diagnostic source. Their complete 156-byte and 140-byte
regions include three zero-padding bytes each and reproduce the original
section hashes. The latter uses the same strictly verified four-byte
source-link alignment as other carved data owners.

The 20 bytes at `.sdata` `0x8047897C–0x80478990` are reconstructed from the
existing OS interfaces: the `OSRegisterVersion` report format, the signed
current-heap handle initialized to `-1`, and the low-arena pointer initialized
to `(void*)-1`. `sdk_range_8009A2D8.c` and `sdk_range_800C470C.c` declare the
heap handle as `s32`; its map extent is refined from eight to four bytes, with
the following independently verified zero word retained as padding.
`OSArena.c` supplies the arena pointer's type and accessors. Both explicit
padding words remain address-named storage. The complete reconstructed bytes
hash to `bd295bb340e3d031a8f97123ad3cddbd8eded5ffbec0fbbe6a47806632b3c444`,
equal to the fifth diagnostic, with no relocations.

These small definitions are included after the existing OS source in
`sdk_r48_80099790_suffix.c`, extending its already aligned `.sdata` section
without editing any function. The eighth build verifies the SDK owners from
native compiled source. The ninth build verifies their integration in the
canonical main executable with unchanged code identities and physical coverage.

## Small game-state source

Three source owners reconstruct 316 of the 336 bytes at
`0x80478820–0x80478970`: `sdata_80478820.c`, `sdata_804788D8.c` and
`sdata_80478958.c`. Typed scalar and array initializers describe task flags,
menu state, counts and small lookup tables. Where an existing map object
includes a zero suffix, its complete storage extent is retained in the typed
array without an invented runtime meaning.

The consumer audit after CI8 identifies `lbl_804788C8` as a two-element
coordinate array. Its four-byte definition and map extent absorb the verified
zero halfword at `0x804788CA`. Two other coordinate arrays and two controller
tables have interior mapped names that require a verified alias mechanism.
Their complete storage remains fallback over `0x804788CC–0x804788D8` (12 bytes)
and `0x80478950–0x80478958` (8 bytes). All original names, addresses and all 336
physical bytes remain in scope. The source and caller evidence is recorded in
[`data_object_bounds.md`](recon/data_object_bounds.md).

The existing implementations provide independent context for the data:

- `menuFight.c` and `menuPokemon.c` identify four-choice menu IDs through
  their switches: `0xC4–0xC7` and `0xE93–0xE96`.
- `pda_exact_80040308.c` indexes the four filter-choice counts, and
  `pda_exact_8004A7A8.c` uses the caption pulse phase of pi divided by six.
- `menuCB_BattleStart.c` indexes the four battle-indicator sprite IDs.
- `cardesavedata.c` uses the eight MSB-first bit masks. Its four controller masks
  and controller visitation order are each four-element arrays; their mapped
  interior labels are retained in the eight-byte fallback described above.
- `menu_bios_range_8005D7F8.c` supplies the record sizes and uses the table
  counts. The first sprite and item counts equal the existing source table
  extents divided by `0x18` and `0x1C`, respectively. Their additional stored
  words remain in their mapped objects without a new semantic claim.

The actual C initializers have been checked against the sixth private-input
diagnostic: every original symbol's bytes hash equally, and the complete
section SHA-256 is
`ab20ac8aec560e027d89020470d4fd6470bd18439f7ef3467a3e4e72dcd6f313`.
The interval has no relocations. The local layout calculation uses the
independently probed MWCC scalar, array and explicit alignment rules. The eighth
build verifies the native 336-byte candidate's bytes, but the subsequent
consumer audit found object-bound conflicts. The ninth build verifies the
corrected 316-byte source ownership: 172, 120 and 24 bytes from the three
native source owners, all exact and source-linked. The other 20 bytes remain
fallback. No function source, original name or physical data interval is removed.

The same audit refines two zero-state definitions to their actual complete
types: `lbl_8047AD04` is a four-port `u8[4]`, and `lbl_8047A60C` is a four-byte
uploader boot key. Each absorbs an existing three-byte zero gap. The strict
zero-layout checks derive the revised extents from the map; the full physical
intervals and existing consumer functions stay unchanged. These corrected
layouts pass in the ninth build.

The battle/purification reconstruction and its precise owner boundaries are
recorded separately in
[`sdata_80478D08_reconstruction.md`](recon/sdata_80478D08_reconstruction.md).
Their typed counts, version pointer and sequence pairs come from
existing source consumers and complete metadata hashes. The intervening
status operands remain subject to the individual reconstruction evidence in
that record. The eighth build's DOL failure was isolated to the first new
owner. The ninth build verifies the corrected 112-byte, 12-byte and 28-byte
source owners, totaling 152 exact and source-linked bytes, with the complete
main executable canonical. The remaining 20 bytes stay fallback.

The eight-byte flag block at `0x80478D78–0x80478D80` retains explicit original
fallback in this checkpoint. `fight_seq.c` saves, clears and restores all
eight elements of `lbl_80478D78`. Its interior address labels at offsets
3, 4 and 5 therefore identify elements of one real `u8[8]` object. Defining
separate one-byte objects for those labels does not satisfy the array extent
used by the existing consumers, even if the linked bytes match.

A source follow-up must define the full array and preserve the existing
`lbl_80478D7B`, `lbl_80478D7C` and `lbl_80478D7D` references through a verified
interior-label mechanism. The existing constant-export helper only renames
an already emitted `.sdata2` literal; it supplies no such `.sdata` aliases.
No new alias mechanism is introduced for this checkpoint. All eight physical
bytes remain in the denominator and receive no source credit while using
fallback.

The subsequent 152-byte initialized-zero source owner at
`0x8038FF64–0x8038FFFC` has independent zero hashes and recorded symbol extents.
Its evidence and layout guard are in
[`initialized_zero_8038FF64.md`](recon/initialized_zero_8038FF64.md).
It was added after the eighth build. The ninth build verifies all 152 bytes
as exact and source-linked, including the guarded source-link alignment and
canonical main executable.

## Resource scope and verified source coverage

The 561,032-byte resource region was original fallback in the verified
baseline, as documented in [`REL_MODULES.md`](REL_MODULES.md) and the corrected
import in PR #646. It remains in the full data denominator and completion scope.
Independently reconstructed implementations, typed data definitions and
verified reuse of existing source may earn matching and source-link credit.
Each claimed gain requires source-object, relocation and canonical-output
evidence. Equal lengths alone do not prove equal data or correct relocations.
An implementation of a resource format does not by itself reconstruct its
contents; copied resource payloads and original-object fallback must not be
relabelled as reconstructed implementation progress.

The first private-input build for [PR #663](https://github.com/dougchansan/pkmn-colosseum/pull/663),
head `35a32f20260da97b2af02b28bf8b31e73cd3cea4`, established equality of four
complete resource spans with definitions already present in the DOL source:

| Existing DOL definition | Common REL `.data` offset | Bytes |
| --- | ---: | ---: |
| `lbl_8027A500` | `0x2D2C` | 273,760 |
| `lbl_802BD260` | `0x45A94` | 14,928 |
| `lbl_802C0CB0` | `0x494E4` | 60,256 |
| `lbl_802CF810` | `0x647B4` | 74,976 |

The known eight-byte font header at `0x45A8C` was also verified as the
`{0xFFFF, 0, 0, 0}` terminator recognized by `GSmsgFontOpen`. The source shares
the four existing definitions through `shared_font_data.c` and
`shared_message_data.c`, adding only that typed structural terminator. It
reuses 423,928 bytes without duplicating the font or message initializers.

The normal DOL preprocessor output is unchanged. In the REL font view only,
31 existing symbolic pixel words resolve to their canonical address values,
because these words are data rather than REL imports. Four-byte alignment
retains each original resource boundary. A 32-bit host compiler sanity check
found the expected symbol offsets, no relocations, and all five resource
hashes equal after translating the host's integer endianness. This is not a
canonical-output result. The third private-input build independently verified
all 423,928 bytes from native ProDG source objects. The eighth build verifies
their integration in the canonical REL, and the ninth reproduces that result
while also passing the main executable.

The other 137,104 resource bytes contain two message groups and a GS VM
script bank. The bounded message diagnostic establishes their structure
without publishing message text. Two additional source owners reconstruct
the headers and key/offset indices, totaling 33,928 bytes:

| Complete original message resource | Original bytes | Typed header/index | Adjacent original storage |
| --- | ---: | --- | --- |
| `0x58044–0x647B4` | 51,056 | `0x58044–0x5BF64` (16,160 bytes; 2,018 entries) | `0x5BF64–0x647B4` (34,896 bytes) |
| `0x76C94–0x89CFC` | 77,928 | `0x76C94–0x7B1FC` (17,768 bytes; 2,219 entries) | `0x7B1FC–0x89CFC` (60,160 bytes) |

This is an intentional ownership refinement of two previously opaque
aggregate symbols. Their original names and addresses remain on the typed
prefixes; new symbols identify the immediately adjacent storage. No gap,
overlap, omitted byte or resource-pointer change is introduced. Entry offsets
remain relative to each unchanged resource base, as required by
`GSmsgFindMessage`. The complete resource hashes remain
`e38470739c2815a81041f140d3f4e019b942d016f64f0cb3ac48c4b6c4211778`
and `0185880becce6f0bb4a3d55666a48124bfb2a8348150b8d628210847e7d1f754`.

The existing DOL header convention supplies the reserved fields, and the
recorded keys and offsets reproduce each entire original prefix hash:
`2f7c61218b1523952a9d2f2e8d97b04adc47fbfbf82097fa92a5f972567fba49`
and `f3e702439d6589668cd0dfff9e0fd72f47ec5c53b1ea7378f8d9343ae332f1c0`.
A host compiler layout check also reproduces these hashes with four-byte
alignment and no relocations after translating integer endianness. The fifth
private-input build independently verified both prefixes as 100% exact and
source-linked with ProDG. It also proved the complete 561,032-byte resource
region equal in the rebuilt REL, including every fallback interval, with
SHA-256 `8e3aacaee0aea8b9b2d90a933f65d184cf007cf0b12ac4ec77cf6e8a3e56c78e`.
The sixth, eighth and ninth diagnostics reproduce that complete-region hash,
and the eighth and ninth builds pass the complete REL. Region equality includes
fallback and cannot assign source credit to those bytes.

The GS VM diagnostic identifies another reconstructible 156-byte prefix:
the 24-byte bank header, 27 relative function offsets (108 bytes), one
relocation-site offset (4 bytes), and five zero-initialized globals (20 bytes).
`script_structure_89CFC.c` defines that typed source over `0x89CFC–0x89D98`.
The original resource base remains unchanged; a new adjacent original-storage
symbol covers `0x89D98–0x8BCB4` (7,964 bytes), retaining the complete original
8,120-byte bank. All four structural interval hashes match the private-input
diagnostic, and their combined source prefix hashes to
`d28fdd2d3b968555026b7e9d82d92cfa5d40e2675935dec2ded1794e147417a8`.
The sixth private-input build verifies the native ProDG prefix as 100% exact
and source-linked, and the complete 8,120-byte bank remains byte-identical.

The current resource ownership is therefore:

| Resource coverage | Bytes | Evidence |
| --- | ---: | --- |
| Shared existing definitions and typed font terminator | 423,928 | Native source verified in the third build |
| Typed message headers and key/offset indices | 33,928 | Native source verified in the fifth build |
| Typed GS VM header, indices and zero globals | 156 | Native source verified in the sixth build |
| **Source-produced subtotal** | **458,012** | Canonical REL and complete-region equality, retained in the ninth build |
| Message storage still using fallback | 95,056 | Full intervals retained; 68 bytes are unlinked reuse candidates |
| Script storage still using fallback | 7,964 | Function-start intervals known; bodies not reconstructed |
| **Complete resource region** | **561,032** | **Every physical byte remains in scope** |

The 103,020 fallback bytes receive no source credit. The searches found no
complete script-function interval already represented in the searched source
data. That is a reuse result, not proof that the scripts cannot be reverse
engineered. Further gains require independently reviewed source, complete
interval comparison and preserved bank/resource boundaries.

## Diagnostic outputs and attribution

`tools/data_match_diagnostics.py` records section and symbol sizes, alignment,
hashes, relocation identities and source comparison results. Its full-output
diagnostic compares all 26 manifest outputs against their original files and
canonical hashes. Bounded changed intervals report offsets and sizes, and
per-owner comparisons locate remaining `common_rel` data differences.
`tools/resource_message_diagnostics.py` records resource structure, complete
region equality and reuse candidates in existing source-backed DOL spans.
These public diagnostics exclude payload bytes, message text and disassembly.

Count-Sheep's original campaign history and contributor credit remain intact.
The rendered page for the
[verified source commit](https://github.com/dougchansan/pkmn-colosseum/commit/dcdfc947cd77221ff38159679f07e704be77d9e4)
lists both `dougchansan` and `Count-Sheep` as authors, confirming that the
continuation's coauthor credit is linked to the contributor's GitHub account.
The original donor history remains an ancestor. No runtime or gameplay result
is implied by data matching.
