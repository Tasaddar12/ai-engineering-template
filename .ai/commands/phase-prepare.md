# Prepare component execution

Read [RULES](../RULES.md), CONTEXT, relevant current SPECs, research and code.
Use the [preparer](../agents/phase-preparer.md) for substantial decomposition.

1. Define bounded components using [IMPLEMENT](../templates/IMPLEMENT.md). Each
   component must state its outcome, owned paths, dependencies, shared interfaces,
   acceptance IDs, required reads, commands and documentation obligations.
   Select useful [repository skills](../../docs/AGENT-SKILLS.md) for the actual
   assignment and put required skill paths in its Read first section.
2. Use exact file paths or directory prefixes ending in `/`. Mark exclusive
   resources. Overlap serializes workers; dependency edges mean a prerequisite
   really must exist. Reject cycles and unnecessary coupling.
3. Agree interfaces before concurrent work. Include integration checks that prove
   independently implemented pieces connect. Assign substantial docs explicitly,
   often as a documentation component dependent on the code it describes. Declare
   each required document on the component that will cover it; reference later
   documentation handoffs in coder prose rather than claiming future coverage.
4. Write VALIDATION when the phase needs shared test setup, manual checks or a
   coverage explanation. Command values belong to config or IMPLEMENT; reference
   them rather than keeping competing copies.
5. Have an independent [checker](../agents/phase-checker.md) assess substantial
   phases. Record its findings and resolution in CONTEXT preparation notes.
   Keep blocking unresolved behavior out of executable assignments.
6. Commit prepared inputs and run the read-only readiness check:

```text
python .ai/runtime/phase.py check 01-authentication
```

Fix gaps and repeat relevant checks. Runtime readiness checks fields and
dependencies; it does not prove semantic completeness. A small fix still needs
one bounded instruction and before/after regression evidence, but can omit
research and a lengthy validation document.

Continue with [phase-start](phase-start.md) when execution is authorized.
