# Client & Keyword Management API

This document describes the API endpoints for managing clients (government agencies) and keywords used for filtering meeting minutes.

## Overview

The Client & Keyword Management system allows:
- **Admins** to manage clients, keywords, and their associations
- **Users** to view active clients, manage favorites, and see associated keywords

---

## Admin Endpoints

### Client Management

#### Create Client
**POST** `/admin/clients`

Create a new client (government agency to track).

**Authentication:** Admin required

**Request Body:**
```json
{
  "name": "City of Jacksonville",
  "description": "Municipal government of Jacksonville, FL",
  "website_url": "https://www.coj.net"
}
```

**Response:** `201 Created`
```json
{
  "client_id": 1,
  "name": "City of Jacksonville",
  "description": "Municipal government of Jacksonville, FL",
  "website_url": "https://www.coj.net",
  "is_active": true,
  "created_at": 1706198400,
  "created_by": 1,
  "updated_at": null,
  "keywords": null
}
```

**Validation Rules:**
- `name`: Required, 3-200 characters, must be unique
- `description`: Optional, max 1000 characters
- `website_url`: Optional, must start with http:// or https://, max 500 characters

---

#### List Clients
**GET** `/admin/clients`

List all clients with optional filtering and pagination.

**Authentication:** Admin required

**Query Parameters:**
- `is_active` (boolean, optional): Filter by active status
- `include_keywords` (boolean, optional): Include associated keywords
- `limit` (integer, optional, default=100): Max results
- `offset` (integer, optional, default=0): Skip results

**Example:**
```bash
GET /admin/clients?is_active=true&include_keywords=true&limit=50&offset=0
```

