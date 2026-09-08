from __future__ import annotations

import hashlib
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path


WORKTREE_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = WORKTREE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from candidates import (  # noqa: E402
    CandidateContext,
    CandidateRequest,
    MaterialInput,
    build_candidate,
    candidate_from_wire,
    verify_candidate,
)
from contracts import ContractRegistry  # noqa: E402
from domain_values import DomainException, ErrorCategory  # noqa: E402


OID40_A = "a" * 40
OID40_B = "b" * 40
OID64_A = "a" * 64
OID64_B = "b" * 64
ADR_PATHS = (
    ".ai/decisions/ADR-001.md",
    ".ai/decisions/ADR-002.md",
)
HANDOFF_PATHS = (
    ".ai/plans/current/PLAN-001/evidence/implementation/TASK-001.md",
)
TASK_001_TASK_PATH = (
    ".ai/plans/current/PLAN-001/tasks/current/TASK-001.json"
)
TASK_001_RECORD = b"""{
  "id": "TASK-001",
  "plan_id": "PLAN-001",
  "depends_on": [],
  "adr_refs": [
    ".ai/decisions/ADR-001.md",
    ".ai/decisions/ADR-002.md",
    ".ai/decisions/ADR-003.md",
    ".ai/decisions/ADR-004.md",
    ".ai/decisions/ADR-005.md"
  ]
}
"""


def material(path: str, content: bytes | bytearray) -> MaterialInput:
    return MaterialInput(path=path, content=content)


def context(**changes: object) -> CandidateContext:
    values: dict[str, object] = {
        "plan": material(".ai/plans/current/PLAN-001/plan.json", b"plan\r\n"),
        "graph": material(".ai/plans/current/PLAN-001/graph.json", b"graph\n"),
        "specs": [material(".ai/plans/current/PLAN-001/spec.json", b"spec")],
        "adrs": [
            material(".ai/decisions/ADR-002.md", b"adr-2"),
            material(".ai/decisions/ADR-001.md", b"adr-1"),
        ],
        "contracts": [material(".ai/shared/architecture/service-contracts.md", b"contract")],
        "handoffs": [
            material(
                HANDOFF_PATHS[0],
                b"handoff",
            )
        ],
        "required_adr_paths": ADR_PATHS,
        "required_handoff_paths": HANDOFF_PATHS,
        "supplemental": [
            material(".ai/shared/workflows/reviews.md", b"reviews"),
            material(".ai/plans/current/PLAN-001/tasks/current/TASK-019.json", b"task"),
        ],
    }
    values.update(changes)
    return CandidateContext(**values)


