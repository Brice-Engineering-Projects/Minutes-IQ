# Phase 3 Implementation Plan: Multi-URL Client Architecture

**Date:** 2026-02-12
**Status:** Ready for Execution
**Dependencies:** Phase 2 Audit Complete ✅

---

## Overview

This plan provides step-by-step instructions for completing the multi-URL client architecture refactor. Work is organized by priority, with estimated effort and risk assessment per task.

**Total Estimated Effort:** ~10 hours
**Risk Level:** Medium
**Recommended Approach:** Incremental implementation with testing between steps

---

## Execution Strategy

### Principles
1. **Fix blocking issues first** - Start with critical P0 items
2. **Backend before frontend** - Stabilize APIs before updating UI
3. **Test continuously** - Run tests after each major change
4. **Deploy incrementally** - Commit working states frequently

### Rollout Plan
1. **Dev Environment** - Implement and test all changes locally
2. **Commit & Review** - Create PR for code review
3. **Staging** - Deploy to staging environment for QA
4. **Production** - Deploy after successful staging validation

---

## Task Breakdown

### Phase 3A: Critical Fixes (P0 - Blocking)

**Total Effort:** 35 minutes | **Risk:** Low

#### Task 3A.1: Fix Admin Endpoint Service Calls

**Priority:** P0 (CRITICAL - Causes 500 errors)
**Effort:** 5 minutes
**Risk:** Low
**File:** `src/minutes_iq/admin/client_routes.py`

**Changes Required:**

**Line 78-83** (create_client):
```python
# BEFORE
success, error_msg, client_data = client_service.create_client(
    name=client.name,
    created_by=admin_user["user_id"],
    description=client.description,
    website_url=client.website_url,  # ← REMOVE THIS
)

# AFTER
success, error_msg, client_data = client_service.create_client(
    name=client.name,
    created_by=admin_user["user_id"],
    description=client.description,
)
```

**Line 150-156** (update_client):
```python
# BEFORE
success, error_msg, client_data = client_service.update_client(
    client_id=client_id,
    name=update.name,
    description=update.description,
    website_url=update.website_url,  # ← REMOVE THIS
    is_active=update.is_active,
)

# AFTER
success, error_msg, client_data = client_service.update_client(
    client_id=client_id,
    name=update.name,
    description=update.description,
    is_active=update.is_active,
)
```

**Testing:**
```bash
# Manual test via curl or Postman
POST /admin/clients
{
  "name": "Test Client",
  "description": "Test"
}
# Should return 201 Created (not 500)
```

---

#### Task 3A.2: Update Admin Pydantic Request Models

**Priority:** P0
**Effort:** 10 minutes
**Risk:** Low
**File:** `src/minutes_iq/admin/client_routes.py`

**Changes Required:**

**Lines 21-26** (ClientCreate):
```python
# BEFORE
class ClientCreate(BaseModel):
    """Request model for creating a client."""
    name: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    website_url: str | None = Field(None, max_length=500)  # ← REMOVE

# AFTER
class ClientCreate(BaseModel):
    """Request model for creating a client."""
    name: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    # Note: URLs are managed separately via ClientUrlRepository
```

**Lines 29-35** (ClientUpdate):
```python
# BEFORE
class ClientUpdate(BaseModel):
    """Request model for updating a client."""
    name: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    website_url: str | None = Field(None, max_length=500)  # ← REMOVE
    is_active: bool | None = None

# AFTER
class ClientUpdate(BaseModel):
    """Request model for updating a client."""
    name: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_active: bool | None = None
    # Note: URLs are managed separately via ClientUrlRepository
```

**Testing:**
- Existing admin endpoint tests should still pass
- API documentation should reflect updated schema

---

#### Task 3A.3: Update Admin Response Model (Temporary)

**Priority:** P0
**Effort:** 20 minutes
**Risk:** Low
**File:** `src/minutes_iq/admin/client_routes.py`

**Approach:** Add `urls` field but keep `website_url` temporarily for backwards compatibility

