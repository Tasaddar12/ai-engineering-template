### 12.10 Mutable Default Arguments

```python
# WRONG — the default list is SHARED across all calls
def append_item(item: str, target: list[str] = []) -> list[str]:
    target.append(item)
    return target

append_item("a")  # Returns ["a"]
append_item("b")  # Returns ["a", "b"] — NOT ["b"]!

# Correct — sentinel pattern
def append_item(
    item: str,
    target: list[str] | None = None,
) -> list[str]:
    if target is None:
        target = []
    target.append(item)
    return target

# Correct — dataclass field factory
from dataclasses import dataclass, field

@dataclass
class Config:
    allowed_hosts: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
```

---
