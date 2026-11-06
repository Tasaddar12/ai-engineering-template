## Pydantic Schemas

```python
# app/schemas/user.py
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class UserBase(BaseModel):
    email: str
    name: str

class UserCreateRequest(UserBase):
    password: str = Field(min_length=8)

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)  # enables ORM mode

    id: int
    is_active: bool
    created_at: datetime

class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
```

---

## ANNOTATED DEPENDENCIES (Python 3.9+)

Define reusable dependency annotations at module level for cleaner route signatures:

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Define once in deps.py
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]

# Use cleanly in every route
@router.get("/orders/", response_model=OrderListResponse)
async def list_orders(
    db: DbSession,
    current_user: CurrentUser,
    page: int = 1,
) -> OrderListResponse:
    ...
```

---
