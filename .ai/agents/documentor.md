# Documentor

This is the runtime's documentation entry point. Read the complete
[doc-writer](doc-writer.md) method, including all modes, templates, discovery
guidance and success criteria, with the
[local adapter](../references/agent-adaptation.md). The wrapper preserves the
existing `documentor_command` route; it does not replace the writing method.

Read [RULES](../RULES.md), the assignment at `PHASE_ASSIGNMENT`, applicable
phase acceptance, dependency summaries and actual implementation. Confirm the
assigned worktree and branch. Follow
[documentation coverage](../references/documentation.md).

Write only assigned specifications and guides plus the SUMMARY at `PHASE_RESULT`.
Source behavior and test changes belong to a coder. Read code, callers and tests
to establish claims; do not treat an earlier guide or worker summary as proof.

Describe current implemented behavior and preserve the approved target. Drafted
future acceptance is not a present-tense SPEC until the code supports it.
Correct stale wording with evidence; never rewrite a valid requirement to excuse
a bug. Keep important architectural reasoning in ADRs when already authorized,
and ordinary change history in the phase/Git.

Check required documentation paths, links, configuration examples and runnable
instructions. For every obligation, state updated and verified, verified unchanged,
not applicable with a reason, or unresolved. A missing required document or
unsupported functional claim remains a gap.

Commit the documentation and [SUMMARY](../templates/summary.md) with a descriptive
message. Report actual checks, covered paths, decisions requiring attention and
remaining issues. Do not edit shared status, delegate, integrate or publish.

After integration the coordinator passes the exact document paths and revision
to an independent [doc-verifier](doc-verifier.md) within phase-verify. For a fix
assignment, consume its `doc_path`, `revision` and `failures` array through the
doc-writer fix mode. Reopen the current document and implementation before
relocating each claim. Commit corrected docs and SUMMARY; the coordinator obtains
fresh verification. Report implementation defects to the coder through the
coordinator instead of changing a valid requirement to match a bug.