def request(**changes: object) -> CandidateRequest:
    values: dict[str, object] = {
        "candidate_id": "CANDIDATE-TASK-019-a1-example",
        "task_id": "TASK-019",
        "plan_id": "PLAN-001",
        "graph_revision": 4,
        "base_oid": OID40_A,
        "head_oid": OID40_B,
        "diff": b"binary\x00diff\r\n",
        "context": context(),
        "validation": [
            material("evidence/validation.bin", b"11 tests\r\nOK\r\n"),
            material("evidence/runtime.bin", b"runtime\x00evidence"),
        ],
        "checklist_version": "PLAN-001-v1",
        "policy": b'{"policy":1}\r\n',
        "model_profile": b'{"model":"sol"}\n',
    }
    values.update(changes)
    return CandidateRequest(**values)


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = ContractRegistry(WORKTREE_ROOT / "schemas" / "v1")

    def test_build_is_deterministic_and_orders_each_context_role(self) -> None:
        first_request = request()
        reversed_context = CandidateContext(
            plan=first_request.context.plan,
            graph=first_request.context.graph,
            specs=reversed(first_request.context.specs),
            adrs=reversed(first_request.context.adrs),
            contracts=reversed(first_request.context.contracts),
            handoffs=reversed(first_request.context.handoffs),
            required_adr_paths=reversed(first_request.context.required_adr_paths),
            required_handoff_paths=reversed(
                first_request.context.required_handoff_paths
            ),
            supplemental=reversed(first_request.context.supplemental),
        )
        second_request = replace(
            first_request,
            context=reversed_context,
            validation=reversed(first_request.validation),
        )

        first = build_candidate(first_request, self.registry)
        second = build_candidate(second_request, self.registry)

        self.assertEqual(first, second)
        self.assertEqual(
            [ref.path for ref in first.context_refs],
            [
                ".ai/plans/current/PLAN-001/plan.json",
                ".ai/plans/current/PLAN-001/graph.json",
                ".ai/plans/current/PLAN-001/spec.json",
                ".ai/decisions/ADR-001.md",
                ".ai/decisions/ADR-002.md",
                ".ai/shared/architecture/service-contracts.md",
                ".ai/plans/current/PLAN-001/evidence/implementation/TASK-001.md",
                ".ai/plans/current/PLAN-001/tasks/current/TASK-019.json",
                ".ai/shared/workflows/reviews.md",
            ],
        )

    def test_hashes_exact_raw_bytes_and_preserves_existing_v1_algorithms(self) -> None:
        source = request()
        candidate = build_candidate(source, self.registry)
        unsigned = candidate.unsigned_wire()
        canonical = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        self.assertEqual(candidate.diff_sha256.value, hashlib.sha256(source.diff).hexdigest())
        self.assertEqual(
            candidate.policy_model_digest.value,
            hashlib.sha256(source.policy + source.model_profile).hexdigest(),
        )
        self.assertEqual(candidate.fingerprint.value, hashlib.sha256(canonical).hexdigest())
        self.assertNotIn("fingerprint", unsigned)

    def test_raw_line_endings_are_material(self) -> None:
        original = build_candidate(request(), self.registry)
        lf = request(diff=b"binary\x00diff\n")
        changed = build_candidate(lf, self.registry)
        self.assertNotEqual(original.diff_sha256, changed.diff_sha256)
        self.assertNotEqual(original.fingerprint, changed.fingerprint)

    def test_accepts_both_full_git_oid_widths_and_rejects_malformed_values(self) -> None:
        self.assertEqual(build_candidate(request(), self.registry).base_oid, OID40_A)
        sha256_candidate = build_candidate(
            request(base_oid=OID64_A, head_oid=OID64_B),
            self.registry,
        )
        self.assertEqual(len(sha256_candidate.base_oid), 64)
        for bad_oid in ("a" * 39, "a" * 41, "A" * 40, "g" * 40, " a" * 20):
            with self.subTest(oid=bad_oid):
                with self.assertRaises(ValueError):
                    request(base_oid=bad_oid)

    def test_task_and_plan_candidates_share_schema_with_explicit_null_identity(self) -> None:
        task_candidate = build_candidate(request(), self.registry)
        plan_candidate = build_candidate(
            request(candidate_id="CANDIDATE-PLAN-001", task_id=None),
            self.registry,
        )
        self.registry.validate(task_candidate.to_wire())
        self.registry.validate(plan_candidate.to_wire())
        self.assertEqual(task_candidate.task_id, "TASK-019")
        self.assertIsNone(plan_candidate.task_id)
        self.assertIsNone(plan_candidate.to_wire()["task_id"])
        self.assertNotEqual(task_candidate.fingerprint, plan_candidate.fingerprint)

    def test_actual_dependency_free_task_context_needs_no_handoff_placeholder(self) -> None:
        task_record = json.loads(TASK_001_RECORD)
        self.assertEqual(task_record["depends_on"], [])
        required_handoffs = tuple(
            f".ai/plans/current/PLAN-001/evidence/implementation/{task_id}.md"
            for task_id in task_record["depends_on"]
        )
        actual_context = CandidateContext(
            plan=material(
                ".ai/plans/current/PLAN-001/plan.json",
                json.dumps(
                    {"id": "PLAN-001", "adr_refs": task_record["adr_refs"]},
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8"),
            ),
            graph=material(
                ".ai/plans/current/PLAN-001/graph.json",
                b'{"nodes":[{"task_id":"TASK-001","depends_on":[]}]}',
            ),
            specs=[
                material(
                    ".ai/plans/current/PLAN-001/spec.json",
                    b'{"id":"SPEC-001","status":"active"}',
                )
            ],
            adrs=[
                material(path, f"{path}\nStatus: accepted\n".encode("utf-8"))
                for path in task_record["adr_refs"]
            ],
            contracts=[
                material(
                    ".ai/shared/architecture/service-contracts.md",
                    b"ReviewService.evaluate(request) -> result\n",
                )
            ],
            handoffs=(),
            required_adr_paths=task_record["adr_refs"],
            required_handoff_paths=required_handoffs,
            supplemental=[
                material(TASK_001_TASK_PATH, TASK_001_RECORD),
                material(
                    ".ai/shared/workflows/reviews.md",
                    b"Candidate identity and invalidation\n",
                ),
            ],
        )
        reconstructed = build_candidate(
            request(
                candidate_id="CANDIDATE-TASK-001-dependency-free-fixture",
                task_id=task_record["id"],
                plan_id=task_record["plan_id"],
                graph_revision=4,
                base_oid="1a5e4ad2c0f476edcec3d55ca0ccc37d4c914751",
                head_oid="d1fc917466410febc6238479e65816dd39591a4f",
                diff=b"diff --git a/src/domain_values.py b/src/domain_values.py\n",
                context=actual_context,
                validation=[
                    material(
                        ".ai/plans/current/PLAN-001/evidence/validation/"
                        "TASK-001-a2-d1fc91746641.txt",
                        b"Ran focused TASK-001 tests\nOK\n",
                    )
                ],
                checklist_version="PLAN-001-v1",
                policy=b'{"review_required":true}\n',
                model_profile=b'{"implementation":"sol/xhigh"}\n',
            ),
            self.registry,
        )
        self.assertEqual(len(reconstructed.context_refs), 11)
        self.assertFalse(
            any(
                "/evidence/implementation/" in ref.path
                for ref in reconstructed.context_refs
            )
        )

    def test_plan_without_adrs_is_a_valid_context(self) -> None:
        no_adr_context = CandidateContext(
            plan=material(".ai/plans/current/PLAN-002/plan.json", b'{"adr_refs":[]}'),
            graph=material(".ai/plans/current/PLAN-002/graph.json", b"graph"),
            specs=[material(".ai/plans/current/PLAN-002/spec.json", b"spec")],
            adrs=(),
            contracts=[
                material(".ai/shared/architecture/service-contracts.md", b"contract")
            ],
            handoffs=(),
            required_adr_paths=(),
            required_handoff_paths=(),
        )
        candidate = build_candidate(
            request(
                candidate_id="CANDIDATE-PLAN-002",
                task_id=None,
                plan_id="PLAN-002",
                context=no_adr_context,
            ),
            self.registry,
        )
        self.assertIsNone(candidate.task_id)
        self.assertEqual(len(candidate.context_refs), 4)

    def test_rejects_missing_required_context_and_validation_evidence(self) -> None:
        for field in ("specs", "contracts"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    context(**{field: []})
        with self.assertRaisesRegex(ValueError, "ADR context is missing"):
            context(adrs=[])
        with self.assertRaisesRegex(ValueError, "handoff context is missing"):
            context(handoffs=[])
        with self.assertRaisesRegex(ValueError, "ADR context is missing"):
            context(
                adrs=[material(ADR_PATHS[0], b"adr")],
                required_adr_paths=[*ADR_PATHS, ".ai/decisions/ADR-003.md"],
            )
        with self.assertRaisesRegex(ValueError, "handoff context is missing"):
            context(
                required_handoff_paths=[
                    *HANDOFF_PATHS,
                    ".ai/plans/current/PLAN-001/evidence/implementation/TASK-004.md",
                ]
            )
        with self.assertRaises(TypeError):
            context(plan=None)
        with self.assertRaises(ValueError):
            request(validation=[])

    def test_rejects_duplicate_and_portable_alias_paths(self) -> None:
        duplicate = material(".ai/decisions/ADR-001.md", b"duplicate")
        with self.assertRaisesRegex(ValueError, "duplicate or aliased"):
            context(supplemental=[duplicate])
        alias = material(".AI/PLANS/CURRENT/PLAN-001/PLAN.JSON", b"alias")
        with self.assertRaisesRegex(ValueError, "duplicate or aliased"):
            context(supplemental=[alias])
        with self.assertRaisesRegex(ValueError, "canonical repository path"):
            material("evidence\\validation.bin", b"bytes")
        with self.assertRaisesRegex(ValueError, "duplicate or aliased"):
            request(
                validation=[
                    material(".AI/PLANS/CURRENT/PLAN-001/PLAN.JSON", b"alias")
                ]
            )
        with self.assertRaisesRegex(ValueError, "aliases supplied path"):
            context(required_adr_paths=[path.upper() for path in ADR_PATHS])

    def test_registry_validates_emitted_shape_and_wire_input(self) -> None:
        candidate = build_candidate(request(), self.registry)
        wire = candidate.to_wire()
        self.registry.validate(wire)
        self.assertEqual(candidate_from_wire(wire, self.registry), candidate)

        wire["unexpected"] = True
        with self.assertRaises(DomainException) as caught:
            candidate_from_wire(wire, self.registry)
        self.assertEqual(caught.exception.category, ErrorCategory.VALIDATION_FAILED)

    def test_rejects_tampered_fingerprint_and_has_no_self_reference(self) -> None:
        candidate = build_candidate(request(), self.registry)
        wire = candidate.to_wire()
        wire["fingerprint"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "does not match"):
            candidate_from_wire(wire, self.registry)

        clean_wire = candidate.to_wire()
        unsigned = {key: value for key, value in clean_wire.items() if key != "fingerprint"}
        self.assertNotIn(candidate.fingerprint.value, json.dumps(unsigned))

    def test_each_material_component_invalidates_the_candidate(self) -> None:
        original_request = request()
        candidate = build_candidate(original_request, self.registry)
        contexts = {
            "plan": replace(
                original_request.context,
                plan=material(original_request.context.plan.path, b"changed plan"),
            ),
            "graph": replace(
                original_request.context,
                graph=material(original_request.context.graph.path, b"changed graph"),
            ),
            "spec": replace(
                original_request.context,
                specs=[material(original_request.context.specs[0].path, b"changed spec")],
            ),
            "adr": replace(
                original_request.context,
                adrs=[
                    material(original_request.context.adrs[0].path, b"changed adr"),
                    original_request.context.adrs[1],
                ],
            ),
            "contract": replace(
                original_request.context,
                contracts=[
                    material(original_request.context.contracts[0].path, b"changed contract")
                ],
            ),
            "handoff": replace(
                original_request.context,
                handoffs=[
                    material(original_request.context.handoffs[0].path, b"changed handoff")
                ],
            ),
            "supplemental": replace(
                original_request.context,
                supplemental=[
                    material(original_request.context.supplemental[0].path, b"changed extra"),
                    original_request.context.supplemental[1],
                ],
            ),
            "applicable_roles_removed": replace(
                original_request.context,
                adrs=(),
                handoffs=(),
                required_adr_paths=(),
                required_handoff_paths=(),
            ),
        }
        variants = {
            "candidate_id": replace(original_request, candidate_id="different"),
            "task_id": replace(original_request, task_id="TASK-020"),
            "plan_id": replace(original_request, plan_id="PLAN-002"),
            "graph_revision": replace(original_request, graph_revision=5),
            "base_oid": replace(original_request, base_oid="c" * 40),
            "head_oid": replace(original_request, head_oid="d" * 40),
            "diff": replace(original_request, diff=b"changed diff"),
            "validation": replace(
                original_request,
                validation=[material(original_request.validation[0].path, b"changed validation")],
            ),
            "checklist": replace(original_request, checklist_version="PLAN-001-v2"),
            "policy": replace(original_request, policy=b"changed policy"),
            "model": replace(original_request, model_profile=b"changed model"),
            **{
                f"context_{name}": replace(original_request, context=value)
                for name, value in contexts.items()
            },
        }

        self.assertIs(verify_candidate(candidate, original_request, self.registry), candidate)
        for name, current in variants.items():
            with self.subTest(component=name):
                with self.assertRaises(DomainException) as caught:
                    verify_candidate(candidate, current, self.registry)
                self.assertEqual(caught.exception.category, ErrorCategory.STATE_CONFLICT)

    def test_defensively_freezes_inputs_and_returns_detached_wire_values(self) -> None:
        diff = bytearray(b"diff")
        policy = bytearray(b"policy")
        validation_bytes = bytearray(b"validation")
        validation = [material("evidence/validation.bin", validation_bytes)]
        adrs = [material(".ai/decisions/ADR-001.md", b"adr")]
        required_adrs = [ADR_PATHS[0]]
        frozen_context = context(adrs=adrs, required_adr_paths=required_adrs)
        frozen_request = request(
            diff=diff,
            policy=policy,
            validation=validation,
            context=frozen_context,
        )
        candidate = build_candidate(frozen_request, self.registry)
        before = candidate.to_wire()

        diff[:] = b"xxxx"
        policy[:] = b"xxxxxx"
        validation_bytes[:] = b"xxxxxxxxxx"
        validation.clear()
        adrs.clear()
        required_adrs.clear()
        detached = candidate.to_wire()
        detached["context_refs"][0]["sha256"] = "f" * 64

        self.assertEqual(candidate.to_wire(), before)
        self.assertEqual(build_candidate(frozen_request, self.registry), candidate)
        self.assertEqual(frozen_context.required_adr_paths, (ADR_PATHS[0],))

    def test_current_mutated_inputs_are_rehashed_instead_of_trusted(self) -> None:
        original = request()
        candidate = build_candidate(original, self.registry)
        changed = request(diff=bytearray(b"mutated current diff"))
        with self.assertRaises(DomainException):
            verify_candidate(candidate.to_wire(), changed, self.registry)


if __name__ == "__main__":
    unittest.main()
