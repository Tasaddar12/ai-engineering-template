# Init, adopt, research and upgrades

Init creates a project identity, framework installation record and seed project-owned settings after validating a clean destination. Adopt inventories existing docs, commands, branch policy and architecture; emits a mapping proposal, imports records with provenance, and preserves originals. Never overwrite existing project decisions or silently enable discovered commands.

Research records question, sources, retrieval date, claims, evidence, uncertainty and relevance. Requirements/spec work turns approved conclusions into measurable acceptance criteria; ADRs record decision, alternatives, consequences, reversibility and supersession. Planning references these artifacts rather than copying every source into each task.

Framework package version, installed asset version and schema version are distinct. A project pins all three. Upgrade computes a dry-run three-way diff using old manifest hashes, installed bytes and new release assets. Only manifest-owned files may update automatically. Local edits to owned files produce conflict proposals; project-owned content is immutable to upgrade logic. Migration runs in an isolated branch/worktree, validates records and compatibility, and records before/after versions. Unsupported newer schemas fail closed.

Seed-only templates become project-owned when instantiated. Central schema sources ship as package data; installed copies are owned assets with digests. Package release tests verify bundled bytes match canonical sources. Upgrade rollback restores a verified prior asset/state checkpoint without erasing subsequent project work; if later state is incompatible, create a forward repair/migration instead of hard reset.
