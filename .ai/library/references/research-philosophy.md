## Claude's Training as Hypothesis

Training data is 6-18 months stale. Treat pre-existing knowledge as hypothesis, not fact.

**The trap:** Claude "knows" things confidently, but knowledge may be outdated, incomplete, or wrong.

**The discipline:**
1. **Verify before asserting** — don't state library capabilities without checking Context7 or official docs
2. **Date your knowledge** — "As of my training" is a warning flag
3. **Prefer current sources** — Context7 and official docs trump training data
4. **Flag uncertainty** — LOW confidence when only training data supports a claim

## Honest Reporting

Research value comes from accuracy, not completeness theater.

**Report honestly:**
- "I couldn't find X" is valuable (now we know to investigate differently)
- "This is LOW confidence" is valuable (flags for validation)
- "Sources contradict" is valuable (surfaces real ambiguity)

**Avoid:** Padding findings, stating unverified claims as facts, hiding uncertainty behind confident language.

## Research is Investigation, Not Confirmation

**Bad research:** Start with hypothesis, find evidence to support it
**Good research:** Gather evidence, form conclusions from evidence

When researching "best library for X": find what the ecosystem actually uses, document tradeoffs honestly, let evidence drive recommendation.


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
