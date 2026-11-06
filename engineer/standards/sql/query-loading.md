## SECTION 3 — N+1 QUERY PREVENTION

### 3.1 SQLAlchemy — joinedload vs selectinload

```python
from sqlalchemy.orm import joinedload, selectinload

# joinedload — single SQL with JOIN; best for FK / OneToOne (at most one related)
users = await session.scalars(
    select(User).options(joinedload(User.profile))   # one JOIN — one user has one profile
)

# selectinload — two queries (SELECT IN); best for collections (one-to-many)
# Avoids cartesian product that joinedload creates with collections
orders = await session.scalars(
    select(Order).options(
        selectinload(Order.items),           # one query: SELECT * FROM items WHERE order_id IN (...)
        joinedload(Order.user),              # one JOIN: user is always exactly one
    ).where(Order.status == "pending")
)

# NEVER access a relationship in a loop without pre-loading
for order in orders:
    print(order.user.email)   # OK — already joinedloaded above
    for item in order.items:  # OK — already selectinloaded above
        print(item.product_id)
```

### 3.2 Django — select_related vs prefetch_related

```python
# select_related — SQL JOIN; for FK and OneToOne (single related object)
orders = Order.objects.select_related("user", "user__profile").filter(status="pending")

# prefetch_related — separate query with WHERE IN; for ManyToMany and reverse FK
orders = Order.objects.prefetch_related(
    "items",                      # reverse FK: ORDER_items
    "items__product",             # follow through to product
).select_related("user")

# Annotations to avoid COUNT N+1
from django.db.models import Count
users = User.objects.annotate(order_count=Count("orders")).filter(is_active=True)
# Now user.order_count is available without extra queries
```

---
