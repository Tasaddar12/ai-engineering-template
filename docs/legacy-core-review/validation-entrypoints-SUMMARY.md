# Validation entrypoints correction

Status: complete (CR05 owned correction).

## Identity and authority

- Worktree: `D:/Codex Projects/ai-engineering-template/.worktrees/validation-entrypoints-203735049`
- Branch: `phase-legacy-validation-entrypoints`
- Input revision: `7605c4f6653f0a4cbb8673fcc26fc95a55f125ec`
- Owned paths: `commands/plan-phase.md`, `skills/plan-phase/SKILL.md`, this summary.
- Authority: CR05; maintenance PLAN component-retirement boundaries; PLANNED-UPDATES R-WF-172/175/190/219/244. Explicit assignment preserves valid TDD/text/reversibility options while retiring missing public modes.

## Change

Removed the public research-only flags `--research-phase` and `--view`, their objective/modifier instructions, the PRD express-ingest flag/instructions, and bounce/skip-bounce flags. Ordinary research, planning and plan verification remain, including valid auto, research, skip-research, gaps, skip-verify, skip-ui, text, TDD, granularity and no-reversibility-gates flags. The command and skill copy are byte-identical. No workflow or agent methods were edited.

## Verification

- Initial location/Git root/branch/HEAD checks matched the assigned clean worktree and input revision.
- Python static check: all 42 command/skill pairs byte-identical.
- Python public-surface check: no research-phase/view/PRD/ingest/reviews/bounce flags or research-only/express-ingest behavior remain in either owned entrypoint; retained flag set and ordinary orchestrator behavior preserved.
- Python structure smoke: standalone context/process/objective/execution-context tags retain baseline balance and code-fence parity.
- `git diff --check`: passed.

## Deferred / limits

Valid workflow flag-initializer repairs and combined independent verification belong to the coordinator's other assignment. No planning records, other commands, source feature implementation, integration, push or publication were performed. No new security-relevant surface was introduced.
