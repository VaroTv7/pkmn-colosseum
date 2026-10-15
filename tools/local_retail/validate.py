#!/usr/bin/env python3
"""Manually run full retail validation for one BASE/HEAD pair on this machine.

Original game files and compilers stay local. Each revision is exported with
`git archive` into its own disposable Docker volume and built in a container
with networking disabled, no credentials, a read-only root filesystem and
read-only originals/toolchain mounts. A fresh container then copies out only
allowlisted regular files, and this (trusted) process verifies them after all
containers have exited. Publication is a separate step: publish.py.

Run it from a reviewed checkout, not from the candidate being tested:

    python tools/local_retail/validate.py --repo . \
        --dol PATH/main.dol --rel-zip PATH/GC6E01-rel-inputs-complete.zip \
        --toolchain PATH/gc-linux-x86_64-20261014 \
        --base BASE_SHA --head HEAD_SHA --work PATH/OUTSIDE/REPO [--dry-run]
"""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ci_retail import prepare_inputs, read_manifest  # noqa: E402
from tools.local_retail import evidence, toolchain, verify  # noqa: E402

HARNESS = Path(__file__).resolve().parent
VERSION = "GC6E01"
CANONICAL_DOL_SHA1 = "870e8b9693ca780782d80f22a6a4572d8ba9458f"
DEFAULT_IMAGE = "pkmn-local-retail:1"
LABEL = "org.pkmn.local-retail.run"
# The validator's own code and pinned inputs; their digest identifies the verifier.
TRUSTED_FILES = (
    "tools/local_retail/__init__.py", "tools/local_retail/evidence.py",
    "tools/local_retail/harvest.py", "tools/local_retail/publish.py",
    "tools/local_retail/toolchain.py", "tools/local_retail/toolchain.lock.json",
    "tools/local_retail/validate.py", "tools/local_retail/verify.py",
    "tools/local_retail/worker.py", "tools/local_retail/Dockerfile",
    "tools/ci_retail.py", "tools/audit_report_transition.py",
    ".github/scripts/check_metric_integrity.py", ".github/scripts/quality_scan.py",
    ".github/scripts/check_asm_wrappers.py", f"config/{VERSION}/build.sha1",
)
BASE_LOGS = ("configure", "all_source_report")
HEAD_LOGS = BASE_LOGS + ("full_link", "unit_tests", "object_map_freeze", "readme_progress")


class Prerequisite(Exception):
    pass


def run(command, **kwargs):
    return subprocess.run(command, check=True, text=True, capture_output=True, **kwargs).stdout.strip()


def git(repo, *args):
    try:
        return run(["git", "-C", str(repo), *args])
    except subprocess.CalledProcessError as error:
        raise Prerequisite(f"git {' '.join(args)} failed: {error.stderr.strip()}") from error


def resolve(repo, rev, label):
    sha = git(repo, "rev-parse", "--verify", f"{rev}^{{commit}}")
    if len(sha) != 40:
        raise Prerequisite(f"{label} does not resolve to a full commit")
    return sha


def validator_identity():
    digest = hashlib.sha256()
    for relative in TRUSTED_FILES:
        data = (ROOT / relative).read_bytes()
        digest.update(f"{relative} {hashlib.sha256(data).hexdigest()}\n".encode())
    return dict(sha=git(ROOT, "rev-parse", "HEAD"), tree_sha256=digest.hexdigest())


def docker(*args, **kwargs):
    return run(["docker", *args], **kwargs)


