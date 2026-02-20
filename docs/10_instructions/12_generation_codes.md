User: Currently, when I enter the Admin panel and click on the generate codes the program yields a json without any codes.  We need to create instructions and a checklist so codes are generated and can be authorized for a specific amount of time 

GitHub Copilot: I'll help you create a plan to fix the authorization code generation issue and establish a proper workflow. Let me research the codebase first to understand the current implementation. 

Research authorization code generation

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/docs/04_security/04_authorization_codes_design.md#1-1), lines 1 to 150

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/migrations/20260125_140000_add_authorization_codes.sql)

Searched for regex `generate.*code|authorization.*code`, 20 results

Searched for files matching `**/admin*.py`, 3 matches

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/docs/04_security/04_authorization_codes_design.md#150-150), lines 150 to 325

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/src/minutes_iq/api/admin_ui.py#1-1), lines 1 to 200

Searched for files matching `**/auth_code*.py`, 3 matches

Searched for text `/admin/auth-codes`, 20 results

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/src/minutes_iq/admin/auth_code_routes.py)

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/src/minutes_iq/db/auth_code_service.py)

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/src/minutes_iq/db/auth_code_repository.py)

Searched for files matching `**/frontend/src/**/Admin*.tsx`, no matches

Searched for files matching `**/frontend/src/**/*admin*`, no matches

Searched for files matching `**/frontend/src/**/*auth*code*`, no matches

Searched for regex `Generate.*Code|generateCode` (`**/frontend/**`), 4 results

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/frontend/src)

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/frontend/tests/e2e/admin.spec.ts#70-70), lines 70 to 150

Searched for regex `/admin|auth.*code` (`**/frontend/src/**`), no results

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/src/minutes_iq/ui/admin_routes.py)

Searched for files matching `**/templates/**/*admin*`, no matches

Searched for regex `auth.*codes.*template|render_template.*auth`, no results

Searched for files matching `**/templates/**`, 20 matches

Searched for text `templates_config`, 6 results

Searched for files matching `**/admin/*auth*`, 2 matches

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/src/minutes_iq/templates/admin/auth_codes.html)

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/src/minutes_iq/api/admin_ui.py#200-200), lines 200 to 898

Searched for text `/api/admin/auth-codes/`, 3 results

Searched for text `include_router` (`**/src/minutes_iq/main.py`), 17 results

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/src/minutes_iq/main.py)

Searched for text `get_auth_code_service` (`**/src/minutes_iq/auth/dependencies.py`), 1 result

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/src/minutes_iq/auth/dependencies.py#1-1), lines 1 to 150

Searched for regex `POST.*auth.*code|create.*auth.*code` (`**/tests/**/*.py`), 10 results

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/tests/integration_tests/auth/test_admin_auth_codes.py#88-88), lines 88 to 170

Excellent! I've identified the issue. The admin panel's "generate codes" button calls a broken endpoint that bypasses the service layer and creates malformed codes. The good news is that a properly working REST API already exists - it's just not being used by the UI.

Before creating the detailed plan, I need to understand your preferences: 

Asked 3 questions (Approach, UI Changes, Deliverable)

Perfect! Now I can create a comprehensive plan to fix the code generation and establish proper operational workflows.

---

## Plan: Fix Authorization Code Generation with Time-Limited Codes

**TL;DR**: The admin panel's "generate codes" button calls a broken endpoint (admin_ui.py) that bypasses the service layer and creates malformed codes. We'll fix this endpoint to use `AuthCodeService` properly, add a form for expiration/usage configuration, and create an operational runbook for admins. This leverages the existing, well-tested service layer that already supports time-limited codes via `expires_in_days`.

**Steps**

1. **Fix the broken UI endpoint** in admin_ui.py
   - Add `AuthCodeService` dependency injection to `generate_auth_code()` function
   - Replace `secrets.token_urlsafe(32)` with `auth_code_service.create_code()` call
   - Accept form parameters: `expires_in_days`, `max_uses`, `notes`
   - Use the formatted code from service layer (format: `XXXX-XXXX-XXXX`)
   - Ensure proper admin validation
   
