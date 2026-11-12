# Async Patterns — Enterprise Standard

**Applies to:** Python services with background processing, event-driven workflows, or distributed tasks.
**Stack:** Celery (heavy) / ARQ (lightweight) / asyncio native.

---

## SECTION 1 — TASK QUEUE (CELERY)

### Setup

```python
# app/workers/celery_app.py
from celery import Celery

celery_app = Celery("myapp")
celery_app.config_from_object({
    "broker_url": settings.redis_url,
    "result_backend": settings.redis_url,
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "task_acks_late": True,           # re-deliver if worker crashes mid-task
    "worker_prefetch_multiplier": 1,  # fair scheduling
    "task_reject_on_worker_lost": True,
})
```

### Task Definition

```python
# app/workers/tasks.py
from app.workers.celery_app import celery_app

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def send_welcome_email(self, user_id: int) -> None:
    """Send welcome email. Retries on transient failures."""
    try:
        user = get_user_sync(user_id)
        email_service.send(to=user.email, template="welcome")
    except TransientError as exc:
        raise self.retry(exc=exc)
```

---

## SECTION 2 — RETRY STRATEGIES

### Retry Rules

| Rule | Rationale |
|------|-----------|
| Always set `max_retries` | Prevent infinite retry loops |
| Use exponential backoff | Avoid thundering herd on recovery |
| Add jitter for high-volume tasks | `countdown = backoff + random.uniform(0, 1)` |
| Log every retry with attempt number | Observability |
| Set `task_time_limit` and `task_soft_time_limit` | Kill stuck tasks |

---

## SECTION 3 — IDEMPOTENCY

Every async task MUST be idempotent — safe to execute multiple times with the same input.

### Idempotency Patterns

- **Idempotency key:** Store task ID + result; return cached result on replay.
- **Database constraints:** Use unique constraints to prevent duplicate inserts.

---

## SECTION 4 — DEAD LETTER QUEUE (DLQ)

Tasks that exhaust retries must not be silently dropped.

```python
@celery_app.task(bind=True, max_retries=3)
def risky_task(self, data: dict) -> None:
    try:
        do_work(data)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            # Send to DLQ for manual inspection
            dead_letter_queue.publish(task="risky_task", data=data, error=str(exc))
            logger.error("task_exhausted_retries", task="risky_task", data=data)
            return
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

---

## SECTION 5 — EVENT-DRIVEN ARCHITECTURE

### Domain Events

```python
# app/events/base.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass(frozen=True)
class DomainEvent:
    """Base for all domain events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class UserRegistered(DomainEvent):
    user_id: int = 0
    email: str = ""


@dataclass(frozen=True)
class OrderCompleted(DomainEvent):
    order_id: int = 0
    total: str = "0"  # Decimal as string for serialization
```

### Event Bus (Simple In-Process)

```python
# app/events/bus.py
from collections import defaultdict
from collections.abc import Callable

_handlers: dict[type, list[Callable]] = defaultdict(list)


def subscribe(event_type: type, handler: Callable) -> None:
    """Register a handler for an event type."""
    _handlers[event_type].append(handler)


async def publish(event: DomainEvent) -> None:
    """Dispatch event to all registered handlers."""
    for handler in _handlers[type(event)]:
        await handler(event)
```


## SECTION 6 — ASYNC TASK PATTERNS (ARQ — Lightweight Alternative)

```python
# app/workers/arq_tasks.py
from arq import create_pool
from arq.connections import RedisSettings

async def send_notification(ctx: dict, user_id: int, message: str) -> None:
    """ARQ task — async-native, no Celery overhead."""
    await notification_service.send(user_id, message)


class WorkerSettings:
    functions = [send_notification]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300
```

---

## SECTION 7 — RULES

| Rule | Rationale |
|------|-----------|
| Every task must be idempotent | At-least-once delivery is the norm |
| Never pass ORM objects to tasks | Serialize IDs; re-fetch inside task |
| Set `task_time_limit` on all tasks | Prevent zombie workers |
| Log task start, completion, and failure | Observability |
| Use separate queues for priority levels | Critical tasks don't wait behind bulk jobs |
| DLQ for exhausted retries | Never silently drop failed work |
| Domain events decouple services | Publisher doesn't know about subscribers |
