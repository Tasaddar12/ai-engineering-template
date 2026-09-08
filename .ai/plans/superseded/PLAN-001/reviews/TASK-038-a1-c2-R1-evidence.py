"""Independent exact-candidate R1 checks; candidate source is read-only."""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from dataclasses import FrozenInstanceError, replace

ROOT = Path(r"D:/Codex Projects/ai-engineering-template")
WT = ROOT / ".worktrees/TASK-038-a1"
PLAN = ".ai/plans/current/PLAN-001"
HEAD = "6f2b12c3283ed7d6e3d4876020fe690c6e0061a3"
BASE = "c945928da13cf9081dcf85c32c849cefdf24b97c"
CREF = f"{PLAN}/reviews/candidates/CANDIDATE-TASK-038-a1-6f2b12c3283e.json"
sys.dont_write_bytecode = True
sys.path.insert(0, str(WT / "src"))
import config
import contracts
import install
from domain_values import DomainException, ErrorCategory

def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=WT)

def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def ok(label: str) -> None:
    print("PASS:", label, flush=True)

rejections = 0
def rejects(label: str, callback, category=None, exception=DomainException):
    global rejections
    try:
        callback()
    except exception as exc:
        if isinstance(exc, DomainException):
            assert exc.category == category, (label, exc.category, category)
            assert not exc.retryable
        rejections += 1
        print("REJECT:", label, "->", str(exc), flush=True)
    else:
        raise AssertionError(f"unexpected acceptance: {label}")

assert git("rev-parse", "HEAD").decode().strip() == HEAD
assert git("status", "--porcelain") == b""
assert git("merge-base", BASE, HEAD).decode().strip() == BASE
candidate = read(ROOT / CREF)
assert candidate["head_oid"] == HEAD and candidate["base_oid"] == BASE
assert sha(git("diff", "--binary", BASE, HEAD)) == candidate["diff_sha256"]
for entry in candidate["context_refs"]:
    assert sha(git("show", f"{HEAD}:{entry['path']}")) == entry["sha256"], entry
for entry in candidate["validation_refs"]:
    assert sha((ROOT / entry["path"]).read_bytes()) == entry["sha256"], entry
assert sha((ROOT / ".ai/project/policy.json").read_bytes() +
           (ROOT / ".ai/project/agent-models.json").read_bytes()) == candidate["policy_model_digest"]
body = {key: value for key, value in candidate.items() if key != "fingerprint"}
assert sha(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()) == candidate["fingerprint"]
assert candidate["fingerprint"] == "b19e2958568f1c67da0c70f28d5e50901143bf9baf627449ae96ea5a39345e0b"
print("BASE", BASE, "HEAD", HEAD)
print("FINGERPRINT", candidate["fingerprint"])
print("DIFF_SHA256", candidate["diff_sha256"])
print("CONTEXT_REFS", len(candidate["context_refs"]), "VALIDATION_REFS", len(candidate["validation_refs"]))
ok("clean candidate, base ancestry, binary diff, committed context, validation, policy/model and canonical fingerprint hashes")

paths = git("diff", "--name-only", BASE, HEAD).decode().splitlines()
assert set(paths) == {"src/config.py", "tests/unit/config/test_config.py", f"{PLAN}/evidence/implementation/TASK-038.md"}
assert not git("diff", "--check", BASE, HEAD)
print("CHANGED_PATHS", json.dumps(paths))
tasks = [read(path) for path in (WT / PLAN / "tasks/current").glob("TASK-*.json")]
graph = read(WT / PLAN / "graph.json")
isolation = read(WT / PLAN / "reviews/r4-isolation-review.json")
digest = contracts.structural_task_digest(tasks)
assert digest == graph["task_set_sha256"] == isolation["task_set_sha256"]
assert graph["status"] == "approved" and graph["revision"] == 4
assert isolation["verdict"] == "pass" and isolation["graph_revision"] == 4
assert {t["id"]: t["depends_on"] for t in tasks} == {n["task_id"]: n["depends_on"] for n in graph["nodes"]}
dependency = read(WT / PLAN / "reviews/candidates/CANDIDATE-TASK-004-a2-e3c1177f993e.json")
dep_oid = dependency["head_oid"]
assert git("merge-base", dep_oid, BASE).decode().strip() == dep_oid
assert read(WT / PLAN / "tasks/current/TASK-004.json")["status"] == "accepted"
assert git("show", f"{HEAD}:src/contracts.py") == git("show", f"{dep_oid}:src/contracts.py")
for stage in ("R1", "R2"):
    review = read(WT / PLAN / f"reviews/TASK-004-a2-c3-{stage}.json")
    assert review["verdict"] == "pass" and review["candidate_fingerprint"] == dependency["fingerprint"]
