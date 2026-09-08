from __future__ import annotations

import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path


WORKTREE_ROOT = Path(__file__).resolve().parents[3]
SRC = WORKTREE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from domain_values import DomainException, ErrorCategory, ScopeClaim, ScopePath
from scope import (
    AccessMode,
    ChangeEndpoint,
    PathChange,
    PathChangeKind,
    ScopeConflict,
    ScopeConflictKind,
    check_change_scope,
    detect_scope_conflicts,
    enforce_change_scope,
)


class ScopeConflictTests(unittest.TestCase):
    def test_exact_write_aliases_conflict_across_case_unicode_and_separators(self) -> None:
        aliases = (
            ("Src/Package/File.py", "src/package/file.py"),
            ("src\\package\\file.py", "src/package/file.py"),
            ("src/Kelvin.py", "SRC/kelvin.py"),
        )
        for left_path, right_path in aliases:
            with self.subTest(left=left_path, right=right_path):
                report = detect_scope_conflicts(
                    ScopeClaim(write_paths=(left_path,)),
                    ScopeClaim(write_paths=(right_path,)),
                    sequenced=False,
                )
                self.assertEqual(
                    [conflict.kind for conflict in report.conflicts],
                    [ScopeConflictKind.WRITE_WRITE],
                )
                self.assertTrue(report.requires_sequencing)
                self.assertTrue(report.blocks_concurrency)
                self.assertTrue(report.has_unsequenced_conflict)
                self.assertFalse(report.sequencing_satisfied)

    def test_ancestor_relationships_conflict_for_prefixes_and_exact_paths(self) -> None:
        pairs = (
            ("src/", "src/package/file.py"),
            ("src/package/", "src/package/nested/"),
            ("src/package", "src/package/file.py"),
        )
        for left_path, right_path in pairs:
            with self.subTest(left=left_path, right=right_path):
                report = detect_scope_conflicts(
                    ScopeClaim(write_paths=(left_path,)),
                    ScopeClaim(write_paths=(right_path,)),
                    sequenced=False,
                )
                self.assertEqual(len(report.conflicts), 1)
                self.assertEqual(report.conflicts[0].kind, ScopeConflictKind.WRITE_WRITE)

        disjoint = detect_scope_conflicts(
            ScopeClaim(write_paths=("src/one/",)),
            ScopeClaim(write_paths=("src/two/",)),
            sequenced=False,
        )
        self.assertFalse(disjoint.requires_sequencing)
        self.assertTrue(disjoint.can_run_concurrently)

    def test_writers_conflict_with_readers_in_either_direction(self) -> None:
        left_writes = detect_scope_conflicts(
            ScopeClaim(write_paths=("schemas/v1/task.schema.json",)),
            ScopeClaim(read_paths=("schemas/v1/",)),
            sequenced=False,
        )
        self.assertEqual(len(left_writes.conflicts), 1)
        self.assertEqual(left_writes.conflicts[0].kind, ScopeConflictKind.WRITE_READ)
        self.assertEqual(left_writes.conflicts[0].left_access, AccessMode.WRITE)
        self.assertEqual(left_writes.conflicts[0].right_access, AccessMode.READ)

        right_writes = detect_scope_conflicts(
            ScopeClaim(read_paths=("schemas/v1/",)),
            ScopeClaim(write_paths=("schemas/v1/task.schema.json",)),
            sequenced=False,
        )
        self.assertEqual(len(right_writes.conflicts), 1)
        self.assertEqual(right_writes.conflicts[0].left_access, AccessMode.READ)
        self.assertEqual(right_writes.conflicts[0].right_access, AccessMode.WRITE)

    def test_read_read_overlap_is_not_exclusive(self) -> None:
        report = detect_scope_conflicts(
            ScopeClaim(read_paths=("schemas/v1/",)),
            ScopeClaim(read_paths=("SCHEMAS\\V1\\task.schema.json",)),
            sequenced=False,
        )
        self.assertEqual(report.conflicts, ())
        self.assertFalse(report.requires_sequencing)
        self.assertTrue(report.can_run_concurrently)

    def test_shared_semantic_resources_force_sequencing(self) -> None:
        report = detect_scope_conflicts(
            ScopeClaim(
                write_paths=("src/one.py",),
                resources=("Component:Planning/Kernel",),
            ),
            ScopeClaim(
                write_paths=("src/two.py",),
                resources=("component:planning/kernel",),
            ),
            sequenced=False,
        )
        self.assertEqual(len(report.conflicts), 1)
        conflict = report.conflicts[0]
        self.assertEqual(conflict.kind, ScopeConflictKind.SEMANTIC_RESOURCE)
        self.assertEqual(conflict.left_resource, "Component:Planning/Kernel")
        self.assertEqual(conflict.right_resource, "component:planning/kernel")
        self.assertTrue(report.blocks_concurrency)

    def test_supplied_sequencing_resolves_concurrency_without_hiding_conflicts(self) -> None:
        left = ScopeClaim(write_paths=("src/shared.py",))
        right = ScopeClaim(read_paths=("src/shared.py",))
        unsequenced = detect_scope_conflicts(left, right, sequenced=False)
        sequenced = detect_scope_conflicts(left, right, sequenced=True)
        self.assertEqual(sequenced.conflicts, unsequenced.conflicts)
        self.assertTrue(sequenced.requires_sequencing)
        self.assertTrue(sequenced.blocks_concurrency)
        self.assertFalse(sequenced.can_run_concurrently)
        self.assertFalse(sequenced.has_unsequenced_conflict)
        self.assertTrue(sequenced.sequencing_satisfied)
        self.assertTrue(unsequenced.has_unsequenced_conflict)
        self.assertFalse(unsequenced.sequencing_satisfied)

    def test_conflict_order_is_independent_of_claim_declaration_order(self) -> None:
        first = detect_scope_conflicts(
            ScopeClaim(write_paths=("z/", "a/")),
            ScopeClaim(write_paths=("Z/file.py", "A/file.py")),
            sequenced=False,
        )
        second = detect_scope_conflicts(
            ScopeClaim(write_paths=("a/", "z/")),
            ScopeClaim(write_paths=("A/file.py", "Z/file.py")),
            sequenced=False,
        )
        self.assertEqual(first.conflicts, second.conflicts)

    def test_conflict_report_is_immutable_and_validates_supplied_facts(self) -> None:
        report = detect_scope_conflicts(
            ScopeClaim(write_paths=("src/file.py",)),
            ScopeClaim(write_paths=("src/file.py",)),
            sequenced=False,
        )
        with self.assertRaises(FrozenInstanceError):
            report.sequenced = True  # type: ignore[misc]
        with self.assertRaises(TypeError):
            detect_scope_conflicts(
                ScopeClaim(), ScopeClaim(), sequenced=1  # type: ignore[arg-type]
            )
        with self.assertRaises(ValueError):
            ScopeConflict(
                ScopeConflictKind.WRITE_WRITE,
                left_path=ScopePath.exact_file("src/one.py"),
                right_path=ScopePath.exact_file("src/two.py"),
                left_access=AccessMode.WRITE,
                right_access=AccessMode.WRITE,
            )
        with self.assertRaises(ValueError):
            ScopeConflict(
                ScopeConflictKind.SEMANTIC_RESOURCE,
                left_resource="component:one",
                right_resource="component:two",
            )


class ChangeScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scope = ScopeClaim(
            write_paths=("src/owned/", "docs/exact.md"),
            prohibited_paths=("src/owned/private/",),
        )

    def test_add_modify_delete_and_rename_inside_scope_are_permitted(self) -> None:
        changes = [
            PathChange("src/owned/new.py", "added"),
            PathChange("docs/exact.md", "modified"),
            PathChange("src/owned/old.py", "deleted"),
            PathChange(
                "src/owned/new_name.py",
                "renamed",
                "src/owned/old_name.py",
            ),
        ]
        report = check_change_scope(self.scope, changes)
        changes.append(PathChange("outside.py", "added"))
        self.assertTrue(report.permitted)
        self.assertEqual(len(report.changes), 4)
        self.assertEqual(report.violations, ())
        self.assertEqual(
            report.changes[-1].to_wire(),
            {
                "path": "src/owned/new_name.py",
                "change": "renamed",
                "previous_path": "src/owned/old_name.py",
            },
        )
        with self.assertRaises(FrozenInstanceError):
            report.changes[0].path = ScopePath.exact_file("outside.py")  # type: ignore[misc]

    def test_each_non_rename_change_checks_its_path_and_prohibited_claims(self) -> None:
        changes = (
            PathChange("elsewhere/new.py", PathChangeKind.ADDED),
            PathChange("src/owned/private/data.py", PathChangeKind.MODIFIED),
            PathChange("elsewhere/old.py", PathChangeKind.DELETED),
        )
        report = check_change_scope(self.scope, changes)
        self.assertFalse(report.permitted)
        self.assertEqual(
            [violation.change.change for violation in report.violations],
            [
                PathChangeKind.ADDED,
                PathChangeKind.MODIFIED,
                PathChangeKind.DELETED,
            ],
        )
        self.assertTrue(
            all(violation.endpoint is ChangeEndpoint.PATH for violation in report.violations)
        )

    def test_exact_file_write_claim_is_not_treated_as_a_directory_prefix(self) -> None:
        scope = ScopeClaim(write_paths=("src/owned",))
        report = check_change_scope(
            scope,
            (
                PathChange("SRC\\OWNED", "modified"),
                PathChange("src/owned/child.py", "added"),
            ),
        )
        self.assertEqual(
            [violation.path.as_wire() for violation in report.violations],
            ["src/owned/child.py"],
        )

    def test_exact_prohibited_file_overrides_directory_write_claim(self) -> None:
        scope = ScopeClaim(
            write_paths=("src/owned/",),
            prohibited_paths=("SRC\\OWNED\\blocked.py",),
        )
        report = check_change_scope(
            scope,
            (
                PathChange("src/owned/allowed.py", "modified"),
                PathChange("src/owned/BLOCKED.py", "deleted"),
            ),
        )
        self.assertEqual(
            [violation.path.as_wire() for violation in report.violations],
            ["src/owned/BLOCKED.py"],
        )

    def test_rename_checks_both_old_and_new_paths(self) -> None:
        old_outside = PathChange(
            "src/owned/new.py", "renamed", "outside/old.py"
        )
        new_outside = PathChange(
            "outside/new.py", "renamed", "src/owned/old.py"
        )
        both_outside = PathChange(
            "outside/newer.py", "renamed", "elsewhere/older.py"
        )
        report = check_change_scope(
            self.scope, (old_outside, new_outside, both_outside)
        )
        self.assertEqual(
            [(item.change, item.endpoint, item.path.as_wire()) for item in report.violations],
            [
                (old_outside, ChangeEndpoint.PREVIOUS_PATH, "outside/old.py"),
                (new_outside, ChangeEndpoint.PATH, "outside/new.py"),
                (both_outside, ChangeEndpoint.PATH, "outside/newer.py"),
                (both_outside, ChangeEndpoint.PREVIOUS_PATH, "elsewhere/older.py"),
            ],
        )

    def test_rename_checks_prohibited_old_and_new_paths(self) -> None:
        changes = (
            PathChange(
                "src/owned/new.py", "renamed", "src/owned/private/old.py"
            ),
            PathChange(
                "src/owned/private/new.py", "renamed", "src/owned/old.py"
            ),
        )
        report = check_change_scope(self.scope, changes)
        self.assertEqual(
            [(item.endpoint, item.path.as_wire()) for item in report.violations],
            [
                (ChangeEndpoint.PREVIOUS_PATH, "src/owned/private/old.py"),
                (ChangeEndpoint.PATH, "src/owned/private/new.py"),
            ],
        )

    def test_change_paths_use_accepted_case_unicode_and_separator_normalization(self) -> None:
        scope = ScopeClaim(
            write_paths=("Src/Kernel/",),
            prohibited_paths=("src/kernel/private/",),
        )
        allowed = check_change_scope(
            scope, (PathChange("SRC\\kelvin.py", "added"),)
        )
        # The sibling is outside the Kernel prefix despite sharing normalization rules.
        self.assertFalse(allowed.permitted)

        normalized = check_change_scope(
            scope,
            (
                PathChange("SRC\\KERNEL\\module.py", "modified"),
                PathChange("src/kernel/PRIVATE/secret.py", "deleted"),
            ),
        )
        self.assertEqual(
            [item.path.as_wire() for item in normalized.violations],
            ["src/kernel/PRIVATE/secret.py"],
        )

    def test_change_value_rejects_ambiguous_endpoints_and_directory_claims(self) -> None:
        with self.assertRaises(ValueError):
            PathChange("src/owned/new.py", "renamed")
        with self.assertRaises(ValueError):
            PathChange("src/owned/file.py", "modified", "src/owned/old.py")
        with self.assertRaises(ValueError):
            PathChange(ScopePath.directory("src/owned/"), "deleted")
        with self.assertRaises(ValueError):
            PathChange(
                "src/owned/new.py",
                "renamed",
                ScopePath.directory("src/owned/old/"),
            )

    def test_enforcement_raises_structured_immutable_scope_error(self) -> None:
        with self.assertRaises(DomainException) as raised:
            enforce_change_scope(
                self.scope,
                (PathChange("outside/new.py", "renamed", "outside/old.py"),),
            )
        error = raised.exception.error
        self.assertEqual(error.category, ErrorCategory.SCOPE_CONFLICT)
        self.assertFalse(error.retryable)
        self.assertEqual(
            error.details.to_dict(),
            {
                "violations": [
                    {
                        "change": "renamed",
                        "endpoint": "path",
                        "path": "outside/new.py",
                    },
                    {
                        "change": "renamed",
                        "endpoint": "previous_path",
                        "path": "outside/old.py",
                    },
                ]
            },
        )


if __name__ == "__main__":
    unittest.main()
