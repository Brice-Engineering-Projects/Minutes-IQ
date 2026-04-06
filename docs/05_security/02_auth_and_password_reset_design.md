# 🔐 Authentication & Password Reset Design

## Scope
This document defines the authentication, registration, and password-reset flows for the FastAPI web application.

The design prioritizes:
- Security appropriate for internal tools
- User autonomy
- Owner-controlled access
- Minimal operational complexity

---

## Authentication Model

### Identity
- Email address (unique)
- Password (user-defined)

### Storage
- Passwords hashed (bcrypt or argon2)
- No plaintext credentials stored
- Secrets managed via environment variables

### Session Strategy
- JWT access tokens
- Stored in HttpOnly cookies
- Short-lived (e.g., 30–60 minutes)

---

## Registration Flow (Authorization Code Required)

### Steps
1. User navigates to `/register`
2. User enters:
   - Email
   - Password
   - Authorization code
3. Server validates:
   - Authorization code
   - Password strength
   - Email uniqueness
4. Account created
5. User redirected to login

### Failure Conditions
- Invalid or expired auth code
- Weak password
- Email already registered

---

## Login Flow

1. User submits email + password
2. Server verifies credentials
3. JWT issued
4. JWT stored in HttpOnly cookie
5. User redirected to dashboard

---

## Logout Flow

- JWT cookie cleared
- Client redirected to login
- No server-side state required

---

## Password Reset Flow

### Step 1: Request Reset
- User submits email
- Server:
  - Generates one-time reset token
  - Hashes token before storing
  - Sets expiration (e.g., 30 minutes)
- Reset link emailed to user

### Step 2: Reset Password
- User clicks reset link
- Token validated
- User enters new password
- Password hashed and stored
- Reset token invalidated

### Security Safeguards
- Tokens expire
- Tokens are single-use
- No indication if email exists
- Rate-limited endpoint

---

## Threat Model Considerations

| Threat | Mitigation |
|------|-----------|
| Credential theft | HttpOnly cookies |
| Token reuse | Expiration + rotation |
| Brute force | Rate limiting |
| XSS | HttpOnly cookies |
| Unauthorized signup | Auth code gating |

---

## Future Enhancements (Optional)

- Refresh tokens
- 2FA (TOTP)
- Admin user management UI
- Account lockout policies

---

**Design Philosophy:**  
> _Security proportional to risk, without enterprise bloat._
