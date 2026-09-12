# Documentation coverage

A phase keeps required documentation attached to the behavior that changes.
IMPLEMENT frontmatter names exact required document paths; code or documentation
components may satisfy them within their assigned ownership. SUMMARY records
what was actually covered. The verifier checks the integrated result.

Assign each required path to the component that will actually cover it. A coder's
declared documentation is checked when that coder's result integrates. For guides
created later, put the required paths on a documentor component dependent on the
code and reference that handoff in the coder's body. Do not make a coder claim
coverage for a future documentor's work.

| Change | Inspect for documentation impact |
|---|---|
| Observable behavior | Relevant SPEC and usage guide |
| Public interface | API/command reference and examples |
| Configuration | Configuration and setup instructions |
| Installation/deployment | Operational guidance |
| Significant architectural choice | Accepted rationale and any needed ADR |
| Internal implementation | Comments or no external change, supported by a reason |

For each obligation, report **updated and verified**, **verified unchanged**,
**not applicable with a reason**, or **unresolved**. Required unresolved coverage
prevents phase completion. A removed obligation changes the approved instructions;
it cannot be dropped simply because implementation did not satisfy it.

Coders update nearby explanation while their understanding is fresh. Assign a
documentor for substantial SPECs and guides, with dependencies on the code it
describes. Verify claims against code/callers/checks at the integrated revision.
Run documented commands where appropriate and inspect links and configuration
examples. References provide navigation; a guide is not evidence for its own claim.

SPECs describe current correct behavior. Keep future promises in phase context,
and history in Git or significant ADRs. No routine amendment is required.
A documentation discrepancy needs an evidenced correction; an implementation
defect needs code repair. Neither author may redefine the intended outcome.

Record editorial findings separately from missing behavior/coverage. Deferred
unrelated findings stay linked to the phase; missing required docs cannot be
spun out to make an unfinished phase appear complete.
