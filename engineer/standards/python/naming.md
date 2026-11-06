## 10. NAMING CONVENTIONS

### 10.1 Complete Reference

| Construct | Style | Example | Notes |
|-----------|-------|---------|-------|
| Package | `lowercase` | `mypackage` | No underscores preferred |
| Module | `lower_with_underscores` | `user_service.py` | Short, descriptive |
| Class | `CapWords` | `UserService` | Acronyms ALL CAPS: `HTTPClient` |
| Exception | `CapWords` + `Error` | `UserNotFoundError` | Or Warning if not an error |
| Type variable | `CapWords`, short | `T`, `KT_contra` | `_co`/`_contra` for variance |
| Function | `lower_with_underscores` | `get_active_users` | Verb-noun |
| Method (instance) | `lower_with_underscores` | `calculate_total` | First arg: self |
| Method (class) | `lower_with_underscores` | `from_dict` | First arg: cls |
| Method (static) | `lower_with_underscores` | `validate_email` | No implicit arg |
| Module constant | `UPPER_CASE` | `MAX_RETRIES = 3` | |
| Instance variable | `lower_with_underscores` | `self.user_id` | |
| Private method/var | `_name` | `_validate_token` | Single underscore |
| Name-mangled | `__name` | `self.__secret` | Use sparingly |
| Dunder | `__name__` | `__init__`, `__all__` | Never invent new ones |
| TypeAlias (3.10+) | `CapWords` | `UserId: TypeAlias = int` | |
| type stmt (3.12+) | `CapWords` | `type UserId = int` | |

### 10.2 Names to Absolutely Avoid

```python
# Never as single-char variable names:
l   # Indistinguishable from 1 in many fonts
O   # Indistinguishable from 0
I   # Indistinguishable from 1 or l

# Never shadow built-ins:
list = []       # Destroys built-in list for this scope
dict = {}
type = "user"   # Shadows built-in type — extremely common mistake
id = 42         # Shadows built-in id
input = ...
filter = ...
map = ...
next = ...
min = ...
max = ...

# Keyword clash — trailing underscore is correct resolution:
class_ = MyClass    # Better than clss
type_ = "user"      # Better than typ
lambda_ = 0.01      # Better than lam
```
