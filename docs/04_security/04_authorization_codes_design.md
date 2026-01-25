# Authorization Codes Design

**Audience:** Developers, security reviewers
**Purpose:** Document the authorization code system for controlled user registration

---

## Overview

The authorization code system prevents unauthorized self-registration by requiring users to possess a valid, admin-issued code before creating an account.

This ensures:
- Only explicitly authorized individuals can register
- Admin maintains control over who has access
- Codes can be time-limited and single-use
- Audit trail of who registered with which code

---

## Requirements

### Functional Requirements

1. **Admin Code Generation**
   - Admins can generate authorization codes
   - Codes are cryptographically secure (sufficient entropy)
   - Codes have optional expiration dates
   - Codes can be single-use or multi-use

2. **Code Validation**
   - Registration endpoint validates code before creating user
   - Expired codes are rejected
   - Used single-use codes are rejected
   - Invalid codes return clear error messages

3. **Code Management**
   - Admins can list all codes (active/expired/used)
   - Admins can revoke codes
   - Audit trail shows which user used which code

### Non-Functional Requirements

1. **Security**
   - Codes are not predictable or guessable
   - Codes are stored securely (no plaintext in logs)
   - Rate limiting prevents brute force attempts

2. **Usability**
   - Codes are easy to share (short, alphanumeric)
   - Clear feedback when code is invalid/expired
   - Codes are case-insensitive for user convenience

---

## Database Schema

### auth_codes Table

```sql
CREATE TABLE auth_codes (
    code_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,           -- The authorization code
    created_by INTEGER NOT NULL,         -- Admin who created it
    created_at INTEGER NOT NULL,         -- Unix timestamp
    expires_at INTEGER,                  -- Unix timestamp, NULL = never expires
    max_uses INTEGER DEFAULT 1,          -- How many times it can be used
    current_uses INTEGER DEFAULT 0,      -- How many times it's been used
    is_active INTEGER DEFAULT 1,         -- 1 = active, 0 = revoked
    notes TEXT,                          -- Optional admin notes
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE INDEX idx_auth_codes_code ON auth_codes(code);
CREATE INDEX idx_auth_codes_is_active ON auth_codes(is_active);
CREATE INDEX idx_auth_codes_expires_at ON auth_codes(expires_at);
```

### code_usage Table

```sql
CREATE TABLE code_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,            -- User who used the code
    used_at INTEGER NOT NULL,            -- Unix timestamp
    FOREIGN KEY (code_id) REFERENCES auth_codes(code_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_code_usage_code_id ON code_usage(code_id);
CREATE INDEX idx_code_usage_user_id ON code_usage(user_id);
```

---

## Code Format

Authorization codes follow this format:
- **Length:** 12 characters
- **Character set:** Uppercase letters and numbers (A-Z, 0-9)
- **Example:** `XK7M-9P2N-4QW8`
- **Grouping:** Hyphens every 4 characters for readability

### Code Generation Algorithm

```python
import secrets
import string

def generate_code() -> str:
    """Generate a secure 12-character authorization code."""
    alphabet = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(12))
    # Format with hyphens for readability
    return f"{code[0:4]}-{code[4:8]}-{code[8:12]}"
```

**Security Note:** Uses `secrets` module (cryptographically secure) rather than `random`.

---

## API Endpoints

### Admin Endpoints (Require Admin Role)

#### POST /admin/auth-codes
Create a new authorization code.

**Request:**
```json
{
  "expires_in_days": 7,      // Optional, null = never expires
  "max_uses": 1,              // Optional, default: 1
  "notes": "For John Doe"     // Optional
}
```

**Response:**
```json
{
  "code_id": 1,
  "code": "XK7M-9P2N-4QW8",
  "created_at": 1737820800,
  "expires_at": 1738425600,
  "max_uses": 1,
  "current_uses": 0,
  "is_active": true
}
```

#### GET /admin/auth-codes
List all authorization codes.

