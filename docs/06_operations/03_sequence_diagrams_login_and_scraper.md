# 🔁 Sequence Diagrams (Core Flows)
*JEA Meeting Minutes Scraper – Web Application*

This document captures the **authoritative interaction flows** for the two core user journeys:
1) Authentication (Login)
2) Scraper Execution

---

## 1️⃣ Registration Flow (with Authorization Code)

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant A as FastAPI Auth
    participant AC as Auth Code Service
    participant US as User Service
    participant DB as Database

    U->>B: Enter username, email, password, auth code
    B->>A: POST /auth/register
    A->>AC: Validate authorization code
    alt Code invalid/expired/used
        AC-->>A: Validation failure
        A-->>B: 400 Bad Request
    else Code valid
        AC-->>A: Code valid
        A->>US: Create user account
        alt Username/email exists
            US-->>A: Duplicate error
            A-->>B: 409 Conflict
        else User created
            US->>DB: Insert user & credentials
            DB-->>US: User ID
            US-->>A: User data
            A->>AC: Mark code as used
            AC->>DB: Increment usage & record
            AC-->>A: Success
            A-->>B: 201 Created + User data
            B-->>U: Registration successful
        end
    end
```

**Notes**
- Authorization codes required for all registrations (controlled access)
- Codes can be single-use or multi-use (configurable by admin)
- Codes can have expiration dates
- Registration tracks which code was used by which user
- Failed registrations don't consume code usage

---

## 2️⃣ Login Flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant A as FastAPI Auth
    participant S as JWT Service

    U->>B: Enter username & password
    B->>A: POST /auth/login
    A->>S: Validate credentials
    alt Invalid credentials
        S-->>A: Auth failure
        A-->>B: 401 Unauthorized
    else Valid credentials
        S-->>A: JWT access token
        A-->>B: Set HttpOnly JWT cookie
        B-->>U: Redirect to /dashboard
    end
```

**Notes**
- JWT stored in **HttpOnly** cookie (no JS access)
- Short-lived access token
- Failed login returns `401` without revealing which field failed

---

## 3️⃣ Admin: Create Authorization Code Flow

```mermaid
sequenceDiagram
    participant A as Admin User
    participant B as Browser
    participant API as FastAPI Admin
    participant AC as Auth Code Service
    participant DB as Database

    A->>B: Create auth code (expires_in_days, max_uses, notes)
    B->>API: POST /admin/auth-codes
    API->>API: Verify admin role (JWT)
    alt Not admin
        API-->>B: 403 Forbidden
    else Is admin
        API->>AC: Generate & create code
        AC->>AC: Generate secure 12-char code
        AC->>DB: Insert code with metadata
        DB-->>AC: Code ID
        AC-->>API: Code data (formatted)
        API-->>B: 201 Created + Code details
        B-->>A: Display code to share
    end
```

**Notes**
- Only admin users can create authorization codes
- Codes are cryptographically secure (12 uppercase alphanumeric chars)
- Format: XXXX-XXXX-XXXX (e.g., A3B7-9K2M-5PQ8)
- Admins can set expiration (days) and usage limits
- Created codes are displayed once and should be saved/shared securely

---

## 4️⃣ Scraper Execution Flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant W as FastAPI Web
    participant BG as Background Task
    participant S as Scraper Service
    participant P as PDF Service

    U->>B: Click "Run Scraper"
    B->>W: POST /run-scraper
    W->>W: Verify JWT (dependency)
    alt Not authenticated
        W-->>B: 401 Unauthorized
    else Authenticated
        W->>BG: Launch background task
        BG->>S: Execute scraper
        S->>P: Generate annotated PDFs
        P-->>BG: Files written to disk
        BG-->>W: Task completed
        W-->>B: Success status
    end
```

**Notes**
- UI remains responsive (non-blocking)
- Long-running tasks handled asynchronously
- Outputs appear on the Downloads page upon completion

---

## ✅ Completion Criteria

This document is considered complete when:
- Authentication boundaries are explicit
- Background execution is non-blocking
- Failure paths are documented
- No implicit or undocumented steps remain
