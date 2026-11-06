### 6.2 Pagination — always required for list queries

```python
from sqlalchemy import func, select

async def get_paginated_users(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    *,
    include_deleted: bool = False,
) -> tuple[list[User], int]:
    """Fetch a page of users with total count.

    Returns:
        Tuple of (users on this page, total user count).
    """
    if page < 1:
        raise ValueError(f"page must be >= 1, got {page}")
    if not 1 <= page_size <= 100:
        raise ValueError(f"page_size must be 1-100, got {page_size}")

    base_query = select(User)
    if not include_deleted:
        base_query = base_query.where(User.deleted_at.is_(None))

    # Count query — uses COUNT(*) on same filters (no ORDER BY; faster)
    count_result = await session.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    # Data query with pagination
    users_result = await session.execute(
        base_query
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return users_result.scalars().all(), total
```

---
