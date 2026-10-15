# Count-Sheep integration validation — 2026-10-12

PR: https://github.com/dougchansan/pkmn-colosseum/pull/638

**The complete DOL + 25 REL reconstruction passes all 26 unchanged canonical
SHA-1 checks and all 26 direct original/rebuilt byte comparisons.** The
2026-10-12 sections below record the original import. Since then master gained
PR #637 (304 Ghidra names); its reconciliation and the 2026-10-14 local
re-validation are recorded at the end. Ordinary CI uses the standard
dtk-template private build image, which now holds all 26 original inputs.

## Revisions and attribution

- Upstream baseline: `5cfe5ca3d09f20c4adc3c9b2a4e8d3c29046f10f`.
- Complete Count-Sheep donor: `741453444805acb817e4d9409416ac9c3de5b20e`.
- Maintainer-approved matching policy: `a57d34f2dd688d669bd5cfe12a4085ef1cbed857`.
- History-preserving reconciliation: `5c2de957e880bc86d8ba54db55dc928c49cbc4bd`.
- Inline-helper name repair: `596e8e7779fe688c2249fdc0d61e0d40962cdcc4`.
- DOL export / loose-REL build repair: `221dd0c1a8a490583a0be9610b8546e38677914c`.
- Fully built source revision: `a6ad511bb49b877e502ed2c406452e9ce524918e`.
- Fully built source tree: `92078a22f48a6ca061e88e6bc3c359c183ec60ae`.
- Audited progress/topology metadata refresh: `30e8633d7ddd6f68a4af94234e92de846eda66f1`.

Both histories and attribution are preserved. Reconciliation resolved 39
conflicted paths and retained all 42 upstream runtime-evidence names. Documented
compiler-control/source-shaping exceptions are accepted under the maintainer's
updated policy. Original hashes and metric-integrity checks were not weakened.

## What was repaired

The public `peopleSetVisible` name collided with a donor static inline helper.
Only that helper and its original two callers were renamed; both bodies were
preserved. The earlier DOL-only hash failure came from losing REL-consumer linker
roots, which stripped 56,640 retail code bytes. The 165-entry code-export manifest
retains those identities without forcing unrelated data or source-only helpers.
It includes aliases/labels and does not represent 165 newly matched functions.

The input planner accepts a complete set of loose original RELs when their FSYS
archives are absent. Available archives remain authoritative; incomplete inputs
still fail. Every original module hash remains checked.

The object-map freeze predated two donor consolidations: 17 entries became two,
reducing total units from 2,178 to 2,163. The audit verified identical unions of
module/section address intervals, plus identical code-byte, data-byte and
function totals. All other unit signatures were unchanged. This is a documented
freeze refresh, not a denominator reduction to inflate progress.

Consolidated regions:

- `main/game/gs_exact_801C8834`: 1,436 code bytes, 220 data bytes, two functions.
- `main/game/fight_range_802249B8_to_8022BB84`: 29,132 code bytes, 360 data bytes,
  39 functions.

The refreshed freeze blob is `504bc98aa8197e93eff02ade313c74d02bab0496`.
Its strict source-status check passes with 2,163 units, 8,677 functions,
2,504,940 code bytes and 3,566,037 data bytes.

## Full-build execution and provenance

The maintainer supplied `GC6E01-rel-inputs-complete.zip`. All 25 originals were
independently checked against the unchanged module hashes before use. Its SHA-256
is `f7ac305017935e89c1913f2a82c98fedaa8ce6da0b389252a2800eb74c90166e`.

Validation used the existing CI compiler/binutils distribution and pinned tools.
The source snapshot's regular tracked files were checked against its Git archive
and remained unchanged throughout binary validation. Two unused absolute local
symlinks in that archive were not materialized in the sandbox.

The sandbox cannot execute 32-bit programs natively. Consequently, the original
Metrowerks compilers ran under QEMU's i386 user-mode runtime and Wibo 0.6.16. The
27 ProDG/3.5 REL translation units compiled on the private CI runner with Wibo
1.0.3, using the exact project flags. No original REL inputs were sent to that
compile job. Each object, all 158 headers, the compiler executables and objcopy
were SHA-256 checked before those compiled objects were used here. The generated
local Ninja ProDG rule used this authenticated compiler cache; it did not insert
retail/fallback objects in place of compiled sources.

Private REL compilation evidence (maintainer access required):
https://github.com/dougchansan/pkmn-colosseum-build/actions/runs/38296919185/job/114970107093

Compiled-object artifact SHA-256:
`f66709ce334ac0116492e20f94f2e5cf698e88df7d9a2afd36669fc0c22dd862`.

The complete 26-module split, source report and final links ran with the canonical
module configuration, dtk 1.8.3, binutils 2.42-1, original compiler flags, and the
unchanged `config/GC6E01/build.sha1`. Limiting toolkit concurrency resolved a
sandbox stall; no disassembly setting or game-source modification was needed.

Validation results:

- Every DOL source and all 27 REL source units compiled.
- All 26 canonical output hashes passed; all 26 files also passed direct byte
  comparison against independent original inputs.
- All 75 checker tests passed; the whole-tree scan checked 2,336 source files.
- Metric integrity found 8,677 unique module/address function identities with
  no duplicate claims.
- Against each previously built upstream/donor DOL report, all 8,602 common
  module/address identities had zero function-score regressions and zero
  unexplained removals. All 75 added REL lifecycle functions match 100%.
