# Phase 2 Audit Report: website_url References

**Date:** 2026-02-12
**Status:** Complete
**Phase:** Multi-URL Client Architecture - Phase 2

---

## Executive Summary

This audit identifies all remaining `website_url` references in the codebase after Phase 1 (database migration and API stabilization). The goal is to provide a complete inventory for Phase 3 (UI refactor) implementation.

**Total Files with `website_url` References: 6**

### Breakdown by Category:
- **Pydantic Models:** 2 files (5 models)
- **Templates:** 1 file (1 form)
- **Tests:** 2 files (test data + schema)
- **Comments Only:** 1 file (safe to ignore)

---

## Detailed Findings

### 1. Pydantic Models

#### 1.1 `src/minutes_iq/api/clients.py`

**Lines 31, 50**

```python
class ClientResponse(BaseModel):
    """Response model for a single client."""
    client_id: int
    name: str
    description: str | None
    website_url: str | None  # ← LINE 31
    is_active: bool
    is_favorited: bool = False
    keywords: list[dict] | None = None


class FavoriteResponse(BaseModel):
    """Response model for a favorited client."""
    client_id: int
    name: str
    description: str | None
    website_url: str | None  # ← LINE 50
    is_active: bool
    favorited_at: int
    keywords: list[dict] | None = None
```

**Impact:** HIGH
**Endpoints Affected:**
- `GET /clients` - List all clients
- `GET /clients/favorites` - Get user favorites

**Phase 3 Action:**
- Replace `website_url: str | None` with `urls: list[ClientUrl]`
- Create new `ClientUrl` Pydantic model
- Update endpoint serialization logic

---

#### 1.2 `src/minutes_iq/admin/client_routes.py`

**Lines 26, 34, 44**

```python
class ClientCreate(BaseModel):
    """Request model for creating a client."""
    name: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    website_url: str | None = Field(None, max_length=500)  # ← LINE 26


class ClientUpdate(BaseModel):
    """Request model for updating a client."""
    name: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    website_url: str | None = Field(None, max_length=500)  # ← LINE 34
    is_active: bool | None = None


class ClientResponse(BaseModel):
    """Response model for a single client."""
    client_id: int
    name: str
    description: str | None
    website_url: str | None  # ← LINE 44
    is_active: bool
    created_at: int
    created_by: int
    updated_at: int | None
    keywords: list[dict] | None = None
```

**Impact:** HIGH
**Endpoints Affected:**
- `POST /admin/clients` - Create client (line 82: passes `website_url` to service)
- `PUT /admin/clients/{id}` - Update client (line 154: passes `website_url` to service)
- `GET /admin/clients` - List clients
- `GET /admin/clients/{id}` - Get client details

**Phase 3 Action:**
- Remove `website_url` from `ClientCreate` and `ClientUpdate` models
- Update `ClientResponse` to use `urls: list[ClientUrl]`
- Update endpoint handlers (lines 78-83, 150-156) to not pass `website_url`
- **CRITICAL:** These endpoints call `client_service.create_client()` and `update_client()` which already reject `website_url` - will cause TypeErrors!

---

### 2. Templates

#### 2.1 `src/minutes_iq/templates/clients/form.html`

**Lines 65-72**

```html
<!-- Website URL -->
<div class="mb-6">
    <label for="website_url" class="block text-sm font-medium text-gray-700 mb-2">
        Website URL
    </label>
    <input
        type="url"
        id="website_url"
        name="website_url"
        value="{{ client.website_url if client else '' }}"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="https://example.com"
    >
</div>
```

**Impact:** MEDIUM
**Used By:**
- `/clients/new` - New client form
- `/clients/{id}/edit` - Edit client form

**Phase 3 Action:**
- Remove entire "Website URL" section (lines 64-77)
- Add new "Client URLs" management section:
  - Display existing URLs (table with alias, url, active status)
  - "Add URL" button
  - Inline edit/delete per URL
  - Use htmx for dynamic add/remove without page reload

---

### 3. Test Files

#### 3.1 `tests/integration_tests/clients/test_admin_client_management.py`

**Lines 19, 27, 44, 263, 270**

```python
# Line 19 - Test data
response = client.post(
    "/admin/clients",
    json={
        "name": "City of Jacksonville",
        "description": "Municipal government",
        "website_url": "https://www.coj.net",  # ← LINE 19
    },
    headers={"Authorization": f"Bearer {admin_token}"},
)

# Line 27 - Assertion
assert data["website_url"] == "https://www.coj.net"  # ← LINE 27

# Line 44 - Assertion (optional URL)
assert data["website_url"] is None  # ← LINE 44

# Line 263 - Update test data
response = client.put(
    f"/admin/clients/{client_id}",
    json={
        "name": "JEA Updated",
        "website_url": "https://example.com",  # ← LINE 263
    },
    headers={"Authorization": f"Bearer {admin_token}"},
)

# Line 270 - Assertion
assert data["website_url"] == "https://example.com"  # ← LINE 270
```

