# Architecture

The toolkit uses flat Python scripts in `src/` and JSON Schema contracts in `schemas/v1/`.

| File | Current behavior |
| --- | --- |
| `src/install.py` | Safely installs reusable AI workflow guidance, schemas, tools, and empty project records into a new or populated folder. |
| `src/ai.py` | Creates and lists isolated plan/task record bundles. |
| `src/validate_foundation.py` | Validates schemas, installed records, references, graph structure, lifecycle placement, and archive hashes. |
| `docs/agents/` | Canonical detailed behavior for each bounded workflow role. |
| `docs/templates/` | Copyable plan, task, spec, review, handoff, decision, research, and evidence documents. |
| `docs/workflows/` | First-run, planning, context, implementation, review, recovery, and completion guidance. |

Installation keeps framework-owned assets separate from project-owned state. It preflights every managed path, rejects symlink/junction escapes and conflicting managed bytes, preserves existing project files, and appends bounded provider guidance only under `.ai/` or `.claude/`.

Each installed project may hold multiple current work streams in its one selected `.ai` or `.claude` namespace. Every stream owns its specification, graph, task records, commands, evidence, reviews, and history. Plan IDs are project-unique; task and related IDs resolve inside the plan bundle. Active linked Git worktrees live under the installed project’s `.worktrees/` directory and are removed after clean integration.

The current code provides setup, record creation, and deterministic validation. Agent execution, automatic review, recovery, remote delivery, and completion are future runtime features.