**Lines 38-49** (ClientResponse):
```python
# TEMPORARY TRANSITION STATE
class ClientUrl(BaseModel):
    """URL associated with a client."""
    id: int
    alias: str
    url: str
    is_active: bool
    last_scraped_at: int | None

class ClientResponse(BaseModel):
    """Response model for a single client."""
    client_id: int
    name: str
    description: str | None
    website_url: str | None = None  # ← DEPRECATED: Keep for backwards compat
    urls: list[ClientUrl] = []       # ← NEW: Multi-URL support
    is_active: bool
    created_at: int
    created_by: int
    updated_at: int | None
    keywords: list[dict] | None = None
```

**Update endpoint handlers to populate `urls`:**

**Lines 91-116** (list_clients):
```python
from minutes_iq.db.dependencies import get_client_url_repository

@router.get("", response_model=ClientListResponse)
async def list_clients(
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
    client_url_repo: Annotated[ClientUrlRepository, Depends(get_client_url_repository)],
    is_active: bool | None = None,
    include_keywords: bool = False,
    limit: int = 100,
    offset: int = 0,
):
    """List all clients with optional filtering."""
    clients, total = client_service.list_clients(
        is_active=is_active,
        include_keywords=include_keywords,
        limit=limit,
        offset=offset,
    )

    # Enrich with URLs
    for client in clients:
        client_urls = client_url_repo.get_client_urls(client["client_id"], active_only=False)
        client["urls"] = client_urls
        # Backwards compat: set website_url to first URL if exists
        client["website_url"] = client_urls[0]["url"] if client_urls else None

    return ClientListResponse(
        clients=[ClientResponse(**c) for c in clients],
        total=total,
        limit=limit,
        offset=offset,
    )
```

**Similar changes for:**
- `GET /admin/clients/{id}` endpoint (lines 118-138)
- `POST /admin/clients` response (lines 68-88)
- `PUT /admin/clients/{id}` response (lines 140-163)

**Testing:**
```bash
# Test that response includes both fields
GET /admin/clients
# Response should include:
# {
#   "client_id": 1,
#   "name": "JEA",
#   "website_url": "https://www.jea.com",  # deprecated
#   "urls": [
#     {"id": 1, "alias": "default", "url": "https://www.jea.com", ...},
#     {"id": 2, "alias": "current", "url": "...", ...},
#     {"id": 3, "alias": "archive", "url": "...", ...}
#   ]
# }
```

---

### Phase 3B: User-Facing API Updates (P0)

**Total Effort:** 30 minutes | **Risk:** Low

#### Task 3B.1: Update User API Response Models

**Priority:** P0
**Effort:** 15 minutes
**Risk:** Low
**File:** `src/minutes_iq/api/clients.py`

**Changes Required:**

**Lines 24-35** (ClientResponse):
```python
# Import at top
from minutes_iq.db.dependencies import get_client_url_repository

class ClientUrl(BaseModel):
    """URL associated with a client."""
    id: int
    alias: str
    url: str
    is_active: bool
    last_scraped_at: int | None

class ClientResponse(BaseModel):
    """Response model for a single client."""
    client_id: int
    name: str
    description: str | None
    website_url: str | None = None  # DEPRECATED
    urls: list[ClientUrl] = []       # NEW
    is_active: bool
    is_favorited: bool = False
    keywords: list[dict] | None = None
```

**Lines 44-53** (FavoriteResponse):
```python
class FavoriteResponse(BaseModel):
    """Response model for a favorited client."""
    client_id: int
    name: str
    description: str | None
    website_url: str | None = None  # DEPRECATED
    urls: list[ClientUrl] = []       # NEW
    is_active: bool
    favorited_at: int
    keywords: list[dict] | None = None
```

---

#### Task 3B.2: Update User API Endpoints

**Priority:** P0
**Effort:** 15 minutes
**Risk:** Low
**File:** `src/minutes_iq/api/clients.py`

