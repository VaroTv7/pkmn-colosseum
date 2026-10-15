#!/usr/bin/env python3
"""Publish a verified local retail-validation summary as commit statuses.

Only this process reads GitHub credentials (through the gh CLI). It publishes
nothing but allowlisted, verifier-computed fields, and only for the exact PR
head, head tree and current base tip that were tested. Without --post it only
prints the payloads.

    python tools/local_retail/publish.py --summary WORK/results/summary.json --pr 638 [--post] [--comment]
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.local_retail import evidence  # noqa: E402

BUILD_CONTEXT = "local-retail/build ({version})"
REGRESSION_CONTEXT = "local-retail/regression ({version})"


class BindingError(Exception):
    pass


def gh_api(path, method="GET", fields=None):
    command = ["gh", "api", "-X", method, path]
    for key, value in (fields or {}).items():
        command += ["-f", f"{key}={value}"]
    return json.loads(subprocess.run(command, check=True, capture_output=True, text=True).stdout or "null")


def bind(summary, pr, fetch=gh_api):
    """The summary must describe the PR exactly as GitHub sees it right now."""
    repo = summary["repository"]
    pull = fetch(f"repos/{repo}/pulls/{pr}")
    if pull.get("state") != "open":
        raise BindingError(f"PR #{pr} is not open")
    head = pull["head"]["sha"]
    if pull["base"]["repo"]["full_name"] != repo:
        raise BindingError("PR does not belong to the summary repository")
    if head != summary["head"]["sha"]:
        raise BindingError(f"stale head: PR is at {head}, summary tested {summary['head']['sha']}")
    base_tip = fetch(f"repos/{repo}/git/ref/heads/{pull['base']['ref']}")["object"]["sha"]
    if base_tip != summary["base"]["sha"]:
        raise BindingError(f"stale base: {pull['base']['ref']} is at {base_tip}, summary tested {summary['base']['sha']}")
    tree = fetch(f"repos/{repo}/commits/{head}")["commit"]["tree"]["sha"]
    if tree != summary["head"]["tree"]:
        raise BindingError("head tree differs from the tested tree")
    return head


def percent(matched, total):
    return f"{100.0 * matched / total:.2f}%" if total else "n/a"


def statuses(summary):
    """Derive both statuses from validated outcomes. Any non-pass is failure."""
    checks, version = summary["checks"], summary["version"]
    outputs, audit, combined = summary["outputs"], summary["audit"], summary["metrics"]["head_combined"]
    build_failed = [name for name in evidence.BUILD_CHECKS if checks[name] != "pass"]
    if outputs["expected"] == 0 or outputs["verified"] != outputs["expected"]:
        build_failed.append("outputs_count")
    regression_failed = [name for name in evidence.REGRESSION_CHECKS if checks[name] != "pass"]
    tested = f"tested {summary['head']['sha'][:8]} on {summary['base']['sha'][:8]}"
    if build_failed:
        build = ("failure", f"Failed: {', '.join(build_failed)}")
    else:
        build = ("success", f"{outputs['verified']}/{outputs['expected']} outputs hash+byte verified, all source built, "
                            f"code {percent(combined['matched_code'], combined['total_code'])}; {tested}")
    if regression_failed:
        regression = ("failure", f"Failed: {', '.join(regression_failed)}")
    else:
        regression = ("success", f"{audit['compared']} identities: {audit['regressions']} regressions, "
                                 f"{audit['missing']} unexplained removals; {tested}")
    return [
        dict(context=BUILD_CONTEXT.format(version=version), state=build[0], description=build[1][:140]),
        dict(context=REGRESSION_CONTEXT.format(version=version), state=regression[0], description=regression[1][:140]),
    ]


def comment(summary):
    metrics = summary["metrics"]
    rows = []
    for label, scope in (("Head DOL only", "head_dol"), ("Head DOL + RELs", "head_combined"), ("Base DOL only", "base_dol")):
        m = metrics[scope]
        rows.append(f"| {label} | {m['matched_code']:,} / {m['total_code']:,} ({percent(m['matched_code'], m['total_code'])}) "
                    f"| {m['matched_functions']:,} / {m['total_functions']:,} "
                    f"| {m['matched_data']:,} / {m['total_data']:,} ({percent(m['matched_data'], m['total_data'])}) |")
    checks = ", ".join(f"{name}={outcome}" for name, outcome in summary["checks"].items())
    return "\n".join([
        "### Local retail validation (machine-generated from the allowlisted summary)",
        f"Head `{summary['head']['sha']}` (tree `{summary['head']['tree']}`), base `{summary['base']['sha']}`.",
        f"Toolchain `{summary['toolchain']['id']}` `{summary['toolchain']['tree_sha256'][:16]}`; "
        f"worker image `{summary['worker_image'][:19]}`; validator `{summary['validator']['sha'][:12]}` "
        f"`{summary['validator']['tree_sha256'][:16]}`.",
        f"Outputs: {summary['outputs']['verified']}/{summary['outputs']['expected']} canonical hash + byte matches. "
        f"Passed: **{summary['passed']}**.",
        "", "| Scope | Matched code | Exact functions | Matched data |", "| --- | ---: | ---: | ---: |", *rows, "",
        f"Audit: {json.dumps(summary['audit'], sort_keys=True)}; DOL denominator drift: "
        f"{json.dumps(summary['denominator_drift'], sort_keys=True)}.",
        f"Checks: {checks}.",
        f"Evidence SHA-256: {json.dumps(summary['evidence'], sort_keys=True)}.",
        "", "Byte-identical outputs still use original fallback objects for unreconstructed regions; "
            "this is not a claim of complete decompilation or gameplay testing.",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--results", type=Path, help="Results directory (default: the summary's directory)")
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--post", action="store_true", help="Actually publish (default: print only)")
    parser.add_argument("--comment", action="store_true", help="Also post the summary table as a PR comment")
    args = parser.parse_args()
    try:
        summary = evidence.load_summary(args.summary)
        evidence.check_evidence(summary, args.results or args.summary.parent)
        sha = bind(summary, args.pr)
    except (evidence.EvidenceError, BindingError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Refusing to publish: {error}", file=sys.stderr)
        return 3
    payloads = statuses(summary)
    for payload in payloads:
        print(json.dumps(payload))
    if args.comment:
        print(comment(summary))
    if not args.post:
        print("Dry run: nothing published (pass --post).")
        return 0
    for payload in payloads:
        gh_api(f"repos/{summary['repository']}/statuses/{sha}", "POST", payload)
    if args.comment:
        gh_api(f"repos/{summary['repository']}/issues/{args.pr}/comments", "POST", dict(body=comment(summary)))
    print(f"Published {len(payloads)} statuses for {sha}.")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
