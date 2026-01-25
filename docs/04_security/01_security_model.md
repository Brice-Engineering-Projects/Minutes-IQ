# Security Model

## 1. Overview

Security is a top priority due to the sensitive nature of scraping a public‑utility environment.  
This document describes authentication, data protection, and access control.

---

## 2. User Registration & Access Control

### Authorization Code System

**Purpose:** Control who can create accounts through invite-only registration.

**Key Features:**
- All new user registrations require a valid authorization code
- Only administrators can create authorization codes
- Codes are cryptographically secure (12 characters: uppercase + digits)
- Format: `XXXX-XXXX-XXXX` (e.g., `A3B7-9K2M-5PQ8`)

**Code Properties:**
- **Max Uses:** Configurable (1 = single-use, N = multi-use)
- **Expiration:** Optional expiration date (days from creation)
- **Revocation:** Admins can revoke codes at any time
- **Usage Tracking:** Full audit trail of who used each code

**Security Benefits:**
- Prevents unauthorized account creation
- Enables controlled user onboarding
- Provides accountability through usage tracking
- Allows time-limited invitations

**Code Generation:**
- Uses Python's `secrets` module (cryptographically secure)
- 12-character alphanumeric codes (62^12 = ~3.2 quintillion combinations)
- Normalized for comparison (case-insensitive, hyphen-flexible)

**Admin Operations:**
- `POST /admin/auth-codes` - Create new codes
- `GET /admin/auth-codes` - List codes (with filters: active, expired, used, revoked)
- `DELETE /admin/auth-codes/{id}` - Revoke a code
- `GET /admin/auth-codes/{id}/usage` - View usage history

---

## 3. Authentication

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

## 4. Password Security

- Passwords hashed using bcrypt (via passlib)
- Minimum 8 characters required
- Stored securely in database
- Never logged or exposed in responses
- Environment variables for admin bootstrap credentials

---

## 5. Route Protection

### User Authentication

Protected routes use dependency injection:

```python
Depends(get_current_user)
```

If authentication fails:
- Token rejected
- Returns `401 Unauthorized`

### Admin-Only Routes

Admin routes require elevated permissions:

```python
Depends(get_current_admin_user)
```

If user is not an admin:
- Returns `403 Forbidden`

**Admin Routes:**
- `/admin/auth-codes/*` - Authorization code management

---

## 6. Secure Deployment

Best practice:

- Deploy behind Cloudflare Access
- Use HTTPS exclusively
- Avoid exposing API publicly
- Restrict access by identity/email
- Rate-limit if required

---

## 7. Data Protection

- Annotated PDFs stored only locally
- No remote storage unless explicitly configured
- Logs should avoid sensitive content
