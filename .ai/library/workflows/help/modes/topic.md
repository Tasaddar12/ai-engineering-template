Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

<purpose>
Emit a section from the full reference for the topic in `$ARGUMENTS`. Read `.ai/library/workflows/help/modes/full.md`, resolve the topic alias to a section heading using the table below, and output the resolved-routing preamble plus the section content. Scope is controlled by a `--brief` flag in `$ARGUMENTS`: full scope (default) emits the entire section; compact scope (`--brief <topic>`) emits only the signature line + one-line summary for a compact scoped lookup. No additions, no surrounding chrome.
</purpose>

<reference>
**Topic resolution table.** Match the topic alias case-insensitively. Strip a single leading `--` if present.

| Topic alias(es) | Section heading in `full.md` |
|---|---|
| `next`, `smart-entry` | `### Smart Entry` |
| `workflow`, `core`, `core-workflow` | `## Core Workflow` (entire section through end of `### Quick Mode`) |
| `init`, `new-project`, `onboard`, `onboarding`, `brownfield` | `### Project Initialization` |
| `map`, `map-codebase` | The `/workflow:map-codebase` block under `### Project Initialization` |
| `discuss`, `discuss-phase` | The `/workflow:discuss-phase` block under `### Phase Planning` |
| `plan`, `planning`, `plan-phase` | `### Phase Planning` |
| `execute`, `exec`, `execute-phase` | `### Execution` |
| `progress`, `route` | `### Progress Tracking` plus `### Smart Router` |
| `quick`, `quick-mode` | `### Quick Mode` |
| `fast` | The `/workflow:fast` block under `### Quick Mode` |
| `phase`, `phases`, `roadmap` | `### Roadmap Management` |
| `milestone`, `milestones` | `### Milestone Management` plus `### Milestone Auditing` |
| `session`, `pause`, `resume` | `### Session Management` |
| `debug`, `debugging` | `### Debugging` |
| `spike` | The `/workflow:spike` and `/workflow:spike --wrap-up` blocks under `### Spiking & Sketching` |
| `sketch` | The `/workflow:sketch` and `/workflow:sketch --wrap-up` blocks under `### Spiking & Sketching` |
| `spike-sketch`, `experiments` | `### Spiking & Sketching` |
| `capture`, `notes`, `todos` | `### Capturing Ideas, Notes, and Todos` |
| `verify`, `verify-work`, `uat` | `### User Acceptance Testing` plus the `/workflow:audit-uat` block |
| `ship`, `pr` | `### Ship Work` plus the `/workflow:pr-branch` block |
| `review`, `peer-review` | The `/workflow:review` block under `### Ship Work` |
| `audit`, `auditing`, `audit-milestone` | `### Milestone Auditing` |
| `config`, `settings`, `configuration` | `### Configuration` |
| `cleanup` | The `/workflow:cleanup` block under `### Utility Commands` |
| `update` | The `/workflow:update` block under `### Utility Commands` |
| `files`, `structure`, `layout` | `## Files & Structure` |
| `modes`, `interactive`, `yolo` | `## Workflow Modes` |
| `planning-config` | `## Planning Configuration` |
| `workflows`, `common-workflows`, `examples` | `## Common Workflows` |
| `help` | `## Getting Help` |

**Output rules:**

1. Parse `$ARGUMENTS`: detect a `--brief` (or `-b`) flag — this selects **compact scope**. Otherwise scope is **full**. Strip the flag, then take the remaining token (with a single leading `--` stripped) as the topic alias.
2. Resolve the alias against the table.
3. If no match: emit a one-line error followed by a comma-separated list of the canonical topic names from the leftmost column (one per row, deduplicated). Suggest `/workflow:help --full` for the complete reference. Stop.
4. If matched: emit a single resolved-routing preamble line so the user sees what was matched:

   ```text
   **Topic:** `<alias>` → `<heading>` *(scope: full | compact)*
   ```

   Use the canonical alias from the leftmost column. Use the literal heading text from the matched cell. State the scope you are about to emit.

5. Read `.ai/library/workflows/help/modes/full.md`. Strip `<reference>` / `</reference>` wrapper tags — never emit them. Apply the extraction rule for the matched table cell, modulated by scope:

   5a. **Single section** (cell contains a single `` `## Heading` `` or `` `### Heading` ``):
   - *Full scope:* emit from that heading up to (but not including) the next sibling or higher-level heading.
   - *Compact scope:* emit the heading, then the first `` **`/workflow:...`** `` bold line within the section (the signature) and the single non-blank line immediately after it (the one-line summary). If the section has no `` **`/workflow:...`** `` bold line, emit the heading and the first paragraph.

   5b. **Multiple sections joined by "plus"**: apply rule 5a to each listed section in document order and emit them sequentially with no gap between them.

   5c. **Sub-block** (cell says `the /workflow:X block under ### Heading` or `the /workflow:X ... blocks under ### Heading`): within the named heading's section, start at each `` **`/workflow:X ...`** `` bold line.
   - *Full scope:* stop immediately before the next `` **`/workflow:...`** `` bold line or the next heading, whichever comes first.
   - *Compact scope:* emit the bold line and the single non-blank line immediately after it (the one-line summary).

   For cells listing multiple sub-blocks, emit them sequentially.

6. After the section content, emit a single closing line:

   ```text
   More: /workflow:help --full · /workflow:help <topic> · /workflow:help --brief <topic>
   ```

7. No project-specific commentary, no follow-up questions.
</reference>


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