print("GRAPH_DIGEST", digest, "ACCEPTED_DEPENDENCY", dep_oid)
ok("owned paths only, approved graph structural/dependency equality, accepted registry source and review ancestry")
assert str(inspect.signature(config.load_project_settings)) == "(root: 'Path', installation: 'InstallationRecord') -> 'ProjectSettings'"
for module in (config, contracts, install):
    assert Path(module.__file__).parent == WT / "src"
    print("IMPORT", module.__name__, module.__file__)

command = read(WT / PLAN / "commands/test.TASK-038.json")
argv = [sys.executable, *command["argv"][1:]]
environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
run = subprocess.run(argv, cwd=WT, env=environment, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True, timeout=180, shell=False)
print("DECLARED_ARGV", json.dumps(argv))
print(run.stdout, end="")
assert run.returncode == 0 and "Ran 29 tests" in run.stdout and "OK" in run.stdout
ok("declared exact-worktree suite: 29 tests, exit 0")

registry = contracts.load_contract_registry(WT / "schemas/v1")
source_refs = [WT / ".ai/framework.json", WT / ".ai/project/policy.json", WT / ".ai/project/agent-models.json"]
source_before = {path: path.read_bytes() for path in source_refs}
source = config.load_project_settings(WT, config.load_installation_record(WT))
assert source.namespace == ".ai"
assert source.policy.action_requirement("local_containers") is config.ActionRequirement.AUTONOMOUS
registry.validate(source.effective_policy().to_wire())
assert source.configured_model("implementation") is None
assert source.model_for_role("implementer").name == "implementation_escalated"
ok("prior finding 001 resolved: actual unchanged source loads local_containers; recommendation remains separate from unconfigured binding")

minimum = dict(max_parallel=1, max_review_cycles=1, max_rewrites=0,
               max_agent_invocations=1, required_sandbox=True)
for cls in (config.RunSettings, config.RunOverrides):
    rejects(f"{cls.__name__} zero configured invocations", lambda cls=cls: cls(max_agent_invocations=0), exception=ValueError)
payload = source.resolve_run().to_payload()
rejects("saved payload zero configured invocations", lambda: config.decode_run_settings(dict(payload, max_agent_invocations=0)), ErrorCategory.INVALID_INPUT)
for invalid in (-1, True, 1.5, "1", None):
    rejects(f"invalid saved invocation {invalid!r}", lambda invalid=invalid: config.decode_run_settings(dict(payload, max_agent_invocations=invalid)), ErrorCategory.INVALID_INPUT)
rejects("unknown saved field", lambda: config.decode_run_settings(dict(payload, invocations_used=0)), ErrorCategory.INVALID_INPUT)
missing = dict(payload)
del missing["required_sandbox"]
rejects("missing saved field", lambda: config.decode_run_settings(missing), ErrorCategory.INVALID_INPUT)

snapshot_count = 0
def boundaries(settings):
    global snapshot_count
    options = [None, config.RunOverrides(), config.RunOverrides(**minimum)]
    options += [config.RunOverrides(**{name: value}) for name, value in minimum.items()]
    for override in options:
        effective = settings.effective_policy(override)
        registry.validate(effective.to_wire())
        decoded = config.decode_run_settings(settings.resolve_run(override).to_payload())
        registry.validate(settings.policy.with_run_settings(decoded).to_wire())
        snapshot_count += 2
    assert settings.effective_policy(config.RunOverrides(**minimum)).max_rewrites == 0
    assert settings.effective_policy(config.RunOverrides(**minimum)).max_agent_invocations == 1

