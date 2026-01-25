# 🔌 API Contract
*JEA Meeting Minutes Scraper – Web Application*

This document defines the **stable API contract** for the JEA web application.
It serves as an internal agreement describing routes, authentication requirements,
request/response formats, and side effects.

This API is **private** and **not intended for public consumption**.

---

## Authentication Overview

- Authentication is handled using **JWT tokens**
- Tokens are stored in **HttpOnly cookies**
- All protected routes enforce authentication via dependency injection
- Unauthorized access returns `401 Unauthorized`

---

## Auth Endpoints

### POST /auth/register

**Purpose**
Register a new user account using an authorization code.

**Authentication**
❌ Not required

**Request Body**
```json
{
  "username": "string",
  "email": "string",
  "password": "string (min 8 chars)",
  "auth_code": "string (format: XXXX-XXXX-XXXX)"
}
```

**Success Response**
- HTTP `201 Created`
```json
{
  "message": "User registered successfully",
  "user": {
    "user_id": 123,
    "username": "string",
    "email": "string",
    "role_id": 2
  }
}
```

**Failure Response**
- HTTP `400 Bad Request` - Invalid/expired/used authorization code
- HTTP `409 Conflict` - Username or email already exists
- HTTP `422 Unprocessable Entity` - Validation errors

**Side Effects**
- Creates new user account
- Creates password credentials
- Marks authorization code as used
- Records code usage history

---

### POST /auth/login

**Purpose**
Authenticate a user and establish a session.

**Authentication**
❌ Not required

**Request Body**
```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response**
- HTTP `302 Found` (redirect to `/dashboard`)
- Side effect: JWT cookie is set (HttpOnly)

**Failure Response**
- HTTP `401 Unauthorized`

**Side Effects**
- Creates authenticated session
- Issues short-lived JWT

---

### POST /auth/logout

**Purpose**
Terminate the user session.

**Authentication**
✅ Required

**Request Body**
None

**Success Response**
- HTTP `302 Found` (redirect to `/login`)
- JWT cookie cleared

**Side Effects**
- Session invalidated

---

### POST /auth/reset-request

**Purpose**
Initiate password reset flow.

**Authentication**
❌ Not required

**Request Body**
```json
{
  "email": "string"
}
```

**Success Response**
- HTTP `200 OK`
- Generic success message (no account enumeration)

**Failure Response**
- HTTP `200 OK` (email existence not disclosed)

**Side Effects**
- Generates single-use reset token
- Sends reset email via SendGrid

---

### POST /auth/reset-confirm

**Purpose**
Finalize password reset using token.

**Authentication**
❌ Not required

**Request Body**
```json
{
  "token": "string",
  "new_password": "string"
}
```

**Success Response**
- HTTP `200 OK`

**Failure Response**
- HTTP `400 Bad Request` (invalid or expired token)

**Side Effects**
- Password updated
- Reset token invalidated

---

## Admin Endpoints

### POST /admin/auth-codes

**Purpose**
Create a new authorization code for user registration.

**Authentication**
✅ Required (Admin only)

**Request Body**
```json
{
  "expires_in_days": 7,
  "max_uses": 1,
  "notes": "Optional description"
}
```

**Success Response**
- HTTP `201 Created`
```json
{
  "code_id": 123,
  "code": "ABCD1234EFGH",
  "code_formatted": "ABCD-1234-EFGH",
  "created_by": 1,
  "created_at": 1706000000,
  "expires_at": 1706604800,
  "max_uses": 1,
  "current_uses": 0,
  "is_active": true,
  "notes": "Optional description"
}
```

**Failure Response**
- HTTP `401 Unauthorized` - Not authenticated
- HTTP `403 Forbidden` - Not an admin user
- HTTP `422 Unprocessable Entity` - Validation errors

**Side Effects**
- Generates cryptographically secure code
- Stores code in database for validation

---

### GET /admin/auth-codes

**Purpose**
List authorization codes with filtering and pagination.

**Authentication**
✅ Required (Admin only)

**Query Parameters**
- `status_filter`: string (active, expired, used, revoked, all) - default: "active"
- `limit`: integer (max 100) - default: 100
- `offset`: integer - default: 0

**Success Response**
- HTTP `200 OK`
```json
{
  "codes": [
    {
      "code_id": 123,
      "code_masked": "ABCD-****-****",
      "created_at": 1706000000,
      "expires_at": 1706604800,
      "max_uses": 1,
      "current_uses": 0,
      "is_active": true,
      "notes": "Description"
    }
  ],
  "total": 42
}
```

**Failure Response**
- HTTP `401 Unauthorized` - Not authenticated
- HTTP `403 Forbidden` - Not an admin user

**Side Effects**
- None (read-only)

---

### DELETE /admin/auth-codes/{code_id}

**Purpose**
Revoke an authorization code (prevents further use).

**Authentication**
✅ Required (Admin only)

**Path Parameters**
- `code_id`: integer

**Success Response**
- HTTP `200 OK`
```json
{
  "message": "Authorization code revoked successfully",
  "code_id": 123
}
```

**Failure Response**
- HTTP `401 Unauthorized` - Not authenticated
- HTTP `403 Forbidden` - Not an admin user
- HTTP `404 Not Found` - Code doesn't exist

**Side Effects**
- Marks code as inactive (is_active = false)
- Code cannot be used for registration after revocation

---

### GET /admin/auth-codes/{code_id}/usage

**Purpose**
View usage history for a specific authorization code.

**Authentication**
✅ Required (Admin only)

**Path Parameters**
- `code_id`: integer

**Success Response**
- HTTP `200 OK`
```json
{
  "code_id": 123,
  "usage_history": [
    {
      "user_id": 456,
      "used_at": 1706000000,
      "username": "johndoe",
      "email": "john@example.com"
    }
  ],
  "total_uses": 1
}
```

**Failure Response**
- HTTP `401 Unauthorized` - Not authenticated
- HTTP `403 Forbidden` - Not an admin user

**Side Effects**
- None (read-only)

---

## Application Endpoints

### GET /dashboard

**Purpose**
Render main application dashboard.

**Authentication**
✅ Required

**Request Body**
None

**Success Response**
- HTTP `200 OK`
- HTML page rendered

---

### POST /run-scraper

**Purpose**
Trigger scraper execution in background.

**Authentication**
✅ Required

**Request Body**
None

**Success Response**
- HTTP `202 Accepted`
- Background task started

**Failure Response**
- HTTP `401 Unauthorized`
- HTTP `500 Internal Server Error`

**Side Effects**
- Launches scraper pipeline
- Generates annotated PDFs on disk

---

## Download Endpoints

### GET /downloads

**Purpose**
List available annotated PDFs.

**Authentication**
✅ Required

**Request Body**
None

**Success Response**
- HTTP `200 OK`
- HTML page with file list

---

### GET /download/{filename}

**Purpose**
Download a specific annotated PDF.

**Authentication**
✅ Required

**Path Parameters**
- `filename`: string

**Success Response**
- HTTP `200 OK`
- File stream (PDF)

**Failure Response**
- HTTP `401 Unauthorized`
- HTTP `404 Not Found`

**Side Effects**
- None (read-only)

---

## Error Handling

| Status Code | Meaning |
|-----------|--------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted / background task started |
| 302 | Redirect |
| 400 | Invalid request |
| 401 | Unauthorized |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 409 | Conflict (duplicate resource) |
| 422 | Unprocessable Entity (validation error) |
| 500 | Internal server error |

---

## Contract Stability

- Route paths are considered stable
- Internal implementations may change
- Breaking changes require documentation update

---

## Status

**API Contract: Finalized**
