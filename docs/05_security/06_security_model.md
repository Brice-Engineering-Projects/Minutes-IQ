# 🔐 Security Model (v1)

This document defines the **security model** for the JEA Web Scraper application.
It is an **authoritative design artifact** and is intentionally aligned with the
database schema, authentication design, and operational constraints.

---

## 1. Scope & Threat Model

### In Scope
- Unauthorized access to application features
- Improper access to other users’ data
- Accidental or improper configuration changes
- Credential compromise via improper storage

### Out of Scope (v1)
- Anonymous or public access
- Multi-factor authentication (MFA)
- OAuth / external SSO providers
- Public APIs or API keys
- Zero-trust networking or perimeter security

The application assumes a **small, explicitly authorized user base**.

---

## 2. Identity Model

- Each human user is represented by exactly one row in `users`
- `users` is the canonical identity table
- Human-readable metadata is stored in `profiles`
- Identity records are not silently deleted
- Deactivation is preferred over deletion

---

## 3. Authentication Model

### Supported Methods (v1)
- Local authentication only (username/email + password)

### Architecture
- Authentication mechanisms are abstracted via `auth_provider`
- Credentials are stored in `auth_credentials`
- Passwords are stored **only as bcrypt hashes**
- Plaintext passwords are never stored or logged

### Authentication Flow
1. User submits credentials
2. Credentials are validated against `auth_credentials`
3. On success, a signed JWT is issued
4. JWT is required for all protected endpoints

### Token Strategy
- JWT-based and stateless
- Signed using a server-side secret
- Short-lived access tokens
- Logout is client-side (token discard)

---

## 4. Authorization Model (RBAC)

### Role-Based Access Control
- Authorization is strictly role-based
- Each user has **exactly one role** in v1
- Roles map to permissions via `role_permission`
- Permissions represent discrete system capabilities

### Design Decision
Single-role-per-user is **intentional for v1**.

The schema allows migration to multi-role-per-user in the future
without breaking existing data or APIs.

---

## 5. Access Boundaries

### User-Scoped Data
Users may access **only their own**:
- Profile data
- Saved searches
- Saved search sources
- Saved search keywords
- Client favorites

### Global Read-Only Data
All authenticated users may read:
- Clients
- Client sources
- Keywords

### Admin-Only Operations
Only users with an administrative role may:
- Create or modify clients
- Create or modify client sources
- Manage keyword pools
- Assign roles to users
- Seed authentication providers

---

## 6. Data Protection & Secrets Handling

- Passwords are hashed with bcrypt
- Hashing cost is centrally configured
- JWT signing secrets are stored in environment variables
- Secrets are never committed to source control
- Database never stores plaintext secrets

---

## 7. Input Validation & Injection Defense

- All external input is validated at API boundaries
- Parameterized queries or ORM usage only
- No dynamic SQL from user input
- Pydantic models enforce schema correctness

---

## 8. Error Handling & Security Failures

### Authentication Failures
- Return generic error messages
- Do not reveal which credential was incorrect

### Authorization Failures
- Return HTTP 403
- Do not disclose permission structure

### Logging
- Security-relevant events are logged
- Sensitive values are never logged

---

## 9. Administrative Guardrails

- Destructive operations are restricted to admins
- Foreign keys use `RESTRICT`
- No silent cascading deletes
- Admin workflows must explicitly handle cleanup

---

## 10. Audit & Observability (v1-lite)

Planned (documentation-only for v1):
- Authentication attempts
- Administrative configuration changes
- Authorization failures

---

## 11. Non-Goals (v1)

- MFA
- OAuth / SSO
- Public APIs
- Anonymous access
- Automatic user provisioning

---

## Status

- **Version:** v1
- **Authorization model:** Role-based only
- **Roles per user:** Single (intentional)
- **Auth method:** Local only
- **Security posture:** Conservative, explicit, auditable