**Update `list_clients` endpoint:**
```python
@router.get("", response_model=ClientListResponse)
async def list_clients(
    current_user: Annotated[dict, Depends(get_current_user)],
    client_service: Annotated[ClientService, Depends(get_client_service)],
    client_url_repo: Annotated[ClientUrlRepository, Depends(get_client_url_repository)],
    favorites_repo: Annotated[FavoritesRepository, Depends(get_favorites_repository)],
    include_keywords: bool = False,
):
    """List all active clients."""
    clients, total = client_service.list_clients(
        is_active=True, include_keywords=include_keywords, limit=1000
    )

    # Get user's favorites
    user_id = current_user["user_id"]
    favorites = favorites_repo.get_user_favorites(user_id)
    favorite_ids = {fav["client_id"] for fav in favorites}

    # Enrich with URLs and favorite status
    client_responses = []
    for c in clients:
        client_urls = client_url_repo.get_client_urls(c["client_id"], active_only=True)
        c["urls"] = client_urls
        c["website_url"] = client_urls[0]["url"] if client_urls else None
        c["is_favorited"] = c["client_id"] in favorite_ids
        client_responses.append(ClientResponse(**c))

    return ClientListResponse(clients=client_responses, total=total)
```

**Similar changes for:**
- `GET /clients/{client_id}` endpoint
- `GET /clients/favorites` endpoint

---

### Phase 3C: Test Updates (P1)

**Total Effort:** 3 hours | **Risk:** Medium

#### Task 3C.1: Update Test Database Schema

**Priority:** P1
**Effort:** 30 minutes
**Risk:** Low
**File:** `tests/conftest.py`

**Changes Required:**

**Line 124** - Remove `website_url` from client table:
```python
CREATE TABLE IF NOT EXISTS client (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    -- website_url TEXT,  ← REMOVE THIS LINE
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    updated_at INTEGER
);
```

**Add `client_urls` table after client table:**
```python
CREATE TABLE IF NOT EXISTS client_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    alias TEXT NOT NULL,
    url TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_scraped_at INTEGER,
    created_at INTEGER NOT NULL,
    updated_at INTEGER,
    FOREIGN KEY (client_id) REFERENCES client(client_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_client_urls_client_id ON client_urls(client_id);
CREATE INDEX IF NOT EXISTS idx_client_urls_is_active ON client_urls(is_active);
```

**Add seed data for test client URLs:**
```python
# After seeding test client (JEA)
cursor.execute(
    """
    INSERT INTO client_urls (client_id, alias, url, is_active, created_at)
    VALUES
        (1, 'default', 'https://www.jea.com', 1, ?),
        (1, 'current', 'https://www.jea.com/About/Public_Meetings/Board_Meetings/', 1, ?),
        (1, 'archive', 'https://www.jea.com/About/Public_Meetings/Archives/', 1, ?)
    """,
    (created_at, created_at, created_at),
)
```

---

#### Task 3C.2: Update Integration Tests

**Priority:** P1
**Effort:** 2 hours
**Risk:** Medium
**File:** `tests/integration_tests/clients/test_admin_client_management.py`

**Changes Required:**

**Test: `test_create_client`** (lines 10-30):
```python
def test_create_client(client, admin_token):
    """Test creating a new client."""
    response = client.post(
        "/admin/clients",
        json={
            "name": "City of Jacksonville",
            "description": "Municipal government",
            # website_url removed
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "City of Jacksonville"
    assert data["description"] == "Municipal government"
    # website_url assertion removed
    assert data["urls"] == []  # No URLs yet
    assert data["is_active"] is True
```

**Test: `test_create_client_minimal_data`** (lines 33-50):
```python
def test_create_client_minimal_data(client, admin_token):
    """Test creating a client with minimal required data."""
    response = client.post(
        "/admin/clients",
        json={"name": "Minimal Client"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Client"
    assert data["description"] is None
    # website_url assertion removed
    assert data["urls"] == []
```

**Test: `test_update_client`** (lines 250-280):
```python
def test_update_client(client, admin_token, setup_test_client):
    """Test updating a client."""
    client_id = setup_test_client

    response = client.put(
        f"/admin/clients/{client_id}",
        json={
            "name": "JEA Updated",
            # website_url removed
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "JEA Updated"
    # website_url assertion removed
```

