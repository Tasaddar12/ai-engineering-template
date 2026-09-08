"""One-off decomposition of the fresh PLAN-002 artifacts, never product runtime."""
from pathlib import Path, PurePosixPath
from itertools import combinations
import yaml

ROOT = Path(__file__).resolve().parents[2]
AI = ROOT / '.ai'

def read(path):
    _, front, body = path.read_text(encoding='utf-8').split('---', 2)
    return yaml.safe_load(front), body.strip()

def write(path, meta, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('---\n' + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True) + '---\n' + body.strip() + '\n', encoding='utf-8')

# Each task is one coherent public boundary or integration behavior. Shared files
# inside one batch are intentional; cross-batch ownership must be ordered.
SPECS = {
40: (2, ['errors.py', 'io.py', 'artifacts.py', 'config.py'], 'test_core.py', [
    'Read/write strict YAML mappings and Markdown front matter with stable IDs, kind/status locations and atomic replacement; reject duplicate IDs and malformed metadata.',
    'Create/find/list/save/transition/next_id obey the PLAN-002 ArtifactStore contract and preserve bodies and historical records.',
    'Reject absolute, traversal, symlink and junction escapes. Plans and plan-specific contracts are PLAN-NNN Markdown under .ai with explicit tasks/features lists; empty lists are allowed only before decomposition.'
], 'Storage owns parsing and lifecycle location, not Git execution or provider calls.'),
41: (3, ['state.py'], 'test_core.py', [
    'StateStore serializes coordinator writes with a process lock and atomically stores a compact index; agent updates cannot overwrite it.',
    'refresh_index reflects current artifact status while retaining Git observations; reconcile reports missing/unknown worktrees, branch/head mismatch and stale review evidence.',
    'Reconciliation detects merge facts through the agreed Git interface; read-only mode changes nothing and apply mode never deletes work or invents approval.'
], 'Use a controlled Git-interface double before FEATURE-002 exists; real Git integration is verified in TASK-045 and TASK-061. Do not import the future git module.'),
42: (2, ['templates.py', 'templates', 'definitions'], 'test_core.py', [
    'Strict rendering rejects missing variables, prefers project .ai/templates and falls back to wheel-packaged assets without escaping either root.',
    'Package seeds include seven roles with separate model-profile references, role/assignment/output templates, command and file/workflow/external-action constraints.',
    'Include reusable templates for plans, tasks, features, bugs, research, ADRs, reviews, handoffs, PRs and project documents. Plan templates explicitly reference .ai tasks and features.'
], 'This task packages and validates definitions; runtime model/provider resolution belongs to TASK-049. Project adoption belongs to TASK-059.'),
43: (2, ['constraints.py'], 'test_execution.py', [
    'Command authorization evaluates tokenized argv, role, explicit action and deny-by-default rules; forbidden rules override matching allow rules and grants.',
    'Scope checks reject path escapes, protected/read-only locations, prohibited secrets and forbidden operations, including alternative Git option order that would bypass a naive prefix check.',
    'External actions require their configured authority; grants never authorize forbidden operations and reviewer permissions cannot modify source.'
], 'Implement policy decisions only; all actual process creation belongs to TASK-044.'),
44: (3, ['runner.py'], 'test_execution.py', [
    'The single process runner accepts argv only, applies policy before execution and rejects shell/batch indirection and unsafe worktree/cwd paths.',
    'Results and YAML evidence capture bounded/redacted output, cwd, timestamps and exit status; distinguish expected nonzero exits, ordinary failure, execution error, timeout and dry-run.',
    'Timeouts terminate child execution without hanging; dry-run launches no process and persists no execution side effects. Product subprocess imports occur only here.'
], 'Portable process-tree termination must report unsupported platform behavior honestly; avoid claiming untested Linux behavior.'),
45: (3, ['git.py'], 'test_execution.py', [
    'Git operations use the runner, validate refs/names and create one registered branch/worktree under .worktrees; observed head/branch/worktree data comes from Git.',
    'Cleanup refuses unknown, escaped, linked, locked, dirty (including ignored data), active and unmerged worktrees; explicit supersession/abandonment may preserve an unmerged branch with its audit reason.',
    'Temporary Git repositories demonstrate merge detection, checked cleanup, clean source preservation and the state reconciliation interface defined in TASK-041.'
], 'This module owns Git primitives, not workflow state transitions; coordinator writes intent before mutation.'),
46: (2, ['planning.py'], 'test_planning.py', [
    'Validate unique task IDs, known prerequisites, acyclic dependencies, explicit nonempty acceptance, supported effort range and safe declared scope.',
    'Validate schema/API resource declarations and task metadata without claiming deterministic checks can prove semantic clarity or detect every hidden dependency.',
    'The Work Decomposition assignment requires source/context inspection and concrete split/merge/prerequisite proposals when semantic boundaries are wrong.'
], 'Semantic review is an agent duty; deterministic validation rejects structural defects with actionable errors.'),
47: (3, ['planning.py'], 'test_planning.py', [
    'Group coherent tasks into features bounded by max_tasks and max_effort, covering each active task exactly once with explicit acceptance and context.',
    'Reflect task prerequisites in feature edges; serialize overlapping path roots and exclusive schema/API resources, rejecting unresolvable cycles.',
    'Produce topological conflict-safe parallel waves and persist new feature IDs plus an immutable decomposition handoff; unchanged graphs are idempotent and started features cannot be overwritten.'
], 'Feature batching reduces worktree/agent count; do not default to one task per agent.'),
48: (3, ['planning.py'], 'test_planning.py', [
    'Accept complete reasoned revision proposals with replacement task lineage, scoped supersession and newly required prerequisites; validate the full resulting graph before writes.',
    'Preserve unaffected completed tasks/features and retained dependencies while redirecting incoming/outgoing edges to explicit replacements.',
    'Rejected revisions leave original artifacts intact. Accepted revisions preserve superseded history, create .ai tasks/features, and produce an approved replacement decomposition.'
], 'Recovery supplies the reasoned proposal; this boundary validates and applies it and must not manufacture scope expansion authority.'),
49: (3, ['agents.py'], 'test_agents.py', [
    'Resolve role definition -> profile -> provider/model/reasoning and permissions independently for all seven roles; reject missing profiles and inadequate reviewer configuration.',
    'CommandAgentProvider uses only the runner and a configured bridge with permission-boundary attestation; persist YAML request/result metadata and validate returned status/output.',
    'Preserve implementation session IDs on repair and require independent reviewer identity; never fabricate provider success or a PASS when the bridge is absent.'
], 'Bridge credentials, paid use and real invocation remain gated by configured authority; tests use controlled providers.'),
50: (2, ['handoffs.py'], 'test_agents.py', [
    'Render immutable Markdown handoffs under .ai/handoffs from dedicated templates, rejecting missing fields, collisions and path escapes.',
    'Assignments include role, subject/tasks, dependency handoffs, worktree/branch, allowed/prohibited scope, relevant references, acceptance, commands and applicable constraints.',
    'Context remains reference-based and bounded; handoffs do not include unrelated repository history or secret values.'
], 'Do not construct scattered ad-hoc agent prompts; rendering and automatic policy/context references have one boundary.'),
51: (3, ['review.py'], 'test_agents.py', [
    'Accept exactly PASS or CHANGES_REQUIRED tied to subject ID and reviewed head; reject stale revisions and implementation/reviewer identity collisions.',
    'CHANGES_REQUIRED provides blocking issues with category, affected files, explanation, required change and required validation; relevant security/documentation findings are explicit.',
    'Review assignment covers the complete base-to-head feature diff, acceptance, completion and actual validation; one stage is reused after repair with a fresh reviewer session.'
], 'Review is evidence validation and assignment generation; scheduler performs repairs and delivery gating.'),
52: (2, ['orchestrator.py'], 'test_orchestration.py', [
    'Load ready plans and relevant references, run semantic Work Decomposition plus deterministic checks, and refuse dispatch until the graph is approved.',
    'Schedule bounded concurrent ready features with one implementation session/worktree per feature; overlapping ownership never runs concurrently.',
    'A dependency becomes eligible only when its code is observed on the selected base. Coordinator alone persists state and launch intents.'
], 'Initial tests use controlled providers and temporary repositories; provider absence is an explicit blocker rather than a completed feature.'),
53: (2, ['orchestrator.py'], 'test_orchestration.py', [
    'Run feature validation commands before critical review and block review on failed or missing required evidence.',
    'Route structured CHANGES_REQUIRED to the same implementation session, rerun validation, and request independent review of the entire updated diff.',
    'Bound review iterations and retain every implementation, validation and review artifact; exhausted repair remains blocked with an actionable reason.'
], 'Ordinary code defects remain in this loop and never silently invoke task supersession.'),
54: (2, ['orchestrator.py'], 'test_orchestration.py', [
    'Persist run/effect intent before worktree, provider or delivery effects and reconcile observed state on resume instead of replaying uncertain effects blindly.',
    'Classify structural failures separately from code defects and call the recovery hook with original subject/tasks/review evidence.',
    'Persist bounded recovery counters and visible blockers while retaining branches, sessions and evidence across interruptions.'
], 'Define the recover hook boundary now and test it with a controlled adapter; TASK-058 supplies the runtime workflow via a late import, avoiding an implementation dependency cycle.'),
55: (2, ['delivery.py', 'orchestrator.py'], 'test_orchestration.py', [
    'Prepare a complete templated PR body before requesting any external authority; push and PR creation use the central runner and configured grants.',
    'Deliver only the current validated reviewed head and retain branch/head/PR URL plus uncertain delivery state for reconciliation.',
    'Review PASS or PR creation leaves work awaiting merge; only observed merge evidence completes included tasks/features and permits checked worktree cleanup.'
], 'No remote writes are authorized by this implementation plan; controlled delivery adapters verify policy and idempotency.'),
56: (2, ['workflows.py'], 'test_workflows.py', [
    'Create/load a .ai BUG artifact and record reproduction evidence or a reason reproduction is impractical, root cause, expected behavior and regression strategy before fix dispatch.',
    'Reuse one managed bug worktree and the shared implementation/validation/critical-review/repair/delivery lifecycle with the smallest declared scope.',
    'Bug results reference actual regression validation and document behavior changes where needed.'
], 'The lightweight bug path does not require artificial task/feature artifacts unless investigation triggers structural escalation.'),
57: (2, ['workflows.py'], 'test_workflows.py', [
    'Substantial architectural investigation creates a new .ai PLAN-NNN document with explicit task/feature references and links back to the bug and root-cause evidence.',
    'Create scoped prerequisite/tasks, invoke Work Decomposition and validate the resulting graph before normal feature scheduling.',
    'Do not continue the small-fix path or silently authorize external actions/material product scope expansion after escalation.'
], 'Escalation is a durable lineage transition; it must remain resumable rather than duplicate plans on retry.'),
58: (3, ['workflows.py'], 'test_workflows.py', [
    'Recovery receives failed feature, original plan/tasks, all relevant reviews and conflict evidence, and returns a reasoned split/reorder/replacement/prerequisite proposal.',
    'Apply revisions through planning, preserve superseded evidence and unaffected completed work, redecompose and resume eligible features automatically within existing scope.',
    'Reject unauthorized material scope expansion and invalid graphs; exhausted attempts preserve an explicit blocker and do not corrupt active workflow state.'
], 'Integrate the TASK-054 hook without importing orchestration at module load time; ordinary defects do not enter recovery.'),
59: (2, ['project.py'], 'test_cli.py', [
    'Initialize/adopt seeds missing .ai configuration, templates, definitions and small operating docs from package assets, without copying repository development plans/history.',
    'Preflight destination links/escapes/collisions, preserve user content on repeat installation and add .worktrees ignore safely.',
    'Dry-run reports intended changes without writes, Git mutation or process launch.'
], 'Do not package the active PLAN-002 or tests as installed project history.'),
60: (2, ['cli.py', '__init__.py', '__main__.py'], 'test_cli.py', [
    'Expose project init/adopt, status, state reconcile, research create, plan create/decompose/implement and bug fix through one main entry point used by ai and python -m ai_engineering.',
    'Support project selection, dry-run and explicit action grants with actionable FrameworkError reporting and truthful exit codes.',
    'All creation commands enforce .ai-only planning artifacts; plan creation records task/feature collections and implementation refuses an incomplete or unapproved graph.'
], 'The CLI delegates orchestration; it must not implement a second runner, policy layer or review workflow.'),
61: (2, [], 'test_acceptance.py', [
    'Controlled end-to-end tests in temporary Git repositories prove concurrency, dependency availability, repair session reuse, structural recovery and review-to-delivery gates.',
    'Exercise interruption/resume and cleanup refusal/success against actual Git worktrees, preserving the user checkout.',
    'Build and install a wheel in isolation; verify package CLI and templates/definitions work without development history or source checkout assumptions.'
], 'Report controlled provider limits explicitly. Real external services are outside these acceptance tests.'),
62: (2, [], None, [
    'Update small core docs and reusable workflow/config/security docs to match actual behavior, provider boundaries, authority, .ai-only planning and safe worktree lifecycle.',
    'CI defines Python 3.11+ validation on Windows and Linux; record actual local results and distinguish configured CI from executed platform evidence.',
    'Product docs link to .ai PLAN artifacts for implementation planning and contain no task list, plan-specific contract or feature graph.'
], 'This task owns public documentation and CI only; implementation planning and execution evidence remain under .ai.')
}
BATCHES = [
    ('core', 'Artifact, configuration and state foundation', range(40,43), []),
    ('execution', 'Constrained commands and managed Git worktrees', range(43,46), [1]),
    ('planning', 'Validated task decomposition and feature graphs', range(46,49), [1]),
    ('agents', 'Configured agents, durable handoffs and critical review', range(49,52), [2]),
    ('orchestration', 'Concurrent implementation, repair and delivery', range(52,56), [3,4]),
    ('workflows', 'Lightweight bugfix and structural recovery', range(56,59), [5]),
    ('cli', 'Project installation, CLI and acceptance', range(59,63), [6]),
]

