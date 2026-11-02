<!-- generated-by: doc-writer -->
# Agent entry point

This repository authors the reusable Engineer workflow. Its canonical sources
are `agents/`, `commands/`, `engineer/`, `hooks/`, `bin/`, `scripts/` and `skills/`.
Read the assigned role in `agents/`, the relevant command in `commands/`, and
the workflow and references that command names. The
[runtime guide](engineer/bin/README.md) documents executable operations.

A checkout supplies source material. Install it through
[the Python installer](docs/INSTALL.md) to register a host configuration and
record the pinned revision in an ownership manifest. A role or command file by
itself does not register an agent or slash command with a host.

## Project records and authority

Do not seed this template repository with an adopting project's placeholder
identity or roadmap. An adopting project establishes its actual intent through
`/onboard` or `/new-project`; the runtime's `project.init` operation creates its
`.planning/` records. Template maintenance history and historical requirements
remain separate from adoption and are preserved in Git history and PLANNED-UPDATES.md.

In an initialized project, read PROJECT, STATE and the selected phase before
changing project work. Preserve the project's identity, requirements, decisions,
history and custom instructions. Discuss each phase with the user before planning
or implementation. A discussion request grants discussion scope;
it does not authorize implementation. Phase creation, planning, design approval
and readiness do not grant implementation permission. Implement only the scope
the user has authorized, and do not ask again for authorization already supplied.

Commands select workflows; workflows orchestrate; runtime verbs own structural
planning mutations. Use `python -I engineer/bin/engineer.py query <verb>` in this
source checkout, or the installed host runtime in an adopting project. Do not
hand-edit runtime-owned phase numbering, roadmap tables, state counters,
requirement traceability, task state or lifecycle records. Narrative prose and
requirement wording remain authored content. Record consequential decisions with
their evidence as they are made. Run the smallest applicable executable check
before recommending an execution dependency or integration.

When evidence and documents disagree, establish which claim is wrong before
repairing it. Preserve approved outcomes and distinguish delegated implementation
choices from new human decisions. Use full templates, including their examples,
counterexamples and consumer instructions; do not replace complete methods with
compact versions without an assignment calling for that change.

## Dispatch and isolation

Use the exact role names in `agents/`. Resolve model and effort through
`engineer_run query resolve-model <role>` and
`engineer_run query resolve-effort <role>`; omit an override resolved as
`inherit`. A source role definition is not proof that the active host registered
that role. Load only the skills and references needed for the assignment.

The coordinator owns routing, shared records, worker lifecycle, integration and
publication. Give each source-changing worker an isolated checkout, explicit
paths, a captured base revision and a result destination. Workers edit only their
assigned files and their own summary; they do not publish or merge. Never edit
or integrate paths still owned by an active write-capable worker. A wait timeout
does not prove exit: confirm that the worker stopped before reassigning ownership.
Preserve dirty, unmerged and blocked checkouts.

During a frozen verification batch, independent read-only checks may inspect the
same captured revision. Wait for every result before accepting evidence, making
repairs or beginning another batch. A source worker completes with owned commits,
its required summary and actual check results. A read-only reviewer or verifier
completes with its cited report; it does not need a source commit or summary.

Fix in-scope defects and verification gaps under the existing authorization.
Keep unrelated findings separate and preserve exact blockers for work that needs
unavailable access or a new scope decision. Do not stop already authorized work
at routine internal stage boundaries. Shared services, databases and resource
benchmarks remain shared even when Git worktrees are isolated.

## Verification and delivery

Source changes require fresh independent code review and applicable independent
verification before completion. Use a separate doc-writer when a change creates a
guide or specification, changes an operational sequence, or explains behavior
across components. Run relevant behavior checks and configured project checks;
report their exact revision, commands, results, failures and skips. A process exit
or a file's presence alone does not establish the intended outcome. Material
changes invalidate earlier evidence for the affected behavior.

Commit each completed meaningful slice with a descriptive message. Stage only
owned paths and inspect staged content; preserve unrelated user work. When
delivery is authorized, push and keep the existing draft PR current, or create
one on the first push. Use the
[canonical Git workflow](engineer/references/git-workflow.md) and the current
[PR](engineer/templates/pull-request.md) and
[issue](engineer/templates/issue.md) templates for publication.

Published, verified and merged are distinct states. Merge only when the user has
explicitly authorized that merge, current verification and review are satisfied,
required checks pass and repository protections permit it. Do not bypass required
checks or reviews. Preserve the branch and report exact blockers when credentials,
remote checks or required human acceptance are unavailable.
