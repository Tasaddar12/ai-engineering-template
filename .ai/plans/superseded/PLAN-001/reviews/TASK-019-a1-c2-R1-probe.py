"""Focused independent immutable candidate boundary verification."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / ".worktrees/TASK-019-a1"
sys.path.insert(0, str(TREE / "src"))
import candidates as c
import contracts
import domain_values as d

registry = contracts.ContractRegistry(TREE / "schemas/v1")
assert all(Path(m.__file__).resolve().parent == TREE / "src" for m in (c, contracts, d))


def fingerprint(value):
    unsigned = {key: item for key, item in value.items() if key != "fingerprint"}
    return hashlib.sha256(json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def rejected(action, expected):
    try:
        action()
    except expected as exc:
        if isinstance(exc, d.DomainException):
            assert exc.category is d.ErrorCategory.STATE_CONFLICT and not exc.retryable
            assert "fingerprint" in exc.error.details["changed_fields"]
        return
    raise AssertionError("invalid or stale candidate was accepted")


def run():
    def material(path, content=b"\xef\xbb\xbf\x00\xff\r\n"):
        return c.MaterialInput(path, content)

    context = c.CandidateContext(plan=material("p/plan.json"), graph=material("p/graph.json"),
        specs=(material("p/spec-z.json"), material("p/spec-a.json")),
        adrs=(), handoffs=(), required_adr_paths=(), required_handoff_paths=(),
        contracts=(material("p/contract-caf\u00e9.md"),), supplemental=(material("p/context.json"),))
    seed = c.CandidateRequest(candidate_id="CANDIDATE-cafe\u0301", task_id="TASK-019", plan_id="PLAN-001", graph_revision=4,
        base_oid="a" * 40, head_oid="b" * 64, diff=b"\xef\xbb\xbf\xff\x00\r\n", context=context,
        validation=(material("v/z.json"), material("v/a.json")), checklist_version="v1-cafe\u0301",
        policy=b"policy\r\n", model_profile=b"model\n")
    results = []
    for task_id in ("TASK-019", None):
        current = replace(seed, task_id=task_id)
        candidate = c.build_candidate(current, registry)
        wire = candidate.to_wire()
        assert wire["fingerprint"] == fingerprint(wire)
        assert wire["diff_sha256"] == hashlib.sha256(current.diff).hexdigest()
        assert wire["policy_model_digest"] == hashlib.sha256(current.policy + current.model_profile).hexdigest()
        assert wire["context_refs"] == [{"path": m.path, "sha256": hashlib.sha256(m.content).hexdigest()} for m in current.context.ordered]
        assert wire["validation_refs"] == [{"path": m.path, "sha256": hashlib.sha256(m.content).hexdigest()} for m in current.validation]
        frozen = d.FrozenJsonObject(wire)
        mixed = dict(wire, context_refs=tuple(d.FrozenJsonObject(ref) for ref in wire["context_refs"]), validation_refs=[MappingProxyType(dict(ref)) for ref in wire["validation_refs"]])
        variants = (wire, frozen, mixed, MappingProxyType(mixed))
        for value in variants:
            registry.validate(value)
            parsed = c.candidate_from_wire(value, registry)
            assert parsed == candidate and parsed.to_wire() == wire
            assert c.verify_candidate(value, current, registry) == candidate
            detached = parsed.to_wire()
            detached["context_refs"][0]["sha256"] = "0" * 64
            assert parsed.to_wire() == wire
        # Mutate caller-owned containers after parsing; the returned Candidate stays detached.
        mutable = copy.deepcopy(wire)
        parsed = c.candidate_from_wire(mutable, registry)
        mutable["validation_refs"].reverse()
        mutable["context_refs"][0]["path"] = "changed.json"
        assert parsed.to_wire() == wire
        stale = (
            replace(current, diff=current.diff.replace(b"\r\n", b"\n")),
            replace(current, policy=current.policy + b"\0"),
            replace(current, model_profile=current.model_profile + b"\0"),
            replace(current, context=replace(context, plan=material(context.plan.path, b"changed"))),
            replace(current, validation=(material(current.validation[0].path, b"changed"), current.validation[1])),
        )
        for changed in stale:
            rejected(lambda: c.verify_candidate(frozen, changed, registry), d.DomainException)
        for field in ("context_refs", "validation_refs"):
            tampered = copy.deepcopy(wire)
            tampered[field][0]["sha256"] = "f" * 64
            registry.validate(d.FrozenJsonObject(tampered))
            rejected(lambda: c.candidate_from_wire(d.FrozenJsonObject(tampered), registry), ValueError)
            reordered = copy.deepcopy(wire)
            reordered[field].reverse()
            rejected(lambda: c.candidate_from_wire(d.FrozenJsonObject(reordered), registry), ValueError)
            # A separately fingerprinted array order is preserved on parse, then
            # rejected against the original current request rather than sorted away.
            reordered["fingerprint"] = fingerprint(reordered)
            parsed = c.candidate_from_wire(d.FrozenJsonObject(reordered), registry)
            assert parsed.to_wire() == reordered
            rejected(lambda: c.verify_candidate(d.FrozenJsonObject(reordered), current, registry), d.DomainException)
        invalid = copy.deepcopy(wire)
        invalid["context_refs"][0]["unknown"] = True
        try:
            c.candidate_from_wire(d.FrozenJsonObject(invalid), registry)
        except d.DomainException as exc:
            assert exc.category is d.ErrorCategory.VALIDATION_FAILED
        else:
            raise AssertionError("schema unknown field was accepted")
        results.append({"task_id": task_id, "fingerprint": candidate.fingerprint.value,
            "representation_parse_reverify_passes": 4, "stale_current_rejections": 5,
            "nested_digest_tamper_rejections": 2, "unchanged_fingerprint_order_rejections": 2,
            "resigned_order_parse_then_current_rejections": 2, "schema_rejections": 1, "mutation_detachment": True})
    return {"python": sys.version, "executable": sys.executable,
        "origins": {m.__name__: m.__file__ for m in (c, contracts, d)}, "results": results}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
