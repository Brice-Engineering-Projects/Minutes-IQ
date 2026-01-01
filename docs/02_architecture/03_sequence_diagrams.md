# 🔄 Sequence Diagrams — Core Application Flows

## Purpose
This document provides **sequence diagrams in Markdown** to describe how major application flows behave.

These diagrams:
- Are implementation-agnostic
- Serve as shared mental models
- Reduce ambiguity before coding
- Can be rendered by GitHub using Mermaid

---

## 1. User Registration (Authorization Code Gated)

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Web UI
    participant API as FastAPI
    participant DB as Database

    U->>UI: Open /register
    UI->>API: Submit email, password, auth_code
    API->>DB: Validate auth_code
    DB-->>API: auth_code valid

    API->>DB: Check email uniqueness
    DB-->>API: email not found

    API->>API: Hash password (bcrypt)
    API->>DB: Create user + profile
    API->>DB: Invalidate or decrement auth_code
    API-->>UI: Registration success
```

---

## 2. Login & Session Establishment

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Web UI
    participant API as FastAPI
    participant DB as Database

    U->>UI: Submit login credentials
    UI->>API: POST /login
    API->>DB: Lookup user by email
    DB-->>API: User record

    API->>API: Verify password (bcrypt)
    API->>API: Generate JWT
    API-->>UI: Set HttpOnly JWT cookie
    UI-->>U: Redirect to dashboard
```

---

## 3. Password Reset (Forgot Password)

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Web UI
    participant API as FastAPI
    participant DB as Database
    participant Mail as Email Service

    U->>UI: Submit email
    UI->>API: POST /forgot-password

    API->>API: Generate reset token
    API->>DB: Store hashed token + expiry
    API->>Mail: Send reset email
    API-->>UI: Generic success response
```

---

## 4. Password Reset (Token-Based)

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Web UI
    participant API as FastAPI
    participant DB as Database

    U->>UI: Open reset link
    UI->>API: POST /reset-password
    API->>DB: Validate reset token
    DB-->>API: Token valid

    API->>API: Hash new password
    API->>DB: Update password
    API->>DB: Mark token as used
    API-->>UI: Password reset success
```

---

## 5. Scraper Job Execution

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Web UI
    participant API as FastAPI
    participant SVC as Scraper Service
    participant FS as File System

    U->>UI: Submit scrape job
    UI->>API: POST /run-scraper
    API->>SVC: Start background task
    API-->>UI: Immediate response

    SVC->>FS: Download PDFs
    SVC->>FS: Annotate & package ZIP
    FS-->>SVC: Files ready
```

---

## Design Notes

- No scraper results stored in DB
- JWT never exposed to JavaScript
- Email responses are intentionally vague
- Background jobs do not block UI

---

**Documentation Rule:**  
> _If behavior is not shown here, it is undefined._
