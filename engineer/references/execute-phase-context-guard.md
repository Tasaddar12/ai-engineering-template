0. **Context exhaustion guard — `context_guard` (BEFORE spawning):**

   Before spawning any agents for this wave, self-assess context pressure using the
   degradation signals in `engineer/references/context-budget.md`. Signs of POOR tier (70%+):
   increasing vagueness, skipped steps, silent partial completion.

   Read `workflow.context_guard_mode` from `.planning/config.json` (default `warn`).

   | Tier | `warn` (default) | `auto` | `off` |
   |------|-----------------|--------|-------|
   | PEAK / GOOD | No output | No output | No output |
   | DEGRADING (50-70%) | Emit: "⚠ Context pressure DEGRADING — use focused reads for remaining waves." Continue. | Same as warn | Skip |
   | POOR (70%+) | Emit: "⚠ Context pressure POOR — risk of context exhaustion. Capture a concise handoff before continuing this wave." Continue. | Capture a concise handoff before continuing this wave. | Skip |

   The guard is heuristic — no programmatic context-percentage API exists. Use your
   assessment of degradation signals, not a fixed token count.
