# Pre-approval task snapshot

This snapshot preserves proposed intent, not completed work.

```json
{
  "note": "Historical pre-approval task snapshot, not a canonical task schema artifact",
  "tasks": [
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-008",
      "plan_id": "PLAN-001",
      "title": "Implement pure guarded transitions",
      "status": "backlog",
      "archived": false,
      "objective": "Implement pure guarded transitions. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-001",
        "TASK-004"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/domain/transitions/",
          "tests/unit/domain_transitions/",
          "docs/implementation/TASK-008.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:domain/transitions"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-008-AC1",
          "description": "Reject illegal entity state transitions and missing evidence guards",
          "verification": "TASK-008 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-008-AC2",
          "description": "Make transition decisions deterministic with immutable events and no IO",
          "verification": "TASK-008 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-01"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-001",
        "handoff:TASK-004"
      ],
      "output_contracts": [
        "domain/transitions public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-008"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-014",
      "plan_id": "PLAN-001",
      "title": "Detect path and semantic conflicts",
      "status": "backlog",
      "archived": false,
      "objective": "Detect path and semantic conflicts. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-001",
        "TASK-004"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/planning/ownership/",
          "tests/unit/planning_ownership/",
          "docs/implementation/TASK-014.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:planning/ownership"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-014-AC1",
          "description": "Detect exact/prefix/case-normalized write overlap and concurrent contract reads",
          "verification": "TASK-014 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-014-AC2",
          "description": "Require sequencing for shared resource claims and report out-of-scope rename/delete changes",
          "verification": "TASK-014 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-03"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-001",
        "handoff:TASK-004"
      ],
      "output_contracts": [
        "planning/ownership public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-014"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-037",
      "plan_id": "PLAN-001",
      "title": "Package assets and configure platform CI",
      "status": "backlog",
      "archived": false,
      "objective": "Package assets and configure platform CI. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-035",
        "TASK-036"
      ],
      "scope": {
        "write_paths": [
          "pyproject.toml",
          ".github/workflows/",
          "tests/package/",
          "docs/implementation/TASK-037.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:release"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-037-AC1",
          "description": "Verify installed package contains versioned schemas/templates and exposes optional ai entry point",
          "verification": "TASK-037 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-037-AC2",
          "description": "Configure Linux/Windows validation/build matrix and report actual support without live provider dependencies",
          "verification": "TASK-037 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-08",
        "AC-09"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-035",
        "handoff:TASK-036"
      ],
      "output_contracts": [
        "release public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-037"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-001",
      "plan_id": "PLAN-001",
      "title": "Define immutable domain values",
      "status": "ready",
      "archived": false,
      "objective": "Define immutable domain values. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [],
      "scope": {
        "write_paths": [
          "src/ai_engineering/domain/values/",
          "tests/unit/domain_values/",
          "docs/implementation/TASK-001.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:domain/values"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-001-AC1",
          "description": "Parse stable IDs, scope claims and revision references with explicit invalid-value errors",
          "verification": "TASK-001 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-001-AC2",
          "description": "Represent all documented lifecycle vocabularies without performing IO",
          "verification": "TASK-001 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-01"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md"
      ],
      "output_contracts": [
        "domain/values public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-001"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-007",
      "plan_id": "PLAN-001",
      "title": "Implement observed Git operations",
      "status": "backlog",
      "archived": false,
      "objective": "Implement observed Git operations. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-002",
        "TASK-006"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/git/",
          "tests/unit/git/",
          "docs/implementation/TASK-007.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:git"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-007-AC1",
          "description": "Inspect real refs, worktrees, dirty files and ancestry using validated Git argv",
          "verification": "TASK-007 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-007-AC2",
          "description": "Create branches and integration commits conditionally on expected heads and return observed facts",
          "verification": "TASK-007 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-02"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-002",
        "handoff:TASK-006"
      ],
      "output_contracts": [
        "git public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-007"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-013",
      "plan_id": "PLAN-001",
      "title": "Build validated dependency graph",
      "status": "backlog",
      "archived": false,
      "objective": "Build validated dependency graph. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-001",
        "TASK-004"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/planning/dag/",
          "tests/unit/planning_dag/",
          "docs/implementation/TASK-013.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:planning/dag"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-013-AC1",
          "description": "Reject cycles, unknown nodes, self dependencies and inconsistent task/graph edges",
          "verification": "TASK-013 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-013-AC2",
          "description": "Return deterministic topological order and dependency-ready frontier with acceptance coverage",
          "verification": "TASK-013 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-03"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-001",
        "handoff:TASK-004"
      ],
      "output_contracts": [
        "planning/dag public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-013"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-030",
      "plan_id": "PLAN-001",
      "title": "Reconcile completed work and archive",
      "status": "backlog",
      "archived": false,
      "objective": "Reconcile completed work and archive. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-012",
        "TASK-029"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/workflows/archive/",
          "tests/unit/workflows_archive/",
          "docs/implementation/TASK-030.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:workflows/archive"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-030-AC1",
          "description": "Mark plan/tasks completed only after observed merge and preserve required artifact/commit references",
          "verification": "TASK-030 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-030-AC2",
          "description": "Create archive manifest and perform only eligible owned worktree cleanup",
          "verification": "TASK-030 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-07"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-012",
        "handoff:TASK-029"
      ],
      "output_contracts": [
        "workflows/archive public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-030"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-025",
      "plan_id": "PLAN-001",
      "title": "Apply isolated recovery and restart",
      "status": "backlog",
      "archived": false,
      "objective": "Apply isolated recovery and restart. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-010",
        "TASK-015",
        "TASK-021",
        "TASK-024"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/workflows/recovery/",
          "tests/unit/workflows_recovery/",
          "docs/implementation/TASK-025.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:workflows/recovery"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-025-AC1",
          "description": "Quiesce affected descendants, preserve evidence and apply only re-reviewed graph transactions",
          "verification": "TASK-025 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-025-AC2",
          "description": "Start replacement attempts in new worktrees with lineage-wide budgets and fresh review requirements",
          "verification": "TASK-025 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-06"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-010",
        "handoff:TASK-015",
        "handoff:TASK-021",
        "handoff:TASK-024"
      ],
      "output_contracts": [
        "workflows/recovery public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-025"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-019",
      "plan_id": "PLAN-001",
      "title": "Fingerprint code and context candidates",
      "status": "backlog",
      "archived": false,
      "objective": "Fingerprint code and context candidates. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-001",
        "TASK-004"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/reviews/candidates/",
          "tests/unit/reviews_candidates/",
          "docs/implementation/TASK-019.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:reviews/candidates"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-019-AC1",
          "description": "Deterministically hash exact base/head, diff, graph, context, validation, policy and checklist inputs",
          "verification": "TASK-019 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-019-AC2",
          "description": "Invalidate candidates for each material code/context input change without self-referential hashes",
          "verification": "TASK-019 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-05"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-001",
        "handoff:TASK-004"
      ],
      "output_contracts": [
        "reviews/candidates public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-019"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-032",
      "plan_id": "PLAN-001",
      "title": "Upgrade owned assets with migration checks",
      "status": "backlog",
      "archived": false,
      "objective": "Upgrade owned assets with migration checks. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-005",
        "TASK-009",
        "TASK-031"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/workflows/upgrade/",
          "tests/unit/workflows_upgrade/",
          "docs/implementation/TASK-032.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:workflows/upgrade"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-032-AC1",
          "description": "Compute dry-run three-way owned-asset changes using manifests and preserve project-owned records",
          "verification": "TASK-032 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-032-AC2",
          "description": "Apply compatible migrations in isolated worktree with validated checkpoint and safe rollback proposal",
          "verification": "TASK-032 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-08"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-005",
        "handoff:TASK-009",
        "handoff:TASK-031"
      ],
      "output_contracts": [
        "workflows/upgrade public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-032"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-006",
      "plan_id": "PLAN-001",
      "title": "Execute commands with durable evidence",
      "status": "backlog",
      "archived": false,
      "objective": "Execute commands with durable evidence. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-002",
        "TASK-004"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/commands/",
          "tests/unit/commands/",
          "docs/implementation/TASK-006.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:commands"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-006-AC1",
          "description": "Execute fixed argv command definitions with cwd policy, timeout, exit status and timestamp capture",
          "verification": "TASK-006 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-006-AC2",
          "description": "Redact/truncate output with explicit evidence flags and handle launch failure and cancellation",
          "verification": "TASK-006 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-02"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-002",
        "handoff:TASK-004"
      ],
      "output_contracts": [
        "commands public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-006"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-011",
      "plan_id": "PLAN-001",
      "title": "Manage one worktree per attempt",
      "status": "backlog",
      "archived": false,
      "objective": "Manage one worktree per attempt. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-007",
        "TASK-010"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/worktrees/lifecycle/",
          "tests/unit/worktrees_lifecycle/",
          "docs/implementation/TASK-011.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:worktrees/lifecycle"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-011-AC1",
          "description": "Idempotently create owned task/integration worktrees and record actual base and branch",
          "verification": "TASK-011 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-011-AC2",
          "description": "Refuse unsafe cleanup of dirty, untracked, live-leased or unmanaged worktrees",
          "verification": "TASK-011 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-02"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-007",
        "handoff:TASK-010"
      ],
      "output_contracts": [
        "worktrees/lifecycle public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-011"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-010",
      "plan_id": "PLAN-001",
      "title": "Reconcile interrupted side-effect intents",
      "status": "backlog",
      "archived": false,
      "objective": "Reconcile interrupted side-effect intents. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-009"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/state/intents/",
          "tests/unit/state_intents/",
          "docs/implementation/TASK-010.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:state/intents"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-010-AC1",
          "description": "Record intents before effects and resolve committed duplicate operation IDs",
          "verification": "TASK-010 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-010-AC2",
          "description": "Return ambiguous outcomes for unresolved effects and never blindly repeat them",
          "verification": "TASK-010 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-02"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-009"
      ],
      "output_contracts": [
        "state/intents public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-010"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-034",
      "plan_id": "PLAN-001",
      "title": "Wire the six major CLI workflows",
      "status": "backlog",
      "archived": false,
      "objective": "Wire the six major CLI workflows. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-026",
        "TASK-027",
        "TASK-030",
        "TASK-031",
        "TASK-032",
        "TASK-033"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/cli/",
          "tests/unit/cli/",
          "docs/implementation/TASK-034.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:cli"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-034-AC1",
          "description": "Expose designed commands through typed dependency composition with truthful JSON/status/exit codes",
          "verification": "TASK-034 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-034-AC2",
          "description": "Ensure dry-run has no state or external mutations and resume uses persisted authorization",
          "verification": "TASK-034 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-09"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-026",
        "handoff:TASK-027",
        "handoff:TASK-030",
        "handoff:TASK-031",
        "handoff:TASK-032",
        "handoff:TASK-033"
      ],
      "output_contracts": [
        "cli public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-034"
      ],
      "estimated_production_files": 5,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-009",
      "plan_id": "PLAN-001",
      "title": "Persist serialized state checkpoints",
      "status": "backlog",
      "archived": false,
      "objective": "Persist serialized state checkpoints. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-002",
        "TASK-007",
        "TASK-008"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/state/checkpoints/",
          "tests/unit/state_checkpoints/",
          "docs/implementation/TASK-009.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:state/checkpoints"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-009-AC1",
          "description": "Commit generation-checked transactions with exclusive coordinator ownership and operation deduplication",
          "verification": "TASK-009 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-009-AC2",
          "description": "Recover projection writes after injected crash without acknowledging an uncommitted generation",
          "verification": "TASK-009 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-02"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-002",
        "handoff:TASK-007",
        "handoff:TASK-008"
      ],
      "output_contracts": [
        "state/checkpoints public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-009"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-005",
      "plan_id": "PLAN-001",
      "title": "Build owned asset catalog",
      "status": "backlog",
      "archived": false,
      "objective": "Build owned asset catalog. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-004"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/templates/",
          "tests/unit/templates/",
          "docs/implementation/TASK-005.md",
          "templates/catalog/"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:templates"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-005-AC1",
          "description": "Build deterministic manifest of framework-owned and seed-only assets",
          "verification": "TASK-005 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-005-AC2",
          "description": "Verify every catalog entry hash and reject duplicate or escaping paths",
          "verification": "TASK-005 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-08"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-004"
      ],
      "output_contracts": [
        "templates public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-005"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-012",
      "plan_id": "PLAN-001",
      "title": "Reconcile worktree records with Git",
      "status": "backlog",
      "archived": false,
      "objective": "Reconcile worktree records with Git. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-011"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/worktrees/reconcile/",
          "tests/unit/worktrees_reconcile/",
          "docs/implementation/TASK-012.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:worktrees/reconcile"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-012-AC1",
          "description": "Detect missing/moved/stale/merged worktrees and unexpected head divergence",
          "verification": "TASK-012 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-012-AC2",
          "description": "Emit repair proposals preserving unknown content and invalidating stale approvals",
          "verification": "TASK-012 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-02"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-011"
      ],
      "output_contracts": [
        "worktrees/reconcile public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-012"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-003",
      "plan_id": "PLAN-001",
      "title": "Freeze agent and workflow service ports",
      "status": "backlog",
      "archived": false,
      "objective": "Freeze agent and workflow service ports. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-001"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/domain/workflow_ports/",
          "tests/unit/domain_workflow_ports/",
          "docs/implementation/TASK-003.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:domain/workflow_ports"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-003-AC1",
          "description": "Define AgentAdapter, ContextBuilder, Validator and ReviewService requests/results",
          "verification": "TASK-003 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-003-AC2",
          "description": "Define DeliveryAdapter and workflow service composition boundaries with cancellation and ambiguous outcomes",
          "verification": "TASK-003 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-01",
        "AC-04"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-001"
      ],
      "output_contracts": [
        "domain/workflow_ports public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-003"
      ],
      "estimated_production_files": 5,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-017",
      "plan_id": "PLAN-001",
      "title": "Implement agent dispatch contract and fake adapter",
      "status": "backlog",
      "archived": false,
      "objective": "Implement agent dispatch contract and fake adapter. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-003",
        "TASK-004"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/agents/",
          "tests/unit/agents/",
          "docs/implementation/TASK-017.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:agents"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-017-AC1",
          "description": "Provide deterministic fake start/poll/cancel behavior with idempotent handles and structured outputs",
          "verification": "TASK-017 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-017-AC2",
          "description": "Reject invalid provenance, missing capabilities and lower-capability review profile bindings",
          "verification": "TASK-017 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-04"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-003",
        "handoff:TASK-004"
      ],
      "output_contracts": [
        "agents public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-017"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-021",
      "plan_id": "PLAN-001",
      "title": "Dispatch fenced task attempts",
      "status": "backlog",
      "archived": false,
      "objective": "Dispatch fenced task attempts. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-010",
        "TASK-011",
        "TASK-016",
        "TASK-017"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/orchestration/dispatch/",
          "tests/unit/orchestration_dispatch/",
          "docs/implementation/TASK-021.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:orchestration/dispatch"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-021-AC1",
          "description": "Persist request/lease/operation identity before dispatch and import only matching structured results",
          "verification": "TASK-021 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-021-AC2",
          "description": "Cancel or isolate workers before releasing scope and reject late callbacks after fencing",
          "verification": "TASK-021 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-04"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-010",
        "handoff:TASK-011",
        "handoff:TASK-016",
        "handoff:TASK-017"
      ],
      "output_contracts": [
        "orchestration/dispatch public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-021"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-020",
      "plan_id": "PLAN-001",
      "title": "Enforce independent two-stage review gates",
      "status": "backlog",
      "archived": false,
      "objective": "Enforce independent two-stage review gates. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-003",
        "TASK-017",
        "TASK-018",
        "TASK-019"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/reviews/gates/",
          "tests/unit/reviews_gates/",
          "docs/implementation/TASK-020.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:reviews/gates"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-020-AC1",
          "description": "Require separate higher-capability R1/R2 invocations and every applicable checklist item with evidence",
          "verification": "TASK-020 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-020-AC2",
          "description": "Restart validation and both reviews after material R2 fixes and reject stale mismatched reports",
          "verification": "TASK-020 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-05"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-003",
        "handoff:TASK-017",
        "handoff:TASK-018",
        "handoff:TASK-019"
      ],
      "output_contracts": [
        "reviews/gates public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-020"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-023",
      "plan_id": "PLAN-001",
      "title": "Integrate accepted task candidates",
      "status": "backlog",
      "archived": false,
      "objective": "Integrate accepted task candidates. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-007",
        "TASK-011",
        "TASK-018",
        "TASK-020"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/orchestration/integration/",
          "tests/unit/orchestration_integration/",
          "docs/implementation/TASK-023.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:orchestration/integration"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-023-AC1",
          "description": "Serially integrate commits into plan branch with actual provenance and fresh reviews on base changes",
          "verification": "TASK-023 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-023-AC2",
          "description": "Route merge conflicts to structural recovery without silently editing task-owned surfaces",
          "verification": "TASK-023 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-05"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-007",
        "handoff:TASK-011",
        "handoff:TASK-018",
        "handoff:TASK-020"
      ],
      "output_contracts": [
        "orchestration/integration public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-023"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-026",
      "plan_id": "PLAN-001",
      "title": "Compose resumable plan execution steps",
      "status": "backlog",
      "archived": false,
      "objective": "Compose resumable plan execution steps. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-012",
        "TASK-015",
        "TASK-018",
        "TASK-020",
        "TASK-022",
        "TASK-023",
        "TASK-025"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/workflows/execution/",
          "tests/unit/workflows_execution/",
          "docs/implementation/TASK-026.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:workflows/execution"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-026-AC1",
          "description": "Drive the documented plan state machine from approved graph through accepted tasks using injected services",
          "verification": "TASK-026 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-026-AC2",
          "description": "Resume from committed phases without duplicate effects and pause durably on unsupported capability or budget",
          "verification": "TASK-026 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-04",
        "AC-06"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-012",
        "handoff:TASK-015",
        "handoff:TASK-018",
        "handoff:TASK-020",
        "handoff:TASK-022",
        "handoff:TASK-023",
        "handoff:TASK-025"
      ],
      "output_contracts": [
        "workflows/execution public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-026"
      ],
      "estimated_production_files": 5,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-002",
      "plan_id": "PLAN-001",
      "title": "Freeze local persistence and process ports",
      "status": "backlog",
      "archived": false,
      "objective": "Freeze local persistence and process ports. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-001"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/domain/local_ports/",
          "tests/unit/domain_local_ports/",
          "docs/implementation/TASK-002.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:domain/local_ports"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-002-AC1",
          "description": "Define typed StateStore, Clock, IdFactory, CommandRunner and GitRepository requests/results",
          "verification": "TASK-002 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-002-AC2",
          "description": "Define WorktreeManager operations and typed side-effect errors without concrete adapters",
          "verification": "TASK-002 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-01",
        "AC-02"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-001"
      ],
      "output_contracts": [
        "domain/local_ports public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-002"
      ],
      "estimated_production_files": 5,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-036",
      "plan_id": "PLAN-001",
      "title": "Verify recovery and delivery lifecycle",
      "status": "backlog",
      "archived": false,
      "objective": "Verify recovery and delivery lifecycle. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-034"
      ],
      "scope": {
        "write_paths": [
          "tests/e2e/recovery_e2e/",
          "docs/implementation/TASK-036.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:recovery_e2e"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-036-AC1",
          "description": "Exercise R2 failure, graph replacement, integration gap and lineage budget exhaustion with fake adapters",
          "verification": "TASK-036 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-036-AC2",
          "description": "Verify current-head CI, observed merge and archive plus dirty worktree retention",
          "verification": "TASK-036 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-09"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-034"
      ],
      "output_contracts": [
        "recovery_e2e public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-036"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-035",
      "plan_id": "PLAN-001",
      "title": "Verify parallel execution and crash resume",
      "status": "backlog",
      "archived": false,
      "objective": "Verify parallel execution and crash resume. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-034"
      ],
      "scope": {
        "write_paths": [
          "tests/e2e/restart_e2e/",
          "docs/implementation/TASK-035.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:restart_e2e"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-035-AC1",
          "description": "Exercise a real temporary Git repo with prerequisite plus parallel fake agents and candidate reviews",
          "verification": "TASK-035 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-035-AC2",
          "description": "Crash at dispatch/checkpoint boundaries then resume from committed artifacts without chat or duplicate effects",
          "verification": "TASK-035 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-09"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-034"
      ],
      "output_contracts": [
        "restart_e2e public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-035"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-028",
      "plan_id": "PLAN-001",
      "title": "Implement delivery intent and fake hosting adapter",
      "status": "backlog",
      "archived": false,
      "objective": "Implement delivery intent and fake hosting adapter. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-003",
        "TASK-010"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/delivery/hosting/",
          "tests/unit/delivery_hosting/",
          "docs/implementation/TASK-028.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:delivery/hosting"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-028-AC1",
          "description": "Prepare local PR payload and idempotent fake publish/observe operations bound to repository/head",
          "verification": "TASK-028 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-028-AC2",
          "description": "Refuse external writes without scoped authorization and reconcile ambiguous creates",
          "verification": "TASK-028 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-07"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-003",
        "handoff:TASK-010"
      ],
      "output_contracts": [
        "delivery/hosting public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-028"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-031",
      "plan_id": "PLAN-001",
      "title": "Initialize or adopt a project safely",
      "status": "backlog",
      "archived": false,
      "objective": "Initialize or adopt a project safely. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-005",
        "TASK-009"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/workflows/project/",
          "tests/unit/workflows_project/",
          "docs/implementation/TASK-031.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:workflows/project"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-031-AC1",
          "description": "Seed new project records and a first Git checkpoint with clear framework/project ownership",
          "verification": "TASK-031 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-031-AC2",
          "description": "Adopt existing repo through non-destructive inventory/mapping and reject unapproved conflicting writes",
          "verification": "TASK-031 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-08"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-005",
        "handoff:TASK-009"
      ],
      "output_contracts": [
        "workflows/project public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-031"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-004",
      "plan_id": "PLAN-001",
      "title": "Implement offline contract validation",
      "status": "backlog",
      "archived": false,
      "objective": "Implement offline contract validation. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-001"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/schemas/",
          "tests/unit/schemas/",
          "docs/implementation/TASK-004.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:schemas"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-004-AC1",
          "description": "Validate every v1 artifact through an offline registry and reject unknown fields or unsupported versions",
          "verification": "TASK-004 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-004-AC2",
          "description": "Map validation failures to typed domain errors and check typed-value parsing parity",
          "verification": "TASK-004 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-01"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-001"
      ],
      "output_contracts": [
        "schemas public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-004"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-022",
      "plan_id": "PLAN-001",
      "title": "Schedule independent task attempts",
      "status": "backlog",
      "archived": false,
      "objective": "Schedule independent task attempts. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-013",
        "TASK-014",
        "TASK-021"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/orchestration/scheduler/",
          "tests/unit/orchestration_scheduler/",
          "docs/implementation/TASK-022.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:orchestration/scheduler"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-022-AC1",
          "description": "Run disjoint ready tasks up to configured parallel limit and wait for integrated prerequisites",
          "verification": "TASK-022 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-022-AC2",
          "description": "Preserve deterministic readiness and cancellation behavior while unrelated tasks fail or repair",
          "verification": "TASK-022 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-04"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-013",
        "handoff:TASK-014",
        "handoff:TASK-021"
      ],
      "output_contracts": [
        "orchestration/scheduler public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-022"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-018",
      "plan_id": "PLAN-001",
      "title": "Run task validation suites",
      "status": "backlog",
      "archived": false,
      "objective": "Run task validation suites. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-003",
        "TASK-006"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/validation/",
          "tests/unit/validation/",
          "docs/implementation/TASK-018.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:validation"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-018-AC1",
          "description": "Execute configured command IDs and bind results to current worktree revision",
          "verification": "TASK-018 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-018-AC2",
          "description": "Reject missing, stale, failed, timed-out or unobserved evidence as a passing suite",
          "verification": "TASK-018 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-05"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-003",
        "handoff:TASK-006"
      ],
      "output_contracts": [
        "validation public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-018"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-027",
      "plan_id": "PLAN-001",
      "title": "Gate combined plan acceptance",
      "status": "backlog",
      "archived": false,
      "objective": "Gate combined plan acceptance. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-018",
        "TASK-019",
        "TASK-020",
        "TASK-025",
        "TASK-026"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/workflows/integration_review/",
          "tests/unit/workflows_integration_review/",
          "docs/implementation/TASK-027.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:workflows/integration_review"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-027-AC1",
          "description": "Run integrated validation and all INT checklist items on exact combined candidate",
          "verification": "TASK-027 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-027-AC2",
          "description": "Create recovery follow-up tasks for cross-task gaps while preserving completed task history",
          "verification": "TASK-027 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-05",
        "AC-06"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-018",
        "handoff:TASK-019",
        "handoff:TASK-020",
        "handoff:TASK-025",
        "handoff:TASK-026"
      ],
      "output_contracts": [
        "workflows/integration_review public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-027"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-033",
      "plan_id": "PLAN-001",
      "title": "Persist research, decisions and plan drafts",
      "status": "backlog",
      "archived": false,
      "objective": "Persist research, decisions and plan drafts. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-004",
        "TASK-009",
        "TASK-013"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/workflows/knowledge/",
          "tests/unit/workflows_knowledge/",
          "docs/implementation/TASK-033.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:workflows/knowledge"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-033-AC1",
          "description": "Record sourced research and ADR/spec references with provenance and explicit status",
          "verification": "TASK-033 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-033-AC2",
          "description": "Create schema-valid plan/task drafts with coverage mapping for subsequent isolation review",
          "verification": "TASK-033 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-01",
        "AC-03"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-004",
        "handoff:TASK-009",
        "handoff:TASK-013"
      ],
      "output_contracts": [
        "workflows/knowledge public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-033"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-029",
      "plan_id": "PLAN-001",
      "title": "Handle CI and remote review repairs",
      "status": "backlog",
      "archived": false,
      "objective": "Handle CI and remote review repairs. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-025",
        "TASK-027",
        "TASK-028"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/delivery/ci/",
          "tests/unit/delivery_ci/",
          "docs/implementation/TASK-029.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:delivery/ci"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-029-AC1",
          "description": "Reject old-head or incomplete required checks and translate findings into reviewed follow-up tasks",
          "verification": "TASK-029 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-029-AC2",
          "description": "Verify authorized observed merge including squash mapping before marking delivery successful",
          "verification": "TASK-029 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-07"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-025",
        "handoff:TASK-027",
        "handoff:TASK-028"
      ],
      "output_contracts": [
        "delivery/ci public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-029"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-015",
      "plan_id": "PLAN-001",
      "title": "Gate graphs through isolation review",
      "status": "backlog",
      "archived": false,
      "objective": "Gate graphs through isolation review. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-003",
        "TASK-013",
        "TASK-014",
        "TASK-017"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/planning/isolation/",
          "tests/unit/planning_isolation/",
          "docs/implementation/TASK-015.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:planning/isolation"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-015-AC1",
          "description": "Build isolation inputs and validate all ISO checklist results against task-set digest",
          "verification": "TASK-015 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-015-AC2",
          "description": "Accept approved graph revisions only after deterministic checks and reject stale review results",
          "verification": "TASK-015 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-03"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-003",
        "handoff:TASK-013",
        "handoff:TASK-014",
        "handoff:TASK-017"
      ],
      "output_contracts": [
        "planning/isolation public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-015"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-024",
      "plan_id": "PLAN-001",
      "title": "Validate recovery graph proposals",
      "status": "backlog",
      "archived": false,
      "objective": "Validate recovery graph proposals. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-013",
        "TASK-014"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/planning/recovery_proposals/",
          "tests/unit/planning_recovery_proposals/",
          "docs/implementation/TASK-024.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:planning/recovery_proposals"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-024-AC1",
          "description": "Preserve acceptance and map successors/dependencies across split, replace, sequence and augment proposals",
          "verification": "TASK-024 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-024-AC2",
          "description": "Reject cycles, ID reuse, altered completed tasks, permission expansion and budget reset",
          "verification": "TASK-024 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-06"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-013",
        "handoff:TASK-014"
      ],
      "output_contracts": [
        "planning/recovery_proposals public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-024"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    },
    {
      "schema_version": "1.0",
      "kind": "task",
      "id": "TASK-016",
      "plan_id": "PLAN-001",
      "title": "Build minimal role context bundles",
      "status": "backlog",
      "archived": false,
      "objective": "Build minimal role context bundles. Implement only this observable slice using the frozen schema and port contracts.",
      "depends_on": [
        "TASK-003",
        "TASK-004"
      ],
      "scope": {
        "write_paths": [
          "src/ai_engineering/context/",
          "tests/unit/context/",
          "docs/implementation/TASK-016.md"
        ],
        "read_paths": [
          "schemas/v1/",
          "docs/architecture/",
          "docs/workflows/",
          "docs/state/",
          "docs/agents/",
          "src/ai_engineering/domain/values/"
        ],
        "prohibited_paths": [
          ".ai/",
          "AGENTS.md",
          "ARCHITECTURE.md",
          "README.md",
          "docs/decisions/"
        ],
        "resources": [
          "component:context"
        ]
      },
      "acceptance_criteria": [
        {
          "id": "TASK-016-AC1",
          "description": "Resolve explicit references and dependency/sibling handoffs to a stable hashed manifest",
          "verification": "TASK-016 owned behavior tests and structured handoff evidence"
        },
        {
          "id": "TASK-016-AC2",
          "description": "Enforce token budget without dropping required acceptance and reject secret/path leakage",
          "verification": "TASK-016 failure-case tests and structured handoff evidence"
        }
      ],
      "plan_acceptance_ids": [
        "AC-04"
      ],
      "spec_refs": [
        ".ai/specs/SPEC-001.json"
      ],
      "adr_refs": [
        "docs/decisions/ADR-001.md",
        "docs/decisions/ADR-002.md",
        "docs/decisions/ADR-003.md",
        "docs/decisions/ADR-004.md",
        "docs/decisions/ADR-005.md"
      ],
      "research_refs": [],
      "input_contracts": [
        "schemas/v1/",
        "docs/architecture/python.md",
        "handoff:TASK-003",
        "handoff:TASK-004"
      ],
      "output_contracts": [
        "context public behavior described by this task acceptance; use predeclared ports"
      ],
      "validation_commands": [
        "test.TASK-016"
      ],
      "estimated_production_files": 3,
      "size_rationale": "One component outcome with two bounded acceptance checks; no central registry edits. Split further through isolation review if implementation exceeds this estimate.",
      "out_of_scope": [
        "Other task-owned modules and tests",
        "Changing shared contracts without a new prerequisite task",
        "Production provider integration, paid services, remote publication and product-scope changes"
      ],
      "handoff_requirements": [
        "Exact base/commit and verified changed paths",
        "Actual test command evidence and acceptance mapping",
        "Public interface/dependency notes, deviations and risks"
      ],
      "attempt_ids": [],
      "superseded_by": [],
      "resume_state": null
    }
  ]
}
```
