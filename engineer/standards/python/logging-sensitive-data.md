## SECTION 8 — WHAT NEVER TO LOG

These are security requirements — violations can cause compliance incidents.

| Never log | Reason | Alternative |
|---|---|---|
| Passwords, secret keys, API tokens | Credentials in logs = breach | Log that auth occurred, not the credential |
| Full credit card numbers | PCI DSS violation | Log last 4 digits only: `card_last4=card[-4:]` |
| Full SSN / national ID | PII / GDPR | Log presence/absence, not value |
| JWT token contents | Token is a credential | Log `token_type`, not the token itself |
| Email addresses in body | GDPR data minimisation | Log `user_id` instead |
| Full request body | May contain PII or credentials | Log specific safe fields only |
| Full response body from external APIs | May contain sensitive data + bloat | Log status code and duration only |
| Database connection strings | Contains credentials | Log only the host portion |
