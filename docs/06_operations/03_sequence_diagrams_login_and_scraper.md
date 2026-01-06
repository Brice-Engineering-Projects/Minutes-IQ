# 🔁 Sequence Diagrams (Core Flows)
*JEA Meeting Minutes Scraper – Web Application*

This document captures the **authoritative interaction flows** for the two core user journeys:
1) Authentication (Login)
2) Scraper Execution

---

## 1️⃣ Login Flow

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

## 3️⃣ Scraper Execution Flow

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
