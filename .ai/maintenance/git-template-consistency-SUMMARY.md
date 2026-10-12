# Git template consistency

Status: implementation pending.

## Scope

- Align `.ai/templates/issue.md` and `.ai/templates/pull-request.md` with the retained authoring templates.
- Preserve required body fields and the existing publication and verification rules.
- Change direct consumers or checks only when needed for the authoring structure.
- Keep adopting-project planning records unfilled.

## Inspected boundary

- Base: `b770c90e6cad1307385bc225d902523c3613cbd0` (`origin/main`).
- The selected files are internal AI authoring sources, not GitHub-native forms.
- No merge-request template or GitHub-native issue/PR template exists in the tracked corpus.
- The existing sources lack the `File Template` wrapper used by the retained template family.

## Verification

Pending. Open the draft PR before running test scripts, as requested.
Run affected template/consumer checks, the repository unit suite and four hook suites after implementation.
No benchmarks. Leave the PR draft and unmerged.