tasks = {}
for number, (effort, modules, test, acceptance, boundary) in SPECS.items():
    path = AI / 'tasks' / 'ready' / f'TASK-{number:03}.md'
    meta, _ = read(path)
    meta['scope'] = [f'src/ai_engineering/{name}' for name in modules]
    if test:
        meta['scope'].append(f'tests/{test}')
    if number == 42:
        meta['scope'].append('pyproject.toml')
    if number == 60:
        meta['scope'].append('pyproject.toml')
    if number == 62:
        meta['scope'].extend(['README.md','ARCHITECTURE.md','SECURITY.md','CONTRIBUTING.md','docs','.github'])
    meta['effort'] = effort
    meta['acceptance'] = acceptance
    meta['context'] = [p for p in meta['context'] if p != '.ai/plans/active/PLAN-002.md'] + ['.ai/plans/active/PLAN-002.md']
    tasks[meta['id']] = meta
    body = f"# {meta['id']} — {meta['title']}\n\n## Acceptance criteria\n\n" + '\n'.join('- ' + a for a in acceptance)
    body += '\n\n## Ownership boundary\n\n' + boundary + '\n\nFollow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.\n'
    write(path, meta, body)

features = []
for i, (batch, title, numbers, dependencies) in enumerate(BATCHES,1):
    members = [tasks[f'TASK-{n:03}'] for n in numbers]
    feature = {
        'id': f'FEATURE-{i:03}', 'title': title, 'status': 'ready', 'plan': 'PLAN-002',
        'tasks': [t['id'] for t in members],
        'dependencies': [f'FEATURE-{n:03}' for n in dependencies],
        'scope': sorted({p for t in members for p in t['scope']}),
        'resources': sorted({r for t in members for r in t['resources']}),
        'acceptance': [a for t in members for a in t['acceptance']],
        'validation': ['tests','lint','format','types'],
        'context': ['AGENTS.md','.ai/plans/active/PLAN-002.md','ARCHITECTURE.md','docs/workflows.md','.ai/constraints.yaml','.ai/project/commands.yaml'],
        'batch': batch, 'effort': sum(t['effort'] for t in members),
        'decomposition': '.ai/handoffs/PLAN-002-decomposition.md'
    }
    features.append(feature)
    body = f"# {feature['id']} — {title}\n\n## Batch objective\n\nImplement the {batch} public boundaries in [PLAN-002](../../plans/active/PLAN-002.md) as one cohesive agent/worktree batch.\n\n## Included tasks\n\n"
    body += '\n'.join(f"- [{t['id']}](../../tasks/ready/{t['id']}.md) — {t['title']}" for t in members)
    body += '\n\n## Dependencies and ownership\n\n' + ('Requires ' + ', '.join(feature['dependencies']) + ' with code available on the selected base.' if dependencies else 'No feature prerequisite; this is the first ready batch.')
    body += '\n\nDeclared scope and exclusive resources are authoritative in front matter. Modify only that scope; API adjustments crossing it return to the coordinator. Tasks share one implementation session and worktree. Do not edit STATE or approve your own review.\n\n## Acceptance criteria\n\n'
    body += '\n'.join('- ' + a for a in feature['acceptance'])
    body += '\n\n## Validation\n\nRun relevant behavioral tests, then tests/lint/format/types from .ai/project/commands.yaml where available. Record actual results, failures and unverified platforms in the completion handoff. Use temporary Git repositories for behavioral tests. One independent critical reviewer must review the complete feature diff before delivery.\n\n## Context\n\nRead the plan contract, included tasks, dependency completion handoffs and listed context only. The coordinator supplies applicable role/model/policy configuration in the assignment.\n'
    write(AI / 'features' / 'ready' / f"{feature['id']}.md", feature, body)

