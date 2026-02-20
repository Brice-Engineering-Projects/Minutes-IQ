# Authorization Code Generation Fix - Implementation Guide

**Document Version:** 1.0  
**Date:** February 19, 2026  
**Status:** ✅ IMPLEMENTED

---

## Executive Summary

This document describes the fix for the authorization code generation issue where the admin panel was returning empty JSON when generating codes. The root cause was that the UI endpoint bypassed the service layer and used incorrect code generation logic.

**Issue:** Admin panel "Generate Code" button called `/api/admin/auth-codes/generate` which used `secrets.token_urlsafe(32)` instead of `AuthCodeService.generate_code()`, resulting in malformed codes.

**Solution:** Updated the endpoint to use `AuthCodeService`, added form fields for configuring expiration and usage limits, and enhanced the display to show all relevant code information.

---

## Changes Implemented

### 1. Backend Fix - `src/minutes_iq/api/admin_ui.py`

#### Added Import
```python
from minutes_iq.db.auth_code_service import AuthCodeService
from minutes_iq.db.dependencies import (..., get_auth_code_service)
```

#### Updated `generate_auth_code()` Function

**Before:**
- Used `secrets.token_urlsafe(32)` - created malformed codes
- No support for expiration or usage configuration
- Hardcoded values for `expires_at=None`, `max_uses=1`

**After:**
- Added `request: Request` parameter to parse form data
- Added `auth_code_service: AuthCodeService` dependency injection
- Parses form parameters: `expires_in_days`, `max_uses`, `notes`
- Uses `auth_code_service.create_code()` with proper parameters
- Returns formatted code (`XXXX-XXXX-XXXX` format)
- Displays expiration date, usage limits, and notes in the response HTML
- Added input validation and error handling

**Key Changes:**
```python
# Parse form data
form_data = await request.form()
expires_in_days = form_data.get("expires_in_days", "")
max_uses = form_data.get("max_uses", "1")
notes = form_data.get("notes", "Generated from admin panel")

# Use service layer
code_record = auth_code_service.create_code(
    created_by=current_user.get("user_id", 1),
    expires_in_days=expires_in_days_int,
    max_uses=max_uses_int,
    notes=notes,
)

# Get formatted code
code_string = code_record.get("code_formatted", code_record["code"])
```

#### Updated `get_auth_codes_list()` Function

Enhanced the code list display to show:
- Expiration date/time in human-readable format
- Status badges: Active, Expired, Used, Revoked
- Usage counter (current_uses / max_uses)
- Notes (if provided)
- Visual distinction for expired codes (red badge)

**Key Changes:**
```python
import time
current_time = time.time()

# Check if expired
is_expired = expires_at and current_time > expires_at

# Format expiration
expires_display = datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M") if expires_at else "Never"

# Show usage
usage_display = f"{current_uses}/{max_uses} uses"
```

### 2. Frontend Fix - `src/minutes_iq/templates/admin/auth_codes.html`

#### Added Configuration Form

Replaced the simple "Generate" button with a comprehensive form containing:

**Form Fields:**
1. **Expiration (days)** - Number input, default: 7, optional
   - Leave empty for no expiration
   - Min value: 1
   
2. **Max Uses** - Number input, default: 1, required
   - How many times the code can be used
   - Min value: 1
   
3. **Notes** - Text input, optional
   - Internal tracking note (purpose, recipient, etc.)

**HTMX Configuration:**
```html
<button
    type="button"
    hx-post="/api/admin/auth-codes/generate"
    hx-include="[name='expires_in_days'], [name='max_uses'], [name='notes']"
    hx-target="#auth-codes-list"
    hx-swap="afterbegin"
    ...
>
```

**Layout:**
- 3-column grid on desktop, stacked on mobile
- Clear labels and help text for each field
- Styled with Tailwind CSS for consistency
- Form wrapped in a card above the codes list

---

## How to Use (Admin Guide)

### Generating Time-Limited Authorization Codes

1. **Navigate to Admin Panel**
   - Go to `/admin` in your browser
   - Click "Auth Codes" in the sidebar

2. **Configure the Code**
   
   **Expiration (days):**
   - Enter `1` for 1-day codes (good for demos/trials)
   - Enter `7` for 7-day codes (recommended default)
   - Enter `30` for 30-day codes (long-term invitations)
   - Leave blank for no expiration (use sparingly)
   
   **Max Uses:**
   - Enter `1` for single-use codes (most secure)
   - Enter `5-10` for small team invitations
   - Enter `50+` for bulk registration events
   
   **Notes:**
   - Add recipient name: "John Doe - Marketing"
   - Add purpose: "Beta testers batch 3"
   - Add context: "Conference attendees 2026"

3. **Generate the Code**
   - Click "Generate New Code"
   - Code appears at top of list with green border
   - Format: `XXXX-XXXX-XXXX` (e.g., `K7M9-P2N4-QW8X`)
   - Click "Copy" to copy to clipboard

