# Phase templates

Templates show the minimum useful shape; placeholder text is not a real decision,
result or verification. Replace it with evidence before using a record.

| Template | Destination |
|---|---|
| [PROJECT](PROJECT.md) | `.ai/PROJECT.md` during adoption |
| [CONTEXT](CONTEXT.md) | `phases/NN-slug/NN-CONTEXT.md` |
| [DISCUSSION-LOG](DISCUSSION-LOG.md) | Optional `NN-DISCUSSION-LOG.md` |
| [RESEARCH](RESEARCH.md) | Optional `NN-RESEARCH.md` |
| [VALIDATION](VALIDATION.md) | Optional `NN-VALIDATION.md` |
| [IMPLEMENT](IMPLEMENT.md) | `NN-CC-IMPLEMENT.md` per component |
| [SUMMARY](SUMMARY.md) | `NN-CC-SUMMARY.md` from its worker |
| [VERIFICATION](VERIFICATION.md) | `NN-VERIFICATION.md` stored by coordinator |
| [UAT](UAT.md) | `NN-UAT.md`, created/updated through runtime |
| [CONTINUE](CONTINUE.md) | Optional `.continue-here.md` |
| [SPEC](SPEC.md) | Current behavior in `.ai/specs/` |
| [ADR](ADR.md) | Significant rationale in `.ai/decisions/` |

Frontmatter is limited to fields the operation uses. Do not add separate schema
files or repeat component requirements in another registry. See
[artifact ownership](../references/phase-artifacts.md). Optional records are
omitted when they add no useful information.
