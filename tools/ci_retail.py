#!/usr/bin/env python3
"""Verify retail inputs and optionally install a private ZIP or compare outputs.

Only paths and hashes are logged. Never publish originals or extracted objects
in a public repository, artifact, cache, or container image.
"""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile


def read_manifest(path):
    """Map canonical output paths to original input paths without changing hashes."""
    entries = []
    seen = set()
    version = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([0-9a-f]{40})\s+([^\s]+)", line)
        if not match:
            raise ValueError("Invalid canonical hash manifest line")
        digest, name = match.groups()
        parts = PurePosixPath(name).parts
        if ("\\" in name or ".." in parts or len(parts) not in (3, 4)
                or parts[0] != "build" or not re.fullmatch(r"[A-Z0-9]+", parts[1])):
            raise ValueError(f"Unsafe or unsupported output path: {name}")
        version = version or parts[1]
        if parts[1] != version:
            raise ValueError("Mixed versions in hash manifest")
        if len(parts) == 3 and parts[2] == "main.dol":
            original = "sys/main.dol"
        elif len(parts) == 4 and parts[3] == parts[2] + ".rel":
            original = "files/" + parts[3]
        else:
            raise ValueError(f"Unsupported retail output: {name}")
        if original in seen:
            raise ValueError(f"Duplicate input identity: {original}")
        seen.add(original)
        entries.append((original, name, digest))
    if not entries or "sys/main.dol" not in seen:
        raise ValueError("Manifest must contain exactly one DOL and any configured RELs")
    return version, entries


def checked_path(root, relative):
    """Do not read or write through symlinks outside the original-input tree."""
    root = Path(root)
    path = root / relative
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError(f"Symlink is not an original input: {candidate}")
        if candidate == root:
            break
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Input escapes its root: {relative}")
    return path


def prepare_inputs(manifest, orig, archive=None):
    version, entries = read_manifest(manifest)
    required = {relative: digest for relative, _, digest in entries}
    pending = {}
    archive = Path(archive) if archive else None
    if archive and archive.exists():
        if not archive.is_file() or archive.is_symlink():
            raise ValueError("Private ZIP must be a regular file")
        with zipfile.ZipFile(archive) as bundle:
            names = [info.filename for info in bundle.infolist()]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate ZIP members")
            if sum(info.file_size for info in bundle.infolist()) > 32 * 1024 * 1024:
                raise ValueError("Original-input ZIP exceeds the 32 MiB limit")
            prefix = f"orig/{version}/"
            for info in bundle.infolist():
                parts = PurePosixPath(info.filename).parts
                if (info.filename.startswith("/") or ".." in parts
                        or "\\" in info.filename or ":" in info.filename
                        or stat.S_ISLNK(info.external_attr >> 16)):
                    raise ValueError("Unsafe ZIP member")
                if info.is_dir():
                    continue
                if not info.filename.startswith(prefix):
                    # The preparation kit includes a hash-verification JSON report.
                    if "/" not in info.filename and info.filename.endswith(".json"):
                        continue
                    raise ValueError(f"Unexpected ZIP member: {info.filename}")
                relative = info.filename[len(prefix):]
                if relative not in required:
                    raise ValueError(f"Unconfigured original in ZIP: {relative}")
                data = bundle.read(info)
                if hashlib.sha1(data).hexdigest() != required[relative]:
                    raise ValueError(f"Original ZIP hash mismatch: {relative}")
                pending[relative] = data
    errors = []
    for relative, _, digest in entries:
        path = checked_path(orig, relative)
        if path.exists():
            if not path.is_file() or hashlib.sha1(path.read_bytes()).hexdigest() != digest:
                errors.append(f"Original hash mismatch: {relative}")
        elif relative not in pending:
            errors.append(f"Missing original: {relative}")
    if errors:
        raise ValueError("\n".join(errors) + "\nInstall the verified input ZIP in the PRIVATE build repository and rebuild its image; do not skip this check.")
    # Write nothing until the entire input set and all archive members validate.
    for relative, data in pending.items():
        path = checked_path(orig, relative)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as output:
                output.write(data)
    for relative, _, digest in entries:
        if hashlib.sha1(checked_path(orig, relative).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Post-install hash mismatch: {relative}")
    print(f"Verified {len(entries)}/{len(entries)} canonical original inputs ({version}).")
    return entries


def compare_outputs(entries, orig, root=Path(".")):
    for relative, output, digest in entries:
        original = checked_path(orig, relative).read_bytes()
        rebuilt = checked_path(root, output).read_bytes()
        if hashlib.sha1(rebuilt).hexdigest() != digest:
            raise ValueError(f"Rebuilt hash mismatch: {output}")
        if rebuilt != original:
            raise ValueError(f"Rebuilt bytes differ: {output}")
        print(f"OK: {output}")
    print(f"Verified {len(entries)}/{len(entries)} rebuilt hashes and direct byte comparisons.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--orig", type=Path, required=True)
    parser.add_argument("--zip", type=Path, help="Optional local PRIVATE original-input ZIP")
    parser.add_argument("--outputs", action="store_true", help="Also compare every rebuilt output")
    args = parser.parse_args()
    try:
        entries = prepare_inputs(args.manifest, args.orig, args.zip)
        if args.outputs:
            compare_outputs(entries, args.orig)
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as error:
        print(f"Retail verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
