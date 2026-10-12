# Count-Sheep integration validation — 2026-10-12

PR: https://github.com/dougchansan/pkmn-colosseum/pull/638

**The complete DOL + 25 REL reconstruction passes all 26 unchanged canonical
SHA-1 checks and all 26 direct original/rebuilt byte comparisons.** All source
units compiled, 75 checker tests passed, and the address-based regression audits
passed. Consult the PR for merge status; the ordinary CI image still has a
separate original-input provisioning limitation described below.

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

## Separate CI infrastructure limitation

The complete originals are available and validated in this session. They were
not uploaded into the ordinary private CI image, which still contains only
`main.dol`. Consequently, ordinary Build/Regression Guard runs can still fail on
missing original REL inputs. The full passing validation above is the distributed
private-compiler / sandbox-link run, not a claim that those GitHub checks are green.
Do not bypass branch protection or alter expected hashes to hide this distinction.

For repeatable ordinary CI, provision the 25 original modules under
`orig/GC6E01/files/` in the PRIVATE `pkmn-colosseum-build` input repository/image,
then rerun the ordinary Build and Regression Guard jobs. Keep all original game
files and compiler distributions out of the public source repository.
