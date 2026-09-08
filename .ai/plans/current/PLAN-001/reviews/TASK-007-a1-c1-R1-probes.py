"""Independent TASK-007 R1 probes; run with an exact candidate path and output path."""
from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import platform
import sys
from pathlib import Path

candidate = Path(sys.argv[1]).resolve(strict=True)
sys.path[:0] = [str(candidate / "src"), str(candidate / "tests/unit/git")]
import commands
import git_ops
import local_ports
from test_git_ops import GitFixture, _payload_action
from domain_values import EntityId, ResultStatus
from local_ports import GitInspectRequest, GitRefExpectation, GitRefQuery, GitRefStatus, LocalWorktreeBinding


class RecordingRunner:
    def __init__(self, fixture, after_publish=None):
        self.fixture = fixture
        self.after_publish = after_publish
        self.records = []

    def execute(self, request):
        result = self.fixture.runner.execute(request)
        streams = {}
        for name, reference in (("stdout", result.stdout_ref), ("stderr", result.stderr_ref)):
            content = (self.fixture.repo / reference.path).read_bytes()
            assert hashlib.sha256(content).hexdigest() == reference.sha256.value
            streams[name] = {"sha256": reference.sha256.value, "base64": base64.b64encode(content).decode()}
        self.records.append({"id": result.id.value, "command_id": result.command_id.value,
                             "argv": result.argv_redacted, "cwd_id": result.cwd_worktree_id.value,
                             "cwd_relative": result.cwd_relative, "status": result.status.value,
                             "exit_code": result.exit_code, "truncated": result.output_truncated,
                             "redacted": result.redactions_applied, "streams": streams})
        argv = request.definition.argv
        if self.after_publish and "--git-ops-helper-v1" in argv and _payload_action(argv[-1]).startswith("publish_"):
            callback, self.after_publish = self.after_publish, None
            callback()
        return result


def run_probe(name, probe):
    fixture = GitFixture()
    fixture.setUp()
    recorder = RecordingRunner(fixture)
    try:
        observation = probe(fixture, recorder)
        entry = {"name": name, "observation": observation, "commands": recorder.records}
        print(json.dumps({"name": name, **observation}), flush=True)
        return entry
    finally:
        fixture.tearDown()


def false_missing_head(f, recorder):
    path = f.repo / "ordinary-subdirectory"
    (path / ".git").mkdir(parents=True)
    binding = LocalWorktreeBinding(f.project.project_id, EntityId("not-a-worktree"), path)
    repository = f.make_repository(recorder)
    result = repository.inspect(GitInspectRequest(f.project.project_id, EntityId("root-probe"), binding,
                                                refs=(GitRefQuery("HEAD"), GitRefQuery("refs/heads/main")),
                                                include_status=False, include_worktrees=False))
    actual_root = f.git("rev-parse", "--show-toplevel", cwd=path).strip()
    actual_head = f.git("rev-parse", "HEAD", cwd=path).strip()
    return {"expected": "reject non-root binding", "status": result.status.value,
            "head_status": None if result.head is None else result.head.status.value,
            "returned_refs": [(r.ref, r.status.value, r.oid) for r in result.refs],
            "actual_git_root": actual_root, "requested_root": str(path), "actual_git_head": actual_head,
            "defect_reproduced": result.status is ResultStatus.SUCCEEDED}


def symbolic_target(f, recorder):
    source = f.candidate_commit()
    f.git("symbolic-ref", "refs/heads/alias", "refs/heads/main")
    before_index = f.git("write-tree").strip()
    repository = f.make_repository(recorder)
    request = f.branch_request(operation="alias-branch", branch="alias", source="refs/heads/candidate",
                               source_oid=source, expected=GitRefExpectation("refs/heads/alias", GitRefStatus.PRESENT, f.base))
    result = repository.create_branch(request)
    actual_main = f.git("rev-parse", "refs/heads/main").strip()
    return {"expected": "preserve checked-out developer main through symbolic alias", "status": result.status.value,
            "changed": result.changed, "base": f.base, "candidate": source, "actual_main": actual_main,
            "alias_target": f.git("symbolic-ref", "refs/heads/alias").strip(),
            "index_unchanged": f.git("write-tree").strip() == before_index,
            "status_after": f.git("status", "--porcelain=v2"),
            "defect_reproduced": actual_main != f.base}


def managed_branch_switch(f, recorder):
    source = f.candidate_commit()
    path, binding, admission = f.managed_integration()
    f.git("branch", "developer", f.base)
    switched = {}
    def switch():
        f.git("checkout", "developer", cwd=path)
        switched.update(branch=f.git("symbolic-ref", "HEAD", cwd=path).strip(),
                        index=f.git("write-tree", cwd=path).strip(),
                        status=f.git("status", "--porcelain=v2", cwd=path),
                        candidate_exists=(path / "candidate.txt").exists())
    recorder.after_publish = switch
    repository = f.make_repository(recorder, (admission,))
    result = repository.merge(f.merge_request(operation="managed-switch", candidate_oid=source))
    read_tree_calls = sum("read-tree" in r["argv"] for r in recorder.records)
    return {"expected": "unknown with switched developer checkout/index preserved", "status": result.status.value,
            "changed": result.changed, "state_after_switch": switched, "read_tree_calls": read_tree_calls,
            "branch_after": f.git("symbolic-ref", "HEAD", cwd=path).strip(),
            "status_after": f.git("status", "--porcelain=v2", cwd=path),
            "index_preserved": f.git("write-tree", cwd=path).strip() == switched["index"],
            "candidate_exists_after": (path / "candidate.txt").exists(),
            "defect_reproduced": read_tree_calls != 0 and (path / "candidate.txt").exists()}


def bound_runtime(f, recorder):
    (f.repo / "git_ops.py").write_text("raise RuntimeError('untrusted project module executed')\n")
    result = f.make_repository(recorder).create_branch(f.branch_request(operation="bound-runtime"))
    return {"expected": "trusted candidate module wins over project cwd shadow", "status": result.status.value,
            "passed": result.status is ResultStatus.SUCCEEDED}


results = [run_probe(name, probe) for name, probe in (
    ("non-root-missing-head", false_missing_head), ("symbolic-target", symbolic_target),
    ("managed-branch-switch", managed_branch_switch), ("bound-runtime", bound_runtime))]
report = {"candidate": str(candidate), "python": sys.version, "platform": platform.platform(),
          "origins": {m.__name__: m.__file__ for m in (git_ops, commands, local_ports)},
          "source_sha256": hashlib.sha256((candidate / "src/git_ops.py").read_bytes()).hexdigest(),
          "probes": results}
Path(sys.argv[2]).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
