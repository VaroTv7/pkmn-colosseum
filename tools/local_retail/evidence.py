"""Strict schema for the only local-validation data that may be published.

Everything outside this allowlist (raw logs, reports, maps, disassembly,
objects, binaries, originals, compiler files, free-form text) stays local.
"""
import hashlib
import json
from pathlib import Path
import re

SCHEMA = "pkmn-local-retail/1"
MAX_SUMMARY_BYTES = 16 * 1024
SHA1 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
REPO = re.compile(r"[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}")
IDENT = re.compile(r"[A-Za-z0-9_.-]{1,64}")
TIMESTAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")

BUILD_CHECKS = (
    "toolchain_verified", "inputs_verified", "manifest_pinned", "configure",
    "all_source", "full_link", "outputs_verified", "metric_integrity",
    "object_map_freeze", "readme_progress", "unit_tests", "asm_wrappers",
    "quality_scan",
)
REGRESSION_CHECKS = (
    "base_report", "unique_identities", "no_regressions", "no_unexplained_removals",
    "no_boundary_shrink", "denominator_reviewed",
)
CHECKS = BUILD_CHECKS + REGRESSION_CHECKS
OUTCOMES = ("pass", "fail", "not_run")
SCOPE_FIELDS = ("total_code", "matched_code", "total_data", "matched_data",
                "total_functions", "matched_functions")
AUDIT_FIELDS = ("compared", "regressions", "missing", "renamed", "boundary_changes",
                "boundary_shrinks", "coalesced", "new_functions", "new_rel_functions")
EVIDENCE_FILES = ("head_report", "base_report", "audit", "outputs", "worker_head", "worker_base")


class EvidenceError(ValueError):
    pass


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _fail(message):
    raise EvidenceError(message)


def _exact_keys(obj, keys, where):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        extra = sorted(set(obj) - set(keys)) if isinstance(obj, dict) else []
        missing = sorted(set(keys) - set(obj)) if isinstance(obj, dict) else list(keys)
        _fail(f"{where}: unexpected fields {extra} / missing fields {missing}")


def _match(pattern, value, where):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        _fail(f"{where}: invalid value")


def _count(value, where):
    if type(value) is not int or not 0 <= value < 10**12:
        _fail(f"{where}: not a bounded non-negative integer")


def _signed(value, where):
    if type(value) is not int or abs(value) >= 10**12:
        _fail(f"{where}: not a bounded integer")


def validate_summary(summary):
    """Reject anything that is not exactly the published allowlist."""
    _exact_keys(summary, ("schema", "repository", "version", "head", "base", "merge_base",
                          "toolchain", "worker_image", "validator", "checks", "metrics",
                          "audit", "denominator_drift", "outputs", "evidence", "passed",
                          "created"), "summary")
    if summary["schema"] != SCHEMA:
        _fail("summary: unsupported schema")
    _match(REPO, summary["repository"], "repository")
    _match(IDENT, summary["version"], "version")
    for side in ("head", "base"):
        _exact_keys(summary[side], ("sha", "tree"), side)
        _match(SHA1, summary[side]["sha"], f"{side}.sha")
        _match(SHA1, summary[side]["tree"], f"{side}.tree")
    _match(SHA1, summary["merge_base"], "merge_base")
    _exact_keys(summary["toolchain"], ("id", "tree_sha256"), "toolchain")
    _match(IDENT, summary["toolchain"]["id"], "toolchain.id")
    _match(SHA256, summary["toolchain"]["tree_sha256"], "toolchain.tree_sha256")
    _match(re.compile(r"sha256:[0-9a-f]{64}"), summary["worker_image"], "worker_image")
    _exact_keys(summary["validator"], ("sha", "tree_sha256"), "validator")
    _match(SHA1, summary["validator"]["sha"], "validator.sha")
    _match(SHA256, summary["validator"]["tree_sha256"], "validator.tree_sha256")
    _exact_keys(summary["checks"], CHECKS, "checks")
    for name, outcome in summary["checks"].items():
        if outcome not in OUTCOMES:
            _fail(f"checks.{name}: invalid outcome")
    _exact_keys(summary["metrics"], ("head_dol", "head_combined", "base_dol"), "metrics")
    for scope, values in summary["metrics"].items():
        _exact_keys(values, SCOPE_FIELDS, f"metrics.{scope}")
        for field, value in values.items():
            _count(value, f"metrics.{scope}.{field}")
        if values["matched_code"] > values["total_code"] or values["matched_data"] > values["total_data"] \
                or values["matched_functions"] > values["total_functions"]:
            _fail(f"metrics.{scope}: matched exceeds total")
    _exact_keys(summary["audit"], AUDIT_FIELDS, "audit")
    for field, value in summary["audit"].items():
        _count(value, f"audit.{field}")
    _exact_keys(summary["denominator_drift"], ("code", "data", "functions", "reviewed"), "denominator_drift")
    for field in ("code", "data", "functions"):
        _signed(summary["denominator_drift"][field], f"denominator_drift.{field}")
    if type(summary["denominator_drift"]["reviewed"]) is not bool:
        _fail("denominator_drift.reviewed: not a boolean")
    _exact_keys(summary["outputs"], ("expected", "verified"), "outputs")
    _count(summary["outputs"]["expected"], "outputs.expected")
    _count(summary["outputs"]["verified"], "outputs.verified")
    _exact_keys(summary["evidence"], EVIDENCE_FILES, "evidence")
    for name, digest in summary["evidence"].items():
        _match(SHA256, digest, f"evidence.{name}")
    if type(summary["passed"]) is not bool:
        _fail("passed: not a boolean")
    _match(TIMESTAMP, summary["created"], "created")
    if summary["passed"] != expected_pass(summary):
        _fail("passed: inconsistent with check outcomes")
    return summary


def expected_pass(summary):
    """Success requires every check to pass and every configured output verified."""
    outputs = summary["outputs"]
    return (all(outcome == "pass" for outcome in summary["checks"].values())
            and outputs["expected"] > 0 and outputs["verified"] == outputs["expected"])


def load_summary(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        _fail("summary must be a regular file")
    data = path.read_bytes()
    if len(data) > MAX_SUMMARY_BYTES:
        _fail("summary exceeds the size limit")
    try:
        summary = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"summary is not JSON: {error}")
    return validate_summary(summary)


def evidence_path(results, name):
    return Path(results) / "evidence" / f"{name}.json"


def check_evidence(summary, results):
    """Recompute digests of the locally retained evidence files."""
    results = Path(results).resolve()
    for name, digest in summary["evidence"].items():
        path = evidence_path(results, name)
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(results):
            _fail(f"evidence {name}: missing or not a regular file")
        if sha256_bytes(path.read_bytes()) != digest:
            _fail(f"evidence {name}: digest mismatch (tampered or stale)")