def preflight(args):
    """Check every prerequisite before any original input is exposed."""
    if sys.version_info < (3, 9) or not hasattr(tarfile, "data_filter"):
        raise Prerequisite("Python 3.12 (or a 3.9-3.11 release with tarfile extraction filters) is required")
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        raise Prerequisite(f"--repo is not a Git checkout: {repo}")
    work = Path(args.work).resolve()
    if work.is_relative_to(repo) or work.is_relative_to(ROOT):
        raise Prerequisite("--work must be outside the repository so nothing derived from originals can be committed")
    if work.exists() and any(work.iterdir()):
        raise Prerequisite(f"--work must be new or empty for clean BASE/HEAD builds: {work}")
    if not 1 <= args.jobs <= 8:
        raise Prerequisite("--jobs must be between 1 and 8")
    head, base = resolve(repo, args.head, "--head"), resolve(repo, args.base, "--base")
    if head == base:
        raise Prerequisite("--base and --head are the same commit")
    pinned = Path(args.manifest).resolve()
    _, entries = read_manifest(pinned)
    dol_digest = {relative: digest for relative, _, digest in entries}.get("sys/main.dol")
    if dol_digest != CANONICAL_DOL_SHA1:
        raise Prerequisite("Pinned manifest does not carry the canonical DOL SHA-1")
    try:
        tools = toolchain.verify(args.toolchain)
    except (OSError, ValueError) as error:
        raise Prerequisite(f"Toolchain: {error}. Install it with tools/local_retail/toolchain.py install") from error
    for label, path in (("--dol", args.dol), ("--rel-zip", args.rel_zip)):
        if not Path(path).is_file():
            raise Prerequisite(f"{label} not found: {path}. Point it at your local original input")
    try:
        docker("info", "--format", "{{.OSType}}")
        image = docker("image", "inspect", args.image, "--format", "{{.Id}}")
    except (OSError, subprocess.CalledProcessError) as error:
        raise Prerequisite(f"Docker daemon or local image {args.image!r} unavailable; build it with "
                           f"docker build -t {args.image} tools/local_retail") from error
    with tempfile.TemporaryDirectory() as tmp:
        stage_originals(pinned, args.dol, args.rel_zip, Path(tmp) / "orig" / VERSION)
    return dict(repo=repo, work=work, head=head, base=base, pinned=pinned, toolchain=tools,
                image=image, entries=entries)


def stage_originals(pinned, dol, rel_zip, dest):
    """Verify all canonical originals with the trusted loader before staging them."""
    data = Path(dol).read_bytes()
    if hashlib.sha1(data).hexdigest() != CANONICAL_DOL_SHA1:
        raise Prerequisite("--dol is not the canonical original main.dol")
    dest.joinpath("sys").mkdir(parents=True)
    dest.joinpath("sys/main.dol").write_bytes(data)
    try:
        prepare_inputs(pinned, dest, rel_zip)
    except ValueError as error:
        raise Prerequisite(f"Original inputs: {error}") from error


class Sandbox:
    def __init__(self, image, run_id, jobs):
        self.image, self.run_id, self.jobs = image, run_id, jobs
        self.volumes = []

    def base_flags(self):
        return ["--rm", "--network", "none", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                "--pids-limit", "4096", "--label", f"{LABEL}={self.run_id}", "--read-only",
                "--tmpfs", "/tmp:rw,exec,size=2g", "--env", "HOME=/tmp"]

    def volume(self, side):
        name = f"pkmn-local-retail-{self.run_id}-{side}"
        docker("volume", "create", "--label", f"{LABEL}={self.run_id}", name)
        self.volumes.append(name)
        return name

    def load_source(self, repo, sha, volume):
        archive = subprocess.Popen(["git", "-C", str(repo), "archive", "--format=tar", sha], stdout=subprocess.PIPE)
        subprocess.run(["docker", "run", "-i", *self.base_flags(), "--mount", f"type=volume,source={volume},target=/w",
                        self.image, "tar", "-x", "-C", "/w"], stdin=archive.stdout, check=True)
        archive.stdout.close()
        if archive.wait() != 0:
            raise RuntimeError(f"git archive {sha} failed")

    def build(self, side, volume, orig_root, tools):
        command = ["docker", "run", *self.base_flags(), "--cpus", str(self.jobs), "--memory", "8g",
                   "--mount", f"type=volume,source={volume},target=/w",
                   "--mount", f"type=bind,source={orig_root},target=/w/orig,readonly",
                   "--mount", f"type=bind,source={tools},target=/toolchain,readonly",
                   "--mount", f"type=bind,source={HARNESS},target=/harness,readonly",
                   self.image, "python3", "/harness/worker.py", "--side", side, "--jobs", str(self.jobs)]
        return subprocess.run(command).returncode

    def harvest(self, volume, dest, paths):
        dest.mkdir(parents=True)
        subprocess.run(["docker", "run", *self.base_flags(),
                        "--mount", f"type=volume,source={volume},target=/w,readonly",
                        "--mount", f"type=bind,source={dest},target=/out",
                        "--mount", f"type=bind,source={HARNESS},target=/harness,readonly",
                        self.image, "python3", "/harness/harvest.py", *paths], check=True)

    def cleanup(self):
        for name in self.volumes:
            subprocess.run(["docker", "volume", "rm", "-f", name], capture_output=True)

    def assert_exited(self):
        alive = docker("ps", "-aq", "--filter", f"label={LABEL}={self.run_id}")
        if alive:
            raise RuntimeError("Worker containers are still present; refusing to verify")


