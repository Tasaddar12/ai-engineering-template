## SECTION 5 — ABAC (Attribute-Based Access Control)

For complex authorization beyond roles:

```python
# app/core/policies.py
from dataclasses import dataclass


@dataclass
class AccessContext:
    user_id: str
    user_role: str
    user_org_id: str
    resource_owner_id: str
    resource_org_id: str
    action: str


def evaluate_policy(ctx: AccessContext) -> bool:
    """Evaluate access based on multiple attributes."""
    # Super admin can do anything
    if ctx.user_role == "super_admin":
        return True

    # Users can only access resources in their org
    if ctx.user_org_id != ctx.resource_org_id:
        return False

    # Owners can edit their own resources
    if ctx.action in ("update", "delete") and ctx.user_id == ctx.resource_owner_id:
        return True

    # Admins can manage anything in their org
    if ctx.user_role == "admin":
        return True

    # Editors can read and create
    if ctx.user_role == "editor" and ctx.action in ("read", "create"):
        return True

    return False
```

---
