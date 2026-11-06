## SECTION 7 — DECIMAL HANDLING FOR MONETARY VALUES

```python
# NEVER use float for money — IEEE 754 float arithmetic loses precision
price: float = 0.1 + 0.2    # 0.30000000000000004 — WRONG

# ALWAYS use Decimal from Python's decimal module
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import Numeric

class Product(Base):
    # Numeric(precision, scale) — exact decimal storage in PostgreSQL
    price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),   # up to 99,999,999.99
        nullable=False,
    )


def calculate_total(price: Decimal, quantity: int, tax_rate: Decimal) -> Decimal:
    """Calculate order total with tax, rounded to 2 decimal places."""
    subtotal = price * quantity
    tax = subtotal * tax_rate
    total = subtotal + tax
    # Always round with an explicit rounding mode for financial calculations
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```
