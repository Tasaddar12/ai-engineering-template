## SECTION 5 — STRUCTURED FIELDS — CONSISTENCY ACROSS THOUSANDS OF LOGS

All log entries for a given event type must use identical field names. Inconsistent field names make log aggregation (Datadog, Splunk, CloudWatch Insights) impossible at scale.

```python
# CORRECT — structured, consistent, searchable
logger.info(
    "order_created",          # event name: snake_case, past-tense verb-noun
    entity="Order",
    entity_id=order.id,
    user_id=current_user.id,
    tenant_id=tenant_id,
    total_amount=order.total,
    item_count=len(order.items),
    duration_ms=round((time.monotonic() - start) * 1000, 2),
)

# WRONG — unstructured string; impossible to query in log aggregation
logger.info(f"Order {order.id} created by user {current_user.id} for ${order.total}")
```

### 5.2 Event Naming Convention

```
Pattern:  {entity}_{action}_{modifier}
Examples:
  user_created
  user_login_failed
  order_payment_processed
  cache_lookup_hit
  cache_lookup_miss
  retry_attempt_succeeded
  rate_limit_exceeded
  db_query_slow             # with duration_ms field
```

---
