# Interface Context for Executors

**Key insight:** "The difference between handing a contractor blueprints versus telling them 'build me a house.'"

When creating plans that depend on existing code or create new interfaces consumed by other plans:

## For plans that USE existing code:
After determining `files_modified`, extract the key interfaces/types/exports from the codebase that executors will need:

```bash
# Extract type definitions, interfaces, and exports from relevant files
grep -n "export\\|interface\\|type\\|class\\|function" {relevant_source_files} 2>/dev/null | head -50
```

Embed these in the plan's `<context>` section as an `<interfaces>` block:

```xml
<interfaces>
<!-- Key types and contracts the executor needs. Extracted from current source at the assigned revision. -->

From src/types/user.ts:
```typescript
export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: Date;
}
```

From src/api/auth.ts:
```typescript
export function validateToken(token: string): Promise<User | null>;
export function createSession(user: User): Promise<SessionToken>;
```
</interfaces>
```

## For plans that CREATE new interfaces:
Record a real `depends_on` edge to the producer plan; a wave label alone is not a prerequisite.

```xml
<task type="auto">
  <name>Task 0: Write interface contracts</name>
  <files>src/types/newFeature.ts</files>
  <action>Create type definitions that downstream plans will implement against. These are the contracts — implementation comes in later tasks.</action>
  <verify>Run the actual project typecheck or contract check against the exact producer revision; verify exported types exist and are consumed.</verify>
  <done>Interface file committed, types exported</done>
</task>
```

## When to include interfaces:
- Plan touches files that import from other modules → extract those module's exports
- Plan creates a new API endpoint → extract the request/response types
- Plan modifies a component → extract its props interface
- Plan depends on a previous plan's output → extract the types from that plan's files_modified

## When to skip:
- Plan is self-contained (creates everything from scratch, no imports)
- Plan is pure configuration (no code interfaces involved)
- Level 0 discovery (all patterns already established)

A producer contract required by a later plan creates a real depends_on edge. Do not assume a Wave 0 skeleton or a declared signature is already implemented; verify against the exact dependency revision.