4. **Share the Code**
   - Send via secure channel (email, Slack, etc.)
   - Include expiration information
   - Instruct user to visit `/register` and enter the code

### Understanding Code Status

**Status Badges:**
- 🟢 **Active** - Code is valid and can be used
- 🔴 **Expired** - Code has passed its expiration date
- ⚫ **Used** - Code has been used (single-use codes)
- ⚫ **Revoked** - Code has been manually deactivated

**Code Information:**
- **Created:** When the code was generated
- **Expires:** Expiration date/time or "Never"
- **Usage:** Current uses / Max uses (e.g., "0/5 uses")
- **Notes:** Internal tracking note (if provided)

### Revoking Codes

To revoke a code before its expiration:
1. Find the code in the list
2. Click the trash icon on the right
3. Confirm deletion
4. Code is immediately deactivated

---

## Implementation Checklist

### ✅ Completed

- [x] Added `AuthCodeService` import to `admin_ui.py`
- [x] Added `get_auth_code_service` dependency import
- [x] Updated `generate_auth_code()` function:
  - [x] Added `request: Request` parameter
  - [x] Added `auth_code_service` dependency injection
  - [x] Parse form data for `expires_in_days`, `max_uses`, `notes`
  - [x] Call `auth_code_service.create_code()` with parameters
  - [x] Use formatted code from service layer
  - [x] Display expiration, usage, and notes in response HTML
  - [x] Added input validation (min values, type checking)
  - [x] Added error handling for invalid inputs
- [x] Updated `get_auth_codes_list()` function:
  - [x] Calculate if code is expired (compare with current time)
  - [x] Format expiration date for display
  - [x] Show status badges (Active/Expired/Used/Revoked)
  - [x] Display usage counter (current_uses/max_uses)
  - [x] Display notes if provided
- [x] Updated `auth_codes.html` template:
  - [x] Replaced simple button with configuration form
  - [x] Added "Expiration (days)" number input (default: 7)
  - [x] Added "Max Uses" number input (default: 1, required)
  - [x] Added "Notes" text input (optional)
  - [x] Added help text for each field
  - [x] Configured HTMX to include form fields in POST
  - [x] Styled form with Tailwind CSS
  - [x] Made responsive (3-col desktop, stacked mobile)

### 📋 Testing Checklist

#### Manual Testing
- [ ] Test code generation with default values (7 days, 1 use)
  - [ ] Verify code format is `XXXX-XXXX-XXXX`
  - [ ] Verify expiration is ~7 days from now
  - [ ] Verify code appears at top of list
- [ ] Test code generation with 1 day expiration
  - [ ] Verify expiration display is correct
- [ ] Test code generation with no expiration
  - [ ] Verify "Never" is displayed
- [ ] Test code generation with max_uses = 5
  - [ ] Verify usage shows "0/5 uses"
- [ ] Test code generation with notes
  - [ ] Verify notes display in code card
- [ ] Test expired code display
  - [ ] Create code with 1-day expiration
  - [ ] Manually update DB to set expires_at to past timestamp
  - [ ] Reload page and verify "Expired" red badge shows
- [ ] Test code usage
  - [ ] Generate a code
  - [ ] Register a user with the code
  - [ ] Verify usage counter updates to "1/1 uses"
  - [ ] Verify status changes to "Used"
- [ ] Test code revocation
  - [ ] Generate a code
  - [ ] Click revoke/delete
  - [ ] Verify code is removed from list (or marked as revoked)

#### Automated Testing
- [ ] Run unit tests: `pytest tests/unit_tests/auth/test_auth_code_generation.py -v`
- [ ] Run service tests: `pytest tests/unit_tests/db/test_auth_code_service.py -v`
- [ ] Run integration tests: `pytest tests/integration_tests/auth/test_admin_auth_codes.py -v`
- [ ] Run E2E tests (if available): `playwright test tests/e2e/admin.spec.ts`

#### Database Verification
```sql
-- Check code format (should be 12 chars without dashes in DB)
SELECT code, LENGTH(code) as len FROM auth_codes ORDER BY created_at DESC LIMIT 5;

-- Check expiration timestamps
SELECT 
    code,
    datetime(created_at, 'unixepoch') as created,
    datetime(expires_at, 'unixepoch') as expires,
    CASE 
        WHEN expires_at IS NULL THEN 'Never expires'
        WHEN expires_at > strftime('%s', 'now') THEN 'Active'
        ELSE 'Expired'
    END as status
FROM auth_codes
ORDER BY created_at DESC
LIMIT 10;

-- Check usage counts
SELECT code, current_uses, max_uses, is_active 
FROM auth_codes 
WHERE max_uses > 1
ORDER BY created_at DESC;
```

---

## Verification Results

### Expected Outcomes

1. **Code Format:**
   - UI displays: `K7M9-P2N4-QW8X` (with dashes)
   - Database stores: `K7M9P2N4QW8X` (without dashes)
   - Length: 12 characters (uppercase + digits only)

