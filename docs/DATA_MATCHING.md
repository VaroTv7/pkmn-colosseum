# Remaining data matching

## Verified starting point

The continuation starts from master
`e354ba3f0475ac50af3b7d9dccc1f2855be8369c`, merged through
[PR #662](https://github.com/dougchansan/pkmn-colosseum/pull/662).
Its [master build](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40835427934)
passes all 26 canonical output hashes and direct original/rebuilt comparisons.
The corresponding verified report has SHA-256
`898380a43cce0515e7936ccc2fbf6c4a0cf2d8d3d058196242b83e769a646114`.

| Measure | Verified baseline |
| --- | ---: |
| Matched code | 2,504,940 / 2,504,940 bytes |
| Exact functions | 8,677 / 8,677 |
| Source-linked code | 2,504,940 bytes |
| Matched data | 2,970,480 / 3,565,996 bytes (83.30%) |
| Source-linked data | 1,897,440 / 3,565,996 bytes (53.21%) |

No new data percentage is established by this draft. The README and strict
topology freeze retain the verified baseline until a fresh private-input build
and address-coverage audit establish the results.

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

## Changes prepared for verification

Sixty-six exact data candidates, totaling 1,077,180 bytes, are selected for
source-link verification. Their existing sources, flags and declaration order
are preserved. This is a proposal: byte matching of an isolated data section
does not prove a correct final layout. The remaining 132-byte
`game/data/data_802EE06C.c` owner stays incomplete because its documented
four-byte retail start conflicts with the compiled section's alignment.

Fourteen new zero-initialized data candidates cover 13,168 bytes using the
existing symbol-map boundaries. These remain `DataCandidate` until the compiled
symbol layouts and full outputs pass. No initialized game payload is added.
The entirely unnamed 20-byte and 16-byte zero-storage holes remain unchanged.

`lbl_8047C9E4` is reduced to its recorded five-byte `aobj` string extent;
the following seven zero bytes belong to section padding. This correction also
requires compiler and canonical-output verification.

`tools/data_match_diagnostics.py` records section and symbol sizes, alignment,
hashes, relocation identities and comparison results. Its public JSON excludes
payload bytes and disassembly. It also checks whether four resource spans match
definitions already present in the DOL, reporting hashes and equality only.

The first private build verified the sound tables' exact literal-pool hashes
and explicit relocation destinations. Their existing literal text is now
given named source definitions, retaining each original string and reference.
`tools/prodg_comparison_object.py` is connected only to these two data-only
owners. It creates a separate source-comparison view after proving exact
relocation semantics and equality of all non-relocation bytes. It normalizes
SN's duplicated in-place RELA addends and preserves the native linker input.
Actual compiler objects must pass these checks and canonical outputs before
any additional matching credit is accepted.

The first verification build retained all 8,677 exact functions but failed
the canonical outputs and 32 of 34 zero-owner layout checks. It exposed
reversed existing BSS declarations and redundant explicit padding in the new
candidates. The next revision corrects declaration order, uses natural or
scalar padding, tests reduced array alignment, and moves two preceding
four-byte globals into aligned data-only owners. Metadata-only linked-address
diagnostics and synthetic compiler probes investigate the remaining layouts.
These failures are not accepted progress measurements.

## Validation requirements

All-zero bytes can compare exactly even when variables have moved. Each
zero-storage owner therefore needs a compiled-symbol address and size check,
in addition to the ordinary report. `tools/verify_zero_data_layout.py` derives
these expectations independently from `symbols.txt` and `splits.txt`; it checks
all 1,440 existing symbol boundaries and the intervening zero-padding ranges in
the fourteen new owners. It also checks the twenty existing BSS owners proposed
for source linking, covering another 641,904 bytes and 136 existing symbols.
The same offset, size, binding, section and alignment requirements apply to both
groups.
Other candidates need actual source and
target section, symbol, relocation and alignment comparison.

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

## Source metadata and linker layout

The first three draft builds kept all 8,677 tracked functions exact, but failed
the canonical output hashes. Their percentages are provisional. The third
build verified all 34 zero-data owners' native symbol layouts, covering
655,080 bytes, and identified the remaining linker shifts. Newly linked
objects need explicit retention, byte-array alignment at packed boundaries,
and the original section boundary alignment. `source_data_exports.txt`
retains only the source definitions introduced by this continuation.

Twenty-one initialized data owners start four bytes past an eight-byte
boundary. MWCC emits eight-byte section alignment even though their actual
C objects require at most four. `tools/source_object_metadata.py align`
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
mapping. Six comparison-only views therefore give the existing anonymous
compiler data objects their independently established target names. This
changes only symbol-name/string-table metadata. All source bytes, symbol
values and sizes, bindings, and relocation records remain unchanged; native
objects remain linker inputs. The standard report generator still performs
the actual byte/relocation comparison, with its full original denominators.

## Resource scope and attribution

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
`{0xFFFF, 0, 0, 0}` terminator recognized by `GSmsgFontOpen`. The draft shares
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
all 423,928 bytes from native ProDG source objects; the source links still
await passing complete output checks, and no accepted percentage is claimed here.
The other 137,104 resource bytes contain two message groups and a GS VM
script bank. The bounded message diagnostic establishes their structure
without publishing message text. Two additional proposed owners reconstruct
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
alignment and no relocations after translating integer endianness. Native
ProDG and canonical output validation remain required. When the rebuilt REL
is available, the diagnostic compares the complete 561,032-byte resource
region and each original message resource, including its fallback storage.

The two new indices do not reconstruct their message text. Their remaining
95,056 storage bytes and the 8,120-byte GS VM bank remain fallback (103,176
bytes total). Current source searches find only 68 bytes of candidate message
storage reuse; this does not justify counting the rest. The script diagnostic
reports its loader header, function-offset/relocation tables and bounded
interval hashes without emitting instructions or literals.

Count-Sheep's original campaign history and contributor credit remain intact.
The continuation's commits retain the account-linked coauthor credit when
building on their source reconstruction. No runtime or gameplay result is
implied by data matching.
