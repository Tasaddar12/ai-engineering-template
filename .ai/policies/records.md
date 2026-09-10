---
tier: contract
authority: agent
title: Record maintenance policy
links: [AMD-002]
---

# Record maintenance policy

[RULES](../RULES.md) owns mutability, document tense, amendment protocols and
the FIX/PLAN distinction. [Truth map](../truth-map.md) owns fact locations;
[config](../config.yaml) owns paths, stages and ID formats. Use those owners
when creating or moving records instead of copying their rules here.

## Every PR keeps its specification current

In this repository's standard mode, every feature or fix PR updates the
affected SPEC in the same change. Changed behavior updates criteria. A pure
conformance repair retains correct criteria and refreshes `verification_refs`
to its actual proof. Do not invent a contract change to describe a repair or
write change history into a specification. No post-merge spec commit is needed.
A consuming project that explicitly chooses light mode uses plan acceptance
criteria; its choice must be recorded in its project configuration.

## Record transitions

Keep IDs and slugs when moving PLAN/FIX records, repair current links, and
journal the transition. Completed records retain their observed result; new
work uses a successor. Preserve old journal entries, including references to
historical revisions. When retiring a referenced file, append its Git-history
location instead of rewriting the earlier event.

A plan in done has passed implementation verification. That directory does
not claim that a PR merged: Git and the forge own delivery facts. Record any
pending delivery explicitly, and follow [deliver](../commands/deliver.md).

## State and evidence

The session coordinator owns shared STATE and the journal; the scheduling
agent owns the run board only when assigned. Track roles write their own
records and return shared-state events to the coordinator. A read-only report
changes no files. Verification/review evidence belongs to the selected PLAN
or FIX; new observations on historical records go in the journal.

Use [JOURNAL](../templates/JOURNAL.md) for each new daily log. Preserve
previous entries; append observations and links rather than updating the past.
