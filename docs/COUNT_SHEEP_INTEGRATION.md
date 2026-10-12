# Count-Sheep integration checkpoint — 2026-10-12

PR: https://github.com/dougchansan/pkmn-colosseum/pull/638

Status: source reconciliation, all-DOL-source compilation, canonical DOL byte
comparison, metric integrity and address-based function regression audits pass.
The full DOL + 25 REL build is NOT validated. Master has not been merged.

## Revisions and attribution

- Upstream baseline: 5cfe5ca3d09f20c4adc3c9b2a4e8d3c29046f10f.
- Complete Count-Sheep donor snapshot: 741453444805acb817e4d9409416ac9c3de5b20e.
- Maintainer-approved matching policy: a57d34f2dd688d669bd5cfe12a4085ef1cbed857.
- History-preserving reconciliation: 5c2de957e880bc86d8ba54db55dc928c49cbc4bd.
- Public/inline peopleSetVisible identity fix: 596e8e7779fe688c2249fdc0d61e0d40962cdcc4.
- Published, validated build repair: 221dd0c1a8a490583a0be9610b8546e38677914c.
- Validated configure.py Git blob: 6d681031cee1619a48f5de8dc3b754a138792e93.

The donor history and attribution are preserved. The reconciliation resolves 39
conflicted paths and carries all 42 upstream runtime-evidence names forward.
The source-style exceptions approved by the maintainer are accepted; original
binary hashes and metric-integrity requirements have not been weakened.

## Repairs

The public peopleSetVisible name collided with a donor static inline helper in
src/game/people/people.c. Only the inline helper and its original two callers
were renamed to peopleSetVisibleInline; both bodies remain unchanged.

The DOL-only diagnostic removed REL consumers and therefore lost linker roots.
Retail code was dead-stripped: the .text section shrank by 56,640 bytes. The
initial donor diagnostic hash failure was not evidence of bad imported function
code. Retaining canonical retail code symbols recovered the exact original DOL.
The durable config/GC6E01/dol_exports.txt manifest contains 165 code identities
(including aliases/labels), not 165 newly matched functions. It does not force
unrelated data or unused source-only helpers into the binary.

The extraction planner now accepts a complete set of loose original REL files
when their FSYS archive is absent. An existing archive remains authoritative.
Partial or missing input sets still fail, and dtk's original module hash checks
remain in force. This removes a redundant archive requirement, not the need for
original game inputs.

## Executed validation

Build evidence:
https://github.com/dougchansan/pkmn-colosseum/actions/runs/38285680548/job/114933360995

That run passed all 75 checker tests, the complete PR source-quality scan,
whole-tree assembly-wrapper scan (2,336 source files), all DOL source compilation,
canonical DOL SHA-1, direct cmp, metric integrity, and both report comparisons.
Its overall workflow conclusion is failure solely because the final bot push
attempted to edit a workflow without workflows permission. The tested files were
not silently changed to work around a build failure.

Publication evidence:
https://github.com/dougchansan/pkmn-colosseum/actions/runs/38286523217/job/114936104717

Publication succeeded after the workflow edit was made separately. The publisher
required identical source, headers, config, tools and checker files, verified the
exact tested configure.py blob, reran 75 tests, and committed configure.py only.
Completed one-off diagnostic/publishing workflows have been removed.

Canonical DOL SHA-1: 870e8b9693ca780782d80f22a6a4572d8ba9458f.
Original and rebuilt DOL size: 3,779,808 bytes. Direct byte comparison passed.
This is a matching reconstruction using original fallback objects where needed,
not a claim that the game is 100% decompiled.

Metric integrity: 8,602 functions at 8,602 distinct addresses, no duplicate claims;
reported code denominator 2,495,112 versus 2,503,264 bytes of DOL text (0.33% apart).

Against upstream: 8,602 common module/address identities, zero function-score
regressions, zero unexplained removals, 41 renames, two boundary changes, one
fully covered exact coalescence. Against donor: zero function-score regressions,
zero unexplained removals, 42 renames, no boundary changes.

The removed standalone fn_800F9D64 four-byte identity is covered by the exact
GSmsgOpen interval. GSmsgOpen and InitMetroTRK_BBA boundaries each expanded by
four bytes. Mutable source paths and names were not used to hide regressions.

## Fresh DOL-only report measurements

| Measure | Upstream | Integrated |
| --- | ---: | ---: |
| Matched code bytes | 1,086,720 | 2,289,984 |
| Code match | 43.554028% | 91.77881% |
| Exact function matches | 6,804 / 8,603 | 8,460 / 8,602 |
| Source-linked code bytes | 732,868 | 2,256,580 |
| Source-linked code | 29.372194% | 90.440025% |
| Matched data bytes | 2,136,689 | 2,085,070 |
| Data match | 97.29471% | 94.94608% |

Net matched code gain: 1,203,264 bytes. Exact function count gain: 1,656.
These are DOL-only reports, not a combined DOL/REL or gameplay measurement.
Data matching decreases by 51,619 reported bytes; zero function regressions must
not be described as zero regressions in every metric. The full rebuilt DOL is
byte-identical despite that report-level data coverage difference. Its detailed
object/relocation scoring explanation has not been established here.

## Remaining known gate: original REL inputs

The accessible private CI input repository and current build container provide
only orig/GC6E01/sys/main.dol. All 25 configured original REL inputs are absent.
The canonical project configuration and expected hashes remain unchanged.

Supply personally dumped GC6E01 Rev 0 files under orig/GC6E01/files/ in private
build inputs, either as the required FSYS archives or these loose modules:

common_rel.rel, mail.rel, S1_out.rel, pocket_menu.rel, worldmap_menu_rel.rel,
S1_shop_1F.rel, S1_out_bf.rel, pda_menu.rel, M1_out.rel, M1_pc_1F.rel,
M1_pc_B1.rel, M1_houseA_1F.rel, M1_houseA_2F.rel, M1_houseB_1F.rel,
M1_houseC_1F.rel, M1_shop_1F.rel, M1_shop_2F.rel, M1_gym_1F.rel,
M1_gym_B1.rel, M1_stadium_1F.rel, M1_carde_1.rel, M1_out_bf.rel,
M1_gym_1F_bf.rel, M1_houseA_1F_bf.rel, M1_water_colo.rel.

Keep original files, generated binaries and compiler distributions out of the
public repository. After the private input image includes these files, run the
unmodified canonical configure/build, all-source report, all 26 expected output
hashes, and Regression Guard. Resolve any newly exposed errors before merging.
No REL hash validation, gameplay test, or final merge is claimed at this checkpoint.
