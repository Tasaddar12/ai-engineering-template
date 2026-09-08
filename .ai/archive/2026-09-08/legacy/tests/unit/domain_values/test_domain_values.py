from __future__ import annotations

import sys
import unittest
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from domain_values import (
    AgentOutputStatus,
    AgentRunStatus,
    CheckConclusion,
    CommandStatus,
    CompletionStatus,
    DecisionStatus,
    DomainError,
    DomainException,
    EntityId,
    ErrorCategory,
    EvidenceRef,
    ExecutionStatus,
    FrozenJsonObject,
    GraphStatus,
    InstallationStatus,
    PendingOperationStatus,
    PlanId,
    PlanStatus,
    ProjectPhase,
    PullRequestReviewDecision,
    PullRequestStatus,
    RecordKind,
    RecordRef,
    RecoveryStatus,
    ResearchStatus,
    ResultEnvelope,
    ResultStatus,
    ReviewCheckStatus,
    ReviewVerdict,
    Revision,
    ScopeClaim,
    ScopePath,
    ScopePathKind,
    Sha256Digest,
    SpecStatus,
    TaskStatus,
    ValidationStatus,
    WorkflowRunStatus,
    WorktreeStatus,
    freeze_json,
)


DIGEST = "a" * 64


class IdentityTests(unittest.TestCase):
    def test_plan_ids_and_revisions_are_canonical_values(self) -> None:
        self.assertEqual(str(PlanId("PLAN-001")), "PLAN-001")
        self.assertEqual(int(Revision(0)), 0)
        self.assertEqual(int(Revision(12)), 12)
        with self.assertRaises(ValueError):
            PlanId("plan-001")
        with self.assertRaises(ValueError):
            PlanId("PLAN-01")
        with self.assertRaises(ValueError):
            Revision(-1)
        with self.assertRaises(TypeError):
            Revision(True)

    def test_plan_local_record_references_cannot_be_bare(self) -> None:
        reference = RecordRef(RecordKind.TASK, EntityId("TASK-001"), PlanId("PLAN-001"))
        self.assertEqual(reference.key, ("task", "PLAN-001", "TASK-001"))
        self.assertEqual(str(reference), "task:PLAN-001:TASK-001")
        self.assertTrue(reference.is_plan_qualified)
        with self.assertRaisesRegex(ValueError, "require plan_id"):
            RecordRef("task", "TASK-001")
        with self.assertRaisesRegex(ValueError, "invalid local ID"):
            RecordRef("task", "COMMAND-001", "PLAN-001")
        for kind in ("command", "review", "evidence"):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "require plan_id"):
                RecordRef(kind, "LOCAL-001")

    def test_project_unique_records_reject_false_plan_qualification(self) -> None:
        plan = RecordRef("plan", "PLAN-123")
        self.assertEqual(plan.key, ("plan", None, "PLAN-123"))
        with self.assertRaisesRegex(ValueError, "cannot carry a plan qualifier"):
            RecordRef("plan", "PLAN-123", "PLAN-123")
        with self.assertRaisesRegex(ValueError, "require plan_id"):
            RecordRef("custom-record", "CUSTOM-001")


