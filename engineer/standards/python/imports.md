## 3. IMPORTS

### 3.1 Grouping and Ordering

Four groups, blank line between each, in this exact order:

```python
"""Module docstring."""

from __future__ import annotations  # Must be first if used

__all__ = ["PublicClass", "public_function"]
__version__ = "1.0.0"

# Group 1: Standard library
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Group 2: Third-party
import httpx
import structlog
from pydantic import BaseModel, Field

# Group 3: Local application
from myapp.core.config import settings
from myapp.core.exceptions import NotFoundError
from myapp.models.user import User

# Group 4: Type-checking only (no circular import at runtime)
if TYPE_CHECKING:
    from myapp.services.auth import AuthService
    from myapp.repositories.user_repository import UserRepository
```

### 3.2 Import Style Rules

```python
# Correct — one module per line
import os
import sys

# Correct — multiple names from one module
from subprocess import PIPE, Popen
from typing import Any, Optional, Union

# WRONG — multiple modules on one line
import sys, os

# WRONG — star import
from os.path import *

# Exception: star imports in __init__.py ONLY for public API re-export
# when __all__ is explicitly declared in the source module.
```

### 3.3 Absolute vs Relative

```python
# Preferred — absolute imports
from mypackage.utils import helper
from mypackage.models.user import User

# Acceptable — explicit relative imports within a package
from . import sibling_module
from .sibling_module import SomeClass
from ..parent_module import ParentClass
```