**Add new tests for URL management:**
```python
def test_get_client_with_urls(client, admin_token, setup_test_client):
    """Test that client response includes URLs."""
    client_id = setup_test_client

    response = client.get(
        f"/admin/clients/{client_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "urls" in data
    assert isinstance(data["urls"], list)
    assert len(data["urls"]) == 3  # JEA has 3 URLs in seed data
    assert data["urls"][0]["alias"] == "default"
    assert data["urls"][0]["url"] == "https://www.jea.com"
```

---

#### Task 3C.3: Add URL Management Tests

**Priority:** P1
**Effort:** 30 minutes
**Risk:** Low
**File:** Create new file `tests/integration_tests/clients/test_client_url_management.py`

**New Test Cases:**
- Test creating URL for client
- Test listing client URLs
- Test updating URL
- Test deleting URL
- Test scraper job creation with client_url_id

*(Full test file content provided separately if needed)*

---

### Phase 3D: UI Updates (P1)

**Total Effort:** 6 hours | **Risk:** High

#### Task 3D.1: Remove website_url from Client Form

**Priority:** P1
**Effort:** 15 minutes
**Risk:** Low
**File:** `src/minutes_iq/templates/clients/form.html`

**Changes Required:**

**Lines 64-77** - Remove entire Website URL section:
```html
<!-- DELETE THIS ENTIRE BLOCK -->
<!-- Website URL -->
<div class="mb-6">
    <label for="website_url" ...>
        Website URL
    </label>
    <input
        type="url"
        id="website_url"
        name="website_url"
        value="{{ client.website_url if client else '' }}"
        ...
    >
</div>
```

**Note:** URL management UI will be added in next task

---

#### Task 3D.2: Add URL Management UI to Client Form

**Priority:** P1
**Effort:** 4 hours
**Risk:** High
**File:** `src/minutes_iq/templates/clients/form.html`

**Insert after description field (around line 64):**

```html
<!-- Client URLs Management -->
<div class="mb-6">
    <div class="flex items-center justify-between mb-3">
        <label class="block text-sm font-medium text-gray-700">
            Client URLs
        </label>
        <button
            type="button"
            onclick="addUrlRow()"
            class="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
        >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            Add URL
        </button>
    </div>

    <!-- Existing URLs (if editing) -->
    <div id="urls-container" class="space-y-3">
        {% if client and client.urls %}
            {% for url in client.urls %}
            <div class="url-row flex gap-2 items-start border border-gray-200 rounded-lg p-3">
                <input type="hidden" name="url_ids[]" value="{{ url.id }}">
                <div class="flex-1">
                    <input
                        type="text"
                        name="url_aliases[]"
                        value="{{ url.alias }}"
                        placeholder="Alias (e.g., current, archive)"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-2"
                        required
                    >
                    <input
                        type="url"
                        name="url_values[]"
                        value="{{ url.url }}"
                        placeholder="https://example.com"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        required
                    >
                </div>
                <div class="flex items-center gap-2">
                    <label class="flex items-center text-sm text-gray-600">
                        <input
                            type="checkbox"
                            name="url_active[]"
                            value="{{ url.id }}"
                            {% if url.is_active %}checked{% endif %}
                            class="mr-1"
                        >
                        Active
                    </label>
                    <button
                        type="button"
                        onclick="removeUrlRow(this)"
                        class="text-red-600 hover:text-red-800"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                    </button>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <!-- Empty state -->
            <p class="text-sm text-gray-500 italic">No URLs yet. Click "Add URL" to add one.</p>
        {% endif %}
    </div>
</div>

<script>
function addUrlRow() {
    const container = document.getElementById('urls-container');
    const newRow = document.createElement('div');
    newRow.className = 'url-row flex gap-2 items-start border border-gray-200 rounded-lg p-3';
    newRow.innerHTML = `
        <div class="flex-1">
            <input
                type="text"
                name="new_url_aliases[]"
                placeholder="Alias (e.g., current, archive)"
                class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-2"
                required
            >
            <input
                type="url"
                name="new_url_values[]"
                placeholder="https://example.com"
                class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                required
            >
        </div>
        <div class="flex items-center gap-2">
            <label class="flex items-center text-sm text-gray-600">
                <input
                    type="checkbox"
                    name="new_url_active[]"
                    checked
                    class="mr-1"
                >
                Active
            </label>
            <button
                type="button"
                onclick="removeUrlRow(this)"
                class="text-red-600 hover:text-red-800"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
            </button>
        </div>
    `;
    container.appendChild(newRow);
}

function removeUrlRow(button) {
    button.closest('.url-row').remove();
}
</script>
```

