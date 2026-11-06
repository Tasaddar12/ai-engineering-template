### Rules for Backfills

- Always process in batches (1000–5000 rows).
- Commit per batch — don't hold a transaction open for millions of rows.
- Log progress so you can resume if interrupted.
- Run backfills as background tasks (Celery), not inside migration files for large tables.
- Add a progress column or flag to track completion.

---
## SECTION 5 — ALEMBIC BEST PRACTICES

```python
# alembic/env.py — always include
def run_migrations_online():
    # Use a transaction per migration for safety
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=True,  # Each migration in its own transaction
        )
        with context.begin_transaction():
            context.run_migrations()
```

### Migration File Rules

- One logical change per migration file.
- Descriptive revision message: `add_full_name_to_users`, not `update_schema`.
- Always implement `downgrade()`.
- Never import application models in migrations — use raw SQL or `op.*` only.
- Pin the migration to a specific schema state (don't reference `models.py`).

---
