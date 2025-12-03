# Security Model

## 1. Overview

Security is a top priority due to the sensitive nature of scraping a public‑utility environment.  
This document describes authentication, data protection, and access control.

---

## 2. Authentication

### JWT Access Tokens

- Short-lived tokens for API access
- Used for user authentication
- Signed using HS256
- Short-lived (30 minutes recommended)
- Stored in **HttpOnly cookies** (cannot be accessed by JavaScript)

### Why HttpOnly?

- Protects against XSS
- Prevents JavaScript theft of tokens
- Enforces server-side validation

---

## 3. Password Security

- Passwords hashed using SHA-256
- Stored in environment variables
- Never committed to repo
- Use hashed passwords if desired (bcrypt)

---

## 4. Route Protection

Each protected route uses:

```text
Depends(get_current_user)
```

If authentication fails:

- Token rejected
- User redirected to login

---

## 5. Secure Deployment

Best practice:

- Deploy behind Cloudflare Access
- Use HTTPS exclusively
- Avoid exposing API publicly
- Restrict access by identity/email
- Rate-limit if required

---

## 6. Data Protection

- Annotated PDFs stored only locally
- No remote storage unless explicitly configured
- Logs should avoid sensitive content
