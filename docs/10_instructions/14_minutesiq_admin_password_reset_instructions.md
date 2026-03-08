# MinutesIQ -- Admin Password Reset (Beta Support Feature)

## Objective

Implement an **Admin Password Reset capability** for MinutesIQ to
support users during the beta phase.

This feature must **NOT replace or disable the existing SendGrid
password reset workflow**.\
Instead, it should exist as an **additional fallback option** when email
delivery is unavailable (for example when corporate email systems block
SendGrid messages).

The system must therefore support **two password reset paths**:

1.  **Standard Reset (Existing -- SendGrid)**
    - User requests password reset
    - Reset email is sent via SendGrid
    - User resets password via secure token link
2.  **Admin Reset (New -- Fallback)**
    - Admin generates a temporary password
    - Temporary password is manually provided to the user
    - User logs in and is forced to change their password

The existing SendGrid functionality must remain **fully operational and
unchanged.**

---

## Feature Requirements

## 1. Admin Reset Endpoint

Create a protected endpoint allowing administrators to reset a user's
password.

### Example Route

POST /admin/reset-user-password

### Authentication

This endpoint must be:

- Protected by authentication
- Restricted to **admin users only**

Use the existing authentication dependency used for protected routes.

Example:

Depends(get_current_user)\
Depends(require_admin)

---

## 2. Request Payload

The request should include the user identifier.

Example:

``` json
{
  "email": "user@example.com"
}
```

---

## 3. Reset Process

The endpoint should perform the following steps.

## Step 1 -- Locate the user

Query the database using the provided email.

If the user does not exist:

Return HTTP 404

---

## Step 2 -- Generate a secure temporary password

Requirements:

- Minimum length: **12 characters**
- Include **uppercase, lowercase, numbers, and symbols**
- Use a **cryptographically secure random generator**

Example approach:

secrets.token_urlsafe()

---

## Step 3 -- Hash the temporary password

Use the **existing password hashing utility** already used during
registration.

Possible implementations include:

bcrypt\
passlib

---

## Step 4 -- Update the user password

Update the stored password hash in the database.

Example logic:

UPDATE users SET password_hash = `<new hash>`{=html} WHERE email =
`<email>`{=html};

---

## Step 5 -- Flag user to force password change

Add or update a field such as:

force_password_change = TRUE

This ensures the user must set a new password after login.

If the field does not exist, add it to the user model.

---

## Step 6 -- Return the temporary password

Return the generated temporary password in the API response.

Example response:

``` json
{
  "message": "Temporary password generated",
  "temporary_password": "Ab3$k29L!xP"
}
```

The administrator will manually provide this password to the user.

---

## 4. Force Password Change After Login

If:

force_password_change == TRUE

Then after login the user must be redirected to:

/change-password

The user must not be allowed to access the dashboard until the password
is changed.

---

## 5. Change Password Endpoint

Create a route:

POST /change-password

Required inputs:

current_password\
new_password\
confirm_password

Validation requirements:

- Current password must match the stored password
- New passwords must match each other
- Enforce existing password strength rules

On success:

force_password_change = FALSE

---

## 6. Logging

Log all admin resets for audit purposes.

Example log entry:

Admin password reset performed\
User: `user@example.com\`
Admin: `admin@example.com\`
Timestamp: `<timestamp>`{=html}

---

## 7. Security Considerations

- Endpoint must be **admin-only**
- Temporary passwords must **never be logged**
- Passwords must always be **stored as hashes**
- Use **secure random generation**
- Apply existing **rate limiting** if available

---

## 8. Important Constraints

The following must remain **unchanged**:

- SendGrid password reset workflow
- Existing reset token logic
- Existing authentication architecture

This feature is **an additional fallback mechanism only**, not a
replacement.

---

## 9. Summary

After implementation, the system will support two password recovery
methods.

  | Reset Method   | Trigger        | Delivery            |
  | -------------- | -------------- | ------------------- |
  | SendGrid Reset | User request   | Email               |
  | Admin Reset    | Admin action   | Temporary password  |

This ensures password recovery is possible even when email delivery
fails during the beta phase.
