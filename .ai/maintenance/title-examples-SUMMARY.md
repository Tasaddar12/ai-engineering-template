---
maintenance: title-examples
status: documentation_committed_validation_pending
scope: issue and pull request title authoring guidance
documentation:
  - .ai/templates/issue.md
  - .ai/templates/pull-request.md
---

# Issue and pull request title examples

## Why

Provide concise, consistent title guidance while keeping issue requests distinct
from implemented pull request outcomes.

## Changes

- Added `type(scope): summary` guidance and four requested-resolution examples to
  the issue template.
- Added the same format guidance and four implemented-outcome examples to the PR
  template. Both sections name the existing type vocabulary and lowercase area
  scopes, and clarify that this Conventional Commits inspired authoring guidance
  is not enforced by Git or GitHub.
- Kept both additions outside the fenced public File Template blocks. Existing
  Purpose, Producer, Consumers, Destination, How to fill, good/bad examples and
  completion/handoff guidance remain present.

## Verification

- Manual source review confirmed each fenced File Template block matches its base
  version exactly; title guidance is outside those blocks.
- `git diff --check` passed.
- Test scripts and broader checks were not run, per assignment. Coordinator
  validation remains pending after the tracking draft is opened.

## Handoff

No issue-closing change was made. Coordinator owns push, draft PR publication and
post-open validation; this summary does not claim those actions are complete.
