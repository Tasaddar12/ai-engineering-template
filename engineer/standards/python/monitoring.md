## SECTION 3 — CUSTOM SPANS

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


async def process_order(order_id: int) -> Order:
    with tracer.start_as_current_span("process_order", attributes={"order.id": order_id}) as span:
        order = await order_repo.get(order_id)
        if not order:
            span.set_status(trace.StatusCode.ERROR, "Order not found")
            raise NotFoundError("Order", order_id)

        span.add_event("payment_started")
        await payment_service.charge(order)
        span.add_event("payment_completed")

        return order
```

---

## SECTION 4 — METRICS PATTERNS

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Counter — things that only go up
request_counter = meter.create_counter(
    "http.requests.total",
    description="Total HTTP requests",
)

# Histogram — measure distributions (latency, sizes)
request_duration = meter.create_histogram(
    "http.request.duration_ms",
    description="Request duration in milliseconds",
    unit="ms",
)

# UpDownCounter — things that go up and down (active connections, queue depth)
active_connections = meter.create_up_down_counter(
    "db.connections.active",
    description="Active database connections",
)
```

## SECTION 5 — STRUCTURED LOGS + TRACE CORRELATION

```python
# Inject trace_id into every log line
import structlog
from opentelemetry import trace


def add_trace_context(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


structlog.configure(
    processors=[
        add_trace_context,
        structlog.processors.JSONRenderer(),
    ]
)
```

---

## SECTION 6 — KEY METRICS TO TRACK (RED + USE)

### RED Method (request-driven services):

| Metric | What | Alert when |
|--------|------|------------|
| **R**ate | Requests per second | Sudden drop (service down) or spike (DDoS) |
| **E**rrors | Error rate (5xx / total) | > 1% sustained |
| **D**uration | p50, p95, p99 latency | p99 > SLO threshold |

### USE Method (resources):

| Metric | What | Alert when |
|--------|------|------------|
| **U**tilization | CPU/memory/disk % | > 80% sustained |
| **S**aturation | Queue depth, thread pool exhaustion | Growing unbounded |
| **E**rrors | Connection failures, OOM kills | Any occurrence |

---
