# MinutesIQ -- Clarifications for Admin Password Reset Implementation

This document answers the implementation questions raised by the AI
coding assistant. These instructions apply to the **MinutesIQ project**,
which uses:

- **FastAPI**
- **Turso (libSQL / SQLite-compatible database)**
- Existing **SendGrid password reset workflow**

⚠️ Important:\
The **existing SendGrid password reset system must remain fully intact
and unchanged**.\
The admin reset feature is a **secondary fallback option only**.

---

## 1. Backend Entry Points (Auth / Admin Routes)

Authentication routes exist in the MinutesIQ auth module.

Recommended structure:

src/minutes_iq/ main.py auth/ routes.py admin_routes.py security.py
schemas.py dependencies.py

Existing authentication routes (login, register, SendGrid reset):

src/minutes_iq/auth/routes.py

Admin reset endpoint should be created in:

src/minutes_iq/auth/admin_routes.py

Register the router in main.py:

``` python
from minutes_iq.auth.admin_routes import router as admin_router

app.include_router(admin_router, prefix="/admin", tags=["admin"])
```

---

## 2. User Model Fields

The users table should use the following field names:

- email
- hashed_password

The password column must be:

hashed_password

Do not create alternate names such as:

password_hash

Example password update:

``` python
user.hashed_password = hash_password(temp_password)
```

---

## 3. Force Password Change Flag

A new column should be added if it does not already exist.

Column name:

force_password_change

Because Turso uses SQLite-compatible SQL, booleans are stored as
integers.

``` sql
ALTER TABLE users
ADD COLUMN force_password_change INTEGER DEFAULT 0;
```

Meaning:

0 = False\
1 = True

---

## 4. Login Enforcement Behavior

Login should **NOT fail** when the force flag is set.

Instead the login response must include:

``` json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "force_password_change": true
}
```

Frontend behavior:

If `force_password_change == true`, redirect the user to:

/change-password

The user must not access the dashboard until the password is changed.

---

## 5. Password Policy Utility

The password validation logic used during registration must be reused.

Expected location:

src/minutes_iq/auth/security.py

Example function:

validate_password_strength(password)

This validator must be used for:

- user registration
- password change
- admin password reset

Password policy must exist in **one place only**.

---

## 6. Audit Logging

For the beta phase, logging should use the existing application logger.

Example:

``` python
logger.info(
    "Admin password reset",
    extra={
        "admin": admin_user.email,
        "target_user": user.email
    }
)
```

Never log:

- temporary passwords
- password hashes

A dedicated audit table is **not required for beta**.

---

## 7. Rate Limiting

If a rate limiter already exists (for example slowapi), apply it to:

/change-password\
/admin/reset-user-password

Suggested limits:

change-password → 5 requests per minute\
admin-reset → 10 requests per hour

If the project does not currently use a limiter, it can be skipped
during beta.

---

## 8. Turso Database Considerations

MinutesIQ uses **Turso (libSQL)**.

Important characteristics:

- SQLite-compatible SQL
- Boolean values stored as integers
- Parameterized queries required
- No Postgres-specific syntax

Example query:

``` python
db.execute(
    "SELECT id, email, hashed_password, force_password_change FROM users WHERE email = ?",
    [email]
)
```

---

## 9. Admin Reset Workflow

Admin reset should follow this sequence:

1. Admin calls `/admin/reset-user-password`
2. Generate secure temporary password
3. Hash password
4. Update database
5. Set force_password_change = 1
6. Return temporary password to admin

Example SQL update:

``` sql
UPDATE users
SET hashed_password = ?, force_password_change = 1
WHERE email = ?;
```

---

## 10. Password Change Workflow

When the user sets a new password:

``` sql
UPDATE users
SET hashed_password = ?, force_password_change = 0
WHERE id = ?;
```

After successful update, user gains normal access.

---

## 11. Important Security Rules

Admin reset must:

- invalidate any existing password reset tokens
- never log temporary passwords
- use secure password generation
- hash passwords before storage

Example:

``` sql
DELETE FROM password_reset_tokens
WHERE user_id = ?;
```

---

## 12. Summary

MinutesIQ will support two password recovery methods.

| Method        | Trigger        | Delivery           |
| ------------- | -------------- | ------------------ |
| SendGrid Reset| User request   | Email              |
| Admin Reset   | Admin action   | Temporary password |

SendGrid reset remains the **primary mechanism**.

Admin reset exists **only as a fallback** when email delivery fails (for
example corporate filters blocking SendGrid).
