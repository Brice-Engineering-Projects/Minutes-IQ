# Password Reset & Credential Ownership Policy

## Purpose
This document defines responsibility boundaries for password management within the JEA Meeting Minutes Scraper application.

Once access is granted, **credential recovery becomes the user’s responsibility**, not the Admin’s.

---

## Policy Statement

- The Admin grants access to users
- Password resets are **self-service**
- The Admin does not reset passwords
- The Admin does not generate reset links
- The Admin does not receive reset notifications

---

## Reset Mechanism

**Method**
- Email-based password reset using SendGrid

**Flow**
1. User clicks "Forgot Password"
2. System generates a cryptographically secure, time-limited token
3. A reset link is emailed to the user
4. User sets a new password
5. Token is invalidated immediately

---

## Security Controls

- Tokens are:
  - Single-use
  - Short-lived (15–30 minutes)
  - Signed and verified server-side
- Passwords are:
  - Hashed (bcrypt / argon2)
  - Never emailed
  - Never logged
- Email delivery:
  - Sent only to the registered email address
  - No alternate recovery paths

---

## Admin Responsibilities

The Admin is responsible for:
- Maintaining the reset infrastructure
- Ensuring email service availability
- Disabling accounts if compromise is reported

The Admin is **not responsible** for:
- Forgotten passwords
- Expired reset links
- Email delivery failures
- User inbox management

---

## Governance Boundary

If a user loses access to their email:
- The Admin may revoke access
- The Admin does not recover credentials

---

## Status

**Password Reset Policy: Defined and Active**
