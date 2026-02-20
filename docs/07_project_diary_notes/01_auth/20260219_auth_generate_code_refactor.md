# 📓 Project Diary — Authorization Code Generation Fix

**Project:** JEA Meeting Web Scraper  
**Branch:** `dev`  
**Date:** February 19, 2026  
**Focus:** Fix broken authorization code generation and registration flow

---

## 🧭 Context & Intent

Authorization codes were designed to gate user registration, allowing admins to control who can create accounts. The system includes:

- Admin panel UI for generating time-limited codes
- Service layer with proper code formatting (`XXXX-XXXX-XXXX`)
- Database schema supporting expiration and usage limits
- REST API for programmatic access

However, the admin panel was **completely non-functional**:

- Clicking "Generate Code" returned empty JSON `{"codes":[],"total":0}`
- No codes were being created in the database
- Registration with authorization codes failed with 422 errors

This blocked all new user registrations and rendered the admin panel's core function broken.

---

## ✅ What Has Been Completed

### 1. Root Cause Analysis: Bypassed Service Layer

**Problem Location:** `src/minutes_iq/api/admin_ui.py` lines 657-696

The `generate_auth_code()` endpoint was completely bypassing the service layer:

```python
# ❌ BROKEN CODE
import secrets
code_string = secrets.token_urlsafe(32)  # Wrong format!

auth_code_repo.create_code(
    code=code_string,              # Malformed code
    expires_at=None,               # No expiration support
    max_uses=1,                    # Hardcoded
    notes="Generated from admin panel"
)
```

**Issues identified:**

- Used `secrets.token_urlsafe(32)` instead of `AuthCodeService.generate_code()`
- Generated base64 strings (e.g., `xY7aB3cD9...`) instead of formatted codes
- No support for expiration time configuration
- No support for multi-use codes
- Bypassed all business logic in service layer

**Fix applied:**

```python
# ✅ CORRECTED CODE
code_record = auth_code_service.create_code(
    created_by=current_user.get("user_id", 1),
    expires_in_days=expires_in_days_int,
    max_uses=max_uses_int,
    notes=notes,
)
code_string = code_record.get("code_formatted", code_record["code"])
```

📌 **Outcome:**  
Codes now generate in correct format (`K7M9-P2N4-QW8X`) with proper expiration and usage tracking.

---

### 2. Frontend Enhancement: Configuration Form

**Problem:** Admin panel had only a simple "Generate" button with no configuration options.

**Solution:** Added comprehensive form in `auth_codes.html` with three fields:

1. **Expiration (days)** - Number input, default 7, optional
   - Leave empty for no expiration
   - Min value: 1

2. **Max Uses** - Number input, default 1, required
   - Single-use vs multi-use codes
   - Min value: 1

3. **Notes** - Text input, optional
   - Internal tracking (recipient, purpose, etc.)

**HTMX Integration:**

```html
<button
    type="button"
    hx-post="/api/admin/auth-codes/generate"
    hx-include="[name='expires_in_days'], [name='max_uses'], [name='notes']"
    hx-target="#auth-codes-list"
    hx-swap="afterbegin"
>
```

📌 **Outcome:**  
Admins can now configure expiration and usage limits without code changes.

---

### 3. Enhanced Display: Expiration & Status Tracking

**Problem:** Code list showed minimal information (created date, used/available).

**Improvements implemented:**

- Display expiration date/time in human-readable format
- Status badges: 🟢 Active, 🔴 Expired, ⚫ Used, ⚫ Revoked
- Usage counter: `current_uses/max_uses` (e.g., "2/5 uses")
- Notes display for tracking purposes
- Visual distinction for expired codes (red badge)

**Logic added:**

```python
import time
current_time = time.time()
is_expired = expires_at and current_time > expires_at
expires_display = datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M")
```

📌 **Outcome:**  
Full visibility into code status, expiration, and usage at a glance.

---

### 4. Critical Bug: Route Registration Order

**Problem discovered during testing:**

```text
GET /admin/auth-codes → returned JSON {"codes":[],"total":0}
```

The admin panel page itself was returning JSON instead of HTML!

**Root cause:** FastAPI route registration order in `main.py`

```python
# ❌ WRONG ORDER
app.include_router(auth_code_routes.router)  # REST API: /admin/auth-codes (JSON)
app.include_router(admin_ui_routes.router)   # UI page: /admin/auth-codes (HTML)
```

FastAPI matches routes in registration order. The REST API route was registered **before** the UI route, so it took precedence.

**Fix applied:**

```python
# ✅ CORRECT ORDER
# Register UI routes BEFORE REST API routes
app.include_router(admin_ui_routes.router)   # UI page registered first
app.include_router(auth_code_routes.router)  # REST API registered second
```

📌 **Outcome:**  
Admin panel now serves HTML page properly. REST API remains accessible for programmatic use.

---

### 5. Registration Form Fix: JSON Encoding

**Problem discovered:** Registration form returned 422 Unprocessable Entity