def closure(node, graph):
    done = set()
    visiting = set()
    def visit(key):
        assert key not in visiting, f'Cycle at {key}'
        if key in done:
            return
        visiting.add(key)
        for dependency in graph[key]:
            assert dependency in graph, f'Missing dependency {dependency}'
            visit(dependency)
        visiting.remove(key)
        done.add(key)
    visit(node)
    return done - {node}

def overlap(left, right):
    for a in left:
        for b in right:
            a, b = PurePosixPath(a), PurePosixPath(b)
            if a == b or a in b.parents or b in a.parents:
                return True
    return False

task_graph = {k: v['depends_on'] for k,v in tasks.items()}
feature_graph = {f['id']: f['dependencies'] for f in features}
owner = {}
for f in features:
    assert len(f['tasks']) <= 5 and f['effort'] <= 8
    for task in f['tasks']:
        assert task not in owner, f'Duplicate coverage: {task}'
        owner[task] = f['id']
assert set(owner) == set(tasks)
for task, prerequisites in task_graph.items():
    closure(task, task_graph)
    for p in prerequisites:
        assert owner[p] == owner[task] or owner[p] in closure(owner[task], feature_graph)
for left,right in combinations(features,2):
    conflicts = overlap(left['scope'],right['scope']) or bool(set(left['resources']) & set(right['resources']))
    if conflicts:
        assert left['id'] in closure(right['id'],feature_graph) or right['id'] in closure(left['id'],feature_graph), f'Unordered ownership: {left["id"]}, {right["id"]}'