---

#### Task 3D.3: Update Form Submission Handler

**Priority:** P1
**Effort:** 1 hour
**Risk:** Medium
**File:** `src/minutes_iq/api/clients_ui.py`

**Update create_client endpoint (lines 236-287):**
```python
from minutes_iq.db.dependencies import get_client_url_repository

@router.post("", response_class=HTMLResponse)
async def create_client(
    request: Request,
    client_repo: Annotated[ClientRepository, Depends(get_client_repository)],
    client_url_repo: Annotated[ClientUrlRepository, Depends(get_client_url_repository)],
    keyword_repo: Annotated[KeywordRepository, Depends(get_keyword_repository)],
):
    """Create a new client."""
    from fastapi.responses import Response

    form_data = await request.form()
    name = str(form_data.get("name", "")).strip()
    description_raw = form_data.get("description", "")
    description = str(description_raw).strip() or None if description_raw else None
    is_active = form_data.get("is_active") == "on"
    keyword_ids = form_data.getlist("keyword_ids")

    # NEW: Get URL data
    new_url_aliases = form_data.getlist("new_url_aliases[]")
    new_url_values = form_data.getlist("new_url_values[]")
    new_url_active = form_data.getlist("new_url_active[]")

    if not name:
        return '<div class="p-4 bg-red-50 border border-red-200 rounded-md"><p class="text-sm text-red-800">Client name is required</p></div>'

    # Create client
    created_by_user = 1  # TODO: Get from current_user
    client = client_repo.create_client(
        name=name,
        description=description,
        is_active=is_active,
        created_by=created_by_user,
    )
    client_id = client["client_id"]

    # NEW: Add URLs
    import time
    created_at = int(time.time())
    for i, alias in enumerate(new_url_aliases):
        if alias and new_url_values[i]:
            is_url_active = str(i) in new_url_active
            client_url_repo.create_url(
                client_id=client_id,
                alias=alias.strip(),
                url=new_url_values[i].strip(),
                is_active=is_url_active,
            )

    # Add keywords (existing logic)
    if keyword_ids:
        for keyword_id_raw in keyword_ids:
            try:
                keyword_id = int(str(keyword_id_raw))
                keyword_repo.add_keyword_to_client(client_id, keyword_id, created_by_user)
            except (ValueError, TypeError):
                pass

    response = Response(
        content='<div class="p-4 bg-green-50 border border-green-200 rounded-md"><p class="text-sm text-green-800">Client created successfully!</p></div>',
        status_code=200,
    )
    response.headers["HX-Redirect"] = f"/clients/{client_id}"
    return response
```

**Similar changes for update_client endpoint (lines 290-334)**

---

#### Task 3D.4: Add URL Display to Client Detail Page

**Priority:** P1
**Effort:** 45 minutes
**Risk:** Low
**File:** `src/minutes_iq/templates/clients/detail.html`

**Insert after Client Info Card (around line 90):**

```html
<!-- Client URLs Card -->
<div class="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Client URLs</h2>
        {% if current_user and current_user.role_id == 1 %}
        <a
            href="/clients/{{ client.client_id }}/edit"
            class="text-sm text-blue-600 hover:text-blue-800"
        >
            Edit URLs
        </a>
        {% endif %}
    </div>

    <div
        hx-get="/api/clients/{{ client.client_id }}/urls"
        hx-trigger="load"
        hx-swap="innerHTML"
    >
        <div class="animate-pulse space-y-2">
            <div class="h-4 bg-gray-200 rounded w-full"></div>
            <div class="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
    </div>
</div>
```