2. **Update the admin frontend template** auth_codes.html
   - Add form fields before the generate button: expires_in_days (number input with default 7), max_uses (number input with default 1), notes (text input, optional)
   - Configure HTMX `hx-vals` to include form field values
   - Add validation for numeric inputs (min=1)
   - Keep existing HTMX target and swap behavior for seamless UX

3. **Enhance the code list display** in auth_codes.html
   - Display expiration date/time (if set) in human-readable format
   - Show "expired" badge for codes past their expiration
   - Display usage count (current_uses / max_uses)  
   - Add visual indicators for active vs expired codes

4. **Create operational runbook** in new file `docs/06_operations/06_authorization_code_workflow.md`
   - Purpose and overview of authorization codes
   - Step-by-step: How to generate codes (with screenshots/examples)
   - Setting expiration times: common scenarios (24 hours, 7 days, 30 days, no expiration)
   - Setting usage limits: single-use vs multi-use codes
   - How to view active codes and check status
   - How to revoke/deactivate codes early
   - Troubleshooting: empty JSON, codes not working, expiration issues
   - Security best practices: when to use expiration, sharing codes securely
   
5. **Update user registration guide** user_registration_guide.md
   - Add reference to new authorization code workflow doc
   - Include examples of time-limited codes in registration flow
   - Update any outdated information about code generation

6. **Add validation and error handling**
   - Validate `expires_in_days` is positive integer or null
   - Validate `max_uses` is positive integer (minimum 1)
   - Return clear error messages if validation fails
   - Handle service layer exceptions gracefully in UI endpoint

**Verification**

1. Start the application locally
2. Log in as admin user
3. Navigate to Admin Panel → Authorization Codes
4. **Test default generation**: Fill form with 7 days, 1 use, generate code
   - Verify code format is `XXXX-XXXX-XXXX` (12 chars, dashes)
   - Verify code appears in list with correct expiration date
   - Verify expiration is ~7 days from now
5. **Test custom expiration**: Generate code with 1 day expiration
   - Verify expires_at timestamp is ~24 hours from now
6. **Test multi-use codes**: Generate code with max_uses=5
   - Verify usage count shows 0/5
7. **Test no expiration**: Generate code with empty/null expires_in_days
   - Verify "No expiration" or similar text appears
8. **Test code format in database**: Query `auth_codes` table, verify code column has formatted codes
9. Run existing tests to ensure no regression: `pytest tests/integration_tests/auth/test_admin_auth_codes.py`
10. Follow the new operational runbook as if you were a new admin to verify clarity

**Decisions**

- **Keep HTMX UI fragment approach**: Maintains consistency with existing admin panel architecture rather than switching to REST API pattern
- **Add form fields for flexibility**: Allows admins to configure expiration and usage without code changes, supporting diverse use cases (demo accounts, temporary access, permanent invites)
- **Leverage existing service layer**: The `AuthCodeService` already implements the correct code format, expiration logic, and database operations - no need to reinvent
- **Separate operational docs**: Creating dedicated workflow guide keeps it scannable for admins vs mixing with technical implementation docs

User: create the instructions in md and place in docs/10_instructions

GitHub Copilot: I'll create the authorization code workflow instructions for you. Let me first check what's currently in the docs/10_instructions directory to understand the structure.  