boundaries(source)
for name in ("max_parallel", "max_review_cycles", "max_rewrites", "max_agent_invocations"):
    rejects(f"broader {name}", lambda name=name: source.resolve_run(config.RunOverrides(**{name: getattr(source.policy, name) + 1})), ErrorCategory.POLICY_DENIED)
saved = config.decode_run_settings(source.resolve_run().to_payload())
stricter = replace(source, policy=source.effective_policy(config.RunOverrides(**minimum)))
assert stricter.resolve_run(saved=saved) is saved
assert stricter.resolve_run().max_agent_invocations == 1 and saved.max_agent_invocations == 300
rejects("saved settings with new overrides", lambda: stricter.resolve_run(config.RunOverrides(), saved=saved), ErrorCategory.INVALID_INPUT)
rejects("sandbox weakening", lambda: stricter.resolve_run(config.RunOverrides(required_sandbox=False)), ErrorCategory.POLICY_DENIED)
rejects("frozen settings mutation", lambda: setattr(saved, "max_agent_invocations", 0), exception=FrozenInstanceError)
detached = saved.to_payload()
detached["max_agent_invocations"] = 0
assert saved.max_agent_invocations == 300
ok("prior finding 002 resolved; configured minimum 1, rewrite minimum 0, strict hydration, restrictive overrides, detached immutable snapshots and saved precedence")

with tempfile.TemporaryDirectory(prefix="TASK-038-a1-c2-R1-") as directory:
    for assistant, namespace in (("codex", ".codex"), ("claude", ".claude")):
        target = Path(directory) / assistant
        install.install(str(target), assistant)
        tracked = [target / namespace / "framework.json", target / namespace / "project/policy.json", target / namespace / "project/agent-models.json"]
        native = target / namespace / ("config.toml" if assistant == "codex" else "settings.json")
        native.write_text("intentionally invalid native settings; must not be parsed", encoding="utf-8")
        before = {path: path.read_bytes() for path in [*tracked, native]}
        loaded = config.load_project_settings(target, config.load_installation_record(target))
        assert loaded.namespace == namespace and loaded.configured_model("implementation") is None
        boundaries(loaded)
        assert {path: path.read_bytes() for path in before} == before
        print("FRESH_INSTALL", assistant, "loaded; native ignored; tracked/native bytes unchanged")
        # Mutations are confined to this disposable fresh installation.
        ppath = tracked[1]
        policy = read(ppath)
        bad = copy.deepcopy(policy)
        bad["autonomous_actions"].append("unknown_future_action")
        ppath.write_text(json.dumps(bad), encoding="utf-8")
        rejects(f"{assistant} unknown action", lambda: config.load_project_settings(target, config.load_installation_record(target)), ErrorCategory.INVALID_INPUT)
        ppath.write_bytes(before[ppath])
        if assistant == "codex":
            for action in config.SENSITIVE_ACTIONS:
                bad = copy.deepcopy(policy)
                bad["approval_actions"].remove(action)
                bad["autonomous_actions"].append(action)
                ppath.write_text(json.dumps(bad), encoding="utf-8")
                rejects(f"sensitive autonomous {action}", lambda: config.load_project_settings(target, config.load_installation_record(target)), ErrorCategory.POLICY_DENIED)
            ppath.write_bytes(before[ppath])
        assert {path: path.read_bytes() for path in before} == before

assert {path: path.read_bytes() for path in source_before} == source_before
assert git("status", "--porcelain") == b""
assert git("rev-parse", "HEAD").decode().strip() == HEAD
print("VALIDATED_EFFECTIVE_POLICY_SNAPSHOTS", snapshot_count)
print("EXPECTED_REJECTIONS", rejections)
ok("source configuration bytes unchanged; final candidate clean at exact head")
print("RESULT: all independent checks passed")