2. **Expiration Calculation:**
   - 7 days = current timestamp + (7 × 24 × 60 × 60) seconds
   - Stored as Unix timestamp (integer)
   - Displayed as human-readable: "2026-02-26 14:30"

3. **UI Behavior:**
   - Form submits via HTMX without page reload
   - New code appears at top of list with green border
   - Code is immediately copyable
   - List automatically updates

4. **Status Display:**
   - Active codes: Green "Active" badge
   - Expired codes: Red "Expired" badge
   - Used codes: Gray "Used" badge
   - Expiration shown in all cards

---

## Troubleshooting

### Issue: Still getting empty JSON

**Solution:**
1. Check browser console for errors
2. Verify backend server restarted after code changes
3. Check backend logs for errors: `tail -f logs/minutesiq.log`
4. Verify `AuthCodeService` is properly imported and injected

### Issue: Code format is still wrong (long base64 string)

**Solution:**
1. Ensure line ~633 in `admin_ui.py` calls `auth_code_service.create_code()`
2. Verify `code_string = code_record.get("code_formatted", ...)` is used
3. Check that `AuthCodeService.generate_code()` returns formatted code

### Issue: Form fields not showing

**Solution:**
1. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
2. Verify `auth_codes.html` was saved correctly
3. Check template rendering in browser DevTools → Elements

### Issue: Expiration not working

**Solution:**
1. Verify form data is being parsed: add logging in `generate_auth_code()`
2. Check that `expires_in_days_int` is correctly calculated
3. Verify `auth_code_service.create_code()` receives the parameter
4. Check database: `SELECT expires_at FROM auth_codes ORDER BY created_at DESC LIMIT 1;`

### Issue: HTMX not submitting form

**Solution:**
1. Check HTMX is loaded in base template
2. Verify `hx-include` attribute is correct
3. Check browser console for HTMX errors
4. Test with browser DevTools → Network tab to see POST request

---

## Security Considerations

### Best Practices

✅ **DO:**
- Use short expiration times for unknown users (1-7 days)
- Use single-use codes for individual invitations
- Track who received codes using Notes field
- Revoke codes if compromised
- Monitor usage patterns for anomalies

❌ **DON'T:**
- Share codes publicly on social media
- Create high-use-limit codes without expiration
- Reuse codes across campaigns
- Share codes via unsecured channels

### Recommended Settings

| Use Case | Expiration | Max Uses | Security Level |
|----------|------------|----------|----------------|
| Individual invite | 7 days | 1 | High ✅ |
| Demo account | 1-3 days | 1 | High ✅ |
| Team invite | 14 days | 5-10 | Medium ⚠️ |
| Event registration | Event duration | 50+ | Medium ⚠️ |
| Public beta | 30 days | 100+ | Low ⚠️ |
| Internal team | No expiration | 1 | Medium ⚠️ |

---

## Database Schema Reference

### `auth_codes` Table

```sql
CREATE TABLE auth_codes (
    code_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    created_by INTEGER NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    expires_at INTEGER,  -- Unix timestamp or NULL for no expiration
    max_uses INTEGER NOT NULL DEFAULT 1,
    current_uses INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);
```

**Key Fields:**
- `code` - 12-character code (stored without dashes)
- `expires_at` - Unix timestamp (seconds since epoch) or NULL
- `max_uses` - Maximum number of times code can be used
- `current_uses` - How many times code has been used
- `is_active` - 1 = active, 0 = revoked
- `notes` - Optional tracking information

---

## Related Documentation

- **Design:** [Authorization Codes Design](../04_security/04_authorization_codes_design.md)
- **Operations:** [User Registration Guide](../06_operations/04_user_registration_guide.md)
- **Security:** [Security Model](../04_security/06_security_model.md)
- **API:** [Admin Auth Code Routes](../../src/minutes_iq/admin/auth_code_routes.py)
- **Service:** [Auth Code Service](../../src/minutes_iq/db/auth_code_service.py)
- **Repository:** [Auth Code Repository](../../src/minutes_iq/db/auth_code_repository.py)

---

## Change Log

| Date | Change | Status |
|------|--------|--------|
| 2026-02-19 | Initial implementation of fix | ✅ Complete |
| 2026-02-19 | Updated backend endpoint to use service layer | ✅ Complete |
| 2026-02-19 | Added form fields to frontend | ✅ Complete |
| 2026-02-19 | Enhanced list display with expiration info | ✅ Complete |
| 2026-02-19 | Created documentation | ✅ Complete |

---

## Next Steps

1. **Deploy to staging** - Test in staging environment
2. **Run full test suite** - Ensure no regressions
3. **Update user documentation** - Update registration guide with new instructions
4. **Train admins** - Show admins how to use new features
5. **Monitor usage** - Track code generation and expiration patterns
6. **Collect feedback** - Get admin feedback on UX improvements

---

**Implementation Status:** ✅ **COMPLETE**

**Tested:** ⏳ **Pending Manual Testing**

**Deployed:** ⏳ **Pending Deployment**
