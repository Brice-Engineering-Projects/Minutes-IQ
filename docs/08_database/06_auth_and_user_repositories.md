# Authentication Architecture: Repositories and Services

**Audience:** Developers, reviewers, auditors  
**Purpose:** Explain how authentication-related data is accessed, verified, and used across production, diagnostics, and testing.

---

## Overview

Authentication in this system is intentionally split across **three distinct layers**:

1. **Database Repositories** – Responsible for retrieving facts from the database  
2. **Authentication Service** – Responsible for validating identity and credentials  
3. **Security Utilities** – Responsible for cryptographic operations (hashing, tokens)

This separation ensures:
- Clear responsibility boundaries
- Safer handling of sensitive data
- Easier testing and diagnostics
- Minimal blast radius for changes

---

## 1. `user_repository`

### Purpose

The `user_repository` is responsible for **retrieving user identity data** from the database.

It answers questions like:
- Does this user exist?
- What is the user’s unique identifier?
- What role is assigned to the user?

It does **not** handle authentication or security decisions.

---

### Responsibilities

- Query the `users` table
- Return identity-related fields (e.g., `user_id`, `username`, `email`, `role_id`)
- Provide a stable interface for other layers

---

### Non-Responsibilities

The `user_repository` must **not**:
- Verify passwords
- Issue tokens
- Apply permission logic
- Know about authentication providers
- Contain cryptographic logic

---

### Usage Contexts

#### Production
- Used after authentication to load user context
- Used by services that need user identity or role information

#### Diagnostic / Sanity Checks
- Can be safely called from scripts to verify database contents
- Used to confirm seeded users or schema correctness

#### Testing
- Can be mocked or pointed at a test database
- Enables deterministic testing of downstream logic

---

## 2. `auth_repository`

### Purpose

The `auth_repository` is responsible for **retrieving authentication-related data** from the database.

It answers questions like:
- What credentials exist for this user?
- Which authentication provider is active?
- Is this credential enabled?

This repository typically involves **joins** across:
- `users`
- `auth_credentials`
- `auth_provider`

---

### Responsibilities

- Retrieve credential records (e.g., hashed passwords)
- Filter by authentication provider (e.g., password-based login)
- Enforce database-level constraints such as `is_active`

---

### Non-Responsibilities

The `auth_repository` must **not**:
- Compare passwords
- Decide whether authentication succeeds
- Issue tokens or cookies
- Apply authorization or permission logic

It reports **facts only**.

---

### Usage Contexts

#### Production
- Called by the authentication service during login
- Acts as the single source of truth for credential lookup

#### Diagnostic / Sanity Checks
- Can be invoked from scripts to verify credential state
- Useful for confirming provider configuration or active credentials

#### Testing
- Can be mocked to simulate authentication scenarios
- Enables testing of auth flows without touching real secrets

---

## 3. `auth_service`

### Purpose

The `auth_service` orchestrates authentication by **combining data from repositories with security logic**.

It answers the question:
> “Is this person who they claim to be?”

---

### Responsibilities

- Call `auth_repository` to retrieve credential data
- Verify provided credentials using security utilities
- Handle authentication success or failure
- Produce an authenticated user context (or error)

---

### Non-Responsibilities

The `auth_service` must **not**:
- Execute SQL
- Know table names
- Manage database connections
- Store secrets directly

---

### Usage Contexts

#### Production
- Used by login routes and authentication dependencies
- Central point for enforcing authentication behavior

#### Diagnostic / Sanity Checks
- Rarely used directly
- Diagnostics should prefer repositories to avoid side effects

#### Testing
- Tested using mocked repositories
- Allows testing of authentication logic independently of the database

---

## 4. Security Utilities (Context)

Security utilities (e.g., password hashing, token creation) are **pure functions** used by the `auth_service`.

They:
- Perform cryptographic operations
- Have no database knowledge
- Are easily unit-testable

---

## Layer Interaction Summary

```text
HTTP Request
    ↓
Auth Route
    ↓
Auth Service
    ↓
Auth Repository  ──→ Database
    ↓
Security Utilities
