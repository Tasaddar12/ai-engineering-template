# Planning workflow

1. Clarify the requested outcome, affected users, constraints, authority, and measurable acceptance. Research changing or uncertain facts and record sources.
2. Copy the blank specification and plan templates into one new current plan bundle. Do not edit the master files under `.codex/templates/`.
3. Decompose the specification into small plan-local tasks. Give each task exact write/read/prohibited paths, resource claims, dependencies, acceptance mapping, commands, contracts, exclusions, and handoff requirements.
4. Check that every requirement and plan acceptance criterion is covered, dependencies form a DAG, and unordered tasks do not overlap writes, resources, or written contracts.
5. Validate the bundle. Then give the complete proposed graph and structural task digest to a fresh task isolation reviewer.

A reviewer may propose a rewritten graph, but only the coordinator records the accepted revision. Implementation remains blocked until a passing isolation review matches the current graph and digest.