waves = []
done = set()
while len(done) < len(features):
    wave = [f['id'] for f in features if f['id'] not in done and set(f['dependencies']) <= done]
    assert wave, 'Feature dependency cycle'
    for a,b in combinations(wave,2):
        left,right = next(f for f in features if f['id']==a),next(f for f in features if f['id']==b)
        assert not overlap(left['scope'],right['scope'])
        assert not set(left['resources']) & set(right['resources'])
    waves.append(wave)
    done.update(wave)

plan_path = AI / 'plans' / 'active' / 'PLAN-002.md'
plan, body = read(plan_path)
plan['features'] = [f['id'] for f in features]
plan['decomposition'] = '.ai/handoffs/PLAN-002-decomposition.md'
plan['decomposition_status'] = 'approved'
plan['context'] = [p for p in plan['context'] if p != '.ai/plans/active/PLAN-002.md']
assert set(plan['tasks']) == set(tasks)
section = '''## Approved implementation graph

Planning location is a hard requirement: this PLAN document and all task, feature and plan-specific contract artifacts live under `.ai/`. Product documentation links here and must not contain the plan's implementation task lists, contracts or feature graph.

The Work Decomposition Agent approved exact coverage of 23 tasks in seven batches. See [decomposition evidence](../../handoffs/PLAN-002-decomposition.md). `ready` means a validated batch; launch still waits for dependencies and available code.

| Feature | Tasks | Prerequisites | Effort |
| --- | --- | --- | --- |
'''
for f in features:
    section += f"| [{f['id']}](../../features/ready/{f['id']}.md) — {f['title']} | " + ', '.join(f"[{t}](../../tasks/ready/{t}.md)" for t in f['tasks']) + f" | {', '.join(f['dependencies']) or 'None'} | {f['effort']} |\n"
