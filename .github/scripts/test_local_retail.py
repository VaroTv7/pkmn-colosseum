"""Local retail validation, verification and publication gates on synthetic fixtures."""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.local_retail import evidence, harvest, publish, toolchain, validate, verify  # noqa: E402

SHA_A, SHA_B, SHA_M = "a" * 40, "b" * 40, "c" * 40
TREE_A, TREE_B = "d" * 40, "e" * 40


def function(name, address, size, score=100.0):
    return dict(name=name, size=str(size), fuzzy_match_percent=score,
                metadata=dict(virtual_address=str(address)))


def unit(module, name, functions):
    sizes = [int(f["size"]) for f in functions]
    matched = [int(f["size"]) for f in functions if f["fuzzy_match_percent"] == 100.0]
    return dict(name=f"{module}/{name}", metadata=dict(module_name=module), functions=functions,
                measures=dict(total_code=str(sum(sizes)), matched_code=str(sum(matched)),
                              total_data="0", matched_data="0", total_functions=len(functions),
                              matched_functions=len(matched)))


def report(units):
    measures = {key: sum(int(u["measures"][key]) for u in units) for key in evidence.SCOPE_FIELDS}
    return dict(units=units, measures=measures)


def dol_bytes(text_size):
    header = bytearray(0x100)
    header[0x90:0x90 + 72] = struct.pack(">18I", text_size, *([0] * 17))
    return bytes(header) + b"synthetic-dol"


class Fixture:
    """A complete passing BASE/HEAD run on disk; tests then break one thing."""

    def __init__(self, root):
        self.root = Path(root)
        self.base_report = report([unit("main", "a", [function("f1", 0x80000000, 16), function("f2", 0x80000010, 8, 50.0)])])
        self.head_report = report([
            unit("main", "a", [function("f1", 0x80000000, 16), function("f2_named", 0x80000010, 8),
                               function("f3_new", 0x80000018, 4)]),
            unit("mod", "b", [function("_prolog", 0, 4)]),
        ])
        self.dol = dol_bytes(self.head_report["measures"]["total_code"])
        self.rel = b"synthetic-rel"
        self.manifest = (hashlib.sha1(self.dol).hexdigest() + "  build/GC6E01/main.dol\n"
                         + hashlib.sha1(self.rel).hexdigest() + "  build/GC6E01/mod/mod.rel\n")
        self.orig = self.root / "orig"
        self.write(self.orig / "sys/main.dol", self.dol)
        self.write(self.orig / "files/mod.rel", self.rel)
        self.raw = self.root / "raw"
        self.write(self.raw / "head/build/GC6E01/main.dol", self.dol)
        self.write(self.raw / "head/build/GC6E01/mod/mod.rel", self.rel)
        self.set_report("head", self.head_report)
        self.set_report("base", self.base_report)
        self.set_worker("head", {"configure": 0, "all_source_report": 0, "full_link": 0,
                                 "unit_tests": 0, "object_map_freeze": 0, "readme_progress": 0})
        self.set_worker("base", {"configure": 0, "all_source_report": 0})
        self.ctx = dict(
            raw=self.raw, orig=self.orig, repository="owner/repo",
            head=SHA_A, head_tree=TREE_A, base=SHA_B, base_tree=TREE_B, merge_base=SHA_M,
            toolchain=dict(id="synthetic", tree_sha256="1" * 64), worker_image="sha256:" + "2" * 64,
            validator=dict(sha=SHA_M, tree_sha256="3" * 64),
            pinned_manifest=self.manifest, head_manifest=self.manifest,
            base_manifest=self.manifest.splitlines()[0] + "\n",
            toolchain_verified=True, inputs_verified=True, quality_scan=True, asm_wrappers=True,
            reviewed_drift=(4, 0, 1), created="2026-10-14T00:00:00Z")

    @staticmethod
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def set_report(self, side, data):
        self.write(self.raw / side / "build/GC6E01/report.json", json.dumps(data).encode())

    def set_worker(self, side, steps, extra=None):
        result = dict(schema=1, side=side, steps=[dict(name=k, rc=v, seconds=1.0) for k, v in steps.items()])
        result.update(extra or {})
        self.write(self.raw / side / "_worker/result.json", json.dumps(result).encode())

    def run(self):
        return verify.verify(self.ctx)


class VerifierTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.fx = Fixture(tmp.name)

    def failed(self, summary):
        self.assertFalse(summary["passed"])
        return {k for k, v in summary["checks"].items() if v != "pass"}

    def test_complete_run_passes_with_separate_scopes(self):
        summary, files, _ = self.fx.run()
        self.assertTrue(summary["passed"], summary["checks"])
        self.assertEqual(summary["outputs"], dict(expected=2, verified=2))
        self.assertEqual(summary["metrics"]["head_dol"]["total_code"], 28)
        self.assertEqual(summary["metrics"]["head_combined"]["total_code"], 32)
        self.assertEqual(summary["denominator_drift"], dict(code=4, data=0, functions=1, reviewed=True))
        self.assertEqual(summary["audit"]["new_rel_functions"], 1)
        self.assertEqual(summary["audit"]["renamed"], 1)
        self.assertEqual(summary["evidence"]["head_report"], evidence.sha256_bytes(files["head_report"]))

    def test_failed_compile_never_passes(self):
        self.fx.set_worker("head", {"configure": 0, "all_source_report": 1})
        failed = self.failed(self.fx.run()[0])
        self.assertIn("all_source", failed)
        self.assertIn("full_link", failed)
        self.assertIn("outputs_verified", failed)

    def test_failed_base_build_fails_regression(self):
        self.fx.set_worker("base", {"configure": 1})
        self.assertIn("base_report", self.failed(self.fx.run()[0]))

    def test_missing_output(self):
        (self.fx.raw / "head/build/GC6E01/mod/mod.rel").unlink()
        self.assertIn("outputs_verified", self.failed(self.fx.run()[0]))

    def test_corrupt_output(self):
        Fixture.write(self.fx.raw / "head/build/GC6E01/mod/mod.rel", b"synthetic-reL")
        self.assertIn("outputs_verified", self.failed(self.fx.run()[0]))

    def test_corrupt_original_breaks_byte_comparison(self):
        Fixture.write(self.fx.orig / "files/mod.rel", b"other")
        self.assertIn("outputs_verified", self.failed(self.fx.run()[0]))

    @unittest.skipIf(os.name == "nt", "symlink creation needs privileges on Windows")
    def test_symlinked_output_is_rejected(self):
        target = self.fx.raw / "head/build/GC6E01/main.dol"
        target.unlink()
        target.symlink_to(self.fx.orig / "sys/main.dol")
        self.assertIn("outputs_verified", self.failed(self.fx.run()[0]))

    def test_tampered_head_manifest(self):
        self.fx.ctx["head_manifest"] = self.fx.manifest.replace(self.fx.manifest[:4], "0000", 1)
        self.assertIn("manifest_pinned", self.failed(self.fx.run()[0]))

    def test_unexpected_worker_field_is_untrusted(self):
        self.fx.set_worker("head", {"configure": 0, "all_source_report": 0, "full_link": 0},
                           extra=dict(passed=True))
        self.assertIn("full_link", self.failed(self.fx.run()[0]))

    def test_unknown_worker_step_is_untrusted(self):
        self.fx.set_worker("head", {"configure": 0, "all_source_report": 0, "full_link": 0, "publish": 0})
        self.assertIn("configure", self.failed(self.fx.run()[0]))

    def test_score_regression(self):
        data = copy.deepcopy(self.fx.head_report)
        data["units"][0]["functions"][0]["fuzzy_match_percent"] = 99.0
        self.fx.set_report("head", data)
        self.assertIn("no_regressions", self.failed(self.fx.run()[0]))

    def test_unexplained_function_removal(self):
        data = copy.deepcopy(self.fx.head_report)
        data["units"][0] = unit("main", "a", [function("f1", 0x80000000, 16), function("f3_new", 0x80000018, 4)])
        data["measures"] = report(data["units"])["measures"]
        self.fx.set_report("head", data)
        self.assertIn("no_unexplained_removals", self.failed(self.fx.run()[0]))

    def test_duplicate_identity(self):
        data = copy.deepcopy(self.fx.head_report)
        data["units"].append(unit("main", "dup", [function("again", 0x80000000, 16)]))
        data["measures"] = report(data["units"])["measures"]
        self.fx.set_report("head", data)
        self.assertIn("unique_identities", self.failed(self.fx.run()[0]))

    def test_unreviewed_denominator_drift(self):
        self.fx.ctx["reviewed_drift"] = None
        self.assertIn("denominator_reviewed", self.failed(self.fx.run()[0]))

    def test_failed_host_quality_scan(self):
        self.fx.ctx["quality_scan"] = False
        self.assertIn("quality_scan", self.failed(self.fx.run()[0]))

    def test_missing_report(self):
        (self.fx.raw / "head/build/GC6E01/report.json").unlink()
        self.assertIn("no_regressions", self.failed(self.fx.run()[0]))


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        fx = Fixture(self.root / "fx")
        self.summary, files, _ = fx.run()
        self.results = self.root / "results"
        (self.results / "evidence").mkdir(parents=True)
        for name, data in files.items():
            evidence.evidence_path(self.results, name).write_bytes(data)

    def test_valid_summary_and_evidence(self):
        evidence.check_evidence(evidence.validate_summary(copy.deepcopy(self.summary)), self.results)

    def test_unexpected_fields_are_rejected(self):
        for path in ((), ("checks",), ("metrics", "head_dol"), ("audit",)):
            bad = copy.deepcopy(self.summary)
            target = bad
            for key in path:
                target = target[key]
            target["note"] = "free text"
            with self.assertRaises(evidence.EvidenceError):
                evidence.validate_summary(bad)

    def test_invalid_values_are_rejected(self):
        for mutate in (lambda s: s["head"].update(sha="HEAD"), lambda s: s["checks"].update(configure="ok"),
                       lambda s: s["audit"].update(regressions=-1), lambda s: s["outputs"].update(verified=True),
                       lambda s: s.update(repository="../evil"), lambda s: s["metrics"]["head_dol"].update(matched_code=10**9)):
            bad = copy.deepcopy(self.summary)
            mutate(bad)
            with self.assertRaises(evidence.EvidenceError):
                evidence.validate_summary(bad)

    def test_claimed_success_with_failed_check_is_rejected(self):
        bad = copy.deepcopy(self.summary)
        bad["checks"]["full_link"] = "fail"
        with self.assertRaises(evidence.EvidenceError):
            evidence.validate_summary(bad)

    def test_oversized_summary_is_rejected(self):
        path = self.root / "summary.json"
        path.write_text(json.dumps(self.summary) + " " * evidence.MAX_SUMMARY_BYTES)
        with self.assertRaises(evidence.EvidenceError):
            evidence.load_summary(path)

    def test_tampered_evidence_is_rejected(self):
        evidence.evidence_path(self.results, "audit").write_bytes(b"{}\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_evidence(self.summary, self.results)

    @unittest.skipIf(os.name == "nt", "symlink creation needs privileges on Windows")
    def test_symlinked_evidence_is_rejected(self):
        path = evidence.evidence_path(self.results, "audit")
        (self.root / "elsewhere.json").write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(self.root / "elsewhere.json")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_evidence(self.summary, self.results)


class PublisherTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.summary = Fixture(tmp.name).run()[0]
        self.github = {
            "repos/owner/repo/pulls/1": dict(state="open", head=dict(sha=SHA_A),
                                             base=dict(ref="master", repo=dict(full_name="owner/repo"))),
            "repos/owner/repo/git/ref/heads/master": dict(object=dict(sha=SHA_B)),
            f"repos/owner/repo/commits/{SHA_A}": dict(commit=dict(tree=dict(sha=TREE_A))),
        }

    def fetch(self, path):
        return self.github[path]

    def test_binding_to_exact_head_tree_and_base(self):
        self.assertEqual(publish.bind(self.summary, 1, self.fetch), SHA_A)

    def test_stale_head_base_tree_or_closed_pr_is_refused(self):
        for path, value in (("repos/owner/repo/pulls/1", dict(head=dict(sha="f" * 40))),
                            ("repos/owner/repo/git/ref/heads/master", dict(object=dict(sha="f" * 40))),
                            (f"repos/owner/repo/commits/{SHA_A}", dict(commit=dict(tree=dict(sha="f" * 40)))),
                            ("repos/owner/repo/pulls/1", dict(state="closed"))):
            saved = copy.deepcopy(self.github)
            self.github[path].update(value)
            with self.assertRaises(publish.BindingError):
                publish.bind(self.summary, 1, self.fetch)
            self.github = saved

    def test_success_only_from_passing_checks(self):
        self.assertEqual([s["state"] for s in publish.statuses(self.summary)], ["success", "success"])
        for check in evidence.CHECKS:
            bad = copy.deepcopy(self.summary)
            bad["checks"][check] = "fail"
            self.assertIn("failure", [s["state"] for s in publish.statuses(bad)], check)
        bad = copy.deepcopy(self.summary)
        bad["outputs"]["verified"] = 1
        self.assertEqual(publish.statuses(bad)[0]["state"], "failure")
        self.assertTrue(all(len(s["description"]) <= 140 for s in publish.statuses(self.summary)))

    def test_invalid_summary_publishes_nothing(self):
        bad = copy.deepcopy(self.summary)
        bad["passed"] = True
        bad["checks"]["configure"] = "fail"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(bad))
            calls = []
            with mock.patch.object(publish, "gh_api", side_effect=lambda *a, **k: calls.append(a)), \
                    mock.patch.object(sys, "argv", ["publish.py", "--summary", str(path), "--pr", "1", "--post"]):
                self.assertEqual(publish.main(), 3)
            self.assertEqual(calls, [])


class ToolchainTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.downloads = self.root / "dl"
        self.downloads.mkdir()
        (self.downloads / "tool").write_bytes(b"tool")
        with zipfile.ZipFile(self.downloads / "pack.zip", "w") as bundle:
            bundle.writestr("GC/cc.exe", b"cc")
        self.lock = self.root / "lock.json"
        self.write_lock()

    def write_lock(self, tool_hash=None):
        artifacts = dict(
            tool=dict(url="https://example.invalid/tool", install="file", target="bin/tool",
                      sha256=tool_hash or toolchain.sha256_file(self.downloads / "tool")),
            pack=dict(url="https://example.invalid/pack.zip", install="unzip", target="compilers",
                      sha256=toolchain.sha256_file(self.downloads / "pack.zip")))
        self.lock.write_text(json.dumps(dict(schema=1, id="synthetic", artifacts=artifacts)))

    def test_install_verify_and_detect_tampering(self):
        dest = self.root / "tc"
        identity = toolchain.install(self.downloads, dest, lock_path=self.lock)
        self.assertEqual(identity["files"], 2)
        self.assertEqual(toolchain.verify(dest, self.lock), identity)
        (dest / "compilers/GC/cc.exe").write_bytes(b"patched")
        with self.assertRaises(ValueError):
            toolchain.verify(dest, self.lock)

    def test_download_hash_mismatch(self):
        self.write_lock(tool_hash="0" * 64)
        with self.assertRaises(ValueError):
            toolchain.install(self.downloads, self.root / "tc", lock_path=self.lock)

    def test_unsafe_archive_member(self):
        with zipfile.ZipFile(self.downloads / "pack.zip", "w") as bundle:
            bundle.writestr("../escape", b"x")
        self.write_lock()
        with self.assertRaises(ValueError):
            toolchain.install(self.downloads, self.root / "tc", lock_path=self.lock)


class OriginalInputTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.fx = Fixture(self.root / "fx")
        self.manifest = self.root / "build.sha1"
        self.manifest.write_text(self.fx.manifest)
        self.dol = self.root / "main.dol"
        self.dol.write_bytes(self.fx.dol)
        self.zip = self.root / "inputs.zip"
        with zipfile.ZipFile(self.zip, "w") as bundle:
            bundle.writestr("orig/GC6E01/files/mod.rel", self.fx.rel)
        patcher = mock.patch.object(validate, "CANONICAL_DOL_SHA1", hashlib.sha1(self.fx.dol).hexdigest())
        patcher.start()
        self.addCleanup(patcher.stop)

    def stage(self, name):
        validate.stage_originals(self.manifest, self.dol, self.zip, self.root / name / "GC6E01")

    def test_complete_inputs_stage(self):
        self.stage("ok")
        self.assertEqual((self.root / "ok/GC6E01/files/mod.rel").read_bytes(), self.fx.rel)

    def test_corrupt_dol(self):
        self.dol.write_bytes(b"corrupt")
        with self.assertRaises(validate.Prerequisite):
            self.stage("bad")

    def test_missing_and_corrupt_rel(self):
        for content in (None, b"corrupt"):
            with zipfile.ZipFile(self.zip, "w") as bundle:
                if content is not None:
                    bundle.writestr("orig/GC6E01/files/mod.rel", content)
            with self.assertRaises((validate.Prerequisite, ValueError)):
                self.stage(f"bad{content is None}")


@unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "harvest runs in the Linux worker")
class HarvestTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.src, self.out = self.root / "w", self.root / "out"
        (self.src / "build").mkdir(parents=True)
        self.out.mkdir()
        (self.src / "build/report.json").write_text("{}")
        (self.root / "secret.dol").write_bytes(b"original")

    def test_regular_files_only(self):
        os.symlink(self.root / "secret.dol", self.src / "build/main.dol")
        os.symlink(self.root, self.src / "linkdir")
        record = harvest.harvest(str(self.src), str(self.out),
                                 ["build/report.json", "build/main.dol", "linkdir/secret.dol", "build/none.rel"])
        self.assertEqual(record["build/report.json"], "copied")
        self.assertTrue(record["build/main.dol"].startswith("refused"))
        self.assertTrue(record["linkdir/secret.dol"].startswith("refused"))
        self.assertEqual(record["build/none.rel"], "missing")
        self.assertFalse((self.out / "build/main.dol").exists())

    def test_unsafe_or_unlisted_paths(self):
        for path in ("../secret.dol", "/etc/passwd.log", "build/x.o", "build/a b.log", ""):
            with self.assertRaises(ValueError):
                harvest.harvest(str(self.src), str(self.out), [path])

    def test_oversized_file(self):
        with mock.patch.dict(harvest.MAX_BYTES, {".json": 1}):
            self.assertEqual(harvest.harvest(str(self.src), str(self.out), ["build/report.json"])["build/report.json"],
                             "refused: oversized")


if __name__ == "__main__":
    unittest.main()
