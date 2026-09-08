"""Independent bounded TASK-019 review probes; not a product dependency."""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path("D:/Codex Projects/ai-engineering-template")
WT = ROOT / ".worktrees/TASK-019-a1"
sys.path.insert(0, str(WT / "src"))
from candidates import CandidateContext, CandidateRequest, MaterialInput, build_candidate, candidate_from_wire, verify_candidate
from contracts import ContractRegistry
from domain_values import DomainException, FrozenJsonObject
from orchestration_ports import CandidateRecord
from workflow_ports import ContentRef

registry = ContractRegistry(WT / "schemas/v1")
results: list[dict[str, object]] = []


def check(name, function):
    try:
        detail = function()
        results.append({"name": name, "pass": True, "detail": detail})
    except Exception as exc:
        results.append({"name": name, "pass": False, "error": f"{type(exc).__name__}: {exc}"})


def rejected(function, exception=(TypeError, ValueError, DomainException)):
    try:
        function()
    except exception:
        return
    raise AssertionError("invalid input accepted")


def M(path, value=b"\xef\xbb\xbf\x00\xff\r\n"):
    return MaterialInput(path, value)


def context():
    return CandidateContext(plan=M("p/plan.json"), graph=M("p/graph.json"),
        specs=[M("p/spec.json")], adrs=[M("p/ADR-001.md"), M("p/ADR-002.md")],
        contracts=[M("p/contracts.md")], handoffs=[M("p/TASK-001.md"), M("p/TASK-004.md")],
        required_adr_paths=["p/ADR-001.md", "p/ADR-002.md"],
        required_handoff_paths=["p/TASK-001.md", "p/TASK-004.md"], supplemental=[M("p/caf\u00e9.md")])


request = CandidateRequest(candidate_id="CANDIDATE-TASK-019-probe", task_id="TASK-019", plan_id="PLAN-001",
    graph_revision=4, base_oid="a" * 64, head_oid="b" * 64, diff=b"\0\xff\r\n", context=context(),
    validation=[M("v/z.bin"), M("v/a.bin")], checklist_version="PLAN-001-v1", policy=b"policy\r\n", model_profile=b"model\n")
candidate = build_candidate(request, registry)