section += '\nSafe waves: ' + ' → '.join(' + '.join(w) for w in waves) + '.\n\nFEATURE-004 may start once FEATURE-002 is integrated even if FEATURE-003 is still running; no ownership overlap exists. FEATURE-005 waits for both. Shared packaging metadata is changed by FEATURE-001 and then FEATURE-007, never concurrently. No database schema is introduced; named API resources model exclusive interface ownership.\n\nState reconciliation is built against the agreed Git interface before its real adapter exists. FEATURE-005 defines and tests the recovery hook; FEATURE-006 supplies it by late import. Runtime model resolution belongs to FEATURE-004, while FEATURE-001 packages validated role/profile references. These explicit boundaries avoid hidden implementation cycles.\n\n'
if '## Approved implementation graph' not in body:
    body = body.replace('# Runtime boundaries for PLAN-002', section + '# Runtime boundaries for PLAN-002')
write(plan_path, plan, body)

report_meta = {'id':'HANDOFF-PLAN-002-DECOMPOSITION','plan':'PLAN-002','status':'approved','agent':'work_decomposition','task_count':len(tasks),'feature_count':len(features),'features':plan['features'],'parallel_waves':waves,'coverage':'exactly_once','blockers':[]}
report = '''# Decomposition — PLAN-002

## Plan

[PLAN-002](../plans/active/PLAN-002.md), authoritative reset of 2026-09-08. All plans and plan-specific contracts are PLAN-NNN Markdown under .ai with explicit task/feature references; task and feature artifacts are also under .ai.

## Status

APPROVED for implementation scheduling. This approves task/feature structure, not code, security, delivery or external authority. No runtime implementation was performed by this decomposition pass.

## Task Changes

Retained all 23 fresh TASK-040 through TASK-062. Each now has narrow file ownership, concrete observable acceptance and a boundary note. No task was discarded, merged or superseded because each represents a coherent public boundary or integration behavior after refinement. Raised complex state/runner/Git/batching/revision/provider/review/recovery tasks to effort 3; every task remains within effort 1..3 and every feature within five tasks/eight effort. Semantic criteria now distinguish agent judgment from deterministic graph checks. The all-.ai planning rule is explicit in persistence, templates, CLI, escalation and documentation acceptance.

## Features

'''
for f in features:
    report += f"- [{f['id']}](../features/ready/{f['id']}.md): {', '.join(f['tasks'])}; effort {f['effort']}; prerequisites {', '.join(f['dependencies']) or 'none'}.\n"