def host_quality(repo, root, base, head, head_src):
    # UTF-8 mode matches the Linux CI runners; Windows' locale codec cannot read the sources.
    env = dict(os.environ, PYTHONUTF8="1")
    scan = subprocess.run([sys.executable, str(root / ".github/scripts/quality_scan.py"), base, head],
                          cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    wrappers = subprocess.run([sys.executable, str(root / ".github/scripts/check_asm_wrappers.py"),
                               str(head_src / "src")], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=env)
    return scan, wrappers


def extract_tree(repo, sha, dest):
    dest.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", sha],
                             capture_output=True, check=True).stdout
    def regular_source(member, path):
        # Links are never materialized on the host; only src/ is scanned here.
        if not (member.isfile() or member.isdir()) or not member.name.startswith("src/"):
            return None
        return tarfile.data_filter(member, path)

    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(dest, filter=regular_source)


def parse_drift(text):
    if not text:
        return None
    try:
        values = tuple(int(part) for part in text.split(","))
    except ValueError:
        values = ()
    if len(values) != 3:
        raise argparse.ArgumentTypeError("expected CODE,DATA,FUNCTIONS byte/function deltas")
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, help="Git checkout containing both revisions")
    parser.add_argument("--dol", required=True, help="Local original main.dol")
    parser.add_argument("--rel-zip", required=True, help="Local verified original REL ZIP")
    parser.add_argument("--toolchain", required=True, help="Installed pinned toolchain directory")
    parser.add_argument("--base", required=True, help="BASE commit (the PR's current base tip)")
    parser.add_argument("--head", required=True, help="HEAD commit (the exact PR head)")
    parser.add_argument("--work", required=True, help="New directory outside the repository")
    parser.add_argument("--repository", default="dougchansan/pkmn-colosseum")
    parser.add_argument("--manifest", default=str(ROOT / "config" / VERSION / "build.sha1"),
                        help="Pinned canonical manifest (default: the validator checkout's)")
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--reviewed-dol-drift", type=parse_drift, default=None,
                        help="Reviewed DOL denominator change CODE,DATA,FUNCTIONS (default: none allowed)")
    parser.add_argument("--dry-run", action="store_true", help="Run every preflight check, then stop")
    parser.add_argument("--keep-volumes", action="store_true")
    args = parser.parse_args()

    try:
        ctx = preflight(args)
    except (Prerequisite, OSError, ValueError) as error:
        print(f"Preflight failed: {error}", file=sys.stderr)
        return 2
    print(f"Preflight OK: head {ctx['head']}, base {ctx['base']}, toolchain {ctx['toolchain']['id']}, "
          f"image {ctx['image']}, {len(ctx['entries'])} canonical outputs, originals verified.")
    if args.dry_run:
        return 0

    work = ctx["work"]
    work.mkdir(parents=True, exist_ok=True)
    try:
        summary = execute(args, ctx, work)
    finally:
        # Keep reports and logs locally; never leave the staged originals, or the
        # rebuilt binaries that are byte-identical to them, behind.
        for scratch in ("orig", "head-src"):
            shutil.rmtree(work / scratch, ignore_errors=True)
        for binary in list((work / "raw").rglob("*.dol")) + list((work / "raw").rglob("*.rel")):
            binary.unlink()
    print(json.dumps(dict(passed=summary["passed"], checks=summary["checks"], outputs=summary["outputs"],
                          audit=summary["audit"], drift=summary["denominator_drift"]), indent=1))
    print(f"Summary: {work / 'results' / 'summary.json'} (publish with tools/local_retail/publish.py)")
    return 0 if summary["passed"] else 1


