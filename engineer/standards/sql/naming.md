## SECTION 2 — NAMING CONVENTIONS

| Element | Convention | Example |
|---|---|---|
| Table name | `snake_case`, plural | `user_orders`, `product_categories` |
| Column name | `snake_case` | `created_at`, `is_active`, `tenant_id` |
| Primary key | Always `id` | `id INTEGER PRIMARY KEY` |
| Foreign key column | `{singular_table}_id` | `user_id`, `order_id` |
| Boolean columns | `is_` or `has_` prefix | `is_active`, `has_verified_email` |
| Timestamp columns | `_at` suffix | `created_at`, `deleted_at`, `published_at` |
| Hashed/encrypted | `_hash` or `_encrypted` suffix | `password_hash`, `ssn_encrypted` |
| Index | `ix_{table}_{columns}` | `ix_users_email`, `ix_orders_user_created` |
| Unique constraint | `uq_{table}_{columns}` | `uq_users_email_tenant` |
| Foreign key constraint | `fk_{table}_{col}_{ref_table}` | `fk_orders_user_id_users` |
| Check constraint | `ck_{table}_{rule}` | `ck_orders_amount_positive` |

---