**Root cause:** Content-Type mismatch

- FastAPI registration endpoint expects **JSON** (Pydantic `RegisterRequest` model)
- HTMX by default sends **application/x-www-form-urlencoded**
- Pydantic validation failed before reaching endpoint logic

**Fix applied:**

1. **Load HTMX JSON extension** in `base.html`:

```html
<script src="https://unpkg.com/htmx-ext-json-enc@2.0.1/json-enc.js"></script>
```

2. **Enable JSON encoding** on registration form:

```html
<form
    id="register-form"
    hx-post="/auth/register"
    hx-ext="json-enc"    <!-- Added this! -->
    ...
>
```

**Before:** Form sends `username=foo&email=bar&...` (form-urlencoded)  
**After:** Form sends `{"username":"foo","email":"bar",...}` (JSON)

📌 **Outcome:**  
Registration with authorization codes now works end-to-end.

---

## 🛠️ Technical Changes Summary

### Files Modified

| File | Changes | Lines Changed |
| ------ | --------- | --------------- |
| `src/minutes_iq/api/admin_ui.py` | Fixed generate endpoint, enhanced list display | ~150 lines |
| `src/minutes_iq/templates/admin/auth_codes.html` | Added configuration form | ~70 lines |
| `src/minutes_iq/main.py` | Reordered router registration | ~25 lines |
| `src/minutes_iq/templates/base.html` | Added HTMX json-enc extension | 1 line |
| `src/minutes_iq/templates/auth/register.html` | Added hx-ext="json-enc" | 1 line |
| `src/minutes_iq/auth/routes.py` | Added debug logging | ~10 lines |

### Key Additions

- **Service integration:** `AuthCodeService` now properly injected via `get_auth_code_service()` dependency
- **Form parsing:** `await request.form()` to capture expiration, max_uses, notes
- **Input validation:** Type checking and min value validation for numeric inputs
- **Error handling:** `raise ... from None` for proper exception chaining
- **Debug logging:** Comprehensive logging throughout code generation flow

---

## 📚 Documentation Created

### Implementation Guide

**File:** `docs/10_instructions/12_authorization_code_generation_fix.md`

Comprehensive 500+ line document including:

- Executive summary of the issue
- Technical implementation details
- Complete admin user guide with usage scenarios
- Implementation checklist
- Testing procedures (manual + automated)
- Troubleshooting guide for common issues
- Security best practices for code management
- Database schema reference
- Related documentation links

📌 **Purpose:** Ensure admins understand how to use time-limited codes and developers can maintain the system.

---

## ⚠️ Issues Discovered & Resolved

### Issue 1: Empty JSON Response

**Symptom:** Admin panel returned `{"codes":[],"total":0}`  
**Root Cause:** Bypassed service layer, used wrong code generation method  
**Fix:** Integrate `AuthCodeService` and use proper formatted codes  
**Status:** ✅ Resolved

### Issue 2: Route Conflict

**Symptom:** GET `/admin/auth-codes` returned JSON instead of HTML page  
**Root Cause:** REST API route registered before UI route  
**Fix:** Reorder router registration to prioritize UI routes  
**Status:** ✅ Resolved

### Issue 3: Registration 422 Error

**Symptom:** Valid authorization codes rejected with 422 status  
**Root Cause:** Form-urlencoded data vs JSON Pydantic model mismatch  
**Fix:** Enable HTMX json-enc extension  
**Status:** ✅ Resolved

---

## 🧪 Testing & Verification

### Manual Testing Completed

- [x] Generate code with default settings (7 days, 1 use)
  - [x] Verify code format is `XXXX-XXXX-XXXX`
  - [x] Verify expiration is ~7 days from now
  - [x] Verify code appears at top of list with green border
- [x] Generate code with 1 day expiration
  - [x] Verify expiration display is correct
- [x] Generate code with no expiration (empty field)
  - [x] Verify "Never" is displayed
- [x] Generate code with max_uses = 5
  - [x] Verify usage shows "0/5 uses"
- [x] Register new user with generated code
  - [x] Verify registration succeeds
  - [x] Verify usage counter updates
  - [x] Verify code marked as used
- [x] Verify admin panel serves HTML (not JSON)
- [x] Verify code list display shows all information

### Automated Testing

**Service layer tests:** Already exist and pass ✅

- `tests/unit_tests/auth/test_auth_code_generation.py`
- `tests/unit_tests/db/test_auth_code_service.py`

**Integration tests:** Already exist and pass ✅

- `tests/integration_tests/auth/test_admin_auth_codes.py`

**No test changes required** - service layer was already correct, only UI integration was broken.

---

## 🔍 Code Quality

### Linting & Formatting

- [x] Fixed B904 exception chaining issue (`raise ... from None`)
- [x] No ruff violations
- [x] Consistent with existing codebase style

### Dependency Management

- [x] Added `AuthCodeService` import to `admin_ui.py`
- [x] Added `get_auth_code_service` to dependencies imports
- [x] Used FastAPI dependency injection properly
- [x] No circular dependencies introduced

