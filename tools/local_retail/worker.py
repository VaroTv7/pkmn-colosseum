#!/usr/bin/env python3
"""Build one exported revision inside the disposable, network-less worker.

Runs in the container only. Everything it writes is untrusted data for the
host verifier, which re-checks outputs and reports independently. It receives
no credentials and cannot reach the network.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time

TOOLS = Path("/toolchain")
RESULT_DIR = Path("_worker")


def configure_command(version):
    return [
        "python3", "configure.py", "--map", "--version", version,
        "--binutils", str(TOOLS / "binutils"), "--compilers", str(TOOLS / "compilers"),
        "--dtk", str(TOOLS / "bin/dtk"), "--objdiff", str(TOOLS / "bin/objdiff-cli"),
        "--sjiswrap", str(TOOLS / "bin/sjiswrap.exe"), "--wrapper", str(TOOLS / "bin/wibo"),
    ]


def plan(side, version, jobs):
    report = f"build/{version}/report.json"
    build = [
        ("configure", configure_command(version)),
        # -k 0 reports every failing unit in one run; any failure still fails the step.
        ("all_source_report", ["ninja", f"-j{jobs}", "-k", "0", "all_source", report]),
    ]
    if side == "base":
        return build, []
    build.append(("full_link", ["ninja", f"-j{jobs}"]))
    # Candidate-side checks are informative here; the host repeats the
    # security-relevant ones with its own pinned copies.
    checks = [
        ("unit_tests", ["python3", "-m", "unittest", "discover", "-s", ".github/scripts", "-p", "test_*.py"]),
        ("object_map_freeze", ["python3", "tools/check_object_map_freeze.py",
                               "--report", report, "--strict-source-status"]),
        ("readme_progress", ["python3", "tools/update_readme_progress.py", "--report", report, "--check"]),
    ]
    return build, checks


def run(name, command, results):
    log = RESULT_DIR / f"{name}.log"
    start = time.monotonic()
    with log.open("wb") as handle:
        rc = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT).returncode
    results.append(dict(name=name, rc=rc, seconds=round(time.monotonic() - start, 1)))
    return rc == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--side", choices=("base", "head"), required=True)
    parser.add_argument("--version", default="GC6E01")
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    RESULT_DIR.mkdir(exist_ok=True)
    build, checks = plan(args.side, args.version, args.jobs)
    results = []
    ok = all(run(name, command, results) for name, command in build)
    if ok:
        for name, command in checks:
            run(name, command, results)
    (RESULT_DIR / "result.json").write_text(json.dumps(dict(schema=1, side=args.side, steps=results)) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
