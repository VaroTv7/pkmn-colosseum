# Pokémon Colosseum Decompilation (GC6E01)

[![Progress](https://decomp.dev/dougchansan/pkmn-colosseum.svg)](https://decomp.dev/dougchansan/pkmn-colosseum)

A matching decompilation project for the GameCube game **Pokémon Colosseum**
(`GC6E01`, NTSC-U). The active project has been reset to the standard
[dtk-template](https://github.com/encounter/dtk-template) workflow.

## Status

**All 8,677 tracked functions and all 2,504,940 tracked code bytes match and
link from source (100%) across the DOL and all 25 configured REL modules.**
This includes accepted assembly implementations with recorded evidence. Data
matching remains partial at **83.30%**.

| Metric | Value |
|---|---|
| Fuzzy match | 100.00% |
| Function match | 100.00% (8,677 / 8,677 functions) |
| Code match | 100.00% (2,504,940 / 2,504,940 matched code bytes) |
| Data match | 83.30% (2,970,480 / 3,565,996 matched data bytes) |
| Source-linked | 2,121 / 2,244 scoring units (100.00% of code) |

The completed Count-Sheep import was verified at source revision
[`ace8ed58268e46584415fe5e03486e7a00768e67`](https://github.com/dougchansan/pkmn-colosseum/commit/ace8ed58268e46584415fe5e03486e7a00768e67).
Its [source-validation run](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40833777512/job/123313705577)
compiled and linked all outputs, passed all **26 unchanged canonical hashes
and direct original/rebuilt byte comparisons**, and passed the assembly
branch-target checks. That run's overall result was red solely because its
topology freeze still described the previous split layout. This metadata
refresh updates the freeze after auditing unchanged function identities,
denominators and physical coverage; the required checks still apply to the
final PR head. The final integration checks are recorded in
[PR #662](https://github.com/dougchansan/pkmn-colosseum/pull/662).

The table comes from that run's
[`GC6E01_report` artifact](https://github.com/dougchansan/pkmn-colosseum/actions/runs/40833777512/artifacts/12880330757).
For subsequent builds, the authoritative report is
`build/GC6E01/report.json`; the root-level `report.json` is historical. See
[`docs/COUNT_SHEEP_INTEGRATION.md`](docs/COUNT_SHEEP_INTEGRATION.md) for exact
provenance, assembly accounting and the retained import history.

The scope of 100% is the project's tracked code and function denominator.
The **7,988-byte interrupt-vector template** remains an explicit original-object
fallback outside that historical denominator. Its full physical interval is
retained and its bytes are covered by the final binary comparisons. The
**561,032-byte `common_rel` resource fallback** remains inside the data
denominator and receives no reconstructed-source credit. The DOL alone is
100% code-matched and 98.56% data-matched; combined source-linked data is
1,897,440 / 3,565,996 bytes (53.21%). These results do not establish a pure-C
percentage or gameplay testing.

**Scoring units are not translation units.** An original source region may be
split into address-owned units with different compiler flags, compiled through
one-line `#include` shims. The full report contains 8,677 distinct module/address
function identities, with no duplicate claims. Its 2,504,940-byte code denominator
contains 2,495,112 DOL bytes and 9,828 REL bytes, all matched and source-linked.
The freeze tracks the section topology of all 2,244 scoring units, including
units that contain data or original fallback regions.

The historical function worklist now has no remaining rows.
[`docs/completed-functions.csv`](docs/completed-functions.csv) retains all
217 campaign entries and their evidence notes. This worklist is a historical
campaign queue, separate from the report's complete function inventory.

![Progress over time](https://raw.githubusercontent.com/dougchansan/pkmn-colosseum/progress-chart/progress.png)

The chart plots fuzzy matching, code matching and function matching. Every
point is an `objdiff` measurement. Points from 2026-07-01 onward come from CI
reports (or, for the first stretch, this table's git history); earlier points
were recovered by building historical commits. The campaign starts on
2026-06-27, when units first became matchable. Points from the PR #638 merge
onward cover the DOL plus REL modules; earlier points have DOL-only scope.

The build workflow republishes the image on every push to master in the
[`progress-chart`](https://github.com/dougchansan/pkmn-colosseum/tree/progress-chart)
branch. Keeping generated images there avoids repeated image commits on the
protected master branch. Render one locally with:

```bash
uv run --with matplotlib tools/plot_progress.py -o /tmp/progress.png
```

After rebuilding the report, refresh the table with:

```bash
python3 tools/update_readme_progress.py
```

Use `python3 tools/update_readme_progress.py --check` to verify that the README
matches the current report.

The published denominator is frozen in
`config/GC6E01/object_map.freeze.json`. After changing `splits.txt`,
`symbols.txt`, or object declarations, rebuild the report and run:

```bash
python3 tools/check_object_map_freeze.py
```

The check locks total code bytes, data bytes, function count, and unit section
topology. Progress counters may rise without updating the freeze. Intentional
split/topology changes must update the freeze in the same change with
`python3 tools/check_object_map_freeze.py --update` and a clear reason. The
current topology still includes auto-generated units; those are visible
placeholders to retire deliberately, not hidden progress. Named extracted units
without a source path are object-map progress only; they are not counted as
decompiled source matches.

## Requirements

You must provide your own legally obtained game files. Place a supported disc
image or extracted disc at `orig/GC6E01/`; see
[`docs/getting_started.md`](docs/getting_started.md).

The build downloads pinned dtk-template tools into `build/` when local paths are
not supplied.

## Build

```bash
python configure.py
ninja
python configure.py progress
```

The build splits `sys/main.dol` and the 25 configured original REL modules,
substitutes only objects declared in `configure.py`, and verifies all 26 rebuilt
outputs against `config/GC6E01/build.sha1`. Original RELs belong under
`orig/GC6E01/files/`; complete loose modules or their FSYS archives are supported.

## Worker Worktrees

Use the helper below for parallel decompilation workers. It creates or repairs a
worktree and links `orig/GC6E01/sys` to the local original game files so
`ninja all_source build/GC6E01/report.json` can validate from the worker tree.

```bash
python3 tools/setup_worker_worktree.py /tmp/pkmn-parallel-example \
  --branch campaign/parallel-example \
  --base origin/master
```

Add `--validate` to run the standard worker checks after setup:

```bash
python3 configure.py --no-progress
ninja all_source build/GC6E01/report.json
python3 tools/update_readme_progress.py --check
git diff --check
```

## Layout

```text
config/GC6E01/          dtk config, symbols, splits, SHA-1
include/                project headers
src/                    active source/data candidates declared in configure.py
tools/                  dtk-template helper scripts
docs/                   dtk-template setup documentation
archive/previous_campaign/
                        old campaign tools, notes, PC-port experiments, and
                        unconfigured source kept for research only
```

## Contributing

Use the dtk-template flow. Add or refine splits in `config/GC6E01/splits.txt`,
declare source objects in `configure.py`, build with `ninja`, and inspect the
generated `objdiff.json` / `build/GC6E01/report.json`.

Do not commit generated `.inc` files, extracted game assets, target objects,
compiler binaries, or asm-wrapper bodies as decompilation progress.

## Contributors

[Count-Sheep](https://github.com/Count-Sheep) contributed the extensive matching
and linking campaign integrated from their
[Pokémon Colosseum fork](https://github.com/Count-Sheep/pkmn-colosseum), including
source reconstruction, compiler analysis, matching tools and supporting evidence.
The integration preserves their original commits and author attribution. See
[`docs/COUNT_SHEEP_INTEGRATION.md`](docs/COUNT_SHEEP_INTEGRATION.md) for the import
history and validation scope.

## License

The decompiled source in this repository is released under the
[MIT license](LICENSE). The Pokémon Colosseum game, assets, and toolchain are
owned by their respective rights holders and are not distributed here.
