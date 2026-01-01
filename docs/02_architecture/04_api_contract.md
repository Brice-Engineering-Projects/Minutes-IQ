# 📡 API Contract — JEA Municipal Intelligence Dashboard

## Purpose
Defines the public-facing API behavior for the FastAPI application.
This document is **authoritative** for route behavior, inputs, outputs, and auth requirements.

---

## Authentication Routes

### POST /register
Auth Required: ❌

**Input**
- email
- password
- auth_code

**Responses**
- 201 Created
- 400 Validation error
- 403 Invalid authorization code

---

### POST /login
Auth Required: ❌

**Input**
- email
- password

**Responses**
- 200 OK (JWT cookie set)
- 401 Invalid credentials

---

### POST /logout
Auth Required: ✔

**Responses**
- 204 No Content

---

### POST /forgot-password
Auth Required: ❌

**Input**
- email

**Responses**
- 200 OK (always generic)

---

### POST /reset-password
Auth Required: ❌

**Input**
- token
- new_password

**Responses**
- 200 OK
- 400 Invalid or expired token

---

## Core Application Routes

### GET /dashboard
Auth Required: ✔

Returns dashboard UI.

---

### POST /run-scraper
Auth Required: ✔

**Input**
- selected_clients
- selected_keywords
- date_range

**Responses**
- 202 Accepted (job started)

---

### GET /downloads
Auth Required: ✔

Returns list of downloadable artifacts.

---

### GET /download/{filename}
Auth Required: ✔

**Responses**
- 200 File stream
- 404 Not found

---

**Contract Rule:**  
> _If it’s not documented here, it’s not a supported API._
