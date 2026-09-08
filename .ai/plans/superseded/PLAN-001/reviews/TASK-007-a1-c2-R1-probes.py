"""Bounded correction verification; candidate source is read-only, fixtures are native temp Git repositories."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import platform
import sys
import time
import unittest
from pathlib import Path

candidate = Path(sys.argv[1]).resolve(strict=True)
output = Path(sys.argv[2])
assert not output.exists(), "verification evidence is never overwritten"
sys.path[:0] = [str(candidate / "src"), str(candidate / "tests/unit/git")]
import commands
import config
import domain_values
import git_ops
import local_ports
from test_git_ops import GitFixture

NAMES = [
    "BranchTests.test_symbolic_target_alias_is_refused_and_preserves_developer_checkout",
    "BranchTests.test_target_retargeted_to_symbolic_alias_cannot_move_developer_branch",
    "MergeTests.test_branch_switch_after_publication_is_preserved_without_read_tree",
    "InspectTests.test_nested_empty_git_directory_cannot_claim_missing_head",
    "InspectTests.test_inspects_missing_head_explicitly",
    "InspectTests.test_registered_linked_worktree_is_observed",
    "MergeTests.test_concurrent_dirty_change_after_ref_publication_is_preserved",
    "MergeTests.test_concurrent_index_change_after_ref_publication_is_preserved",
    "MergeTests.test_ref_published_but_checkout_not_advanced_stays_unknown_without_retry",
    "MergeTests.test_admitted_managed_integration_is_advanced_and_developer_tree_preserved",
    "BranchTests.test_source_race_aborts_the_guarded_transaction",
    "BranchTests.test_target_race_preserves_the_concurrent_ref",
    "BranchTests.test_completed_receipt_does_not_override_a_later_target_move",
    "BranchTests.test_head_source_is_resolved_and_verified",
    "BranchTests.test_uncertain_publication_is_reconciled_without_duplicate_effect",
]
log = io.StringIO()
start = time.monotonic()
suite = unittest.defaultTestLoader.loadTestsFromNames(["test_git_ops." + name for name in NAMES])
result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
elapsed = time.monotonic() - start
print(log.getvalue(), flush=True)


class RecordingRunner:
    def __init__(self, fixture):
        self.fixture = fixture
        self.records = []

    def execute(self, request):
        observed = self.fixture.runner.execute(request)
        streams = {}
        for name, ref in (("stdout", observed.stdout_ref), ("stderr", observed.stderr_ref)):
            assert ref is not None
            content = (self.fixture.repo / ref.path).read_bytes()
            assert hashlib.sha256(content).hexdigest() == ref.sha256.value
            streams[name] = {"sha256": ref.sha256.value, "base64": base64.b64encode(content).decode()}
        self.records.append({"id": observed.id.value, "argv": observed.argv_redacted,
                             "status": observed.status.value, "exit_code": observed.exit_code,
                             "truncated": observed.output_truncated, "redacted": observed.redactions_applied,
                             "streams": streams})
        return observed


def metadata_observation(linked):
    f = GitFixture()
    f.setUp()
    recorder = RecordingRunner(f)
    try:
        if linked:
            path, binding, _ = f.managed_integration()
            marker = path / ".git"
            original_pointer = marker.read_bytes()
            metadata = Path(f.git("rev-parse", "--absolute-git-dir", cwd=path).strip())
            assert metadata.resolve().is_relative_to(f.repo.resolve())
            # Remove only this disposable fixture's HEAD, leaving Git's pointers unchanged.
            (metadata / "HEAD").unlink()
        else:
            path = f.repo / "nested-with-git-shape"
            for directory in ("objects", "refs"):
                (path / ".git" / directory).mkdir(parents=True)
            binding = local_ports.LocalWorktreeBinding(f.project.project_id, domain_values.EntityId("fake-root"), path)
        observed = f.make_repository(recorder).inspect(local_ports.GitInspectRequest(
            f.project.project_id, domain_values.EntityId("supplemental-metadata"), binding,
            refs=(local_ports.GitRefQuery("HEAD"),), include_status=False, include_worktrees=False))
        facts = {"case": "linked-missing-head" if linked else "nested-shaped-metadata",
                 "status": observed.status.value,
                 "head": None if observed.head is None else observed.head.status.value,
                 "error": None if observed.error is None else observed.error.category.value,
                 "refs": [(r.ref, r.status.value, r.oid) for r in observed.refs]}
        if linked:
            facts["pointer_unchanged"] = marker.read_bytes() == original_pointer
            assert facts["pointer_unchanged"]
            assert observed.status is domain_values.ResultStatus.SUCCEEDED
            assert observed.head.status is local_ports.GitHeadStatus.MISSING
            assert observed.refs[0].status is local_ports.GitRefStatus.MISSING
        else:
            facts["git_fallback_head"] = f.git("rev-parse", "HEAD", cwd=path).strip()
            assert facts["git_fallback_head"] == f.base
            assert observed.status is domain_values.ResultStatus.FAILED
            assert observed.head is None and not observed.refs
            assert observed.error.category is domain_values.ErrorCategory.INVALID_INPUT
        return {"observation": facts, "commands": recorder.records}
    finally:
        f.tearDown()


probes = [metadata_observation(linked) for linked in (True, False)]
report = {
    "candidate": str(candidate), "python": sys.version, "platform": platform.platform(),
    "origins": {m.__name__: m.__file__ for m in (git_ops, commands, config, domain_values, local_ports)},
    "source_sha256": hashlib.sha256((candidate / "src/git_ops.py").read_bytes()).hexdigest(),
    "tests": NAMES, "tests_run": result.testsRun, "skips": len(result.skipped),
    "success": result.wasSuccessful(), "elapsed_seconds": elapsed, "unittest_log": log.getvalue(),
    "probes": probes,
}
for origin in report["origins"].values():
    assert Path(origin).resolve().is_relative_to(candidate / "src")
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"tests_run": result.testsRun, "success": result.wasSuccessful(),
                  "probes": [p["observation"] for p in probes]}), flush=True)
assert result.testsRun == len(NAMES) and not result.skipped and result.wasSuccessful()
