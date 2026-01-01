# 📘 Rationale: Turso + Authorization Code Access Model

## Purpose
This document explains the architectural and cost rationale behind using **Turso** as the database and an **authorization-code–gated registration model** for the JEA / Municipal Meeting Intelligence Dashboard.

This rationale is intended for:
- Future maintainers
- Management review
- Justifying technical decisions if the project scales

---

## Why Turso?

### 1. Usage Profile
This application is:
- Used by a **small, trusted internal group**
- Read/write light
- Not latency-critical
- Not analytics-heavy

Turso (distributed SQLite) is well-matched to this profile.

### 2. Cost Control
- Near-zero cost at small scale
- No always-on database server
- No minimum monthly spend
- No operational overhead

> Scaling happens **only if business value is proven**.

### 3. Operational Simplicity
- SQLite-compatible
- Easy local ↔ production parity
- Minimal DevOps burden
- Simple backups and migrations

### 4. Upgrade Path
If adoption grows:
- Migrate schema to Postgres
- Swap DB client at service layer
- No rewrite of business logic

---

## Why Authorization-Code–Gated Registration?

### Problem Being Solved
- Prevent unauthorized access
- Avoid manual account creation
- Maintain owner control
- Reduce admin overhead

### Solution
Users may:
- Create their **own account**
- Choose their **own password**
- Only if they possess a valid **authorization code**

### Benefits
- Lightweight access control
- No invite system complexity
- No external identity provider
- Easy to rotate or revoke

### How It Works (High Level)
1. Owner generates authorization code
2. Code shared manually with approved users
3. User enters code during registration
4. Code validated server-side
5. Account created if valid

---

## Why This Is the Right Tradeoff (Now)

| Concern | Decision |
|------|---------|
| Cost | Minimized |
| Security | Sufficient for internal use |
| Complexity | Intentionally low |
| Control | Retained by owner |
| Scalability | Deferred, not blocked |

---

## Future Alternatives (If Needed)
- Invite-token system
- Email-domain allowlisting
- SSO (Azure AD / Google Workspace)
- Role-based access control

---

**Guiding Principle:**  
> _Build for today’s risk profile, not tomorrow’s fantasy scale._
