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
| 202 | Accepted / background task started |
| 302 | Redirect |
| 400 | Invalid request |
| 401 | Unauthorized |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Contract Stability

- Route paths are considered stable
- Internal implementations may change
- Breaking changes require documentation update

---

## Status

**API Contract: Finalized**
