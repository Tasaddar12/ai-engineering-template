Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# --analyze mode — trade-off tables before each question

> **Lazy-loaded overlay.** Read this file from `.ai/library/workflows/discuss-phase.md`
> when `--analyze` is present in `$ARGUMENTS`. Combinable with default,
> `--all`, `--chain`, `--text`, `--batch`.

## Effect

Before presenting each question (or question group, in batch mode), provide
a brief **trade-off analysis** for the decision:
- 2-3 options with pros/cons based on codebase context and common patterns
- A recommended approach with reasoning
- Known pitfalls or constraints from prior phases

## Example

```markdown
**Trade-off analysis: Authentication strategy**

| Approach | Pros | Cons |
|----------|------|------|
| Session cookies | Simple, httpOnly prevents XSS | Requires CSRF protection, sticky sessions |
| JWT (stateless) | Scalable, no server state | Token size, revocation complexity |
| OAuth 2.0 + PKCE | Industry standard for SPAs | More setup, redirect flow UX |

💡 Recommended: OAuth 2.0 + PKCE — your app has social login in requirements (REQ-04) and this aligns with the existing NextAuth setup in `src/lib/auth.ts`.

How should users authenticate?
```

This gives the user context to make informed decisions without extra
prompting.

When `--analyze` is absent, present questions directly as before (no
trade-off table).

## Sourcing the analysis

- Pros/cons should reflect the codebase context loaded in `scout_codebase`
  and any prior decisions surfaced in `load_prior_context`.
- The recommendation must explicitly tie to project context (e.g.,
  existing libraries, prior phase decisions, documented requirements).
- If a related ADR or spec is referenced in CONTEXT.md `<canonical_refs>`,
  cite it in the recommendation.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
