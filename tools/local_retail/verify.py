"""Trusted verification of a finished local retail validation.

Runs on the host after every worker container has exited. Worker results and
reports are parsed as untrusted data; binaries are re-hashed against the pinned
canonical manifest and compared byte-for-byte with the original inputs.
"""
import collections
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

from tools.audit_report_transition import compare_reports, index_report  # noqa: E402
from tools.ci_retail import read_manifest  # noqa: E402
from tools.local_retail import evidence  # noqa: E402

MAX_REPORT_BYTES = 128 << 20
MAX_WORKER_BYTES = 64 << 10
BASE_STEPS = ("configure", "all_source_report")
HEAD_STEPS = BASE_STEPS + ("full_link",)
HEAD_CHECK_STEPS = ("unit_tests", "object_map_freeze", "readme_progress")
SCOPE_KEYS = evidence.SCOPE_FIELDS
DOL_MODULE = "main"


def regular_bytes(path, limit):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or not a regular file: {path.name}")
    if path.stat().st_size > limit:
        raise ValueError(f"oversized: {path.name}")
    return path.read_bytes()


def load_worker(path, side):
    """Parse an untrusted worker result into {step: rc}."""
    data = json.loads(regular_bytes(path, MAX_WORKER_BYTES).decode("utf-8"))
    if not isinstance(data, dict) or set(data) != {"schema", "side", "steps"} \
            or data["schema"] != 1 or data["side"] != side or not isinstance(data["steps"], list):
        raise ValueError("unexpected worker result shape")
    steps = {}
    allowed = set(HEAD_STEPS + HEAD_CHECK_STEPS)
    for step in data["steps"]:
        if not isinstance(step, dict) or set(step) != {"name", "rc", "seconds"} \
                or step["name"] not in allowed or step["name"] in steps or type(step["rc"]) is not int:
            raise ValueError("unexpected worker step")
        steps[step["name"]] = step["rc"]
    return steps


def scope_measures(report, module=None):
    totals = collections.Counter()
    for unit in report["units"]:
        name = (unit.get("metadata") or {}).get("module_name") or unit["name"].split("/", 1)[0]
        if module is not None and name != module:
            continue
        for key in SCOPE_KEYS:
            totals[key] += int((unit.get("measures") or {}).get(key, 0))
    if module is None:
        for key in SCOPE_KEYS:
            if int(report["measures"].get(key, 0)) != totals[key]:
                raise ValueError(f"report total {key} does not equal its unit sum")
    return {key: totals[key] for key in SCOPE_KEYS}


def metric_integrity(report_path, dol_path):
    import check_metric_integrity
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        rc = check_metric_integrity.main(["check_metric_integrity.py", str(report_path), str(dol_path)])
    return rc == 0, output.getvalue()


def verify_outputs(entries, orig_root, built_root):
    """Every configured output must exist, match its pinned hash and its original."""
    verified, digests = 0, {}
    for relative, output, digest in entries:
        rebuilt = regular_bytes(Path(built_root) / output, 16 << 20)
        original = regular_bytes(Path(orig_root) / relative, 16 << 20)
        if hashlib.sha1(rebuilt).hexdigest() != digest:
            raise ValueError(f"rebuilt hash mismatch: {output}")
        if rebuilt != original:
            raise ValueError(f"rebuilt bytes differ from original: {output}")
        digests[output] = digest
        verified += 1
    return verified, digests


def manifest_entries(text):
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "build.sha1"
        path.write_text(text, encoding="utf-8")
        return read_manifest(path)