def exact_hashes():
    wire = candidate.to_wire()
    sha = lambda b: hashlib.sha256(b).hexdigest()
    assert wire["diff_sha256"] == sha(request.diff)
    assert wire["policy_model_digest"] == sha(request.policy + request.model_profile)
    assert wire["context_refs"] == [{"path": m.path, "sha256": sha(m.content)} for m in request.context.ordered]
    assert wire["validation_refs"] == [{"path": m.path, "sha256": sha(m.content)} for m in request.validation]
    unsigned = {k: v for k, v in wire.items() if k != "fingerprint"}
    assert wire["fingerprint"] == sha(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
    assert candidate_from_wire(wire, registry) == candidate
    return "Exact raw binary/BOM/non-ASCII inputs and canonical unsigned v1 JSON match independent hashlib calculations."


def invalidation():
    variants = [replace(request, **change) for change in [
        {"candidate_id": "other"}, {"task_id": None}, {"plan_id": "PLAN-002"}, {"graph_revision": 5},
        {"base_oid": "c" * 64}, {"head_oid": "d" * 64}, {"diff": b"\0\xff\n"},
        {"checklist_version": "v2"}, {"policy": b"policy\n"}, {"model_profile": b"model\r\n"},
        {"validation": [M("v/new.bin")]},
    ]]
    for role in ("plan", "graph", "specs", "adrs", "contracts", "handoffs", "supplemental"):
        old = getattr(request.context, role)
        changed = M(old.path, old.content + b"x") if isinstance(old, MaterialInput) else (M(old[0].path, old[0].content + b"x"), *old[1:])
        variants.append(replace(request, context=replace(request.context, **{role: changed})))
    for variant in variants:
        try:
            verify_candidate(candidate, variant, registry)
        except DomainException as exc:
            assert exc.category.value == "state_conflict" and not exc.retryable
            assert "fingerprint" in exc.error.details["changed_fields"]
        else:
            raise AssertionError("stale candidate accepted")
    return f"{len(variants)} independent mutations rejected with immutable non-retryable state_conflict."


def applicable_roles():
    task = json.loads((WT / ".ai/plans/current/PLAN-001/tasks/current/TASK-001.json").read_bytes())
    assert task["depends_on"] == []
    no_handoffs = replace(request.context, handoffs=(), required_handoff_paths=tuple(f"p/{d}.md" for d in task["depends_on"]))
    build_candidate(replace(request, task_id=task["id"], context=no_handoffs), registry)
    none = replace(no_handoffs, adrs=(), required_adr_paths=())
    plan_candidate = build_candidate(replace(request, task_id=None, context=none), registry)
    assert candidate_from_wire(plan_candidate.to_wire(), registry).task_id is None
    for role, required in (("adrs", "required_adr_paths"), ("handoffs", "required_handoff_paths")):
        rejected(lambda: replace(request.context, **{role: getattr(request.context, role)[:1]}))
        rejected(lambda: replace(request.context, **{required: [*getattr(request.context, required), "p/missing.md"]}))
    return "Actual TASK-001 has no dependencies; task without handoffs and plan without ADRs succeed; each missing declared material rejects."


def boundaries():
    for path in ("../escape", "/absolute", "x\\name", "x/CON", "x/a:stream", "p/cafe\u0301.md"):
        rejected(lambda: M(path))
    rejected(lambda: replace(request.context, supplemental=[M("p/\uff43af\u00e9.md"), M("p/caf\u00e9.md")]))
    rejected(lambda: replace(request, validation=[M("P/PLAN.JSON")]))
    for oid in ("a" * 7, "a" * 63, "a" * 65, "A" * 64, "a" * 40 + "\n"):
        rejected(lambda: replace(request, head_oid=oid))
    rejected(lambda: replace(request, graph_revision=True))
    mutable = bytearray(b"snapshot")
    frozen = replace(request, diff=memoryview(mutable))
    mutable[:] = b"changed!"
    assert frozen.diff == b"snapshot"
    wire = candidate.to_wire(); parsed = candidate_from_wire(wire, registry)
    wire["validation_refs"][0]["path"] = "mutated"
    assert parsed == candidate
    return "Portable aliases/unsafe paths, full OID boundaries, boolean revision, memoryview detachment and parsed output isolation checked."


def historical_and_dto():
    names = ("CANDIDATE-TASK-001-a2-d1fc91746641.json", "CANDIDATE-TASK-004-a2-e3c1177f993e.json")
    for name in names:
        wire = json.loads((WT / ".ai/plans/current/PLAN-001/reviews/candidates" / name).read_bytes())
        assert candidate_from_wire(wire, registry).to_wire() == wire
    for item in (candidate, build_candidate(replace(request, task_id=None), registry)):
        wire = item.to_wire()
        values = {k: v for k, v in wire.items() if k not in {"schema_version", "kind"}}
        for name in ("context_refs", "validation_refs"):
            values[name] = tuple(ContentRef(**ref) for ref in wire[name])
        dto = CandidateRecord(**values)
        assert dto.fingerprint == item.fingerprint and dto.task_id is None if item.task_id is None else dto.task_id.value == item.task_id
    return "Both accepted dependency candidate wires round-trip exactly; normal task and plan outputs adapt to accepted CandidateRecord without new fields."


def immutable_mapping_input():
    frozen = FrozenJsonObject(candidate.to_wire())
    registry.validate(frozen)
    assert candidate_from_wire(frozen, registry) == candidate
    assert verify_candidate(frozen, request, registry) == candidate
    return "Accepted immutable JSON mapping supports parse and current-input verification."


def dependency_closure():
    tree = ast.parse((WT / "src/candidates.py").read_bytes())
    modules = sorted({n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
    assert set(modules) <= {"__future__", "hashlib", "json", "re", "collections", "dataclasses", "typing", "contracts", "domain_values"}
    for name in ("candidates", "contracts", "domain_values", "orchestration_ports", "workflow_ports"):
        assert Path(sys.modules[name].__file__).resolve() == (WT / "src" / (name + ".py")).resolve()
    return {"imports": modules, "origins": {name: sys.modules[name].__file__ for name in ("candidates", "contracts", "domain_values")}}


for name, function in (("exact_hashes", exact_hashes), ("invalidation", invalidation), ("applicable_roles", applicable_roles), ("boundaries", boundaries), ("historical_and_dto", historical_and_dto), ("immutable_mapping_input", immutable_mapping_input), ("dependency_closure", dependency_closure)):
    check(name, function)

print(json.dumps({"python": sys.version, "results": results}, indent=2))
sys.exit(0 if all(result["pass"] for result in results) else 1)