**Create new API endpoint in `clients_ui.py`:**
```python
@router.get("/{client_id}/urls", response_class=HTMLResponse)
async def get_client_urls(
    client_id: int,
    client_url_repo: Annotated[ClientUrlRepository, Depends(get_client_url_repository)],
):
    """Get HTML fragment showing client URLs."""
    urls = client_url_repo.get_client_urls(client_id, active_only=False)

    if not urls:
        return '<p class="text-sm text-gray-500">No URLs configured for this client.</p>'

    html = '<div class="space-y-3">'
    for url_data in urls:
        status_badge = (
            '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">Active</span>'
            if url_data["is_active"]
            else '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">Inactive</span>'
        )

        last_scraped = (
            f'Last scraped: {url_data["last_scraped_at"]}'
            if url_data["last_scraped_at"]
            else 'Never scraped'
        )

        html += f'''
        <div class="border border-gray-200 rounded-lg p-4">
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="font-medium text-gray-900">{url_data["alias"]}</span>
                        {status_badge}
                    </div>
                    <a href="{url_data["url"]}" target="_blank" class="text-sm text-blue-600 hover:text-blue-800 break-all">
                        {url_data["url"]}
                    </a>
                    <p class="text-xs text-gray-500 mt-1">{last_scraped}</p>
                </div>
            </div>
        </div>
        '''
    html += '</div>'

    return html
```

---

### Phase 3E: Documentation & Cleanup (P2)

**Total Effort:** 1 hour | **Risk:** Low

#### Task 3E.1: Update API Documentation

**Priority:** P2
**Effort:** 30 minutes
**File:** Create/Update API docs

**Document new `ClientUrl` model**
**Document URL management endpoints**
**Mark `website_url` as DEPRECATED in docs**

---

#### Task 3E.2: Remove Comments

**Priority:** P2
**Effort:** 5 minutes
**File:** `src/minutes_iq/api/clients_ui.py`

Remove or update comments on lines 256, 308

---

#### Task 3E.3: Final Cleanup

**Priority:** P2
**Effort:** 25 minutes

- Remove `website_url` field entirely from admin response models (remove backwards compat)
- Update any remaining documentation
- Run full test suite
- Update CHANGELOG

---

## Testing Checklist

- [ ] All existing tests pass
- [ ] New URL management tests pass
- [ ] Manual testing: Create client with URLs
- [ ] Manual testing: Edit client URLs
- [ ] Manual testing: Delete client (cascades to URLs)
- [ ] Manual testing: Create scrape job with specific URL
- [ ] Manual testing: Admin endpoints return URLs
- [ ] Manual testing: User endpoints return URLs
- [ ] API documentation is accurate
- [ ] No console errors in browser
- [ ] Mobile responsiveness verified

---

## Rollback Plan

If issues arise during Phase 3:

1. **Immediate rollback**: Revert to Phase 1 commit
2. **Database**: No schema changes in Phase 3, so no DB rollback needed
3. **Partial rollback**: Can revert specific files while keeping others

---

## Success Criteria

- ✅ All admin endpoints accept/return `urls` array
- ✅ All user endpoints return `urls` array
- ✅ Client forms support adding/editing/deleting URLs
- ✅ Client detail pages display all URLs
- ✅ Scraper job creation references `client_url_id`
- ✅ All tests pass (200+ tests)
- ✅ No `website_url` references remain (except deprecated fields)
- ✅ Documentation updated

---

## Next Steps

1. Review this plan
2. Execute Phase 3A (critical fixes) immediately
3. Execute Phase 3B-3E incrementally
4. Test thoroughly after each phase
5. Deploy to staging
6. Deploy to production

---

**Plan Created By:** Claude Code
**Review Status:** Ready for execution
**Estimated Completion:** 1-2 days (with testing)