def verify(ctx):
    """ctx: dict with pinned/head/base manifest texts, paths and identities.

    Returns (summary, local_audit). Never raises for check failures: a failure
    is recorded as a failed check so that it can only ever publish failure.
    """
    checks = {name: "not_run" for name in evidence.CHECKS}
    notes = []
    raw = Path(ctx["raw"])
    for name in ("toolchain_verified", "inputs_verified"):
        checks[name] = "pass" if ctx[name] else "fail"

    version, pinned = manifest_entries(ctx["pinned_manifest"])
    _, head_entries = manifest_entries(ctx["head_manifest"])
    _, base_entries = manifest_entries(ctx["base_manifest"])
    pinned_set = set(pinned)
    checks["manifest_pinned"] = "pass" if (set(head_entries) == pinned_set
                                           and set(base_entries) <= pinned_set) else "fail"

    def worker(side):
        # A missing step leaves its check "not_run", which can never publish success.
        try:
            return load_worker(raw / side / "_worker" / "result.json", side)
        except (OSError, ValueError) as error:
            notes.append(f"{side} worker result rejected: {error}")
            return {}

    head_steps, base_steps = worker("head"), worker("base")
    for check, step in (("configure", "configure"), ("all_source", "all_source_report"),
                        ("full_link", "full_link"), ("unit_tests", "unit_tests"),
                        ("object_map_freeze", "object_map_freeze"),
                        ("readme_progress", "readme_progress")):
        if step in head_steps:
            checks[check] = "pass" if head_steps[step] == 0 else "fail"
    base_built = all(base_steps.get(step) == 0 for step in BASE_STEPS)
    for name in ("asm_wrappers", "quality_scan"):
        checks[name] = "pass" if ctx[name] else "fail"

    verified, output_digests = 0, {}
    if checks["full_link"] == "pass":
        try:
            verified, output_digests = verify_outputs(pinned, ctx["orig"], raw / "head")
            checks["outputs_verified"] = "pass"
        except (OSError, ValueError) as error:
            checks["outputs_verified"] = "fail"
            notes.append(f"outputs: {error}")

    reports, report_bytes = {}, {}
    for side in ("head", "base"):
        path = raw / side / "build" / version / "report.json"
        try:
            report_bytes[side] = regular_bytes(path, MAX_REPORT_BYTES)
            reports[side] = json.loads(report_bytes[side].decode("utf-8"))
        except (OSError, ValueError) as error:
            notes.append(f"{side} report: {error}")
    checks["base_report"] = "pass" if base_built and "base" in reports else "fail"

    metrics = {scope: {key: 0 for key in SCOPE_KEYS} for scope in ("head_dol", "head_combined", "base_dol")}
    audit_counts = {key: 0 for key in evidence.AUDIT_FIELDS}
    drift = dict(code=0, data=0, functions=0, reviewed=False)
    audit = {}
    if "head" in reports and "base" in reports:
        try:
            index_report(reports["head"]), index_report(reports["base"])
            checks["unique_identities"] = "pass"
            ok, text = metric_integrity(raw / "head" / "build" / version / "report.json", Path(ctx["orig"]) / "sys/main.dol")
            checks["metric_integrity"] = "pass" if ok else "fail"
            notes.append(text.strip())
            audit = compare_reports(reports["base"], reports["head"])
            shrinks = [e for e in audit["boundary_changes"] if e["after"]["size"] < e["before"]["size"]]
            checks["no_regressions"] = "pass" if not audit["regressions"] else "fail"
            checks["no_unexplained_removals"] = "pass" if not audit["missing_functions"] else "fail"
            checks["no_boundary_shrink"] = "pass" if not shrinks else "fail"
            metrics["head_dol"] = scope_measures(reports["head"], DOL_MODULE)
            metrics["head_combined"] = scope_measures(reports["head"])
            metrics["base_dol"] = scope_measures(reports["base"], DOL_MODULE)
            drift.update(
                code=metrics["head_dol"]["total_code"] - metrics["base_dol"]["total_code"],
                data=metrics["head_dol"]["total_data"] - metrics["base_dol"]["total_data"],
                functions=metrics["head_dol"]["total_functions"] - metrics["base_dol"]["total_functions"])
            observed = (drift["code"], drift["data"], drift["functions"])
            drift["reviewed"] = observed == (0, 0, 0) or observed == tuple(ctx["reviewed_drift"] or ())
            checks["denominator_reviewed"] = "pass" if drift["reviewed"] else "fail"
            audit_counts = dict(
                compared=audit["compared_functions"], regressions=len(audit["regressions"]),
                missing=len(audit["missing_functions"]), renamed=len(audit["renamed_functions"]),
                boundary_changes=len(audit["boundary_changes"]), boundary_shrinks=len(shrinks),
                coalesced=len(audit["coalesced_functions"]), new_functions=len(audit["new_functions"]),
                new_rel_functions=sum(1 for f in audit["new_functions"] if f["module"] != DOL_MODULE))
        except (KeyError, TypeError, ValueError) as error:
            notes.append(f"report audit: {error}")
            for name in ("unique_identities", "metric_integrity", "no_regressions",
                         "no_unexplained_removals", "no_boundary_shrink", "denominator_reviewed"):
                if checks[name] == "not_run":
                    checks[name] = "fail"
    else:
        for name in ("unique_identities", "metric_integrity", "no_regressions",
                     "no_unexplained_removals", "no_boundary_shrink", "denominator_reviewed"):
            checks[name] = "fail"

    def canonical(obj):
        return (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode("utf-8")

    evidence_files = {
        "head_report": report_bytes.get("head", b""),
        "base_report": report_bytes.get("base", b""),
        "audit": canonical(audit),
        "outputs": canonical(output_digests),
        "worker_head": canonical(head_steps),
        "worker_base": canonical(base_steps),
    }
    summary = dict(
        schema=evidence.SCHEMA, repository=ctx["repository"], version=version,
        head=dict(sha=ctx["head"], tree=ctx["head_tree"]),
        base=dict(sha=ctx["base"], tree=ctx["base_tree"]),
        merge_base=ctx["merge_base"], toolchain=ctx["toolchain"], worker_image=ctx["worker_image"],
        validator=ctx["validator"], checks=checks, metrics=metrics, audit=audit_counts,
        denominator_drift=drift, outputs=dict(expected=len(pinned), verified=verified),
        evidence={name: evidence.sha256_bytes(data) for name, data in evidence_files.items()},
        passed=False, created=ctx["created"],
    )
    summary["passed"] = evidence.expected_pass(summary)
    evidence.validate_summary(summary)
    return summary, evidence_files, notes