**Impact:** HIGH (Causes test failures)
**Tests Affected:**
- `test_create_client` - Expects `website_url` in response
- `test_create_client_minimal_data` - Expects `website_url: null`
- `test_update_client` - Sends and expects `website_url`

**Phase 3 Action:**
- Remove `website_url` from all test request payloads
- Update assertions to check `urls` array instead
- Add new tests for URL management (add, edit, delete URLs)

---

#### 3.2 `tests/conftest.py`

**Line 124**

```python
# Test database schema
CREATE TABLE IF NOT EXISTS client (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    website_url TEXT,  # ← LINE 124
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    updated_at INTEGER
);
```

**Impact:** HIGH (Schema mismatch)
**Current State:** Test database schema still has `website_url` column

**Phase 3 Action:**
- Remove `website_url TEXT,` from client table schema
- Add `client_urls` table to test schema
- Seed test data with URLs in `client_urls` table

---

### 4. Comments Only (Safe)

#### 4.1 `src/minutes_iq/api/clients_ui.py`

**Lines 256, 308**

```python
# Line 256
# Create client (website_url is ignored - use ClientUrlRepository for URLs)

# Line 308
# Update client (website_url is ignored - use ClientUrlRepository for URLs)
```

**Impact:** NONE
**Action:** Keep comments for documentation, or remove in Phase 3 cleanup

---

## Critical Issues Requiring Immediate Attention

### ⚠️ BREAKING: Admin Endpoints Will Fail

**File:** `src/minutes_iq/admin/client_routes.py`

**Problem:**
Lines 82 and 154 pass `website_url` parameter to `client_service.create_client()` and `client_service.update_client()`, but these methods no longer accept this parameter (removed in Phase 1).

**Current Code:**
```python
# Line 78-83
success, error_msg, client_data = client_service.create_client(
    name=client.name,
    created_by=admin_user["user_id"],
    description=client.description,
    website_url=client.website_url,  # ← TypeError: unexpected keyword argument
)

# Line 150-156
success, error_msg, client_data = client_service.update_client(
    client_id=client_id,
    name=update.name,
    description=update.description,
    website_url=update.website_url,  # ← TypeError: unexpected keyword argument
    is_active=update.is_active,
)
```

**Impact:** Any admin attempting to create or update clients via `/admin/clients` endpoints will get 500 errors.

**Immediate Fix Required:**
```python
# Remove website_url parameter from both calls
success, error_msg, client_data = client_service.create_client(
    name=client.name,
    created_by=admin_user["user_id"],
    description=client.description,
)

success, error_msg, client_data = client_service.update_client(
    client_id=client_id,
    name=update.name,
    description=update.description,
    is_active=update.is_active,
)
```

---

## Summary Table

| Category | File | Lines | Impact | Priority |
|----------|------|-------|--------|----------|
| Pydantic Models | `api/clients.py` | 31, 50 | HIGH | P0 |
| Pydantic Models | `admin/client_routes.py` | 26, 34, 44 | HIGH | P0 |
| Admin Endpoints | `admin/client_routes.py` | 82, 154 | **CRITICAL** | **P0** |
| Templates | `templates/clients/form.html` | 65-72 | MEDIUM | P1 |
| Tests | `test_admin_client_management.py` | 19, 27, 44, 263, 270 | HIGH | P1 |
| Tests | `conftest.py` | 124 | HIGH | P1 |
| Comments | `api/clients_ui.py` | 256, 308 | NONE | P2 |

---

## Phase 3 Recommendations

### Immediate (Blocking)
1. **Fix admin endpoints** - Remove `website_url` parameter from service calls (2 lines)
2. **Fix Pydantic models in admin routes** - Remove `website_url` from request models (2 models)

### High Priority
3. **Update API response models** - Add `urls: list[ClientUrl]` to responses (2 models)
4. **Update test schema** - Remove `website_url`, add `client_urls` table
5. **Update integration tests** - Remove `website_url` from test data and assertions

### Medium Priority
6. **Update client form template** - Replace single URL field with URL management UI
7. **Add URL display to client detail page** - Show all URLs with aliases

### Low Priority
8. **Remove comments** - Clean up `website_url` comments in `clients_ui.py`

---

## Estimated Effort

| Task | Effort | Risk |
|------|--------|------|
| Fix admin endpoints | 5 minutes | Low |
| Update Pydantic models | 30 minutes | Low |
| Update test schema + data | 1 hour | Medium |
| Update integration tests | 2 hours | Medium |
| Build URL management UI | 4 hours | High |
| Update client detail display | 2 hours | Medium |
| **Total** | **~10 hours** | **Medium** |

---

## Next Steps

1. ✅ **Phase 2 Complete** - Audit report generated
2. **Phase 3 Planning** - Create detailed implementation plan with:
   - File-by-file change list
   - UI mockups for URL management
   - Test update strategy
   - Rollout plan (dev → staging → production)
3. **Phase 3 Execution** - Implement changes in priority order

---

**Audit Completed By:** Claude Code
**Review Status:** Pending human review
**Recommended Next Action:** Fix critical admin endpoint issue immediately, then proceed with Phase 3 planning
