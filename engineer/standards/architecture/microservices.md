# Microservices Patterns

**Applies to:** Teams running 2+ independently deployed Python services.

## 1. SERVICE BOUNDARY RULES

### When to Split

| Split when | Don't split when |
|-----------|-----------------|
| Different deployment cadences needed | Team has < 4 developers |
| Different scaling requirements (CPU vs I/O) | Shared database is acceptable |
| Different team ownership | Communication overhead exceeds benefit |
| Fault isolation required (payment must not crash catalog) | You're splitting by technical layer (API service, DB service) |

### Bounded Context Heuristic

A service owns ONE bounded context from Domain-Driven Design:
- **Order Service** — order lifecycle, cart, checkout
- **Payment Service** — charges, refunds, invoices
- **User Service** — registration, profile, auth
- **Notification Service** — email, SMS, push

**Anti-pattern:** A "shared" service that every other service depends on. That's a monolith with extra network hops.

## 2. INTER-SERVICE COMMUNICATION

### Synchronous (HTTP/gRPC)

```python
# app/clients/user_client.py
import httpx
from app.core.config import settings


class UserClient:
    """HTTP client for User Service."""

    def __init__(self) -> None:
        self.base_url = settings.user_service_url
        self.timeout = httpx.Timeout(5.0, connect=2.0)

    async def get_user(self, user_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/users/{user_id}",
                headers={"Authorization": f"Bearer {await get_service_token()}"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()["data"]
```

### When to use sync vs async communication

| Use synchronous (HTTP) | Use asynchronous (events/queues) |
|------------------------|----------------------------------|
| Need immediate response | Fire-and-forget |
| Query/read operations | State change notifications |
| Simple request-reply | Fan-out to multiple consumers |
| Low latency required | Eventual consistency acceptable |

### Asynchronous (Events)

```python
# Order Service publishes event
await event_bus.publish("order.completed", {
    "order_id": order.id,
    "user_id": order.user_id,
    "total": str(order.total),
})

# Notification Service subscribes
@event_handler("order.completed")
async def send_order_confirmation(event: dict) -> None:
    await email_service.send_template(
        to=event["user_id"],
        template="order_confirmation",
        context=event,
    )
```

## 3. API CONTRACTS

### Contract-First Design

Define the API contract BEFORE implementation:

### Versioning Between Services

- Internal APIs use header versioning: `Accept: application/vnd.myapp.v2+json`
- Breaking changes require a new version + migration period.
- Consumer services declare which version they depend on.
- Provider maintains N and N-1 versions simultaneously.

## 4. SHARED LIBRARIES

### What to Share

| Share | Don't share |
|-------|-------------|
| Auth middleware / token verification | Business logic |
| Logging configuration | Database models |
| Error response format | Service-specific schemas |
| Health check boilerplate | Domain entities |
| OpenTelemetry setup | Anything that creates coupling |

### Structure

```
packages/
├── aurigait-common/          ← Shared utilities
│   ├── src/aurigait_common/
│   │   ├── auth.py
│   │   ├── logging.py
│   │   ├── health.py
│   │   └── errors.py
│   └── pyproject.toml
└── aurigait-events/          ← Event schemas (shared contract)
    ├── src/aurigait_events/
    │   ├── order_events.py
    │   └── user_events.py
    └── pyproject.toml
```

**Rule:** Shared libraries must be versioned and published to internal registry. Never use git submodules or path dependencies in production.

## 6. DATA OWNERSHIP RULES

| Rule | Rationale |
|------|-----------|
| Each service owns its database | No shared databases between services |
| Services expose data via APIs, not DB access | Encapsulation — schema changes don't break consumers |
| Duplicate data is acceptable | Denormalize for autonomy; sync via events |
| Use eventual consistency where possible | Reduces coupling, improves availability |
| Saga pattern for distributed transactions | No distributed locks or 2PC |
