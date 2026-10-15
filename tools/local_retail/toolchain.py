#!/usr/bin/env python3
"""Install and verify the pinned local retail-validation toolchain.

The toolchain is acquired and hash-checked before any original game input is
exposed to a build. Nothing here reads or writes original game files.

    python tools/local_retail/toolchain.py install --downloads DIR --dest DIR [--fetch]
    python tools/local_retail/toolchain.py verify --dest DIR
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import urllib.request
import zipfile

LOCK = Path(__file__).resolve().with_name("toolchain.lock.json")
TREE_MANIFEST = "TOOLCHAIN.json"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_lock(path=LOCK):
    lock = json.loads(Path(path).read_text(encoding="utf-8"))
    if lock.get("schema") != 1 or not lock.get("artifacts"):
        raise ValueError("Unsupported toolchain lock")
    for name, item in lock["artifacts"].items():
        target = PurePosixPath(item["target"])
        if target.is_absolute() or ".." in target.parts or item["install"] not in ("unzip", "file"):
            raise ValueError(f"Unsafe toolchain lock entry: {name}")
    return lock


def safe_extract(archive, dest):
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            parts = PurePosixPath(info.filename).parts
            if (info.filename.startswith("/") or ".." in parts or "\\" in info.filename
                    or ":" in info.filename or stat.S_ISLNK(info.external_attr >> 16)):
                raise ValueError(f"Unsafe toolchain archive member: {info.filename}")
        bundle.extractall(dest)


def install(downloads, dest, fetch=False, lock_path=LOCK):
    lock = load_lock(lock_path)
    downloads, dest = Path(downloads), Path(dest)
    if dest.exists():
        raise ValueError(f"Destination already exists: {dest}")
    downloads.mkdir(parents=True, exist_ok=True)
    for name, item in lock["artifacts"].items():
        source = downloads / PurePosixPath(item["url"]).name
        if not source.is_file() and fetch:
            print(f"Fetching {item['url']}")
            request = urllib.request.Request(item["url"], headers={"User-Agent": "pkmn-local-retail"})
            with urllib.request.urlopen(request, timeout=120) as response, open(source, "xb") as out:
                shutil.copyfileobj(response, out)
        if not source.is_file():
            raise ValueError(f"Missing toolchain download for {name}: {source}")
        if sha256_file(source) != item["sha256"]:
            raise ValueError(f"Toolchain download hash mismatch: {name}")
    staging = dest.with_name(dest.name + ".partial")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for name, item in lock["artifacts"].items():
        source = downloads / PurePosixPath(item["url"]).name
        target = staging / item["target"]
        if item["install"] == "unzip":
            target.mkdir(parents=True)
            safe_extract(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    for path in staging.rglob("*"):
        if path.is_file():
            path.chmod(0o755)
    files = tree_files(staging)
    manifest = dict(schema=1, lock_id=lock["id"], lock_sha256=sha256_file(lock_path), files=files)
    (staging / TREE_MANIFEST).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    staging.rename(dest)
    print(f"Installed {len(files)} toolchain files ({lock['id']}) into {dest}")
    return verify(dest, lock_path)


def tree_files(root):
    root = Path(root)
    files = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if relative == TREE_MANIFEST:
            continue
        if path.is_symlink():
            raise ValueError(f"Toolchain contains a symlink: {relative}")
        if path.is_file():
            files[relative] = sha256_file(path)
    return files


def verify(dest, lock_path=LOCK):
    """Re-hash every installed file. Returns the toolchain identity digest."""
    dest = Path(dest)
    lock = load_lock(lock_path)
    manifest_path = dest / TREE_MANIFEST
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError(f"Toolchain is not installed: missing {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("lock_id") != lock["id"] or manifest.get("lock_sha256") != sha256_file(lock_path):
        raise ValueError("Installed toolchain does not match the pinned lock")
    actual = tree_files(dest)
    if actual != manifest.get("files"):
        changed = sorted(set(actual.items()) ^ set(manifest.get("files", {}).items()))
        raise ValueError(f"Toolchain files changed since installation: {changed[:5]}")
    identity = hashlib.sha256("".join(f"{k} {v}\n" for k, v in sorted(actual.items())).encode()).hexdigest()
    return dict(id=lock["id"], tree_sha256=identity, files=len(actual))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    install_parser = sub.add_parser("install")
    install_parser.add_argument("--downloads", type=Path, required=True)
    install_parser.add_argument("--dest", type=Path, required=True)
    install_parser.add_argument("--fetch", action="store_true", help="Download missing pinned artifacts")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = install(args.downloads, args.dest, args.fetch) if args.command == "install" else verify(args.dest)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f"Toolchain error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
