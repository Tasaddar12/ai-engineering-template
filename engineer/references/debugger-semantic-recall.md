# Semantic Knowledge-Base Recall

Use the project's durable plain-text debug knowledge base to find earlier
resolutions that may explain the current symptoms. Recall is a hypothesis
generator: compare the prior case with the present evidence before adopting its
root cause or fix.

## Read and compare

At the start of an investigation, inspect `.planning/debug/knowledge-base.md` if
it exists. Search for error text, identifiers, affected components, and the
observable behavior. `rg` can narrow the entries to inspect; it does not decide
whether two cases are semantically equivalent.

For each plausible entry, compare the cases across these dimensions:

| Dimension | Compare |
|---|---|
| Trigger | What action, input, load, or sequence starts the failure? |
| Observable behavior | What fails, hangs, changes, or remains unchanged? |
| Conditions | Which environment, state, timing, or dependency conditions matter? |
| Mechanism | Which component and causal mechanism produced the prior failure? |
| Evidence | Which observations or checks established that mechanism? |
| Resolution | What change fixed it, and what recurrence guard verified the fix? |

Treat wording and keyword overlap as weak signals. Two descriptions can refer to
the same mechanism with different words; similar words can also describe
different causes. State the matching and conflicting dimensions, then classify
the entry as a useful hypothesis, a partial analogy, or unrelated. Test useful
hypotheses against current evidence; do not copy a prior fix solely because the
symptoms sound alike.

If no entry is a plausible match, continue the investigation from current
evidence. Do not infer that the knowledge base is complete or that a missing
match rules out a known failure mode.

## Record resolved cases

The project knowledge base remains the durable source of truth. After the
resolution is established, append a concise case using the repository's
existing entry format and commit it through the owning workflow. Record the
agent-authored root cause, verified fix, discriminating evidence, and a useful
recurrence guard. Do not write raw user-supplied symptoms or unreviewed report
text into a shared knowledge base. Remove secrets and personal data from any
quoted error or example before recording it.

## Scope

Recall uses ordinary files and search, followed by explicit semantic comparison
and evidence checking. It introduces no external memory service, embedding
pipeline, vector store, or new command.
