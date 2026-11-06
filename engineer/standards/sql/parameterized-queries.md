## SECTION 4 — SQL INJECTION PREVENTION

```python
# CORRECT — ORM with parameterised queries (always safe)
result = await session.execute(
    select(User).where(User.email == email)    # parameterised internally by SQLAlchemy
)

# CORRECT — explicit parameterised text() when raw SQL is necessary
from sqlalchemy import text
result = await session.execute(
    text("SELECT * FROM users WHERE email = :email AND tenant_id = :tid"),
    {"email": email, "tid": tenant_id},   # parameters; never interpolated
)

# WRONG — string interpolation into SQL — classic SQL injection
result = await session.execute(
    text(f"SELECT * FROM users WHERE email = '{email}'")   # CRITICAL VULNERABILITY
)

# WRONG — .format() is equally dangerous
query = "SELECT * FROM users WHERE name = '{}'".format(name)   # CRITICAL VULNERABILITY
```

---
