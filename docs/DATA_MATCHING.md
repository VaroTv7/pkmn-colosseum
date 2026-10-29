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

## Resource scope and attribution

The 561,032-byte resource region currently remains original fallback, as
documented in [`REL_MODULES.md`](REL_MODULES.md) and the corrected import in
PR #646. It remains in the full data denominator and in the completion scope.
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
ProDG build or canonical-output result: both new owners are proposed source
links awaiting those required checks, and no new percentage is claimed here.
The other 137,104 resource bytes retain original fallback pending further
reconstruction.

Count-Sheep's original campaign history and contributor credit remain intact.
The continuation's commits retain the account-linked coauthor credit when
building on their source reconstruction. No runtime or gameplay result is
implied by data matching.