- The upstream audit records 41 renames, two boundary adjustments and one exact
  interval coalescence; the donor audit records all 42 runtime renames, with no
  boundary change. The removed four-byte `fn_800F9D64` identity is covered by
  exact `GSmsgOpen` code, not silently discarded.
- The strict refreshed object-map freeze and README/report consistency pass.

Canonical DOL SHA-1: `870e8b9693ca780782d80f22a6a4572d8ba9458f`.
Original and rebuilt DOL size: 3,779,808 bytes.

Metadata publication reproduced the exact locally checked file blobs and reran
all 75 tests; it is not presented as a replacement full binary build:
https://github.com/dougchansan/pkmn-colosseum/actions/runs/38297983057/job/114973628635

## Fresh progress, with scopes kept separate

| Metric | DOL only | DOL + 25 REL modules |
| --- | ---: | ---: |
| Matched code | 2,289,984 / 2,495,112 | 2,299,812 / 2,504,940 |
| Code matching | 91.77881% | 91.81106% |
| Exact functions | 8,460 / 8,602 | 8,535 / 8,677 |
| Source-linked code | 90.440025% | 90.47754% |
| Matched data | 2,085,070 / 2,196,057 | 2,098,410 / 3,566,037 |
| Data matching | 94.94608% | 58.844315% |

Full-report fuzzy matching is 99.68803%; 1,891 of 2,163 scoring units are linked
from source. The lower combined data percentage includes `common_rel`'s
1,356,832-byte data region, of which only 192 bytes are reported as matched.
It is not a fall from 94.95% to 58.84% within the same measurement scope.

Relative to upstream's prior DOL-only build, matched code increased by 1,203,264
bytes and exact function count by 1,656. Upstream DOL data matching was 97.29471%
versus the imported 94.94608%, a 51,619-byte report decrease retained and disclosed
throughout this integration. Zero function regressions is not a claim that every
reported data metric improved.

A byte-identical reconstruction still uses original fallback objects for
unreconstructed regions. It does not mean all game source or data is decompiled,
and no gameplay validation is claimed.

## Reconciliation with master `fd207bc8` (PR #637) — 2026-10-14

PR #637 renamed 304 `fn_` placeholders from a map
(`config/GC6E01/symbolmap/ghidra_names.txt`). Its 157 textual conflicts came
from the donor's consolidation of the same files, so the merge keeps the
integration side of `src/`, `include/`, `symbols.txt` and `subsystem_map.json`
and reapplies the map by address. All 304 addresses were still placeholders
here, so no donor or runtime-evidence name was overridden. The rename touches
code tokens only (comments, strings and `#if 0` blocks keep `fn_` notes);
replaying the same renamer on `5cfe5ca3` reproduces master's `src/` and
`include/` exactly except for #637's manual edits, which were reproduced.

The local retail build then exposed two collisions, repaired in `e2947f1d`:

- `peopleStartTurn` (`fn_8018805C`) collided with the donor's static inline
  copy of the same body. As with `peopleSetVisible`, only the inline helper and
  its 11 original callers were renamed (`peopleStartTurnInline`).
- #637 named `fn_8019CB70` `HSD_GXInit`, but the donor's HAL-derived
  `initialize.c` already contains the real static `HSD_GXInit`, which
  `fn_8019CB70` calls. That address uses HAL's `HSD_InitComponent` (the donor's
  annotation and `hsd_initialize.h` prototype) instead: the only departure
  from #637's map.

The renamed first-party asm routine at `0x800F106C` (`cms_CallStdTrampoline`)
keeps its registered evidence under the new name.

## Local retail validation — 2026-10-14

Base `fd207bc8` (master, DOL-only configuration) and the reconciled game-source
tree `35a9a0ef` were built locally in separate network-less containers with
the private image's compiler/binutils distribution (binutils 2.42-1,
compilers_20250812) plus dtk 1.8.3, objdiff-cli 3.6.1, sjiswrap 1.2.2 and
wibo 1.0.3, at `-j2`:

- Every HEAD source unit compiled and all 26 outputs (DOL + 25 RELs) matched
  the unchanged canonical SHA-1s and the originals byte for byte.
- Metric integrity: 8,677 unique module/address identities; denominator
  0.07% from the DOL text size.
- Against master: 8,602 common identities, 0 score regressions, 0
  unexplained removals, 0 shrinking boundaries, 42 renames, 1 exact interval
  coalescence (`fn_800F9D64`), 75 new REL functions.
- Reviewed DOL denominator change versus master: +4 code bytes, -43 data
  bytes, -1 function (the coalescence above).
- Object-map freeze, README/report consistency, checker tests, quality scan
  and whole-tree asm-wrapper scan passed.

| Scope | Matched code | Exact functions | Matched data |
| --- | ---: | ---: | ---: |
| Head, DOL only | 2,289,984 / 2,495,112 (91.78%) | 8,460 / 8,602 | 2,085,070 / 2,196,057 (94.95%) |
| Head, DOL + 25 RELs | 2,299,812 / 2,504,940 (91.81%) | 8,535 / 8,677 | 2,098,410 / 3,566,037 (58.84%) |
| Master `fd207bc8`, DOL only | 1,086,720 / 2,495,108 (43.55%) | 6,804 / 8,603 | 2,136,689 / 2,196,100 (97.29%) |

The DOL-only data figure remains 51,619 bytes below master's, as disclosed
above; the combined data percentage includes `common_rel` and is not
comparable with the DOL-only one. The required Build and Regression Guard
checks on the PR head remain the binding evidence.
