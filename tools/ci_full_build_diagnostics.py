#!/usr/bin/env python3
"""Temporarily bound the final Ninja build and report metadata on a stall."""

import argparse
from contextlib import suppress
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import time


def linker_command_summary(argv, version):
    """Return only allowlisted executable names and a confined output path."""
    basename = lambda value: value.replace("\\", "/").rsplit("/", 1)[-1]
    if not argv or basename(argv[0]) != "wibo":
        return None
    names = ["wibo"]
    if len(argv) > 1 and basename(argv[1]) in {"mwldeppc.exe", "mwcceppc.exe", "ngccc.exe"}:
        names.append(basename(argv[1]))
    outputs = [argv[i + 1] for i, value in enumerate(argv[:-1]) if value == "-o"]
    output = "unavailable"
    if len(outputs) == 1:
        candidate = outputs[0]
        path = PurePosixPath(candidate)
        if (len(candidate) <= 256 and re.fullmatch(r"[A-Za-z0-9_./-]+", candidate)
                and not path.is_absolute() and path.parts[:2] == ("build", version)
                and len(path.parts) > 2 and ".." not in path.parts
                and str(path) == candidate):
            output = candidate
    return " -> ".join(names) + "; output=" + output


def linker_process_metadata(version, proc_root=Path("/proc")):
    print("Build diagnostic: Wibo executable names and validated build output only", flush=True)
    for entry in sorted(proc_root.iterdir()):
        if not entry.name.isdigit():
            continue
        try:
            if (entry / "comm").read_text().strip() != "wibo":
                continue
            with (entry / "cmdline").open("rb") as command_line:
                raw = command_line.read(65537)
            if len(raw) > 65536:
                continue
            argv = [part.decode("utf-8", "replace") for part in raw.rstrip(b"\0").split(b"\0")]
            summary = linker_command_summary(argv, version)
            if summary is not None:
                print(f"PID {entry.name}: {summary}", flush=True)
        except (OSError, UnicodeError):
            continue


def snapshot(version):
    print("Build diagnostic: process IDs, parent IDs, elapsed time, names", flush=True)
    try:
        subprocess.run(["ps", "-eo", "pid,ppid,etime,comm"], check=False, timeout=3)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Process metadata unavailable: {type(exc).__name__}", flush=True)
    linker_process_metadata(version)
    build_dir = Path("build") / version
    paths = {build_dir / "main.elf", build_dir / "main.dol"}
    manifest = Path("config") / version / "build.sha1"
    if manifest.is_file():
        for line in manifest.read_text().splitlines():
            fields = line.split(maxsplit=1)
            if len(fields) != 2:
                continue
            path = Path(fields[1].lstrip("*"))
            if path.suffix == ".rel" and path.is_relative_to(build_dir):
                paths.add(path)
    print("Build diagnostic: output existence and byte sizes only", flush=True)
    for path in sorted(paths):
        try:
            print(f"{path}: {path.stat().st_size} bytes", flush=True)
        except FileNotFoundError:
            print(f"{path}: missing", flush=True)


def stop_group(process):
    # A separate session keeps cancellation confined to Ninja and its children.
    with suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)
    with suppress(subprocess.TimeoutExpired):
        process.wait(timeout=1)


def run_build(version, command=("ninja", "-j2"), snapshot_after=90, timeout=180):
    started = time.monotonic()
    process = subprocess.Popen(command, start_new_session=True)
    try:
        try:
            result = process.wait(timeout=snapshot_after)
        except subprocess.TimeoutExpired:
            snapshot(version)
            try:
                result = process.wait(timeout=max(0, timeout - (time.monotonic() - started)))
            except subprocess.TimeoutExpired:
                print(f"Build diagnostic: final Ninja build exceeded {timeout} seconds", flush=True)
                stop_group(process)
                return 124
        return result if result >= 0 else 128 - result
    finally:
        stop_group(process)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="GC6E01")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_]+", args.version):
        parser.error("version must contain only letters, digits, and underscores")

    def cancelled(signum, _frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGINT, cancelled)
    signal.signal(signal.SIGTERM, cancelled)
    return run_build(args.version)


if __name__ == "__main__":
    raise SystemExit(main())