def execute(args, ctx, work):
    orig = work / "orig" / VERSION
    stage_originals(ctx["pinned"], args.dol, args.rel_zip, orig)
    head_src = work / "head-src"
    extract_tree(ctx["repo"], ctx["head"], head_src)

    run_id = uuid.uuid4().hex[:12]
    sandbox = Sandbox(ctx["image"], run_id, args.jobs)
    outputs = [output for _, output, _ in ctx["entries"]]
    report = f"build/{VERSION}/report.json"
    try:
        for side, sha, logs in (("base", ctx["base"], BASE_LOGS), ("head", ctx["head"], HEAD_LOGS)):
            volume = sandbox.volume(side)
            sandbox.load_source(ctx["repo"], sha, volume)
            print(f"[{side}] building {sha} in network-less container (-j{args.jobs})", flush=True)
            rc = sandbox.build(side, volume, orig.parent, Path(args.toolchain).resolve())
            print(f"[{side}] worker exited with {rc}", flush=True)
            paths = [report, "_worker/result.json"] + [f"_worker/{name}.log" for name in logs]
            if side == "head":
                paths += outputs
            sandbox.harvest(volume, work / "raw" / side, paths)
        sandbox.assert_exited()
    finally:
        if not args.keep_volumes:
            sandbox.cleanup()

    scan, wrappers = host_quality(ctx["repo"], ROOT, ctx["base"], ctx["head"], head_src)
    (work / "raw" / "quality_scan.log").write_text(scan.stdout + scan.stderr, encoding="utf-8")
    (work / "raw" / "asm_wrappers.log").write_text(wrappers.stdout + wrappers.stderr, encoding="utf-8")
    repo = ctx["repo"]
    verify_ctx = dict(
        raw=work / "raw", orig=orig, repository=args.repository,
        head=ctx["head"], head_tree=git(repo, "rev-parse", f"{ctx['head']}^{{tree}}"),
        base=ctx["base"], base_tree=git(repo, "rev-parse", f"{ctx['base']}^{{tree}}"),
        merge_base=git(repo, "merge-base", ctx["base"], ctx["head"]),
        toolchain=dict(id=ctx["toolchain"]["id"], tree_sha256=ctx["toolchain"]["tree_sha256"]),
        worker_image=ctx["image"], validator=validator_identity(),
        pinned_manifest=ctx["pinned"].read_text(encoding="utf-8"),
        head_manifest=git(repo, "show", f"{ctx['head']}:config/{VERSION}/build.sha1") + "\n",
        base_manifest=git(repo, "show", f"{ctx['base']}:config/{VERSION}/build.sha1") + "\n",
        toolchain_verified=toolchain.verify(args.toolchain)["tree_sha256"] == ctx["toolchain"]["tree_sha256"],
        inputs_verified=True, quality_scan=scan.returncode == 0, asm_wrappers=wrappers.returncode == 0,
        reviewed_drift=args.reviewed_dol_drift,
        created=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    summary, evidence_files, notes = verify.verify(verify_ctx)
    results = work / "results"
    (results / "evidence").mkdir(parents=True)
    for name, data in evidence_files.items():
        evidence.evidence_path(results, name).write_bytes(data)
    (results / "notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
    (results / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return summary

if __name__ == "__main__":
    raise SystemExit(main())
