# 🛡️ Admin Control & Data Governance Policy

## Purpose
This document defines **who may modify what** within the application and explains **why strict admin control is required** for certain operations.

This policy exists to:
- Protect scraper stability
- Preserve trust in results
- Prevent accidental system breakage

---

## Roles

### Admin
- System owner / maintainer
- Responsible for data integrity
- Controls application configuration

### User
- Authorized internal user
- Consumer of data
- No system mutation rights

---

## Permission Matrix

| Action | Admin | User |
|-----|------|------|
| Register account | ✔ (via auth code) | ✔ |
| Login / logout | ✔ | ✔ |
| Edit own profile | ✔ | ✔ |
| Select favorite clients | ✔ | ✔ |
| Run scraper jobs | ✔ | ✔ |
| Add new client | ✔ | ❌ |
| Modify client sources | ✔ | ❌ |
| Enable / disable client | ✔ | ❌ |
| Rotate auth codes | ✔ | ❌ |
| View system logs | ✔ | ❌ |

---

## Why Client Creation Is Admin-Only

Scraping targets are **not generic inputs**.

Each client requires:
- Website structure validation
- PDF availability confirmation
- Pagination logic review
- Keyword coverage testing
- Failure-mode testing

Allowing unrestricted creation would:
- Break production jobs
- Create silent failures
- Undermine confidence
- Increase maintenance burden

---

## User Request Model (Non-Disruptive)

Users may:
- Request new clients via offline process
- Submit URLs for consideration
- Provide context for desired coverage

Admins:
- Test new clients in isolation
- Add sources incrementally
- Enable client only after validation

---

## Future Enhancements (Optional)

- Admin-only UI panel
- Staging vs production sources
- Client request workflow
- Audit trail for changes

---

**Governance Principle:**  
> _Stability beats flexibility in internal intelligence systems._
