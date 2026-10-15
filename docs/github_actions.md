# CI and local retail validation

Validation is split in two, so that original game files and proprietary
compilers never leave the maintainer's machine:

| Layer | Where it runs | Has originals/compilers | Publishes |
| --- | --- | --- | --- |
| Public source checks | GitHub-hosted runners | No | `source-only checks (no retail inputs)`, `quality` |
| Retail validation | Locally, in a network-less container | Yes, read-only and local | `local-retail/build (GC6E01)`, `local-retail/regression (GC6E01)` commit statuses |

A green public check is **not** a retail build. Only the `local-retail/*`
statuses describe compiled sources, linked binaries and canonical hashes.

## Public checks (anyone, no originals)

`.github/workflows/build.yml` ("Source checks") and
`.github/workflows/quality-lint.yml` run on GitHub-hosted runners with
`contents: read` and `persist-credentials: false`. They use only synthetic
fixtures: checker and validator unit tests, the canonical-manifest pin, the
whole-tree live asm-wrapper scan, the PR-diff quality scan, and a configure
smoke test. No container image, cache or artifact carries original-derived
data, and no workflow uses `pull_request_target`.

Run the same checks locally without originals:

```bash
python -m unittest discover -s .github/scripts -p "test_*.py"
python -m unittest discover -s tools -p "test_*.py"
python .github/scripts/check_asm_wrappers.py src
python .github/scripts/quality_scan.py origin/master HEAD
```

## Local retail validation (maintainers with originals)

### Prerequisites

- Docker with a Linux engine (Docker Desktop on Windows works).
- Python 3.12+ and Git on the host; `gh` only for publication.
- Your own original `sys/main.dol` and the verified 25-REL ZIP
  (`GC6E01-rel-inputs-complete.zip`). Keep them outside every Git checkout.
- The pinned toolchain, installed once (network, no originals involved):

```bash
python tools/local_retail/toolchain.py install --fetch --downloads ~/pkmn-toolchain/dl --dest ~/pkmn-toolchain/gc-linux-x86_64-20261014
docker build -t pkmn-local-retail:1 tools/local_retail
```

`toolchain.lock.json` pins every artifact by SHA-256 (binutils 2.42-1,
compilers_20250812, dtk v1.8.3, objdiff-cli v3.6.1, sjiswrap v1.2.2,
wibo 1.0.3). Installation writes a per-file manifest that every run re-hashes.

### Run

Run the validator from a **reviewed** checkout (it is the trusted verifier),
naming the exact PR head and the current base tip:

```bash
python tools/local_retail/validate.py --repo . --dol PATH/main.dol --rel-zip PATH/GC6E01-rel-inputs-complete.zip --toolchain ~/pkmn-toolchain/gc-linux-x86_64-20261014 --base BASE_SHA --head HEAD_SHA --work ~/pkmn-validation/HEAD_SHA --dry-run
```

`--dry-run` performs every preflight (Git revisions, Docker daemon and local
image, toolchain hashes, canonical manifest pin, and all 26 original input
hashes in a temporary directory) and stops with a specific message for any
missing prerequisite. Drop `--dry-run` to build. `--jobs` defaults to 2. If
the DOL denominator legitimately changes, pass the reviewed delta with
`--reviewed-dol-drift CODE,DATA,FUNCTIONS`; any other drift fails.

What a run does:

1. Verifies the toolchain and stages the originals through the trusted
   `tools/ci_retail.py` loader into the work directory (outside the repo).
2. Exports BASE and HEAD with `git archive` into two separate fresh Docker
   volumes; no Git metadata, hooks or caches cross over.
3. Builds each revision with `--network none`, all capabilities dropped,
   `no-new-privileges`, a read-only root filesystem, and read-only mounts of
   the originals and toolchain. Nothing from the host home directory, SSH
   agent, Docker socket or GitHub credentials is mounted. BASE builds its own
   configured report (it may be DOL-only); HEAD runs
   `ninja -j2 all_source build/GC6E01/report.json` then `ninja -j2` and the
   candidate-side object-map freeze, README progress and unit-test checks.
4. A fresh network-less container mounts the finished volume read-only and
   copies out only allowlisted regular files. Symlinks, special files, path
   escapes and oversized files are refused, not followed.
5. After every container has exited, the host verifier re-hashes all 26
   outputs against the pinned `config/GC6E01/build.sha1` (HEAD's manifest must
   equal it; BASE's must be a subset), compares each byte-for-byte with the
   original, and runs metric integrity, the module/address regression audit,
   duplicate-identity, removal, boundary and denominator checks with its own
   pinned code. It also runs `quality_scan.py` over `BASE...HEAD` and the
   whole-tree asm-wrapper scan.
6. Reports, logs and the full audit stay in `WORK/raw` and
   `WORK/results`; the staged originals and the rebuilt binaries (byte-identical
   to them) are deleted on every exit path.
   `WORK/results/summary.json` holds only the allowlisted fields.

### Publish

```bash
python tools/local_retail/publish.py --summary WORK/results/summary.json --pr PR_NUMBER
python tools/local_retail/publish.py --summary WORK/results/summary.json --pr PR_NUMBER --post --comment
```

The publisher is a separate process and the only one that reads GitHub
credentials (via `gh`). It rejects any summary with unexpected fields,
invalid values or more than 16 KiB, re-hashes the retained evidence files,
and refuses to publish unless the PR is open, its head SHA and tree equal the
tested ones, and the base branch tip equals the tested base. Each status is
`success` only when every one of its checks passed; anything else is
`failure`. Without `--post` it prints the payloads only. Raw logs, reports,
maps, disassembly, objects, binaries, originals and compilers are never
uploaded.

A new head commit or base tip invalidates a result: rerun the validation.

## Trust boundaries and limits

- Trusted: the reviewed validator checkout, the pinned manifest and
  toolchain lock, the host verifier and the publisher.
- Untrusted: everything a candidate revision controls, including
  `configure.py`, `tools/project.py`, linker scripts and anything the worker
  writes. The verifier proves the produced bytes equal the originals; it
  cannot prove *how* candidate build logic produced them. Review build-system
  changes accordingly.
- Commit statuses are posted with the maintainer's own `gh` credentials.
  Branch protection can require the `local-retail/*` contexts, but unless
  they are pinned to a dedicated GitHub App, any account with write access can
  set them. Keep write access limited.
- Byte-identical outputs still use original fallback objects for
  unreconstructed regions. They do not show complete decompilation or
  gameplay correctness.

## Branch protection mapping

The previous required checks `build (GC6E01)` and `regression (GC6E01)` came
from GitHub Actions jobs inside a private container holding originals. They
are replaced by the locally published `local-retail/build (GC6E01)` and
`local-retail/regression (GC6E01)` statuses; `quality` is unchanged. Changing
the required contexts is a maintainer decision made in the repository
settings after a genuine run has been published.

The previous Actions-published progress chart (`progress-chart` branch) needed
a retail report and is no longer updated by public CI.
