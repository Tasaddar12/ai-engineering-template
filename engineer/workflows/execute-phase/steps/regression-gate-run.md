# Run configured regression checks

Read the complete prior-suite discovery evidence from regression-gate.md. Run `engineer_run query verification.run-checks "${PHASE_NUMBER}"` from the integrated session revision when execution is authorized. The configured checks own argv and per-command timeouts; do not sniff a test command, normalize an invented command, or replace coverage with a successful empty runner.

Reuse only passing receipts whose input fingerprints are current. Retain command IDs, exit codes, timeouts, bounded output tails, origin phase coverage and the checked revision in the joined evidence. A timed-out runner halts dependent verification; never silently continue or call it a passed regression gate. A user-deferred run remains pending. Route demonstrated failures through the bounded isolated correction procedure and rerun invalidated checks after integration.