Read [](file:///home/brice-nelson/Documents/computerScience/PROJECTS/engineering_projects/minutes_iq/docs/10_instructions)

Searched for files matching `**/docs/10_instructions/**`, 13 matches

Perfect! I can see the naming pattern. Here's the comprehensive authorization code workflow instruction document. Save this as `docs/10_instructions/12_authorization_code_workflow.md`:

```markdown
# Authorization Code Generation & Management - Complete Workflow

**Document Version:** 1.0  
**Date:** February 19, 2026  
**Status:** Active Implementation Guide

---

## Table of Contents

1. [Overview](#overview)
2. [Current Problem](#current-problem)
3. [Technical Fix Required](#technical-fix-required)
4. [Admin User Guide](#admin-user-guide)
5. [Implementation Checklist](#implementation-checklist)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)
8. [Security Best Practices](#security-best-practices)

---

## Overview

Authorization codes are time-limited, single-use or multi-use tokens that allow new users to register for the MinutesIQ platform. Admins generate these codes and share them with prospective users.

**Code Format:** `XXXX-XXXX-XXXX` (12 uppercase alphanumeric characters with dashes)  
**Example:** `K7M9-P2N4-QW8X`

**Current Status:** 🔴 **BROKEN** - Admin panel returns empty JSON, codes not generated

**Architecture:**
- **Database:** `auth_codes` table with expiration support (`expires_at` field)
- **Service Layer:** `AuthCodeService` - fully implemented and tested ✅
- **REST API:** `/admin/auth-codes` - fully working ✅
- **UI Fragment API:** `/api/admin/auth-codes/generate` - **BROKEN** ❌
- **Frontend:** `auth_codes.html` - calls broken endpoint

---

## Current Problem

### Root Cause

**File:** `src/minutes_iq/api/admin_ui.py` lines 657-696

The `generate_auth_code()` function bypasses the service layer and creates malformed codes:

```python
# ❌ CURRENT BROKEN CODE (line 669)
code_string = secrets.token_urlsafe(32)  # Wrong format!
# Generates: "xY7aB3cD9..." (base64 string)

# ✅ SHOULD BE
formatted_code = auth_code_service.create_code(...)
# Generates: "K7M9-P2N4-QW8X" (formatted code)
```

### Symptoms

1. Admin clicks "Generate Code" button → Returns empty/invalid JSON
2. Codes in wrong format (if any are created)
3. No expiration time support in UI
4. No control over max uses or notes

---

## Technical Fix Required

### Step 1: Fix the UI Endpoint

**File:** admin_ui.py  
**Function:** `generate_auth_code()` (lines 657-696)

**Changes:**

1. **Add AuthCodeService dependency:**

```python
@router.post("/auth-codes/generate", response_class=HTMLResponse)
async def generate_auth_code(
    request: Request,  # ADD THIS
    current_user: Annotated[dict, Depends(get_current_user)],
    auth_code_service: Annotated[AuthCodeService, Depends(get_auth_code_service)],  # ADD THIS
):
```

2. **Parse form data:**

```python
# Get form parameters
form_data = await request.form()
expires_in_days = form_data.get("expires_in_days")
max_uses = form_data.get("max_uses", "1")
notes = form_data.get("notes", "Generated from admin panel")

# Convert to proper types
expires_in_days_int = int(expires_in_days) if expires_in_days and expires_in_days.strip() else None
max_uses_int = int(max_uses) if max_uses else 1
```

3. **Use the service layer:**

```python
# Replace the broken secrets.token_urlsafe(32) call
code_record = auth_code_service.create_code(
    created_by=current_user["user_id"],
    expires_in_days=expires_in_days_int,
    max_uses=max_uses_int,
    notes=notes,
)

# Get the formatted code
code_string = code_record.get("code_formatted", code_record["code"])
expiration_display = code_record.get("expires_at_display", "No expiration")
```

4. **Update HTML response to show expiration:**

```python
return f"""
<div id="generated-code-display" class="mt-4 p-4 bg-green-50 border border-green-200 rounded">
    <p class="text-sm text-gray-600 mb-2">New authorization code generated:</p>
    <p class="text-2xl font-mono font-bold text-green-700">{escape(code_string)}</p>
    <p class="text-sm text-gray-500 mt-2">Expires: {escape(expiration_display)}</p>
    <p class="text-sm text-gray-500">Max uses: {max_uses_int}</p>
    <p class="text-xs text-gray-400 mt-2">Share this code with the user. They can use it once to register.</p>
</div>
"""
```

### Step 2: Update Frontend Template

**File:** auth_codes.html  
**Section:** Around line 21 (the generate button)

**Add form fields before the button:**

```html
<div class="space-y-4">
    <!-- Form fields -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
            <label for="expires_in_days" class="block text-sm font-medium text-gray-700 mb-1">
                Expiration (days)
            </label>
            <input 
                type="number" 
                id="expires_in_days" 
                name="expires_in_days" 
                min="1" 
                value="7"
                placeholder="7"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
            <p class="text-xs text-gray-500 mt-1">Leave empty for no expiration</p>
        </div>
        
        <div>
            <label for="max_uses" class="block text-sm font-medium text-gray-700 mb-1">
                Max Uses
            </label>
            <input 
                type="number" 
                id="max_uses" 
                name="max_uses" 
                min="1" 
                value="1"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
            <p class="text-xs text-gray-500 mt-1">How many times can this code be used</p>
        </div>
        
        <div>
            <label for="notes" class="block text-sm font-medium text-gray-700 mb-1">
                Notes (optional)
            </label>
            <input 
                type="text" 
                id="notes" 
                name="notes" 
                placeholder="Purpose or recipient"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
            <p class="text-xs text-gray-500 mt-1">Internal note for tracking</p>
        </div>
    </div>
    
    <!-- Generate button -->
    <button
        hx-post="/api/admin/auth-codes/generate"
        hx-include="[name='expires_in_days'], [name='max_uses'], [name='notes']"
        hx-target="#generated-code-display"
        hx-swap="outerHTML"
        class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded shadow-sm transition-colors duration-200"
    >
        Generate New Code
    </button>
    
    <!-- Display area -->
    <div id="generated-code-display"></div>
</div>
```

### Step 3: Enhance Code List Display

**File:** admin_ui.py  
**Function:** `list_auth_codes_fragment()` (lines 527-655)

**Improve the HTML generation to show expiration:**

```python
# Inside the loop where you generate table rows for each code
expires_display = "Never" if not code["expires_at"] else datetime.fromtimestamp(code["expires_at"]).strftime("%Y-%m-%d %H:%M")
is_expired = code["expires_at"] and time.time() > code["expires_at"]
status_badge = f'<span class="px-2 py-1 text-xs rounded {"bg-red-100 text-red-800" if is_expired else "bg-green-100 text-green-800"}">{"Expired" if is_expired else "Active"}</span>'

# Add a column for expiration in the table
<td class="px-4 py-2 text-sm text-gray-900">{escape(expires_display)}</td>
<td class="px-4 py-2">{status_badge}</td>
<td class="px-4 py-2 text-sm text-gray-600">{code["current_uses"]}/{code["max_uses"]}</td>
```

---

## Admin User Guide

### How to Generate Authorization Codes

1. **Log in as Admin**
   - Navigate to `/admin` or click "Admin Panel" in the navigation menu
   - You must have admin role (role_id = 1)

2. **Access Authorization Codes**
   - Click "Auth Codes" in the admin panel sidebar
   - Or navigate directly to `/admin/auth-codes`

3. **Configure the Code**
   
   **Expiration Time (days):**
   - **1 day** - For demo/trial accounts
   - **7 days** - Default, good for most invites (recommended)
   - **30 days** - For slower onboarding processes
   - **Empty/blank** - No expiration (use sparingly for security)
   
   **Max Uses:**
   - **1** - Single-use code (recommended for individual invites)
   - **5-10** - For small team invites
   - **50+** - For bulk registration events
   
   **Notes (optional):**
   - Add recipient name, purpose, or any tracking info
   - Examples: "John Doe - Marketing", "Beta testers batch 3", "Conference attendees"

4. **Generate the Code**
   - Click "Generate New Code"
   - Code will appear in green box: `K7M9-P2N4-QW8X`
   - **IMPORTANT:** Copy this code immediately and share with the user
   - Code will also appear in the list below

5. **Share the Code**
   - Send via secure channel (email, Slack, etc.)
   - Instruct user to go to `/register` and enter the code
   - User must use code before expiration
   - Single-use codes become invalid after first successful registration

### Managing Existing Codes

**View Active Codes:**
- All generated codes appear in the table
- Green "Active" badge = code is valid and usable
- Red "Expired" badge = code has passed expiration time
- Usage counter shows uses remaining

**Revoke a Code:**
- Click the "Revoke" button next to any code
- Code will be deactivated immediately
- User will not be able to use it for registration
- Use this if code is compromised or no longer needed

**Check Code Status:**
- See creation date, creator, expiration date
- See usage count (how many times it's been used)
- See notes if any were added

---

## Implementation Checklist

Use this checklist to ensure complete implementation:

### Backend Changes

- [ ] Update `generate_auth_code()` in admin_ui.py
  - [ ] Add `request: Request` parameter
  - [ ] Add `auth_code_service: Annotated[AuthCodeService, Depends(get_auth_code_service)]` dependency
  - [ ] Parse form data for `expires_in_days`, `max_uses`, `notes`
  - [ ] Replace `secrets.token_urlsafe(32)` with `auth_code_service.create_code()`
  - [ ] Update HTML response to show expiration and usage info
  - [ ] Add error handling for invalid inputs

- [ ] Update `list_auth_codes_fragment()` in admin_ui.py
  - [ ] Add expiration date column to table
  - [ ] Add status badge (Active/Expired)
  - [ ] Add usage counter display (current_uses / max_uses)
  - [ ] Handle expired codes with visual indicator

### Frontend Changes

- [ ] Update auth_codes.html
  - [ ] Add form fields for `expires_in_days` (number input, default 7)
  - [ ] Add form field for `max_uses` (number input, default 1)
  - [ ] Add form field for `notes` (text input, optional)
  - [ ] Update button's `hx-include` to capture form values
  - [ ] Add input validation (min=1 for numeric fields)
  - [ ] Add help text for each field
  - [ ] Update table headers to show new columns

### Testing

- [ ] **Unit Tests** (already exist, ensure they still pass)
  - [ ] Run `pytest tests/unit_tests/auth/test_auth_code_generation.py`
  - [ ] Run `pytest tests/unit_tests/db/test_auth_code_service.py`

- [ ] **Integration Tests** (already exist, ensure they still pass)
  - [ ] Run `pytest tests/integration_tests/auth/test_admin_auth_codes.py`

- [ ] **Manual Testing**
  - [ ] Generate code with default settings (7 days, 1 use)
  - [ ] Verify code format is `XXXX-XXXX-XXXX`
  - [ ] Verify expiration date is ~7 days from now
  - [ ] Generate code with 1 day expiration
  - [ ] Generate code with no expiration (empty field)
  - [ ] Generate code with max_uses = 5
  - [ ] Verify codes appear in list with correct info
  - [ ] Verify usage counter updates after code is used
  - [ ] Verify expired codes show red badge
  - [ ] Test code revocation works

- [ ] **E2E Tests** (may need update)
  - [ ] Review admin.spec.ts
  - [ ] Update if needed to test new form fields

### Documentation

- [ ] This document created in `docs/10_instructions/12_authorization_code_workflow.md` ✅
- [ ] Update 04_user_registration_guide.md to reference this guide
- [ ] Add link to this guide in admin panel UI (optional)

---

## Verification & Testing

### Automated Testing

```bash
# Run all auth-related tests
pytest tests/unit_tests/auth/ -v
pytest tests/integration_tests/auth/ -v

# Run specific test files
pytest tests/unit_tests/auth/test_auth_code_generation.py -v
pytest tests/unit_tests/db/test_auth_code_service.py -v
pytest tests/integration_tests/auth/test_admin_auth_codes.py -v
```

### Manual Testing Scenarios

#### Scenario 1: Standard 7-Day Code
1. Log in as admin
2. Navigate to Auth Codes section
3. Set: expires_in_days = 7, max_uses = 1, notes = "Test user"
4. Click "Generate New Code"
5. **Verify:** Code format is `XXXX-XXXX-XXXX`
6. **Verify:** Expiration date is 7 days from now
7. **Verify:** Code appears in list with "Active" badge
8. **Verify:** Usage shows 0/1

#### Scenario 2: Multi-Use Code
1. Generate code with max_uses = 5
2. **Verify:** Code shows 0/5 usage
3. Register a user with this code
4. Return to admin panel
5. **Verify:** Usage shows 1/5
6. **Verify:** Code still shows "Active"

#### Scenario 3: No Expiration Code
1. Generate code with empty expires_in_days field
2. **Verify:** Code generated successfully
3. **Verify:** Expiration shows "Never" or "No expiration"
4. **Verify:** Code works for registration

#### Scenario 4: 1-Day Expiration Code
1. Generate code with expires_in_days = 1
2. **Verify:** Expiration date is ~24 hours from now
3. **Simulate expiration:** Update database `expires_at` to past timestamp
4. Reload admin page
5. **Verify:** Code shows "Expired" red badge
6. **Verify:** Code cannot be used for registration

#### Scenario 5: Code Revocation
1. Generate a code
2. Click "Revoke" button
3. **Verify:** Code status changes to inactive
4. **Verify:** Code cannot be used for registration
5. **Verify:** Clear error message to user attempting to use revoked code

### Database Verification

```sql
-- Check generated codes format
SELECT code, expires_at, max_uses, current_uses, is_active, created_at
FROM auth_codes
ORDER BY created_at DESC
LIMIT 10;

-- Verify code format (should be XXXX-XXXX-XXXX)
-- Code should be 14 characters including dashes

-- Verify expiration timestamps
SELECT 
    code,
    datetime(expires_at, 'unixepoch') as expiration_time,
    CASE 
        WHEN expires_at IS NULL THEN 'Never expires'
        WHEN expires_at > strftime('%s', 'now') THEN 'Active'
        ELSE 'Expired'
    END as status
FROM auth_codes
ORDER BY created_at DESC;
```

### Success Criteria

✅ **Fix is complete when:**
- Admin can generate codes in format `XXXX-XXXX-XXXX`
- Codes are properly stored with correct expiration timestamp
- Admin UI shows all form fields and they work correctly
- Generated codes appear immediately in the list
- Expiration dates display correctly in human-readable format
- Usage counters update correctly
- Expired codes show red badge
- All existing tests pass
- Manual test scenarios succeed

---

## Troubleshooting

### Issue: Still Getting Empty JSON

**Symptoms:** Click "Generate Code" → nothing happens or empty response

**Possible Causes:**
1. Backend code not updated properly
2. Missing `AuthCodeService` dependency
3. Form data not being parsed
4. Database connection issue

**Solution:**
```bash
# Check backend logs
tail -f logs/minutesiq.log

# Verify service layer works directly
pytest tests/unit_tests/db/test_auth_code_service.py -v

# Check if dependency injection is configured
grep -n "get_auth_code_service" src/minutes_iq/api/admin_ui.py
```

### Issue: Code Format Still Wrong

**Symptoms:** Generated code is long base64 string like `xY7aB3cD9wT5...`

**Cause:** Still using `secrets.token_urlsafe(32)` instead of service layer

**Solution:**
- Ensure line ~669 in `admin_ui.py` calls `auth_code_service.create_code()`
- Do NOT use `secrets.token_urlsafe()` directly

### Issue: Expiration Not Working

**Symptoms:** All codes show "No expiration" even when setting expires_in_days

**Possible Causes:**
1. Form data not being parsed
2. `expires_in_days` not passed to service layer
3. Timezone issues

**Debug:**
```python
# Add logging in generate_auth_code()
import logging
logger = logging.getLogger(__name__)

form_data = await request.form()
logger.info(f"Form data received: {dict(form_data)}")
expires_in_days = form_data.get("expires_in_days")
logger.info(f"Expires in days: {expires_in_days}, type: {type(expires_in_days)}")
```

**Check database:**
```sql
SELECT code, expires_at, datetime(expires_at, 'unixepoch') 
FROM auth_codes 
WHERE expires_at IS NOT NULL 
ORDER BY created_at DESC 
LIMIT 5;
```

### Issue: Form Fields Not Appearing

**Symptoms:** Admin UI still shows just a button

**Cause:** Frontend template not updated

**Solution:**
- Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
- Verify template file saved correctly
- Restart FastAPI server
- Check browser console for JavaScript errors

### Issue: Permission Denied

**Symptoms:** 403 Forbidden when accessing /admin/auth-codes

**Cause:** User doesn't have admin role

**Check user role:**
```sql
SELECT user_id, username, email, role_id 
FROM users 
WHERE user_id = <your_user_id>;
```

**Fix:** Update user to admin:
```sql
UPDATE users SET role_id = 1 WHERE user_id = <your_user_id>;
```

### Issue: Codes Not Appearing in List

**Symptoms:** Code generated but doesn't show in table below

**Possible Causes:**
1. HTMX swap not working correctly
2. List endpoint returning wrong format
3. JavaScript error

**Debug:**
- Open browser DevTools → Network tab
- Generate a code
- Check for `/api/admin/auth-codes/generate` request
- Check response format
- Look for HTMX errors in console

---

## Security Best Practices

### When to Use Time-Limited Codes

✅ **Use expiration for:**
- General user invitations (7 days recommended)
- Demo/trial accounts (1-3 days)
- Event-based registrations (duration of event)
- Temporary access grants
- External/unknown users

❌ **Consider no expiration for:**
- Permanent public registration (if applicable)
- Internal team members
- Long-running invitation campaigns

### Usage Limits

✅ **Single-use (max_uses = 1):**
- Individual user invitations
- Security-sensitive scenarios
- When you need to track exactly who was invited

✅ **Multi-use (max_uses > 1):**
- Team invitations
- Batch registrations
- Event attendees
- Open beta testing

### Code Sharing

✅ **Best Practices:**
- Share codes via secure channels (encrypted email, Slack DM)
- Include expiration information when sharing
- Keep track of who received which code (use notes field)
- Revoke codes if compromised

❌ **Avoid:**
- Posting codes on public websites or social media
- Sharing codes without expiration
- Reusing codes across multiple campaigns
- Sharing high-use-limit codes publicly

### Monitoring & Auditing

**Regular Checks:**
```sql
-- Check for expired unused codes
SELECT code, notes, datetime(expires_at, 'unixepoch') as expired_on
FROM auth_codes
WHERE expires_at < strftime('%s', 'now')
  AND is_active = 1
  AND current_uses = 0;

-- Revoke them
UPDATE auth_codes
SET is_active = 0
WHERE expires_at < strftime('%s', 'now')
  AND is_active = 1;
```

**Monthly Audit Questions:**
- Are there unused codes older than 30 days?
- Are there multi-use codes with suspicious usage patterns?
- Are there codes without expiration that should be revoked?

### Database Maintenance

**Clean up old codes periodically:**
```sql
-- Archive codes older than 90 days that were never used
-- (Production should have proper archival, not DELETE)
SELECT COUNT(*) FROM auth_codes 
WHERE created_at < strftime('%s', 'now', '-90 days')
  AND current_uses = 0;
```

---

## Related Documentation

- **Design:** Authorization Codes Design
- **Operations:** User Registration Guide
- **Security:** Security Model
- **API:** Auth Code API Routes (if documented)
- **Testing:** E2E Testing Instructions

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-19 | 1.0 | Initial documentation - problem identified, fix designed, admin guide created |

---

**Status:** 🟡 Awaiting Implementation

**Next Steps:**
1. Developer implements backend fix in `admin_ui.py`
2. Developer updates frontend template `auth_codes.html`
3. Run verification tests
4. Update user registration guide with references
5. Mark this document as ✅ Complete
```

This comprehensive document provides:
- **Technical implementation details** for the developer
- **Step-by-step admin user guide** for generating time-limited codes
- **Complete checklist** to track implementation progress
- **Thorough verification procedures** with test scenarios
- **Troubleshooting guide** for common issues
- **Security best practices** for safe code management

Save this as `docs/10_instructions/12_authorization_code_workflow.md` and you'll have everything needed to fix the issue and properly document the workflow!This comprehensive document provides:
- **Technical implementation details** for the developer
- **Step-by-step admin user guide** for generating time-limited codes
- **Complete checklist** to track implementation progress
- **Thorough verification procedures** with test scenarios
- **Troubleshooting guide** for common issues
- **Security best practices** for safe code management

Save this as `docs/10_instructions/12_authorization_code_workflow.md` and you'll have everything needed to fix the issue and properly document the workflow!