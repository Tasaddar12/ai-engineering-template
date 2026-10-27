<!-- workflow: milestone-summary; read-only unless --write -->
<purpose>
Explain an actual milestone for onboarding or review from complete committed evidence. Present the document in the response by default. Write and commit only when --write was explicitly supplied; never mutate STATE.
</purpose>
<response_language>
Read `engineer_run query config-get response_language --raw` through the sourced launcher. Apply the configured language to every user-facing prose surface: narration between tool calls, status updates, progress notes, findings, route explanations, headings and the final result. Preserve literal code, paths, identifiers, parser keys and canonical markers. Missing configuration uses the established conversation language; do not invent a language alias in an init bundle.
</response_language>
<process>
<step name="resolve_version">
Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Run milestone.list; use the explicit target, otherwise the active milestone, otherwise the newest actually shipped milestone. If none exists, report /new-milestone as the missing setup. Never guess an archive path from a version-shaped string.
</step>
<step name="locate_artifacts">
Run init.complete-milestone and resolve its actual target milestone_phases membership. Read PROJECT and REQUIREMENTS, each target phase's CONTEXT/complete SUMMARY/VERIFICATION, relevant UAT and milestone narrative. Use bounded relevant reads and source references for implementation details; do not load unrelated records or replace evidence with roadmap headings alone. An unavailable target membership is a report limitation, not an invented phase list.
</step>
<step name="gather_statistics">
## Step 4: Gather Git Statistics

Try each method in order until one succeeds:

**Method 1 — Tagged milestone** (check first):
```bash
git tag -l "v${VERSION}" | head -1
```
If the tag exists:
```bash
git log v${VERSION} --oneline | wc -l
git diff --stat $(git log --format=%H --reverse v${VERSION} | head -1)..v${VERSION}
```

**Method 2 — STATE.md date range** (if no tag):
Read STATE.md and extract the `started_at` or earliest session date. Use it as the `--since` boundary:
```bash
git log --oneline --since="<started_at_date>" | wc -l
```

**Method 3 — Earliest phase commit** (if STATE.md has no date):
Find the earliest `.planning/phases/` commit:
```bash
git log --oneline --diff-filter=A -- ".planning/phases/" | tail -1
```
Use that commit's date as the start boundary.

**Method 4 — Skip stats** (if none of the above work):
Report "Git statistics unavailable — no tag or date range could be determined." This is not an error — the summary continues without the Stats section.

Extract (when available):
- Total commits in milestone
- Files changed, insertions, deletions
- Timeline (start date → end date)
- Contributors (from git log authors)


</step>
<step name="generate_document">
Keep the complete seven-section format and examples below. Distinguish delivered, in-progress, planned, deferred and unverified outcomes. Cite actual paths and revisions; do not claim a test or acceptance passed from narrative alone. Known Gaps is explicit even when it states none were found. Default output is the response; the path in the template applies only to --write.

```markdown
# Milestone v{VERSION} — Project Summary

**Generated:** {date}
**Purpose:** Team onboarding and project review

---

## 1. Project Overview

{From PROJECT.md: "What This Is", core value proposition, target users}
{If mid-milestone: note which phases are complete vs in-progress}

## 2. Architecture & Technical Decisions

{From CONTEXT.md files across phases: key technical choices}
{From SUMMARY.md decisions: patterns, libraries, frameworks chosen}
{From PROJECT.md: tech stack if documented}

Present as a bulleted list of decisions with brief rationale:
- **Decision:** {what was chosen}
  - **Why:** {rationale from CONTEXT.md}
  - **Phase:** {which phase made this decision}

## 3. Phases Delivered

| Phase | Name | Status | One-Liner |
|-------|------|--------|-----------|
{For each phase: number, name, status (complete/in-progress/planned), one_liner from SUMMARY.md}

## 4. Requirements Coverage

{From REQUIREMENTS.md: list each requirement with status}
- ✅ {Requirement met}
- ⚠️ {Requirement partially met — note gap}
- ❌ {Requirement not met — note reason}

{If MILESTONE-AUDIT.md exists: include audit verdict}

## 5. Key Decisions Log

{Aggregate from all CONTEXT.md <decisions> sections}
{Each decision with: ID, description, phase, rationale}

## 6. Tech Debt, Deferred Items & Known Gaps

{From VERIFICATION.md files: actual gaps and anti-patterns; explicitly state Known Gaps even when none remain}
{From RETROSPECTIVE.md: lessons learned, what to improve}
{From CONTEXT.md <deferred> sections: ideas parked for later}

## 7. Getting Started

{Entry points for new contributors:}
- **Run the project:** {from PROJECT.md or SUMMARY.md}
- **Key directories:** {from codebase structure}
- **Tests:** {test command from PROJECT.md or AGENTS.md}
- **Where to look first:** {main entry points, core modules}

---

## Stats

- **Timeline:** {start} → {end} ({duration})
- **Phases:** {count complete} / {count total}
- **Commits:** {count}
- **Files changed:** {count} (+{insertions} / -{deletions})
- **Contributors:** {list}
```


</step>
<step name="write_and_commit">
Only when --write is explicit, write the full document to `.planning/reports/MILESTONE_SUMMARY-v${VERSION}.md`. If that exact file already exists, ask overwrite or view; view preserves it and returns its complete existing contents. Commit only that report through engineer_run query commit after an authorized overwrite/new write. Without --write, do not create directories, files, commits or STATE continuity entries.
</step>
<step name="present">
Present the full requested explanation and its factual limitations, or its exact path/commit when written. Keep the relevant Q&A offer: answer questions about an actual phase, decision or entry point from the evidence. Do not recommend unrelated workflow commands or imply a written report when only a response was requested.
</step>
</process>
<anti_patterns>
No roadmap-only account, fabricated verification, hidden known gaps, unrequested report write, or STATE mutation.
</anti_patterns>
<success_criteria>
The complete seven-section explanation is supported by actual milestone evidence and explicit known gaps; output remained read-only unless --write was supplied and its exact overwrite/commit scope was authorized.
</success_criteria>
