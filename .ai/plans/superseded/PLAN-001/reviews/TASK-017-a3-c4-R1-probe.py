"""Independent bounded persistence/provenance check; no owned-test imports."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import fields, is_dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / ".worktrees/TASK-017-a3"
sys.path.insert(0, str(TREE / "src"))
import agents
import config
import contracts
import domain_values as d
import workflow_ports as w

MODULES = (agents, config, contracts, d, w)
assert all(Path(m.__file__).resolve().parent == TREE / "src" for m in MODULES)
TEXT = "Cafe\u0301\n\t\x00\x1b\u200d|\udfff0|\udfffsd800|\ud83d\ude00|\U0001f600|" + "".join(chr(n) for n in range(0xD800, 0xE000)) + "end"
META = {"": "", " spaced\nkey ": [True, None, -0.0, 2.5, {TEXT: TEXT, "\ud83d\ude00": "pair", "\U0001f600": "scalar", "\udfff": "marker"}]}
STAMP = datetime(2026, 9, 8, tzinfo=timezone.utc)


def wire(value):
    if isinstance(value, d.ScopeClaim):
        return value.to_wire()
    if isinstance(value, d.ScopePath):
        return value.as_wire()
    if isinstance(value, (d.EntityId, d.PlanId, d.Revision, d.Sha256Digest)):
        return value.value
    if isinstance(value, d.FrozenJsonObject):
        return value.to_dict()
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: wire(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, tuple):
        return [wire(v) for v in value]
    return value


def exact_digest(value):
    # repr distinguishes surrogate code units from a true non-BMP scalar.
    return hashlib.sha256(repr(wire(value)).encode("utf-8", "surrogatepass")).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def fixture(path, mapped=True, model_id=None):
    shutil.copytree(TREE / "schemas/v1", path / "schemas/v1")
    (path / ".ai/project").mkdir(parents=True)
    shutil.copyfile(TREE / ".ai/framework.json", path / ".ai/framework.json")
    models = json.loads((TREE / ".ai/project/agent-models.json").read_bytes())
    policy = json.loads((TREE / ".ai/project/policy.json").read_bytes())
    if mapped:
        for provider in models["providers"].values():
            provider["profiles"]["independent_review"] = copy.deepcopy(provider["profiles"]["review_high"])
        models["policy_profile_map"]["review_high"] = "independent_review"
    selected = models["providers"]["openai"]["profiles"][models["policy_profile_map"]["review_high"]]
    if model_id is not None:
        selected["model_id"] = model_id
    for row in policy["model_profiles"]:
        chosen = models["providers"]["openai"]["profiles"][models["policy_profile_map"][row["name"]]]
        row.update(configured=True, provider="OpenAI", model_id=chosen["model_id"], capability_rank=chosen["capability_rank"])
    dump(path / ".ai/project/agent-models.json", models)
    dump(path / ".ai/project/policy.json", policy)


def load(path):
    return config.load_project_settings(path, config.load_installation_record(path))


def request(key="ordinary-key", rich=False, number=0):
    payload = TEXT if rich else "plain"
    return w.AgentRequest(
        id=f"request-{number}", workflow_id="workflow-17", run_id="run-17", attempt_id="attempt-17",
        task_id=None, plan_id="PLAN-001", spec_refs=("spec:" + payload, "spec:second"),
        role="task-isolation-reviewer", graph_revision=4, base_oid="a" * 40, current_oid="b" * 40,
        worktree_id="tree-17", scope=d.ScopeClaim(write_paths=(" leading/Cafe\u0301.py",), read_paths=(" leading/read/",), prohibited_paths=(" leading/blocked.py",), resources=("component:agents",)),
        context_ref="context:" + payload, allowed_command_ids=("cmd:" + payload,),
        acceptance_criteria=(w.AcceptanceCriterion("criterion:" + payload, "description:" + payload, "verification:" + payload),),
        dependency_handoffs=("handoff:" + payload,), checklist_ids=("check:" + payload,),
        model_profile="review_high", policy_ref=".ai/project/policy.json", permission_subset=("permission:" + payload,),
        lease_generation=7, idempotency_key=key,
    )


def adapter(settings, state, req, adapter_id="independent-adapter"):
    return agents.DeterministicFakeAgentAdapter(project_id="independent-project", settings=settings,
        capabilities=agents.AgentAdapterCapabilities(roles=(req.role,), permissions=req.permission_subset,
            command_ids=req.allowed_command_ids, model_profiles=settings.models.provider().profiles),
        provider_state=state, adapter_id=adapter_id)


def evidence():
    return d.EvidenceRef(" leading-evidence/Cafe\u0301.json", "d" * 64, META)


def observation(handle, model, status=d.AgentRunStatus.SUCCEEDED, rich=True):
    text = TEXT if rich else "plain"
    success = status is d.AgentRunStatus.SUCCEEDED
    output = w.AgentOutputRecord("output-17", handle.request_id, handle.attempt_id, d.AgentOutputStatus.SUCCEEDED,
        model, ("artifact:" + text,), ("command-evidence:" + text,), ("discovery:" + text,), ("scope-change:" + text,), None, "summary:" + text) if success else None
    run = w.AgentRunRecord("agent-run-17", f"agent-request:{handle.plan_id.value}:{handle.request_id.value}",
        handle.attempt_id, status, handle.adapter_id, handle.external_handle, model,
        STAMP if success else None, STAMP if success else None,
        "agent-output:PLAN-001:output-17" if success else "optional:" + text,
        None if success else "category:" + text, handle.lease_generation)
    error = None if success else d.DomainError(d.ErrorCategory.TRANSIENT_PROVIDER, "Expected independent unknown result", True, (evidence(),), META)
    return w.AgentObservation(status, handle, run, output, (evidence(),), error)


def reject(action, category=d.ErrorCategory.VALIDATION_FAILED):
    try:
        action()
    except d.DomainException as exc:
        assert exc.category is category, (exc.category, category)
    else:
        raise AssertionError("operation unexpectedly admitted")


def operations(a, h, req):
    return (lambda: a.start(req, req.idempotency_key), lambda: a.poll(h), lambda: a.cancel(h), lambda: a.expected_model(h))


def child(path, case, phase):
    settings = load(path)
    statepath = path / "state.json"
    state = agents.FakeAgentProviderState(statepath)
    registry = contracts.ContractRegistry(path / "schemas/v1")
    records = []
    routes = [("independent-adapter", "ordinary-key")] if case == "identity" else [("x\ny", "z"), ("x", "y\nz"), ("adapter:" + TEXT, "key:" + TEXT)]
    if case in ("decomposed", "pair"):
        routes = [("negative-adapter", f"negative-{i}") for i in range(5)]
    for i, (name, key) in enumerate(routes):
        req = request(key, case != "identity", i)
        registry.validate(wire(req))
        a = adapter(settings, state, req, name)
        if phase == 3:
            # Changed selected effort must reject all terminal handle shortcuts.
            h = w.AgentHandle("independent-project", req.plan_id, req.run_id, req.id, req.attempt_id, req.lease_generation, name, key,
                json.loads(statepath.read_bytes())["effects"][i]["handle"]["external_handle"])
            # Look up external handles by request ID because persisted order is routing order.
            saved = next(e for e in json.loads(statepath.read_bytes())["effects"] if e["request"]["id"] == req.id.value)
            h = replace(h, external_handle=saved["handle"]["external_handle"])
            before = statepath.read_bytes()
            for op in operations(a, h, req):
                reject(op)
                assert statepath.read_bytes() == before
            records.append({"request": i, "terminal_binding_rejections": 4})
            continue
        h = a.start(req, key)
        assert a.start(req, key) == h
        expected = a.expected_model(h)
        if case in ("decomposed", "pair"):
            field = ("profile", "provider", "model_id", "capability_rank", "invocation_id")[i]
            wrong = "review-cafe\u0301" if case == "decomposed" else "review-\ud83d\ude00"
            value = wrong if field == "model_id" else (expected.capability_rank + 1 if field == "capability_rank" else getattr(expected, field) + "\n\ud800")
            observed = replace(expected, **{field: value})
            assert observed != expected
            if phase == 0:
                state.script(h, polls=(observation(h, observed),))
            before = statepath.read_bytes()
            for _ in range(2):
                reject(lambda: a.poll(h))
                assert statepath.read_bytes() == before
            records.append({"field": field, "rejected_twice": True, "handle": h.external_handle})
            continue
        succeeded = observation(h, expected, rich=case != "identity")
        unknown = observation(h, expected, d.AgentRunStatus.UNKNOWN, rich=case != "identity")
        if phase == 0:
            assert a.poll(h).status is d.AgentRunStatus.QUEUED
            state.script(h, polls=(unknown, succeeded), cancellations=(w.CancelObservation(w.CancelStatus.UNKNOWN, h, False, (evidence(),), unknown.error), w.CancelObservation(w.CancelStatus.CANCELLED, h, True, (evidence(),))))
            result = a.poll(h)
            assert result.run == unknown.run and result.error == unknown.error and result.evidence_refs[0] == evidence()
            cancelled = a.cancel(h)
            assert cancelled.error == unknown.error and cancelled.evidence_refs[0] == evidence()
        else:
            before = statepath.read_bytes()
            reject(lambda: a.start(replace(req, context_ref=req.context_ref + " changed"), key), d.ErrorCategory.STATE_CONFLICT)
            assert statepath.read_bytes() == before
            result = a.poll(h)
            assert result.output == succeeded.output and result.run == succeeded.run and result.evidence_refs[0] == evidence()
            assert a.cancel(h).status is w.CancelStatus.ALREADY_TERMINAL
            registry.validate(wire(result.output))
            if phase == 2:
                assert statepath.read_bytes() == before
        registry.validate(wire(result.run))
        records.append({"request": i, "handle": h.external_handle, "status": result.status.value,
            "request_exact_digest": exact_digest(req), "output_exact_digest": exact_digest(result.output), "record_exact_digest": exact_digest(result)})
    if phase != 3:
        assert state.effect_count == len(routes)
        saved = json.loads(statepath.read_bytes())["effects"]
        if case in ("decomposed", "pair"):
            assert all(e["poll_position"] == 0 for e in saved)
        else:
            assert all(e["cancel_position"] == 1 and e["poll_position"] == (1 if phase == 0 else 2) for e in saved)
    return {"case": case, "phase": phase, "pid": os.getpid(), "settings_sha256": hashlib.sha256((path / ".ai/project/policy.json").read_bytes() + (path / ".ai/project/agent-models.json").read_bytes()).hexdigest(),
        "requested_profile": "review_high", "resolved_profile": settings.configured_model("review_high").name,
        "records": records, "effect_count": state.effect_count, "state_sha256": hashlib.sha256(statepath.read_bytes()).hexdigest()}


def local_boundaries(path):
    settings = load(path)
    statepath = path / "boundary.json"
    req = request()
    state = agents.FakeAgentProviderState(statepath)
    a = adapter(settings, state, req)
    with patch("agents.os.replace", side_effect=OSError("independent replacement failure")):
        reject(lambda: a.start(req, req.idempotency_key), d.ErrorCategory.INTERNAL_ERROR)
    assert state.effect_count == 0 and not statepath.exists()
    h = a.start(req, req.idempotency_key)
    baseline = json.loads(statepath.read_bytes())
    full_bindings = 0
    for field, value in (("provider", "other"), ("name", "other"), ("model_id", "other"), ("capability_rank", 99), ("reasoning_effort", "medium"), ("effort", "high")):
        payload = copy.deepcopy(baseline)
        e = payload["effects"][0]
        e["configured_model"][field] = value
        if field in ("provider", "model_id", "capability_rank"):
            e["expected_model"][field] = value
        dump(statepath, payload)
        restored = agents.FakeAgentProviderState(statepath)
        aa = adapter(settings, restored, req)
        before = statepath.read_bytes()
        for op in operations(aa, h, req):
            reject(op)
            assert statepath.read_bytes() == before
            full_bindings += 1
    malformed = 0
    for field, value in (("capability_rank", True), ("capability_rank", 0), ("reasoning_effort", 3), ("effort", "x\ny"), ("name", " bad"), ("provider", "\udfff")):
        payload = copy.deepcopy(baseline)
        payload["effects"][0]["configured_model"][field] = value
        dump(statepath, payload)
        before = statepath.read_bytes()
        reject(lambda: agents.FakeAgentProviderState(statepath))
        assert statepath.read_bytes() == before
        malformed += 1
    dump(statepath, baseline)
    state = agents.FakeAgentProviderState(statepath)
    a = adapter(settings, state, req)
    expected = a.expected_model(h)
    obs = observation(h, expected, d.AgentRunStatus.UNKNOWN)
    cancellation = w.CancelObservation(w.CancelStatus.CANCELLED, h, True, (evidence(),))
    actions = (lambda: state.script(h, polls=(obs,), cancellations=(cancellation,)), lambda: a.poll(h), lambda: a.cancel(h))
    for action in actions:
        before = statepath.read_bytes()
        with patch("agents.os.replace", side_effect=OSError("independent replacement failure")):
            reject(action, d.ErrorCategory.INTERNAL_ERROR)
        assert statepath.read_bytes() == before
        assert not list(path.glob(".boundary.json.*.tmp"))
        action()
    restored = agents.FakeAgentProviderState(statepath)
    aa = adapter(settings, restored, req)
    assert aa.cancel(h).status is w.CancelStatus.CANCELLED
    reject(lambda: aa.poll(h), d.ErrorCategory.STATE_CONFLICT)
    return {"saved_binding_rejections": full_bindings, "strict_profile_rejections": malformed, "atomic_replace_rollbacks": 4, "confirmed_cancel_stable": True}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        print(json.dumps(child(Path(sys.argv[2]), sys.argv[3], int(sys.argv[4])), ensure_ascii=True))
        return
    # An explicit Git directory avoids Linux interpreting the Windows absolute
    # path inside this Windows-created linked worktree's .git pointer.
    result = {"head": subprocess.check_output(["git", "--git-dir", str(ROOT / ".git/worktrees/TASK-017-a3"), "--work-tree", str(TREE), "rev-parse", "HEAD"]).decode().strip(),
        "runtime": sys.version, "executable": sys.executable, "platform": platform.platform(), "origins": {m.__name__: m.__file__ for m in MODULES}, "groups": []}
    with tempfile.TemporaryDirectory(prefix="independent-017-c4-") as temporary:
        root = Path(temporary)
        for case in ("identity", "mapped", "decomposed", "pair"):
            path = root / case
            fixture(path, case != "identity", "review-caf\u00e9" if case == "decomposed" else "review-\U0001f600" if case == "pair" else None)
            group = []
            for phase in (0, 1, 2):
                proc = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--child", str(path), case, str(phase)], cwd=TREE, capture_output=True, text=True, shell=False)
                assert proc.returncode == 0, (case, phase, proc.stdout, proc.stderr)
                group.append(json.loads(proc.stdout))
            assert len({r["settings_sha256"] for r in group}) == 1
            assert len({r["pid"] for r in group}) == 3
            if case in ("identity", "mapped"):
                assert group[1]["records"] == group[2]["records"]
                assert group[1]["state_sha256"] == group[2]["state_sha256"]
                assert len({r["handle"] for r in group[0]["records"]}) == group[0]["effect_count"]
            else:
                assert group[0]["state_sha256"] == group[1]["state_sha256"] == group[2]["state_sha256"]
            result["groups"].append(group)
            if case == "mapped":
                models_path = path / ".ai/project/agent-models.json"
                models = json.loads(models_path.read_bytes())
                models["providers"]["openai"]["profiles"]["independent_review"]["reasoning_effort"] = "medium"
                dump(models_path, models)
                proc = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--child", str(path), case, "3"], cwd=TREE, capture_output=True, text=True, shell=False)
                assert proc.returncode == 0, proc.stderr
                result["terminal_effort"] = json.loads(proc.stdout)
        fixture(root / "boundaries")
        result["boundaries"] = local_boundaries(root / "boundaries")
    suffix = "windows" if os.name == "nt" else "linux"
    if suffix == "linux":
        result["initial_harness_setup_failure"] = "Initial git -C identity preflight failed before behavioral checks because the linked .git pointer contains a Windows absolute path. Explicit Git directory fixed harness setup; no source defect or historical writer execution."
    out = Path(__file__).with_name("TASK-017-a3-c4-R1-probe-" + suffix + ".json.txt")
    assert not out.exists()
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "fresh_processes": 13, "groups": 4, "boundaries": result["boundaries"], "terminal_effort_rejections": 12}))


if __name__ == "__main__":
    main()
