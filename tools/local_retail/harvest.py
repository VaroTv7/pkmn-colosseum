#!/usr/bin/env python3
"""Copy allowlisted results out of a finished worker volume.

Runs in a fresh network-less container after the worker has exited, with the
worker volume mounted read-only. Only regular files at allowlisted relative
paths are copied; symlinks, special files, path escapes and oversized files are
refused and recorded, never followed.
"""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

MAX_BYTES = {
    ".dol": 16 << 20,
    ".rel": 16 << 20,
    ".json": 128 << 20,
    ".log": 64 << 20,
}
SAFE_PART = re.compile(r"[A-Za-z0-9_.-]+")


def check_relative(relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts or any(
            part in ("", ".", "..") or not SAFE_PART.fullmatch(part) for part in path.parts):
        raise ValueError(f"Unsafe result path: {relative!r}")
    if path.suffix not in MAX_BYTES:
        raise ValueError(f"Result type is not allowlisted: {relative!r}")
    return path


def open_regular(root, relative):
    """Open root/relative without following a symlink at any component."""
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        parts = relative.parts
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
    finally:
        os.close(fd)
    info = os.fstat(file_fd)
    if not stat.S_ISREG(info.st_mode):
        os.close(file_fd)
        raise ValueError("not a regular file")
    return file_fd, info.st_size


def harvest(root, dest, paths):
    record = {}
    for relative in paths:
        path = check_relative(relative)
        try:
            file_fd, size = open_regular(root, path)
        except FileNotFoundError:
            record[relative] = "missing"
            continue
        except (OSError, ValueError) as error:
            record[relative] = f"refused: {type(error).__name__}"
            continue
        with os.fdopen(file_fd, "rb") as handle:
            if size > MAX_BYTES[path.suffix]:
                record[relative] = "refused: oversized"
                continue
            target = Path(dest, *path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "xb") as out:
                out.write(handle.read(size))
        record[relative] = "copied"
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="/w")
    parser.add_argument("--dest", default="/out")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    record = harvest(args.root, args.dest, args.paths)
    with open(os.path.join(args.dest, "harvest.json"), "x") as out:
        json.dump(record, out, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