**Response:** `200 OK`
```json
{
  "clients": [
    {
      "client_id": 1,
      "name": "JEA",
      "description": "Jacksonville Electric Authority",
      "website_url": "https://www.jea.com",
      "is_active": true,
      "created_at": 1706198400,
      "created_by": 1,
      "updated_at": null,
      "keywords": [
        {
          "keyword_id": 5,
          "keyword": "water",
          "category": "Utilities",
          "description": "Water service related",
          "is_active": true,
          "created_at": 1706198400,
          "created_by": 1
        }
      ]
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

#### Get Client Details
**GET** `/admin/clients/{client_id}`

Get a specific client by ID with its keywords.

**Authentication:** Admin required

**Response:** `200 OK`
```json
{
  "client_id": 1,
  "name": "JEA",
  "description": "Jacksonville Electric Authority",
  "website_url": "https://www.jea.com",
  "is_active": true,
  "created_at": 1706198400,
  "created_by": 1,
  "updated_at": null,
  "keywords": [
    {
      "keyword_id": 5,
      "keyword": "water",
      "category": "Utilities",
      "description": null,
      "is_active": true,
      "created_at": 1706198400,
      "created_by": 1
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Client does not exist

---

#### Update Client
**PUT** `/admin/clients/{client_id}`

Update a client's information.

**Authentication:** Admin required

**Request Body:** (all fields optional)
```json
{
  "name": "JEA - Jacksonville Electric Authority",
  "description": "Updated description",
  "website_url": "https://www.jea.com",
  "is_active": false
}
```

**Response:** `200 OK`
```json
{
  "client_id": 1,
  "name": "JEA - Jacksonville Electric Authority",
  "description": "Updated description",
  "website_url": "https://www.jea.com",
  "is_active": false,
  "created_at": 1706198400,
  "created_by": 1,
  "updated_at": 1706284800,
  "keywords": null
}
```

**Error Responses:**
- `404 Not Found`: Client does not exist
- `400 Bad Request`: Validation error (e.g., duplicate name)

---

#### Delete Client
**DELETE** `/admin/clients/{client_id}`

Soft delete a client (sets `is_active` to false).

**Authentication:** Admin required

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found`: Client does not exist

---

### Client-Keyword Association

#### Add Keyword to Client
**POST** `/admin/clients/{client_id}/keywords`

Associate a keyword with a client.

**Authentication:** Admin required

**Request Body:**
```json
{
  "keyword_id": 5
}
```

**Response:** `201 Created`
```json
{
  "message": "Keyword added to client successfully"
}
```

**Error Responses:**
- `404 Not Found`: Client or keyword does not exist
- `400 Bad Request`: Keyword already associated, or client/keyword is inactive

---

#### Remove Keyword from Client
**DELETE** `/admin/clients/{client_id}/keywords/{keyword_id}`

Remove a keyword association from a client.

**Authentication:** Admin required

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found`: Association does not exist

---

#### Get Client Keywords
**GET** `/admin/clients/{client_id}/keywords`

Get all keywords associated with a client.

**Authentication:** Admin required

**Response:** `200 OK`
```json
{
  "client_id": 1,
  "keywords": [
    {
      "keyword_id": 5,
      "keyword": "water",
      "category": "Utilities",
      "description": null,
      "is_active": true,
      "created_at": 1706198400,
      "created_by": 1
    },
    {
      "keyword_id": 12,
      "keyword": "infrastructure",
      "category": "Public Works",
      "description": "Infrastructure projects",
      "is_active": true,
      "created_at": 1706198400,
      "created_by": 1
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Client does not exist

---

### Keyword Management

#### Create Keyword
**POST** `/admin/keywords`

Create a new keyword for filtering meeting minutes.

**Authentication:** Admin required

**Request Body:**
```json
{
  "keyword": "infrastructure",
  "category": "Public Works",
  "description": "Related to roads, bridges, and public facilities"
}
```

**Response:** `201 Created`
```json
{
  "keyword_id": 12,
  "keyword": "infrastructure",
  "category": "Public Works",
  "description": "Related to roads, bridges, and public facilities",
  "is_active": true,
  "created_at": 1706198400,
  "created_by": 1
}
```

**Validation Rules:**
- `keyword`: Required, 2-100 characters, must be unique
- `category`: Optional, max 50 characters
- `description`: Optional, max 500 characters

---

#### List Keywords
**GET** `/admin/keywords`

List all keywords with optional filtering and pagination.

**Authentication:** Admin required

**Query Parameters:**
- `is_active` (boolean, optional): Filter by active status
- `category` (string, optional): Filter by category
- `limit` (integer, optional, default=100): Max results
- `offset` (integer, optional, default=0): Skip results

**Example:**
```bash
GET /admin/keywords?category=Utilities&is_active=true&limit=50
```

**Response:** `200 OK`
```json
{
  "keywords": [
    {
      "keyword_id": 5,
      "keyword": "water",
      "category": "Utilities",
      "description": "Water service related",
      "is_active": true,
      "created_at": 1706198400,
      "created_by": 1
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

#### Search Keywords
**GET** `/admin/keywords/search`

Search for keywords by partial text match.

**Authentication:** Admin required

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (integer, optional, default=50): Max results

**Example:**
```bash
GET /admin/keywords/search?q=water&limit=10
```

**Response:** `200 OK`
```json
{
  "query": "water",
  "results": [
    {
      "keyword_id": 5,
      "keyword": "water",
      "category": "Utilities",
      "description": null,
      "is_active": true,
      "created_at": 1706198400,
      "created_by": 1
    },
    {
      "keyword_id": 6,
      "keyword": "wastewater",
      "category": "Utilities",
      "description": null,
      "is_active": true,
      "created_at": 1706198400,
      "created_by": 1
    }
  ]
}
```

---

#### Get Keyword Suggestions
**GET** `/admin/keywords/suggest`

Get keyword suggestions for autocomplete (prioritizes keywords that start with query).

**Authentication:** Admin required

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (integer, optional, default=10): Max suggestions

**Example:**
```bash
GET /admin/keywords/suggest?q=infra&limit=5
```

**Response:** `200 OK`
```json
{
  "query": "infra",
  "suggestions": [
    {
      "keyword_id": 12,
      "keyword": "infrastructure",
      "category": "Public Works",
      "description": null,
      "is_active": true,
      "created_at": 1706198400,
      "created_by": 1
    }
  ]
}
```

---

#### Get Keyword Categories
**GET** `/admin/keywords/categories`

Get all unique keyword categories.

**Authentication:** Admin required

**Response:** `200 OK`
```json
{
  "categories": [
    "Finance",
    "Infrastructure",
    "Public Works",
    "Utilities"
  ]
}
```

---

#### Get Keyword Details
**GET** `/admin/keywords/{keyword_id}`

Get a specific keyword by ID.

**Authentication:** Admin required

**Response:** `200 OK`
```json
{
  "keyword_id": 12,
  "keyword": "infrastructure",
  "category": "Public Works",
  "description": "Infrastructure projects",
  "is_active": true,
  "created_at": 1706198400,
  "created_by": 1
}
```

**Error Responses:**
- `404 Not Found`: Keyword does not exist

---

#### Update Keyword
**PUT** `/admin/keywords/{keyword_id}`

Update a keyword's information.

**Authentication:** Admin required

**Request Body:** (all fields optional)
```json
{
  "keyword": "updated_keyword",
  "category": "New Category",
  "description": "Updated description",
  "is_active": false
}
```

**Response:** `200 OK`

**Error Responses:**
- `404 Not Found`: Keyword does not exist
- `400 Bad Request`: Validation error (e.g., duplicate keyword)

---

#### Delete Keyword
**DELETE** `/admin/keywords/{keyword_id}`

Soft delete a keyword (sets `is_active` to false).

**Authentication:** Admin required

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found`: Keyword does not exist

---

#### Get Keyword Usage
**GET** `/admin/keywords/{keyword_id}/usage`

Get all clients using a specific keyword.

**Authentication:** Admin required

**Response:** `200 OK`
```json
{
  "keyword_id": 12,
  "keyword": "infrastructure",
  "clients": [
    {
      "client_id": 1,
      "name": "City of Jacksonville"
    },
    {
      "client_id": 3,
      "name": "JEA"
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Keyword does not exist

---

## User Endpoints

### Client Viewing

#### List Available Clients
**GET** `/clients`

List all active clients available to the user (with favorite status).

**Authentication:** User required

**Query Parameters:**
- `include_keywords` (boolean, optional): Include associated keywords

**Response:** `200 OK`
```json
{
  "clients": [
    {
      "client_id": 1,
      "name": "JEA",
      "description": "Jacksonville Electric Authority",
      "website_url": "https://www.jea.com",
      "is_active": true,
      "is_favorited": true,
      "keywords": null
    },
    {
      "client_id": 2,
      "name": "City of Jacksonville",
      "description": null,
      "website_url": null,
      "is_active": true,
      "is_favorited": false,
      "keywords": null
    }
  ],
  "total": 2
}
```

**Notes:**
- Only returns active clients
- `is_favorited` indicates if the current user has favorited the client

---

#### Get Client Details
**GET** `/clients/{client_id}`

Get a specific client by ID with keywords and favorite status.

**Authentication:** User required

**Response:** `200 OK`
```json
{
  "client_id": 1,
  "name": "JEA",
  "description": "Jacksonville Electric Authority",
  "website_url": "https://www.jea.com",
  "is_active": true,
  "is_favorited": true,
  "keywords": [
    {
      "keyword_id": 5,
      "keyword": "water",
      "category": "Utilities",
      "description": null,
      "is_active": true,
      "created_at": 1706198400,
      "created_by": 1
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Client does not exist or is inactive

---

### Favorites Management

#### Add to Favorites
**POST** `/clients/{client_id}/favorite`

Add a client to the current user's favorites.

**Authentication:** User required

**Response:** `201 Created`
```json
{
  "message": "Client added to favorites"
}
```

**Notes:**
- Idempotent: Adding the same favorite twice returns success
- Only active clients can be favorited

**Error Responses:**
- `404 Not Found`: Client does not exist or is inactive

---

#### Remove from Favorites
**DELETE** `/clients/{client_id}/favorite`

Remove a client from the current user's favorites.

**Authentication:** User required

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found`: Client is not in user's favorites

---

#### Get User Favorites
**GET** `/clients/favorites`

Get all clients favorited by the current user.

**Authentication:** User required

**Response:** `200 OK`
```json
[
  {
    "client_id": 1,
    "name": "JEA",
    "description": "Jacksonville Electric Authority",
    "website_url": "https://www.jea.com",
    "is_active": true,
    "favorited_at": 1706284800,
    "keywords": null
  }
]
```

**Notes:**
- Results are ordered by `favorited_at` descending (most recent first)
- Favorites are isolated per user

---

## Error Responses

All endpoints follow standard HTTP error codes:

### 400 Bad Request
Validation error or business logic violation.

```json
{
  "detail": "Client with name 'JEA' already exists"
}
```

### 401 Unauthorized
Missing or invalid authentication token.

```json
{
  "detail": "Not authenticated - no token in Authorization header or cookie"
}
```

### 403 Forbidden
Insufficient permissions (e.g., regular user accessing admin endpoint).

```json
{
  "detail": "Admin privileges required"
}
```

### 404 Not Found
Resource does not exist.

```json
{
  "detail": "Client not found"
}
```

### 422 Unprocessable Entity
Request body validation failed (Pydantic validation).

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Authentication

All endpoints require authentication via JWT token.

### Methods:
1. **Authorization Header** (recommended for API clients):
   ```
   Authorization: Bearer <token>
   ```

2. **HttpOnly Cookie** (for browser clients):
   ```
   Cookie: access_token=Bearer <token>
   ```

### Getting a Token:
```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=adminpass
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. This may be added in future versions.

---

## Pagination

List endpoints support pagination via `limit` and `offset` parameters:

```bash
# Get first 50 results
GET /admin/clients?limit=50&offset=0

# Get next 50 results
GET /admin/clients?limit=50&offset=50
```

**Response includes total count:**
```json
{
  "clients": [...],
  "total": 125,
  "limit": 50,
  "offset": 0
}
```

---

## Examples

### Admin Workflow: Setting up a New Client

```bash
# 1. Create client
curl -X POST http://localhost:8000/admin/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "JEA",
    "description": "Jacksonville Electric Authority",
    "website_url": "https://www.jea.com"
  }'

# 2. Create keywords
curl -X POST http://localhost:8000/admin/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "water", "category": "Utilities"}'

curl -X POST http://localhost:8000/admin/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "rates", "category": "Finance"}'

# 3. Associate keywords with client
curl -X POST http://localhost:8000/admin/clients/1/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keyword_id": 1}'

curl -X POST http://localhost:8000/admin/clients/1/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keyword_id": 2}'
```

### User Workflow: Browsing and Favoriting Clients

```bash
# 1. List available clients
curl -X GET http://localhost:8000/clients \
  -H "Authorization: Bearer $USER_TOKEN"

# 2. Get client details with keywords
curl -X GET http://localhost:8000/clients/1 \
  -H "Authorization: Bearer $USER_TOKEN"

# 3. Add to favorites
curl -X POST http://localhost:8000/clients/1/favorite \
  -H "Authorization: Bearer $USER_TOKEN"

# 4. View all favorites
curl -X GET http://localhost:8000/clients/favorites \
  -H "Authorization: Bearer $USER_TOKEN"
```
