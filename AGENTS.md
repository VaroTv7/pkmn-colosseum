# AGENTS.md — Pokémon Colosseum Decompilation Guardrails

## Matching acceptance — maintainer decision, 2026-10-11

The upstream maintainer has authorized importing the complete Count-Sheep
campaign through `741453444805acb817e4d9409416ac9c3de5b20e`, including matching
improvements that the previous strict source-style policy rejected. Do not
filter this import to pragma-free or shaping-free functions.

Prefer clear, natural C/C++, but documented compiler-control pragmas,
source-shaping temporaries, aliases, masks, and reconstructed inline helpers
are acceptable when supported by reproducible matching evidence. Preserve
the donor's exception records and attribution. A historical `RULE-EXCEPTION`
tag is a record of an engineering tradeoff, not an automatic rejection.
This decision supersedes conflicting strict source-style rejection language
in older campaign documents and handoffs. It does not waive correctness,
validation, licensing, or honest progress reporting.

Retain build, relocation, section-layout, canonical-hash, metric-integrity,
and regression checks. Compare renamed/repartitioned functions by original
module, section/address and size; keep exact-source and linked-code gains
separate. Registered assembly remains accepted under the evidence rules
below and must be reported separately from decompiled C/C++. A failed compiler
probe is evidence about the tested candidates, not proof that C is impossible.
Do not count original-object fallback as compiled-source progress, hide a
regression by changing the denominator, or claim runtime testing from hashes.

The imported branch is an integration candidate, not proof of a completed
merge or a fresh byte-matching measurement. Preserve upstream changes through
`5cfe5ca3d09f20c4adc3c9b2a4e8d3c29046f10f` (including PRs #633–#636) when
reconciling it with master. Never resolve that reconciliation by replacing
master with the donor tree or discarding recent upstream names and fixes.

## Active Project

The active build/report path is `configure.py` -> `ninja` ->
`build/GC6E01/report.json`.

- Target: Pokémon Colosseum `GC6E01`.
- Source candidates: `src/`.
- Headers: `include/`.
- Canonical config: `config/GC6E01/config.yml`, `symbols.txt`, `splits.txt`,
  `build.sha1`.
- Archived old campaign material: `archive/previous_campaign/`.

## Hard Rules

- Do not add, edit, stage, or commit `.inc` files.
- Do not count asm wrappers, inline asm, or included assembly as decompiled C.
  Preserve the donor's existing Dolphin paired-single allowlist and the
  per-function evidence registry in `docs/asm_evidence/registry.json`.
  Registered library and first-party assembly may contribute to matching and
  linked-code totals, with assembly contributions reported separately.
  Preserve the evidence documents, compiler-probe checks, branch-target
  declarations, and `.github/scripts/verify_asm_branch_targets.py` validation.
  Registry extensions need explicit evidence and corresponding CI coverage.
- Do not commit extracted game assets, target objects, compiler binaries, or
  generated build products.
- Do not move archived campaign material back into the active tree unless it is
  reintroduced through the dtk-template pipeline.
- Do not rename symbols or change splits without a concrete build/report reason.
- Keep source changes scoped to objects declared in `configure.py`.
- Do not introduce uninitialized reads, unexplained side effects, or changed
  game semantics merely to improve a score. Investigate such findings rather
  than treating the relaxed source-style policy as a correctness waiver.

## Validation

Use the smallest check that proves the change:

1. `python configure.py --no-progress`
2. `ninja all_source build/GC6E01/report.json`
3. `ninja`
4. `python configure.py progress`

Also run the applicable quality, metric-integrity, object-map and regression
checks with their documented arguments. A final DOL hash alone does not
validate an incomplete CodeCandidate object. Check actual source objects,
data, relocations and sibling functions. If a command cannot run in the
environment, report the exact command and why. Never change canonical hashes
or bypass required checks merely to make the import green.

## Campaign Operations

When `tools/local_campaign.py` is running, claim the assigned function with
`python3 tools/local_campaign.py claim SYMBOL --worker Codex` before editing.
The claim covers its entire source owner. Run builds, objdiff, and verification
through `python3 tools/local_campaign.py build --worker Codex -- COMMAND`.
Release the owner with the returned claim token after validation. Read
`docs/LOCAL_LLM_CAMPAIGN.md` for the coordination and queue-refresh workflow.
The harness itself lives in its own repository (sibling folder
`Pokemon-Decomp-Harness`, github.com/Count-Sheep/pokemon-decomp-harness); the
`tools/local_campaign*.py` files here are forwarding stubs.

Before resuming fleet, farm, worktree-reconciliation, or batch-integration work,
read `docs/CAMPAIGN_OPERATIONS.md`. Its restart/cleanup playbook and handoff
ledger remain useful; the matching acceptance decision above overrides older
strict source-style restrictions. Keep exact-source and newly linked progress
separate. Leave other people's dirty or active worktrees untouched.

## Cloud Sessions (no retail disc)

The donor's diff bridge was switched off on 2026-09-30. Its Tailscale Funnel,
launchd services and token were removed; do not assume `tools/cloud_diff.py`
works or that any branch is automatically merged. See the harness's
`docs/LOCAL_LLM_CAMPAIGN.md` for historical setup details.

A cloud checkout without `orig/` cannot independently validate matching bytes.
Use authorized CI or a checkout with the maintainer's original game files.
Keep credentials and retail disassembly out of commits, logs and public
artifacts. State clearly which results were reproduced and which were only
reported by the donor.

## Naming

Rename conservatively and preserve address traceability. A nontrivial rename
needs evidence from callsites, strings, known SDK patterns, data tables, or
confirmed assembly/decompiler analysis. Preserve upstream runtime-evidence
names during the full-fork integration.
