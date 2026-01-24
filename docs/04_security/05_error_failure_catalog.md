# ⚠️ Error & Failure Mode Catalog

## Purpose
Documents expected failures, user-facing behavior, and logging strategy.

---

## Authentication Errors

| Scenario | User Message | Logged |
|-------|-------------|--------|
| Invalid login | Invalid credentials | ✔ |
| Invalid auth code | Registration failed | ✔ |
| Expired reset token | Reset link expired | ✔ |

---

## Authorization Errors

| Scenario | User Message | Logged |
|-------|-------------|--------|
| No JWT | Please log in | ✔ |
| Expired JWT | Session expired | ✔ |
| Non-admin mutation | Unauthorized | ✔ |

---

## Scraper Failures

| Scenario | User Message | Logged |
|-------|-------------|--------|
| Source unreachable | Partial results | ✔ |
| PDF parse error | Skipped document | ✔ |
| Job timeout | Job incomplete | ✔ |

---

## System Errors

| Scenario | User Message | Logged |
|-------|-------------|--------|
| DB unavailable | Service unavailable | ✔ |
| File I/O error | Download unavailable | ✔ |

---

## Logging Rules

- No sensitive data logged
- Stack traces only in dev
- Job IDs included in logs

---

**Error Rule:**  
> _Fail safely, log clearly, expose minimally._
