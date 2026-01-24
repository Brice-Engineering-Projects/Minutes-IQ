# 🔐 Authentication Routes — Pseudocode & Flow Specification

## Purpose
This document defines the **authentication-related routes** for the FastAPI application using **pseudocode and flow descriptions only**.

It is intentionally **non-code** and serves as:
- An implementation guide
- A shared contract for behavior
- A guardrail against scope creep

---

## Design Constraints

- Email + password authentication
- bcrypt for password hashing
- JWT stored in HttpOnly cookies
- Registration gated by 6-digit authorization code
- Password reset via email token
- No external identity providers

---

## Route: POST /register

### Intent
Allow a user to self-register **only if** they possess a valid authorization code.

### Input
- email
- password
- auth_code (6 digits)

### Pseudocode
```
IF auth_code is invalid OR inactive:
    reject with generic error

IF email already exists:
    reject with generic error

IF password fails strength rules:
    reject with validation error

hash password using bcrypt
create user record (is_active = true, is_admin = false)
create empty profile record
invalidate or decrement auth_code if single-use
return success response
```

---

## Route: POST /login

### Intent
Authenticate user and issue session token.

### Input
- email
- password

### Pseudocode
```
lookup user by email

IF user not found OR inactive:
    reject with generic error

IF bcrypt verification fails:
    reject with generic error

generate JWT (short-lived)
set JWT in HttpOnly cookie
return redirect to dashboard
```

---

## Route: POST /logout

### Intent
Terminate user session.

### Pseudocode
```
clear JWT cookie
redirect to login page
```

---

## Route: POST /forgot-password

### Intent
Initiate password reset without revealing account existence.

### Input
- email

### Pseudocode
```
ALWAYS return generic success message

IF email exists:
    generate random reset token
    hash token before storage
    store token with expiration
    send reset email
```

---

## Route: POST /reset-password

### Intent
Allow user to set a new password using a one-time token.

### Input
- reset_token
- new_password

### Pseudocode
```
lookup reset token hash

IF token not found OR expired OR used:
    reject with error

IF new_password fails strength rules:
    reject

hash new password
update user password
mark reset token as used
invalidate all active sessions
return success response
```

---

## Security Guarantees

- No plaintext passwords
- No token reuse
- No account enumeration
- No client-side JWT access
- Rate-limited auth routes

---

**Implementation Rule:**  
> _Behavior must match this document exactly unless explicitly revised._