**Query Parameters:**
- `status`: "active", "expired", "used", "revoked", or "all" (default: "active")
- `limit`: Max results (default: 100)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "codes": [
    {
      "code_id": 1,
      "code": "XK7M-****-****",  // Masked for security
      "created_at": 1737820800,
      "expires_at": 1738425600,
      "max_uses": 1,
      "current_uses": 0,
      "is_active": true,
      "notes": "For John Doe"
    }
  ],
  "total": 1
}
```

#### DELETE /admin/auth-codes/{code_id}
Revoke an authorization code.

**Response:**
```json
{
  "message": "Authorization code revoked successfully",
  "code_id": 1
}
```

### Public Endpoint (Modified)

#### POST /auth/register
User registration (now requires auth code).

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securePassword123",
  "auth_code": "XK7M-9P2N-4QW8"  // NEW: Required field
}
```

**Response (Success):**
```json
{
  "user_id": 5,
  "username": "johndoe",
  "email": "john@example.com",
  "role_id": 2
}
```

**Response (Invalid Code):**
```json
{
  "detail": "Invalid or expired authorization code"
}
```

---

## Validation Logic

When a user attempts to register with a code:

1. **Normalize the code** (remove hyphens, convert to uppercase)
2. **Look up the code** in the database
3. **Validate:**
   - Code exists
   - Code is active (`is_active = 1`)
   - Code is not expired (`expires_at IS NULL OR expires_at > NOW()`)
   - Code has uses remaining (`current_uses < max_uses`)
4. **Create the user** (if validation passes)
5. **Record usage:**
   - Increment `current_uses` in `auth_codes`
   - Insert record into `code_usage`
6. **Return user data**

---

## Security Considerations

1. **Rate Limiting**
   - Limit registration attempts per IP (e.g., 5 attempts per hour)
   - Prevent brute force code guessing

2. **Code Masking**
   - When listing codes, mask part of the code (e.g., `XK7M-****-****`)
   - Full code only shown at creation time

3. **Audit Logging**
   - Log all code creation events
   - Log all code validation attempts (success and failure)
   - Track IP addresses and timestamps

4. **Code Expiration**
   - Recommend short expiration periods (7 days default)
   - Automatic cleanup of expired codes (optional)

---

## Admin Workflow

### Creating a Code for a New User

1. Admin logs into admin panel
2. Navigates to "Authorization Codes"
3. Clicks "Generate New Code"
4. Sets expiration (e.g., 7 days) and max uses (e.g., 1)
5. Adds notes: "For Jane Smith - Invited on 2026-01-25"
6. Copies code: `XK7M-9P2N-4QW8`
7. Shares code with Jane via secure channel (email, Slack, etc.)
8. Jane uses code to register
9. Admin sees code marked as "used"

### Revoking a Code

1. Admin views list of codes
2. Identifies unused code that should be revoked
3. Clicks "Revoke" button
4. Code is marked inactive and can no longer be used

---

## Future Enhancements (Not in Phase 3)

- **Code Groups:** Organize codes by department or campaign
- **Usage Analytics:** Track registration conversion rates
- **Email Integration:** Automatically send code via email
- **Invite Links:** Generate shareable registration URLs with embedded codes
- **Bulk Code Generation:** Create multiple codes at once

---

## Testing Strategy

### Unit Tests
- Code generation produces valid format
- Code validation logic (expired, used, revoked)
- Usage tracking increments correctly

### Integration Tests
- Registration succeeds with valid code
- Registration fails with invalid/expired/used code
- Admin can create and revoke codes

### Security Tests
- Rate limiting prevents brute force
- Codes are cryptographically secure
- Expired codes cannot be used

---

## Migration Path

Phase 3 implementation order:
1. Create database schema (migration)
2. Implement repository layer
3. Implement service layer
4. Add admin endpoints
5. Modify registration endpoint
6. Add comprehensive tests
7. Update documentation