---

## 🧠 Notes / Lessons Learned

### 1. Service Layer Bypassing is Dangerous

The broken endpoint directly called the repository, bypassing all business logic:

- No code formatting
- No expiration calculation
- No validation

**Lesson:** Always use the service layer. Repositories are for data access only.

### 2. Router Registration Order Matters

FastAPI matches routes in the order they're registered. When two routes have the same path, the first one wins.

**Lesson:** Register UI routes before REST API routes when they share paths. Document this pattern clearly.

### 3. HTMX Default Behavior

HTMX sends form-urlencoded data by default, which is incompatible with Pydantic request models expecting JSON.

**Lesson:** For JSON APIs with HTMX, always use the `json-enc` extension. Consider making this the default in `base.html`.

### 4. 422 Errors are Pre-Endpoint

A 422 error means Pydantic validation failed **before** the endpoint function runs. No amount of logging in the endpoint will help debug these.

**Lesson:** Check Content-Type, request format, and Pydantic model structure for 422 errors.

### 5. Documentation-First Pays Off

The authorization code design document already existed with full specifications. The bug was purely in implementation, not design.

**Lesson:** Good design docs make debugging faster because expected behavior is clear.

---

## 🎯 Definition of "Done" for This Phase

This phase is complete when:

- [x] Authorization codes generate in correct format (`XXXX-XXXX-XXXX`)
- [x] Expiration time can be configured (1-N days or no expiration)
- [x] Usage limits can be configured (single-use or multi-use)
- [x] Code list displays all relevant information (expiration, usage, notes)
- [x] Admin panel page serves HTML (not JSON)
- [x] Registration with authorization codes works end-to-end
- [x] All existing tests pass
- [x] No lint violations
- [x] Documentation created for admins and developers
- [x] Debug logging added for troubleshooting

All criteria met. ✅

---

## 🔜 Future Enhancements (Deferred)

The following are working but could be improved:

### Potential Improvements

- **Bulk code generation:** Generate multiple codes at once
- **Code templates:** Pre-defined configs (e.g., "7-day trial", "team invite")
- **Email integration:** Send codes directly to recipients
- **Usage analytics:** Track which codes are most used
- **CSV export:** Download code list with usage stats
- **Expiration notifications:** Alert admins of soon-to-expire unused codes
- **Automatic cleanup:** Archive or delete old expired codes

These are **not blockers** - the system is fully functional as-is.

---

## 📊 Impact Assessment

### Before This Fix

- ❌ Admin panel code generation completely broken
- ❌ No new user registrations possible
- ❌ No control over code expiration or usage limits
- ❌ Poor visibility into code status
- ❌ Admin panel returned JSON instead of UI

### After This Fix

- ✅ Time-limited codes with configurable expiration
- ✅ Single-use and multi-use code support
- ✅ Full visibility into code status and usage
- ✅ Admin panel UI fully functional
- ✅ End-to-end registration flow working
- ✅ Comprehensive documentation for operations

**Business impact:** User registration flow is now fully operational. Admins can control access with time-limited codes.

---

## 🔗 Related Documentation

- **Design:** [Authorization Codes Design](../../04_security/04_authorization_codes_design.md)
- **Operations:** [User Registration Guide](../../06_operations/04_user_registration_guide.md)
- **Implementation:** [Authorization Code Generation Fix](../../10_instructions/12_authorization_code_generation_fix.md)
- **Security:** [Security Model](../../04_security/06_security_model.md)
- **API:** [Auth Code Routes](../../../src/minutes_iq/admin/auth_code_routes.py)
- **Service:** [Auth Code Service](../../../src/minutes_iq/db/auth_code_service.py)

---

**Status:** ✅ Complete  
**Next Focus:** Resume feature development - registration flow is unblocked

---

## 📝 Commit History

```bash
1. fix(admin): implement time-limited authorization code generation
   - Fix empty JSON response from code generation endpoint
   - Use AuthCodeService for proper XXXX-XXXX-XXXX format
   - Add form fields for expiration, max uses, and notes
   - Display expiration dates and usage counts in code list
   - Add comprehensive documentation and admin guide

2. fix(admin): fix route conflict - auth codes page now serves HTML not JSON
   - Reorder router registration: UI routes before REST API routes
   - Fix /admin/auth-codes returning JSON instead of HTML template
   - Add debug logging to generate_auth_code() endpoint

3. fix(auth): enable JSON encoding for registration form
   - Add HTMX json-enc extension to send JSON instead of form data
   - Fix 422 validation error when registering with authorization codes
   - Add debug logging to registration endpoint
```

---

**Total Time Investment:** ~4 hours (investigation, implementation, testing, documentation)  
**Lines of Code Changed:** ~250 lines  
**Documentation Created:** ~500 lines  
**Tests Affected:** 0 (no test changes needed)  
**Bugs Fixed:** 3 critical bugs blocking user registration

🎉 **Authorization code system is now fully operational!**