report += '''
## Dependencies

Task order is preserved within each coherent feature. Cross-feature prerequisites match the plan graph. Core state uses the agreed Git API with controlled test doubles; real integration waits for execution. Core packages model/role assets; agent resolution belongs to agents. Orchestration owns the recovery hook; workflows supplies it through a late import. These are contractual prerequisites, not missing implementations to conceal. No additional prerequisite task is needed within the approved scope.

## Parallel Waves

'''
report += '\n'.join(f"{i}. {', '.join(w)}" for i,w in enumerate(waves,1))
report += '''

FEATURE-004 can begin after FEATURE-002 code is available even while FEATURE-003 continues; FEATURE-005 waits for both. Runtime concurrency is capped by framework configuration. A task never receives its own worktree merely because it is a task.

## Ownership Checks

All 23 plan task IDs occur exactly once across seven features. Both DAGs are acyclic and every task prerequisite is either in the same feature or reachable through feature dependencies. FEATURE-002 and FEATURE-003 have disjoint source/test paths and exclusive resources. All other overlapping ownership, including core/CLI packaging metadata, is transitively serialized. No database schema exists in this change; core, execution, planning, agents, orchestration, workflows and CLI API resources are distinct. Same-batch source/test overlap is deliberate and handled by one implementer.

## Rationale

Seven feature agents balance bounded context and conflict avoidance. A larger fanout would create shared-module ownership conflicts and unnecessary worktrees; a single batch would obscure validation and review scope. Review stays one independent complete-diff stage. Ordinary defects return to the implementer; structural mistakes return through recovery and this decomposition contract.

## Context Refs

- AGENTS.md
- .ai/STATE.yaml
- .ai/plans/active/PLAN-002.md
- .ai/agents/work_decomposition.yaml
- .ai/templates/agents/work-decomposition.md
- ARCHITECTURE.md
- docs/workflows.md
- .ai/constraints.yaml
- .ai/project/commands.yaml

## Constraints

Writes were limited to fresh .ai plan/task/feature/handoff files and a temporary .ai/local decomposition validator. Coordinator retains exclusive STATE ownership. No Git mutation, provider call, external write or runtime implementation occurred. Repository role permissions describe future runtime behavior; the direct decomposition assignment expressly authorized these local artifact edits.

## Validation evidence

The one-off Python validator `.ai/local/approve_plan_002.py` checked all task/feature metadata, task and feature DAGs, exact coverage, task-to-feature edge preservation, batch limits, resource/path serialization and every parallel wave. It completed successfully using the existing local virtual environment. No product planning implementation exists yet, so this is an independent bootstrap graph check.

The required initial `python -m ai_engineering status` returned `No module named ai_engineering` before runtime installation; this is preserved as baseline evidence and is not an approval of runtime functionality. System Python also lacked PyYAML; the repository virtual environment supplied PyYAML 6.0.3. No dependency was installed.
'''
write(AI / 'handoffs' / 'PLAN-002-decomposition.md', report_meta, report)
print(yaml.safe_dump({'status':'approved','tasks':len(tasks),'features':len(features),'waves':waves,'checks':'DAGs, exact coverage, bounds, ownership, .ai plan references passed'},sort_keys=False))
