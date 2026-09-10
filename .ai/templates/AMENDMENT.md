---
tier: log
authority: agent
id: AMD-{nnn}
title: <What changed, in a few words>
date: YYYY-MM-DD
amends: SPEC-{nnn}
raised_by: <agent name>
links: []
---

# AMD-{nnn}: <What changed, in a few words>

> **`log` tier — append only.** Never edit or delete a past amendment. If this
> one is later superseded, write a new record saying so.

## What the document said

Quote or paraphrase the claim that turned out to be wrong. Be precise enough
that a reader can find it in the history.

## What is actually true

The reality that contradicts it, and how you established it — a test, observed
behavior, a constraint in `intent/PROJECT.md`, a decision made with the user.

## Why they diverged

One of: the requirement was always wrong · the world changed · the spec
described an implementation that has since been replaced · two documents
disagreed and this one lost · we learned something during execution.

## What I changed it to

The new wording, and anything downstream that had to move with it — other
specs, plans, docs, tests. If the requirement went away entirely, say what was
deleted: the criterion, the section, or the whole spec file.

**This record is why the spec does not have to carry any of it.** The spec now
reads as a clean statement of what is true today, with no "was previously", no
"deprecated", and no trace of the old wording. Quote the before-text here
instead — that is what this section is for.

## Superseded

Delete unless applicable. Amendment ids this record replaces, and why.

<!--
Naming: AMD-{nnn}-{slug}.md in .ai/decisions/amendments/.

Write this BEFORE editing the spec, then add this id to the spec's `links:`,
then commit all of it together with the code change. Three sentences per
section is plenty — the record exists so a human can audit why the contract
moved, not to slow you down.

An amendment is never a failure. A project whose specs are never amended is a
project whose specs are being ignored.
-->