class ScopePathTests(unittest.TestCase):
    def test_trailing_separator_distinguishes_directory_prefix_from_exact_file(self) -> None:
        exact = ScopePath("src/domain_values.py")
        directory = ScopePath("src/domain_values/")
        self.assertIs(exact.kind, ScopePathKind.EXACT_FILE)
        self.assertIs(directory.kind, ScopePathKind.DIRECTORY_PREFIX)
        self.assertEqual(exact.as_wire(), "src/domain_values.py")
        self.assertEqual(directory.as_wire(), "src/domain_values/")
        self.assertTrue(directory.contains("src/domain_values/test.py"))
        self.assertTrue(directory.contains("src/domain_values/nested/"))
        self.assertTrue(directory.contains(directory))
        self.assertFalse(directory.contains("src/domain_values"))
        self.assertFalse(exact.contains(directory))
        self.assertFalse(exact.contains("src/domain_values.py/child"))
        self.assertFalse(directory.overlaps("src/domain_values_extra.py"))

    def test_windows_separators_normalize_without_changing_prefix_semantics(self) -> None:
        path = ScopePath("tests\\unit\\domain_values\\")
        self.assertEqual(path.as_wire(), "tests/unit/domain_values/")
        self.assertTrue(path.contains(r"tests\unit\domain_values\test_values.py"))

    def test_unsafe_cross_platform_paths_are_rejected(self) -> None:
        invalid = [
            "CON",
            "con.txt",
            "folder/CON .txt",
            "CONIN$",
            "COM\N{SUPERSCRIPT ONE}.txt",
            "\N{FULLWIDTH LATIN CAPITAL LETTER A}"
            "\N{FULLWIDTH LATIN CAPITAL LETTER U}"
            "\N{FULLWIDTH LATIN CAPITAL LETTER X}.txt",
            "bad:name",
            "bad\N{FULLWIDTH COLON}stream",
            "bad<name",
            "trailing.",
            "C:/repo/file.py",
            "/repo/file.py",
            "//server/share/file.py",
            "a/../b.py",
            "a//b.py",
            "a/\u200b/b.py",
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                ScopePath(value)

    def test_unicode_normalization_and_case_aliases_conflict(self) -> None:
        composed = ScopePath("caf\N{LATIN SMALL LETTER E WITH ACUTE}/Stra\N{LATIN SMALL LETTER SHARP S}e/")
        decomposed = ScopePath("cafe\N{COMBINING ACUTE ACCENT}/STRASSE/file.py")
        self.assertTrue(composed.overlaps(decomposed))
        left = ScopeClaim(write_paths=[composed], resources=["Component:Domain/Values"])
        right = ScopeClaim(read_paths=[decomposed], resources=["component:domain/values"])
        self.assertTrue(left.conflicts_with(right))

    def test_conflicts_include_exact_file_ancestors_and_all_descendant_kinds(self) -> None:
        parent = ScopePath("src/generated")
        child_file = ScopePath("src/generated/value.py")
        child_directory = ScopePath("src/generated/nested/")
        for child in (child_file, child_directory):
            with self.subTest(child=child):
                self.assertTrue(parent.overlaps(child))
                self.assertTrue(child.overlaps(parent))
                self.assertTrue(
                    ScopeClaim(write_paths=[parent]).conflicts_with(
                        ScopeClaim(write_paths=[child])
                    )
                )
                self.assertTrue(
                    ScopeClaim(write_paths=[child]).conflicts_with(
                        ScopeClaim(write_paths=[parent])
                    )
                )
                self.assertTrue(
                    ScopeClaim(write_paths=[parent]).conflicts_with(
                        ScopeClaim(read_paths=[child])
                    )
                )
                self.assertTrue(
                    ScopeClaim(read_paths=[child]).conflicts_with(
                        ScopeClaim(write_paths=[parent])
                    )
                )
                self.assertTrue(
                    ScopeClaim(read_paths=[parent]).conflicts_with(
                        ScopeClaim(write_paths=[child])
                    )
                )
                self.assertTrue(
                    ScopeClaim(write_paths=[child]).conflicts_with(
                        ScopeClaim(read_paths=[parent])
                    )
                )

        unicode_parent = ScopePath("SRC/caf\N{LATIN SMALL LETTER E WITH ACUTE}")
        unicode_child = ScopePath(
            "src/cafe\N{COMBINING ACUTE ACCENT}/nested/"
        )
        self.assertTrue(unicode_parent.overlaps(unicode_child))
        self.assertTrue(unicode_child.overlaps(unicode_parent))
        self.assertTrue(
            ScopeClaim(write_paths=[unicode_parent]).conflicts_with(
                ScopeClaim(read_paths=[unicode_child])
            )
        )
        self.assertFalse(parent.overlaps("src/generator/value.py"))
        self.assertFalse(child_file.overlaps("src/generated_other/value.py"))
        self.assertFalse(
            ScopeClaim(write_paths=[parent]).conflicts_with(
                ScopeClaim(write_paths=["src/generator/value.py"])
            )
        )

    def test_scope_rejects_scalar_collections_instead_of_splitting_characters(self) -> None:
        fields = ("write_paths", "read_paths", "prohibited_paths", "resources")
        for field_name in fields:
            with self.subTest(field=field_name), self.assertRaisesRegex(TypeError, "scalar string"):
                ScopeClaim(**{field_name: "src/domain_values.py"})
        with self.assertRaisesRegex(ValueError, "duplicate or aliased"):
            ScopeClaim(write_paths=["src/domain_values", "src/domain_values/"])

    def test_scope_permissions_honor_exact_prefix_and_prohibited_claims(self) -> None:
        scope = ScopeClaim(
            write_paths=["src/domain_values.py", "tests/unit/domain_values/"],
            read_paths=["schemas/v1/"],
            prohibited_paths=["tests/unit/domain_values/secret/"],
        )
        self.assertTrue(scope.permits_write("src/domain_values.py"))
        self.assertFalse(scope.permits_write("src/domain_values.py.bak"))
        self.assertTrue(scope.permits_write("tests/unit/domain_values/test_values.py"))
        self.assertFalse(scope.permits_write("tests/unit/domain_values"))
        self.assertFalse(scope.permits_write("tests/unit/domain_values/secret/key.txt"))
        self.assertTrue(scope.permits_read("schemas/v1/task.schema.json"))
        with self.assertRaisesRegex(ValueError, "exact-file"):
            scope.permits_write(ScopePath.directory("tests/unit/domain_values"))
        with self.assertRaisesRegex(ValueError, "exact-file"):
            scope.permits_read(ScopePath.directory("schemas/v1"))


class ImmutableEnvelopeTests(unittest.TestCase):
    def test_evidence_detaches_and_deeply_freezes_nested_json(self) -> None:
        metadata = {"command": {"argv": ["python", "-m", "unittest"]}}
        evidence = EvidenceRef("evidence/test.json", DIGEST, metadata)
        metadata["command"]["argv"].append("mutated")
        self.assertEqual(
            evidence.metadata.to_dict(),
            {"command": {"argv": ["python", "-m", "unittest"]}},
        )
        self.assertIsInstance(evidence.sha256, Sha256Digest)
        self.assertIsInstance(evidence.metadata["command"], FrozenJsonObject)
        with self.assertRaises(TypeError):
            evidence.metadata["new"] = "value"  # type: ignore[index]
        with self.assertRaises(AttributeError):
            evidence.metadata._items = ()  # type: ignore[misc]
        with self.assertRaises(AttributeError):
            del evidence.metadata._items  # type: ignore[misc]
        self.assertIsInstance(hash(evidence), int)

    def test_frozen_json_rejects_non_json_values_and_cycles(self) -> None:
        with self.assertRaises(TypeError):
            freeze_json({"bad": {1, 2}})
        with self.assertRaises(ValueError):
            freeze_json({"bad": float("nan")})
        cyclic: list[object] = []
        cyclic.append(cyclic)
        with self.assertRaisesRegex(ValueError, "cycle"):
            freeze_json(cyclic)

    def test_domain_error_is_immutable_but_wrapper_propagates_normally(self) -> None:
        evidence = EvidenceRef("evidence/failure.json", DIGEST)
        error = DomainError(
            ErrorCategory.VALIDATION_FAILED,
            "validation failed",
            evidence_refs=[evidence],
            details={"failed_checks": ["test.TASK-001"]},
        )
        with self.assertRaises(FrozenInstanceError):
            error.message = "changed"  # type: ignore[misc]

        observed_traceback: list[bool] = []

        @contextmanager
        def boundary():
            try:
                yield
            except DomainException as exc:
                observed_traceback.append(exc.__traceback__ is not None)
                raise

        with self.assertRaises(DomainException) as caught:
            with boundary():
                raise DomainException(error)
        self.assertIs(caught.exception.error, error)
        self.assertIs(caught.exception.category, ErrorCategory.VALIDATION_FAILED)
        self.assertEqual(observed_traceback, [True])

    def test_results_require_explicit_error_or_content_addressed_success_evidence(self) -> None:
        evidence = EvidenceRef("evidence/success.json", DIGEST)
        payload = {"record": {"status": "accepted"}}
        result = ResultEnvelope(ResultStatus.SUCCEEDED, [evidence], payload=payload)
        payload["record"]["status"] = "mutated"
        self.assertEqual(result.payload.to_dict(), {"record": {"status": "accepted"}})
        with self.assertRaisesRegex(ValueError, "require content-addressed evidence"):
            ResultEnvelope(ResultStatus.SUCCEEDED, [])
        with self.assertRaisesRegex(ValueError, "require an explicit DomainError"):
            ResultEnvelope(ResultStatus.FAILED, [])


class VocabularyTests(unittest.TestCase):
    def test_schema_and_service_lifecycle_vocabularies_are_complete(self) -> None:
        expected = {
            PlanStatus: {
                "draft", "isolation", "approved", "running", "integration_review",
                "replanning", "delivery_ready", "delivering", "completed", "blocked",
            },
            TaskStatus: {
                "backlog", "ready", "running", "validating", "review_1", "review_2",
                "repairing", "accepted", "completed", "replanning", "superseded", "blocked",
            },
            WorkflowRunStatus: {"queued", "running", "paused", "succeeded", "failed", "cancelled"},
            AgentRunStatus: {"queued", "running", "succeeded", "failed", "cancelled", "unknown"},
            WorktreeStatus: {"planned", "active", "retained", "cleanup_pending", "removed"},
            PullRequestStatus: {"prepared", "open", "checks_pending", "ready", "merged", "closed"},
            ExecutionStatus: {"progress", "waiting", "tasks_accepted", "paused", "failed", "cancelled"},
            CompletionStatus: {"progress", "waiting", "delivery_ready", "completed", "paused", "failed"},
            GraphStatus: {"proposed", "approved", "superseded"},
            RecoveryStatus: {"proposed", "isolation_pending", "approved", "applied", "rejected"},
            CommandStatus: {"launch_failed", "running", "exited", "timed_out", "cancelled", "unknown"},
            DecisionStatus: {"proposed", "accepted", "superseded"},
            AgentOutputStatus: {"failed", "succeeded", "blocked", "cancelled"},
            CheckConclusion: {"pending", "success", "failure", "cancelled", "skipped", "unknown"},
            PullRequestReviewDecision: {"unknown", "approved", "changes_requested"},
            ReviewVerdict: {"fail", "pass", "inconclusive"},
            ReviewCheckStatus: {"fail", "pass", "not_applicable"},
            ValidationStatus: {"failed", "passed", "not_run", "unknown"},
            InstallationStatus: {"source_foundation", "installed", "upgrade_pending"},
            ResearchStatus: {"active", "archived", "superseded"},
            PendingOperationStatus: {"intent", "observed", "ambiguous"},
            ProjectPhase: {"foundation", "implementation", "operational"},
            SpecStatus: {"draft", "active", "superseded", "archived"},
        }
        for enum_type, values in expected.items():
            with self.subTest(enum=enum_type.__name__):
                self.assertEqual({member.value for member in enum_type}, values)
        self.assertEqual(
            {member.value for member in ErrorCategory},
            {
                "invalid_input", "policy_denied", "unsupported_capability", "state_conflict",
                "scope_conflict", "git_conflict", "validation_failed", "review_failed",
                "transient_provider", "ambiguous_side_effect", "budget_exhausted", "internal_error",
            },
        )


if __name__ == "__main__":
    unittest.main()
